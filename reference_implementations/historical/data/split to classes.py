# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/split to classes.py
# Original SHA-256: ce8298ca4c4e4a2c75d73cb8bb7d892dd46e54008a96f9fa3edab49bbb271997
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 16 18:26:14 2025

@author: original project author (workstation identifier redacted)
"""

# -*- coding: utf-8 -*-
import os
import shutil
import pandas as pd

# -------------------- YOUR PATHS (exactly as you gave) --------------------
IMAGE_DIR = r"PROJECT_ROOT\dataset\PADUFES20\images\imgs_part_1"
META_CSV  = r"PROJECT_ROOT\dataset\PADUFES20\images\metadata.csv"
OUT_DIR   = r"PROJECT_ROOT\dataset\PADUFES20\images\images based on class"

# -------------------- Class mapping (like your first attachment) ----------
LABEL_MAP_6CLS = {
    "ACK": "AK",
    "SEK": "BKL",
    "NEV": "NV",
    "BOD": "SCC",
    "SCC": "SCC",
    "BCC": "BCC",
    "MEL": "MEL",
}

IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

# -------------------- Load metadata --------------------------------------
meta = pd.read_csv(META_CSV)

# Find the column in metadata that stores the image filename/id
candidate_cols = ["img_id", "image_id", "image", "filename", "file", "img"]
img_col = next((c for c in candidate_cols if c in meta.columns), None)
if img_col is None:
    raise ValueError(
        f"Could not find an image-name column in metadata.csv. "
        f"Looked for: {candidate_cols}. Columns found: {list(meta.columns)}"
    )

# Ensure required columns exist
for c in ["patient_id", "diagnostic"]:
    if c not in meta.columns:
        raise ValueError(f"metadata.csv is missing required column: {c}")

# Normalize diagnostic + map to 6 classes
meta["diagnostic_norm"] = meta["diagnostic"].astype(str).str.strip().str.upper()
meta["class_6"] = meta["diagnostic_norm"].map(LABEL_MAP_6CLS)

# Build fast lookup from filename (and stem) -> row
# We support metadata having filename with extension OR without extension
meta[img_col] = meta[img_col].astype(str).str.strip()
meta["img_name_full"] = meta[img_col]
meta["img_name_stem"] = meta[img_col].apply(lambda x: os.path.splitext(x)[0])

lookup_by_full = {}
lookup_by_stem = {}

for _, r in meta.iterrows():
    lookup_by_full.setdefault(r["img_name_full"], []).append(r)
    lookup_by_stem.setdefault(r["img_name_stem"], []).append(r)

# -------------------- Split images into class folders ---------------------
os.makedirs(OUT_DIR, exist_ok=True)

copied, missing_in_meta, unknown_diag, skipped_nonimage = 0, 0, 0, 0

for fname in os.listdir(IMAGE_DIR):
    src = os.path.join(IMAGE_DIR, fname)
    if not os.path.isfile(src):
        continue

    ext = os.path.splitext(fname)[1].lower()
    if ext not in IMG_EXTS:
        skipped_nonimage += 1
        continue

    stem = os.path.splitext(fname)[0]

    rows = lookup_by_full.get(fname) or lookup_by_stem.get(stem)
    if not rows:
        missing_in_meta += 1
        continue

    # if multiple rows match, just take the first
    row = rows[0]

    cls = row["class_6"]
    if pd.isna(cls):
        unknown_diag += 1
        continue

    dst_dir = os.path.join(OUT_DIR, cls)
    os.makedirs(dst_dir, exist_ok=True)

    dst = os.path.join(dst_dir, fname)
    shutil.copy2(src, dst)   # copy (safe). If you want MOVE, replace with shutil.move(src, dst)
    copied += 1

print("DONE.")
print("Copied images:", copied)
print("Images missing in metadata:", missing_in_meta)
print("Images with diagnostic not in mapping (skipped):", unknown_diag)
print("Non-image files skipped:", skipped_nonimage)

# Optional: save a small report (what exists in imgs_part_1 and its mapped class)
report_rows = []
for fname in os.listdir(IMAGE_DIR):
    ext = os.path.splitext(fname)[1].lower()
    if ext not in IMG_EXTS:
        continue
    stem = os.path.splitext(fname)[0]
    rows = lookup_by_full.get(fname) or lookup_by_stem.get(stem)
    if not rows:
        report_rows.append({"filename": fname, "status": "missing_in_metadata"})
    else:
        r = rows[0]
        report_rows.append({
            "filename": fname,
            "patient_id": r["patient_id"],
            "diagnostic": r["diagnostic"],
            "mapped_class": r["class_6"],
            "status": "ok" if pd.notna(r["class_6"]) else "diagnostic_not_mapped"
        })

report = pd.DataFrame(report_rows)
report.to_csv(os.path.join(OUT_DIR, "split_report_imgs_part_1.csv"), index=False)
print("Report saved to:", os.path.join(OUT_DIR, "split_report_imgs_part_1.csv"))
