# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/skin_csv_dataset.py
# Original SHA-256: d7f8ee22e2ce94c23fe9e784b3384ae4a03d4d329540918e33ab8e45340f669b
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
"""
skin_csv_dataset.py
====================

This module defines a simple PyTorch ``Dataset`` that reads image paths
and labels from a CSV file.  Each row in the CSV must contain the
columns ``path``, ``label`` and ``class_name``.  The dataset loads
images on demand using Pillow, applies a user‑supplied transform, and
returns a tuple ``(image, label)`` (or optionally ``(image, label, path)``).

It was adapted from ``01_skin_csv_dataset.py`` provided in the chat.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image
import torch
from torch.utils.data import Dataset

# Allowed image file extensions
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}


@dataclass(frozen=True)
class Sample:
    path: str
    label: int
    class_name: str


def read_split_csv(csv_path: str | Path) -> List[Sample]:
    """Read a split CSV and return a list of ``Sample`` records."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f'CSV not found: {csv_path}')
    samples: List[Sample] = []
    with csv_path.open('r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {'path', 'label', 'class_name'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f'CSV must contain columns {sorted(required)}; found {reader.fieldnames}')
        for row in reader:
            p = row['path']
            y = int(row['label'])
            c = row['class_name']
            samples.append(Sample(path=p, label=y, class_name=c))
    if not samples:
        raise RuntimeError(f'No rows found in CSV: {csv_path}')
    return samples


class SkinCSVImageDataset(Dataset):
    """
    PyTorch dataset for skin lesion images stored on disk, as listed in a
    CSV file.  Each item returns ``image`` and ``label``.  If
    ``return_path`` is True, the image path is also returned.
    """
    def __init__(
        self,
        csv_path: str | Path,
        transform: Optional[Callable] = None,
        return_path: bool = False,
        verify_files: bool = True,
    ) -> None:
        self.csv_path = Path(csv_path)
        self.samples = read_split_csv(self.csv_path)
        self.transform = transform
        self.return_path = return_path
        if verify_files:
            missing = [s.path for s in self.samples if not Path(s.path).exists()]
            if missing:
                msg = (f'{len(missing)} image files referenced in CSV do not exist.\n'
                       f'First missing: {missing[0]}\n')
                raise FileNotFoundError(msg)
        # number of classes inferred from the labels
        self.num_classes = len({s.label for s in self.samples})

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        s = self.samples[idx]
        img_path = Path(s.path)
        # Always open as RGB
        with Image.open(img_path) as im:
            im = im.convert('RGB')
        if self.transform is not None:
            im = self.transform(im)
        label = s.label
        if self.return_path:
            return im, label, str(img_path)
        return im, label

    def class_distribution(self) -> Dict[int, int]:
        dist: Dict[int, int] = {}
        for s in self.samples:
            dist[s.label] = dist.get(s.label, 0) + 1
        return dist
