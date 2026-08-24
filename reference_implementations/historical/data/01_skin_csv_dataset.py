# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/01_skin_csv_dataset.py
# Original SHA-256: f7051fc49578082670f2efbc8c9433830d1a0fe60ba8e163c9a8abdf002c5780
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 10:54:48 2025

@author: original project author (workstation identifier redacted)
"""

# 01_skin_csv_dataset.py
# PyTorch Dataset for your split CSVs:
#   columns: path,label,class_name
#
# Works with your current split outputs:
#   S1_train.csv, S2_val.csv, S3_test.csv
#   T1_train.csv, T2_val.csv, T3_test.csv

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset
from PIL import Image


@dataclass(frozen=True)
class Sample:
    path: str
    label: int
    class_name: str


def read_split_csv(csv_path: str | Path) -> List[Sample]:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    samples: List[Sample] = []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"path", "label", "class_name"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"CSV must contain columns {sorted(required)}. "
                f"Found: {reader.fieldnames}"
            )
        for row in reader:
            p = row["path"]
            y = int(row["label"])
            c = row["class_name"]
            samples.append(Sample(path=p, label=y, class_name=c))

    if len(samples) == 0:
        raise RuntimeError(f"No rows found in CSV: {csv_path}")

    return samples


class SkinCSVImageDataset(Dataset):
    """
    Dataset that reads image paths/labels from a CSV.
    CSV columns: path,label,class_name

    Returns:
      image: Tensor (C,H,W) if transform provided, else PIL Image
      label: int
    """

    def __init__(
        self,
        csv_path: str | Path,
        transform: Optional[Callable] = None,
        return_path: bool = False,
        verify_files: bool = True,
    ):
        self.csv_path = Path(csv_path)
        self.samples = read_split_csv(self.csv_path)
        self.transform = transform
        self.return_path = return_path

        if verify_files:
            missing = [s.path for s in self.samples if not Path(s.path).exists()]
            if missing:
                show = "\n".join(missing[:10])
                raise FileNotFoundError(
                    f"{len(missing)} image files referenced in CSV do not exist.\n"
                    f"First 10 missing:\n{show}\n\n"
                    f"Tip: if you moved your dataset folder, regenerate splits or update paths."
                )

        # quick metadata
        self.num_classes = len({s.label for s in self.samples})

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        s = self.samples[idx]
        img_path = s.path

        # Always read as RGB (3-channel) for compatibility with P-DARTS CNN stem
        with Image.open(img_path) as im:
            im = im.convert("RGB")

        if self.transform is not None:
            im = self.transform(im)

        y = s.label
        if self.return_path:
            return im, y, img_path
        return im, y

    def class_distribution(self) -> Dict[int, int]:
        dist: Dict[int, int] = {}
        for s in self.samples:
            dist[s.label] = dist.get(s.label, 0) + 1
        return dist


# --------------------- OPTIONAL SIMPLE TRANSFORMS ---------------------
def build_basic_transforms(image_size: int = 32):
    """
    P-DARTS CIFAR defaults are 32x32.
    Your manuscript mentions resizing to CIFAR-equivalent.
    We'll keep it simple for now: Resize -> ToTensor.
    (We'll add augmentation + normalization later in the training script.)
    """
    try:
        import torchvision.transforms as T
    except ImportError as e:
        raise ImportError("torchvision is required for transforms. Install torchvision.") from e

    return T.Compose([
        T.Resize((image_size, image_size)),
        T.ToTensor(),
    ])


# --------------------------- SMOKE TEST ---------------------------
if __name__ == "__main__":
    # EDIT THIS PATH to one of your CSV splits to test quickly
    CSV = r"PROJECT_ROOT\output\splits\S1_train.csv"

    tfm = build_basic_transforms(image_size=32)
    ds = SkinCSVImageDataset(CSV, transform=tfm, return_path=True, verify_files=True)

    print("Loaded:", CSV)
    print("Num samples:", len(ds))
    print("Num classes:", ds.num_classes)
    print("Class dist:", ds.class_distribution())

    x, y, p = ds[0]
    print("Sample 0:")
    print(" path:", p)
    print(" label:", y)
    print(" tensor shape:", tuple(x.shape))
    print(" tensor dtype:", x.dtype)
    print(" tensor min/max:", float(x.min()), float(x.max()))
