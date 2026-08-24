"""Validate public dataset contracts without accessing research data."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "datasets"
EXAMPLE_MANIFEST = ROOT / "examples" / "manifests" / "image_manifest.example.csv"

EXPECTED_DATASETS = {"isic_2019", "pad_ufes_20", "dermamnist"}
ALLOWED_SPLITS = {"train", "validation", "test"}
ALLOWED_MODES = {"historical_image_level", "patient_grouped", "official_partition"}
ABSOLUTE_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|/)")


def fail(message: str) -> None:
    raise ValueError(message)


def validate_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))

    if config.get("schema_version") != 1:
        fail(f"{path}: unsupported schema version")

    dataset_id = config.get("dataset_id")
    if not dataset_id:
        fail(f"{path}: missing dataset_id")

    if config.get("data_in_repository") is not False:
        fail(f"{path}: data_in_repository must be false")

    labels = config.get("label_schema", [])
    label_ids = [row.get("label_id") for row in labels]
    if label_ids != list(range(6)):
        fail(f"{path}: expected ordered label IDs 0 through 5")

    if len({row.get("code") for row in labels}) != len(labels):
        fail(f"{path}: label codes must be unique")

    modes = set(config.get("supported_split_modes", []))
    if not modes or not modes <= ALLOWED_MODES:
        fail(f"{path}: invalid split modes")

    for record in config.get("partition_records", []):
        calculated = (
            int(record["train"])
            + int(record["validation"])
            + int(record["test"])
        )
        if calculated != int(record["total"]):
            fail(f"{path}: inconsistent partition total")

    return config


def validate_example(configs: dict[str, dict]) -> int:
    with EXAMPLE_MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    required = {
        "sample_id",
        "image_path",
        "label_id",
        "patient_id",
        "dataset_id",
        "split",
        "split_mode",
    }

    if not rows:
        fail("example manifest contains no rows")

    if set(rows[0]) != required:
        fail("example manifest columns do not match the public contract")

    sample_keys: set[tuple[str, str]] = set()
    patient_splits: dict[tuple[str, str], str] = {}

    for row in rows:
        dataset_id = row["dataset_id"]
        if dataset_id not in configs:
            fail(f"unknown dataset_id: {dataset_id}")

        if ABSOLUTE_PATH.match(row["image_path"]):
            fail(f"absolute image path is prohibited: {row['image_path']}")

        if row["split"] not in ALLOWED_SPLITS:
            fail(f"invalid split: {row['split']}")

        if row["split_mode"] not in ALLOWED_MODES:
            fail(f"invalid split mode: {row['split_mode']}")

        valid_labels = {
            int(item["label_id"])
            for item in configs[dataset_id]["label_schema"]
        }
        if int(row["label_id"]) not in valid_labels:
            fail(f"invalid label for {dataset_id}: {row['label_id']}")

        sample_key = (dataset_id, row["sample_id"])
        if sample_key in sample_keys:
            fail(f"duplicate sample key: {sample_key}")
        sample_keys.add(sample_key)

        if row["split_mode"] == "patient_grouped":
            if not row["patient_id"]:
                fail("patient_grouped row lacks patient_id")

            patient_key = (dataset_id, row["patient_id"])
            previous = patient_splits.get(patient_key)
            if previous is not None and previous != row["split"]:
                fail(f"patient crosses partitions: {patient_key}")
            patient_splits[patient_key] = row["split"]

    return len(rows)


def main() -> int:
    paths = sorted(CONFIG_DIR.glob("*.json"))
    configs = {
        config["dataset_id"]: config
        for config in (validate_config(path) for path in paths)
    }

    if set(configs) != EXPECTED_DATASETS:
        fail(
            f"expected datasets {sorted(EXPECTED_DATASETS)}, "
            f"found {sorted(configs)}"
        )

    if configs["isic_2019"]["class_5_semantics"] != "SCC":
        fail("ISIC class 5 must be SCC")

    if configs["pad_ufes_20"]["class_5_semantics"] != "SCC":
        fail("PAD class 5 must be SCC")

    if configs["dermamnist"]["class_5_semantics"] != "VASC":
        fail("DermaMNIST class 5 must be VASC")

    if "patient_grouped" not in configs["pad_ufes_20"]["supported_split_modes"]:
        fail("PAD must support patient_grouped mode")

    row_count = validate_example(configs)

    print(f"[OK] Dataset configurations: {len(configs)}")
    print(f"[OK] Fictional manifest rows: {row_count}")
    print("[OK] Partition totals are internally consistent.")
    print("[OK] Class-5 semantics are dataset-specific.")
    print("[OK] Patient-grouped manifest constraints passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
