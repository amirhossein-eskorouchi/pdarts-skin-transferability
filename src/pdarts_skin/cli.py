"""Command-line interface for portable manifest validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_dataset_config
from .data import read_manifest, validate_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a P-DARTS skin-lesion image manifest."
        )
    )

    parser.add_argument(
        "manifest",
        type=Path,
    )

    parser.add_argument(
        "--dataset-id",
        required=True,
    )

    parser.add_argument(
        "--config-directory",
        type=Path,
        default=Path("configs/datasets"),
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    config = load_dataset_config(
        args.config_directory,
        args.dataset_id,
    )

    records = read_manifest(
        str(args.manifest)
    )

    validate_manifest(
        records,
        config,
    )

    print(f"[OK] Dataset: {config.dataset_id}")
    print(f"[OK] Manifest records: {len(records)}")
    print(f"[OK] Split mode: {records[0].split_mode}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
