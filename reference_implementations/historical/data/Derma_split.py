# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/Derma_split.py
# Original SHA-256: ddb6457198c71204f6652e86c180bf861d86fafde054fecba2d23b11e9642618
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 23 11:31:35 2025

@author: original project author (workstation identifier redacted)
"""

# -*- coding: utf-8 -*-
"""
00_make_splits_dermamnist_padaligned.py

Creates PAD-aligned 6-class DermaMNIST dataset:
- Reads the extracted PNGs + labels.csv from:
    dermamnist/train, dermamnist/val, dermamnist/test
- Re-splits ALL samples using the same scheme as your supervisor:
    20% test
    remaining 80% -> 70% train, 30% val
  (stratified by class)

- Keeps test split untouched (no NV downsampling in test)
- Downsamples NV in TRAIN and VAL only so:
    NV <= 1.5 * MEL  (per split)

- Aligns class order with PAD:
    0 AK   (Derma: AKIEC)
    1 BCC
    2 BKL
    3 MEL
    4 NV
    5 VASC  (Derma-only; PAD has SCC here)

Outputs:
1) Clean folder tree with copied images:
   OUT_DATASET_ROOT/
     train/AK/*.png ... train/VASC/*.png
     val/AK/*.png   ... val/VASC/*.png
     test/AK/*.png  ... test/VASC/*.png

2) CSV splits (same schema as your pipeline expects):
   OUT_SPLITS_DIR/
     D1_train.csv
     D2_val.csv
     D3_test.csv

3) A JSON summary for reproducibility.
"""


import csv
import json
import random
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# ------------------------- EDIT THESE PATHS -------------------------
DERMA_EXTRACT_ROOT = Path("PROJECT_ROOT/dataset/DermaMNIST/dermamnist")  # has train/val/test from extraction

# New clean reproducible dataset root (copied images go here)
OUT_DATASET_ROOT   = Path("PROJECT_ROOT/dataset/DermaMNIST/dermamnist/dermamnist_padaligned_224_6class")

# Where to save CSV split files (same style as your S/T splits)
OUT_SPLITS_DIR     = Path("PROJECT_ROOT/output/splits")
# -------------------------------------------------------------------


# Reproducibility
SEED = 0

# Supervisor split scheme
TEST_FRAC = 0.20
TRAIN_FRAC_OF_REST = 0.70
VAL_FRAC_OF_REST   = 0.30

# Your PAD-aligned class order (6 classes)
CLASS_NAMES = ["AK", "BCC", "BKL", "MEL", "NV", "VASC"]  # PAD has SCC at index 5; Derma uses VASC at index 5

# NV downsampling rule (applied to TRAIN and VAL only)
NV_MULT_OF_MEL = 1.5

# File extensions
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


# DermaMNIST 6-class IDs from our extraction script (already remapped):
# label_id_6 meanings (from MedMNIST):
# 0: AKIEC -> we call it "AK" for PAD alignment
# 1: BCC
# 2: BKL
# 3: MEL
# 4: NV
# 5: VASC
DERMA6_ID_TO_CLASS = {
    0: "AK",
    1: "BCC",
    2: "BKL",
    3: "MEL",
    4: "NV",
    5: "VASC",
}

CLASS_TO_IDX = {c: i for i, c in enumerate(CLASS_NAMES)}  # should match the list order


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def read_extracted_split(split_name: str) -> List[dict]:
    """
    Read dermamnist/<split_name>/labels.csv and return records:
      {src_path, label, class_name}
    where label is PAD-aligned int 0..5 and class_name is one of CLASS_NAMES.
    """
    split_dir = DERMA_EXTRACT_ROOT / split_name
    img_dir = split_dir / "images"
    csv_path = split_dir / "labels.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing labels.csv: {csv_path}")
    if not img_dir.exists():
        raise FileNotFoundError(f"Missing images dir: {img_dir}")

    records: List[dict] = []
    with csv_path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"filename", "label_id_6", "label_name"}
        if not required.issubset(set(r.fieldnames or [])):
            raise RuntimeError(f"{csv_path} missing required columns. Found: {r.fieldnames}")

        for row in r:
            filename = row["filename"]
            y6 = int(row["label_id_6"])

            if y6 not in DERMA6_ID_TO_CLASS:
                # Safety: ignore anything unexpected
                continue

            class_name = DERMA6_ID_TO_CLASS[y6]
            label = CLASS_TO_IDX[class_name]  # ensures PAD-aligned order

            src_path = img_dir / filename
            if not src_path.exists():
                # Some OS may have different casing; this should be rare
                raise FileNotFoundError(f"Image referenced in CSV not found: {src_path}")

            records.append({
                "src_path": str(src_path.resolve()),
                "label": label,
                "class_name": class_name,
            })

    return records


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
    for rec in records:
        by_class[rec["class_name"]].append(rec)

    train, val, test = [], [], []

    for c in class_names:
        items = by_class[c]
        rng.shuffle(items)

        n = len(items)
        n_test = int(round(n * TEST_FRAC))
        rest = n - n_test

        n_train = int(round(rest * TRAIN_FRAC_OF_REST))
        n_val = rest - n_train

        test_c = items[:n_test]
        rest_c = items[n_test:]
        train_c = rest_c[:n_train]
        val_c = rest_c[n_train:]

        assert len(train_c) + len(val_c) + len(test_c) == n

        train.extend(train_c)
        val.extend(val_c)
        test.extend(test_c)

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


def downsample_nv(records: List[dict], seed: int, split_name: str) -> List[dict]:
    """
    Apply NV <= 1.5 * MEL constraint within a split (train or val).
    Keeps other classes unchanged.
    """
    rng = random.Random(seed + (1 if split_name == "train" else 2))

    nv = [r for r in records if r["class_name"] == "NV"]
    mel = [r for r in records if r["class_name"] == "MEL"]
    others = [r for r in records if r["class_name"] != "NV"]

    max_nv = int(NV_MULT_OF_MEL * len(mel))

    if len(nv) <= max_nv:
        return records  # already fine

    rng.shuffle(nv)
    nv_kept = nv[:max_nv]
    out = others + nv_kept
    rng.shuffle(out)
    return out


def count_by_class(records: List[dict], class_names: List[str]) -> Dict[str, int]:
    counts = {c: 0 for c in class_names}
    for r in records:
        counts[r["class_name"]] += 1
    return counts


def copy_into_clean_folders(records: List[dict], split_name: str, out_root: Path) -> List[dict]:
    """
    Copy image files into:
      out_root/split_name/<class_name>/<filename>.png

    Returns new records with:
      {path,label,class_name}
    where 'path' points to the copied file.
    """
    out_records: List[dict] = []

    for idx, rec in enumerate(records):
        src = Path(rec["src_path"])
        class_name = rec["class_name"]
        label = rec["label"]

        # create destination folder
        dst_dir = out_root / split_name / class_name
        ensure_dir(dst_dir)

        # deterministic filename for reproducibility
        # include split, class, label, and a running index
        dst_name = f"{split_name}_{class_name}_y{label}_{idx:06d}{src.suffix.lower()}"
        dst = dst_dir / dst_name

        # copy
        shutil.copy2(src, dst)

        out_records.append({
            "path": str(dst.resolve()),
            "label": label,
            "class_name": class_name,
        })

    return out_records


def save_csv(records: List[dict], out_csv: Path) -> None:
    ensure_dir(out_csv.parent)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "label", "class_name"])
        w.writeheader()
        w.writerows(records)


def main():
    print("Reading extracted DermaMNIST splits...")
    rec_train = read_extracted_split("train")
    rec_val   = read_extracted_split("val")
    rec_test  = read_extracted_split("test")

    all_records = rec_train + rec_val + rec_test
    print(f"Total records (after DF removal/remap): {len(all_records)}")
    print("Original extracted counts:", count_by_class(all_records, CLASS_NAMES))

    # 1) Re-split ALL records using supervisor scheme
    print("\nCreating stratified 80/20 then 70/30 split (PAD-aligned classes)...")
    train, val, test = stratified_split(all_records, CLASS_NAMES, SEED)

    print("Pre-downsample counts:")
    print("  train:", count_by_class(train, CLASS_NAMES))
    print("  val  :", count_by_class(val, CLASS_NAMES))
    print("  test :", count_by_class(test, CLASS_NAMES))

    # 2) Downsample NV in train + val only; keep test untouched
    print("\nApplying NV <= 1.5×MEL (train + val only); test unchanged...")
    train_ds = downsample_nv(train, SEED, "train")
    val_ds   = downsample_nv(val, SEED, "val")
    test_ds  = test  # untouched

    print("Post-downsample counts:")
    print("  train:", count_by_class(train_ds, CLASS_NAMES))
    print("  val  :", count_by_class(val_ds, CLASS_NAMES))
    print("  test :", count_by_class(test_ds, CLASS_NAMES), " (untouched)")

    # 3) Copy into clean reproducible folder tree and write CSVs pointing to new paths
    print(f"\nCopying selected files into clean dataset folders:\n  {OUT_DATASET_ROOT}")
    ensure_dir(OUT_DATASET_ROOT)

    train_out = copy_into_clean_folders(train_ds, "train", OUT_DATASET_ROOT)
    val_out   = copy_into_clean_folders(val_ds,   "val",   OUT_DATASET_ROOT)
    test_out  = copy_into_clean_folders(test_ds,  "test",  OUT_DATASET_ROOT)

    # 4) Save CSVs (D1/D2/D3) like your S/T CSVs
    ensure_dir(OUT_SPLITS_DIR)
    d1 = OUT_SPLITS_DIR / "D1_train.csv"
    d2 = OUT_SPLITS_DIR / "D2_val.csv"
    d3 = OUT_SPLITS_DIR / "D3_test.csv"
    save_csv(train_out, d1)
    save_csv(val_out,   d2)
    save_csv(test_out,  d3)

    # 5) Save summary JSON
    summary = {
        "dataset": "DermaMNIST_224_PADAligned_6class",
        "source_extracted_root": str(DERMA_EXTRACT_ROOT.resolve()),
        "clean_dataset_root": str(OUT_DATASET_ROOT.resolve()),
        "seed": SEED,
        "class_names_padaligned": CLASS_NAMES,
        "class_to_idx": CLASS_TO_IDX,
        "derma6_id_to_class": DERMA6_ID_TO_CLASS,
        "split_scheme": {
            "test_frac": TEST_FRAC,
            "train_frac_of_rest": TRAIN_FRAC_OF_REST,
            "val_frac_of_rest": VAL_FRAC_OF_REST,
        },
        "nv_downsample_rule": {
            "applied_to": ["train", "val"],
            "test_untouched": True,
            "nv_max": f"{NV_MULT_OF_MEL} * MEL (per split)",
        },
        "counts": {
            "all_records": len(all_records),
            "train": len(train_out),
            "val": len(val_out),
            "test": len(test_out),
            "train_by_class": count_by_class(train_out, CLASS_NAMES),
            "val_by_class": count_by_class(val_out, CLASS_NAMES),
            "test_by_class": count_by_class(test_out, CLASS_NAMES),
        }
    }

    summary_path = OUT_SPLITS_DIR / "DermaMNIST_PADAligned_6class_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nSaved:")
    print(f"  Clean dataset root: {OUT_DATASET_ROOT}")
    print(f"  {d1}")
    print(f"  {d2}")
    print(f"  {d3}")
    print(f"  {summary_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
