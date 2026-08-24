# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/splits.py
# Original SHA-256: 2dc6bea51e05b587ed5df858049234858f986c0d9618942dbcc03323a4b81827
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 10:47:09 2025

@author: original project author (workstation identifier redacted)
"""

# 00_make_splits_skin.py
# Creates fixed CSV splits for:
#   ISIC-2019 -> S1(train), S2(val), S3(test)
#   PAD-UFES-20 -> T1(train), T2(val), T3(test)
#
# Split scheme (from paper Figure 4):
#   20% test
#   remaining 80% -> 70% train, 30% val
#   => overall: train=56%, val=24%, test=20%

from __future__ import annotations
import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

# ------------------------- EDIT THESE PATHS -------------------------
# Your folder-per-class structure (from your screenshots) is compatible with this script.
ISIC_ROOT = Path("PROJECT_ROOT/dataset/ISIC")  # contains AK,BCC,BKL,MEL,NV,SCC
PAD_ROOT  = Path("PROJECT_ROOT/dataset/PADUFES20/images")  # contains AK,BCC,BKL,MEL,NV,SCC

OUT_DIR   = Path("PROJECT_ROOT/output/splits")

# Classes to keep (must match folder names)
CLASS_NAMES = ["AK", "BCC", "BKL", "MEL", "NV", "SCC"]

# Reproducibility
SEED = 0

# Split params (match Figure 4 logic)
TEST_FRAC = 0.20              # 20% test
TRAIN_FRAC_OF_REST = 0.70     # of remaining 80%
VAL_FRAC_OF_REST   = 0.30     # of remaining 80%

# File extensions to include
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
# -------------------------------------------------------------------


def _list_images_in_class(root: Path, class_name: str) -> List[Path]:
    """Recursively list image files under root/class_name."""
    class_dir = root / class_name
    if not class_dir.exists():
        raise FileNotFoundError(f"Missing class folder: {class_dir}")

    files = []
    for p in class_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            files.append(p)

    if len(files) == 0:
        raise RuntimeError(f"No images found in: {class_dir}")

    return sorted(files)


def collect_records(root: Path, class_names: List[str]) -> Tuple[List[dict], Dict[str, int]]:
    """
    Collect records:
      {path, label, class_name}
    Returns: (records, class_to_idx)
    """
    class_to_idx = {c: i for i, c in enumerate(class_names)}
    records: List[dict] = []

    for c in class_names:
        imgs = _list_images_in_class(root, c)
        for p in imgs:
            records.append({
                "path": str(p.resolve()),
                "label": class_to_idx[c],
                "class_name": c,
            })
    return records, class_to_idx


def stratified_split(records: List[dict], class_names: List[str], seed: int) -> Tuple[List[dict], List[dict], List[dict]]:
    """
    Stratified split by class:
      test = TEST_FRAC
      rest = 1 - TEST_FRAC
      train = TRAIN_FRAC_OF_REST of rest
      val = VAL_FRAC_OF_REST of rest
    """
    rng = random.Random(seed)

    by_class: Dict[str, List[dict]] = {c: [] for c in class_names}
    for r in records:
        by_class[r["class_name"]].append(r)

    train, val, test = [], [], []

    for c in class_names:
        items = by_class[c]
        rng.shuffle(items)

        n = len(items)
        n_test = int(round(n * TEST_FRAC))
        rest = n - n_test

        n_train = int(round(rest * TRAIN_FRAC_OF_REST))
        n_val = rest - n_train  # whatever remains

        test_c = items[:n_test]
        rest_c = items[n_test:]
        train_c = rest_c[:n_train]
        val_c = rest_c[n_train:]

        # sanity
        assert len(train_c) + len(val_c) + len(test_c) == n

        train.extend(train_c)
        val.extend(val_c)
        test.extend(test_c)

    # Shuffle combined splits (optional but nice)
    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)

    return train, val, test


def save_csv(records: List[dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "label", "class_name"])
        w.writeheader()
        w.writerows(records)


def count_by_class(records: List[dict], class_names: List[str]) -> Dict[str, int]:
    counts = {c: 0 for c in class_names}
    for r in records:
        counts[r["class_name"]] += 1
    return counts


def run_one_dataset(name: str, root: Path, prefix: str) -> None:
    print(f"\n=== {name} ===")
    print(f"Root: {root}")

    records, class_to_idx = collect_records(root, CLASS_NAMES)
    train, val, test = stratified_split(records, CLASS_NAMES, SEED)

    # Save
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_csv(train, OUT_DIR / f"{prefix}1_train.csv")
    save_csv(val,   OUT_DIR / f"{prefix}2_val.csv")
    save_csv(test,  OUT_DIR / f"{prefix}3_test.csv")

    # Summary
    summary = {
        "dataset": name,
        "root": str(root.resolve()),
        "seed": SEED,
        "class_names": CLASS_NAMES,
        "class_to_idx": class_to_idx,
        "counts": {
            "total": len(records),
            "train": len(train),
            "val": len(val),
            "test": len(test),
            "train_by_class": count_by_class(train, CLASS_NAMES),
            "val_by_class": count_by_class(val, CLASS_NAMES),
            "test_by_class": count_by_class(test, CLASS_NAMES),
        },
        "split_scheme": {
            "test_frac": TEST_FRAC,
            "train_frac_of_rest": TRAIN_FRAC_OF_REST,
            "val_frac_of_rest": VAL_FRAC_OF_REST,
            "overall_expected": {
                "train": (1.0 - TEST_FRAC) * TRAIN_FRAC_OF_REST,
                "val":   (1.0 - TEST_FRAC) * VAL_FRAC_OF_REST,
                "test":  TEST_FRAC,
            }
        }
    }

    with (OUT_DIR / f"{name}_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Saved:")
    print(f"  {OUT_DIR / f'{prefix}1_train.csv'}")
    print(f"  {OUT_DIR / f'{prefix}2_val.csv'}")
    print(f"  {OUT_DIR / f'{prefix}3_test.csv'}")
    print(f"  {OUT_DIR / f'{name}_summary.json'}")
    print("Counts:", summary["counts"])


if __name__ == "__main__":
    # Source dataset splits: S1/S2/S3
    run_one_dataset("ISIC_2019", ISIC_ROOT, prefix="S")

    # Target dataset splits: T1/T2/T3
    run_one_dataset("PAD_UFES_20", PAD_ROOT, prefix="T")

    print("\nDone. Next step after this: build a Dataset class that reads these CSVs and plug it into train_search.py.")
