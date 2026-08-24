#!/usr/bin/env python3
"""Create a read-only inventory of the original P-DARTS source archive.

This script does not extract, edit, move, or delete archive contents.
It records archive identity, file counts, extensions, sizes, and paths
for provenance review before files are selected for the public
repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LARGE_FILE_THRESHOLD = 5 * 1024 * 1024

SENSITIVE_PATH_TOKENS = (
    "c:\\users\\",
    "d:\\",
    "e:\\",
    "f:\\",
    "/home/",
    "/data/home/",
    "ae1028",
)

REVIEW_EXTENSIONS = {
    ".ckpt",
    ".csv",
    ".doc",
    ".docx",
    ".h5",
    ".hdf5",
    ".json",
    ".log",
    ".npy",
    ".npz",
    ".onnx",
    ".pdf",
    ".pem",
    ".pkl",
    ".ppt",
    ".pptx",
    ".pt",
    ".pth",
    ".pyc",
    ".zip",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def normalize_archive_path(name: str) -> str:
    return name.replace("\\", "/")


def classify_entry(name: str, size: int) -> list[str]:
    normalized = normalize_archive_path(name)
    lowered = normalized.lower()
    suffix = Path(normalized).suffix.lower()
    reasons: list[str] = []

    if suffix in REVIEW_EXTENSIONS:
        reasons.append(f"review_extension:{suffix}")

    if size >= LARGE_FILE_THRESHOLD:
        reasons.append("large_file")

    if "__pycache__/" in lowered or suffix == ".pyc":
        reasons.append("generated_python_cache")

    if any(token in lowered for token in SENSITIVE_PATH_TOKENS):
        reasons.append("workstation_or_user_path")

    if "/output/" in lowered or "/outputs/" in lowered:
        reasons.append("generated_or_historical_output")

    if "/dataset/" in lowered or "/datasets/" in lowered:
        reasons.append("dataset_material")

    return reasons


def build_inventory(archive_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    extension_counts: Counter[str] = Counter()
    top_level_counts: Counter[str] = Counter()
    total_uncompressed = 0
    file_count = 0
    directory_count = 0

    with zipfile.ZipFile(archive_path, "r") as archive:
        bad_member = archive.testzip()

        if bad_member is not None:
            raise RuntimeError(
                f"Archive integrity test failed at member: {bad_member}"
            )

        for info in archive.infolist():
            normalized = normalize_archive_path(info.filename)

            if info.is_dir():
                directory_count += 1
                continue

            file_count += 1
            total_uncompressed += info.file_size

            relative_parts = [
                part for part in normalized.split("/") if part
            ]
            top_level = (
                relative_parts[1]
                if len(relative_parts) > 1
                else relative_parts[0]
            )

            suffix = Path(normalized).suffix.lower() or "[no_extension]"
            extension_counts[suffix] += 1
            top_level_counts[top_level] += 1

            reasons = classify_entry(normalized, info.file_size)

            rows.append(
                {
                    "archive_path": normalized,
                    "uncompressed_bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "extension": suffix,
                    "crc32": f"{info.CRC:08x}",
                    "review_required": bool(reasons),
                    "review_reasons": ";".join(reasons),
                }
            )

    rows.sort(key=lambda row: row["archive_path"].lower())

    summary: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_name": archive_path.name,
        "archive_size_bytes": archive_path.stat().st_size,
        "archive_sha256": sha256_file(archive_path),
        "archive_integrity": "PASS",
        "file_count": file_count,
        "directory_count": directory_count,
        "total_uncompressed_bytes": total_uncompressed,
        "review_required_count": sum(
            1 for row in rows if row["review_required"]
        ),
        "extension_counts": dict(sorted(extension_counts.items())),
        "top_level_counts": dict(sorted(top_level_counts.items())),
    }

    return summary, rows


def write_outputs(
    output_directory: Path,
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)

    summary_path = output_directory / "source_archive_summary.json"
    inventory_path = output_directory / "source_archive_inventory.csv"

    summary_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    fieldnames = [
        "archive_path",
        "uncompressed_bytes",
        "compressed_bytes",
        "extension",
        "crc32",
        "review_required",
        "review_reasons",
    ]

    with inventory_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Summary:   {summary_path}")
    print(f"[OK] Inventory: {inventory_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit the original P-DARTS ZIP archive without extracting it."
    )
    parser.add_argument(
        "archive",
        type=Path,
        help="Path to the original P-DARTS ZIP archive.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/inventory/generated"),
        help="Directory for generated audit records.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive_path = args.archive.expanduser().resolve()

    if not archive_path.exists():
        print(
            f"[ERROR] Archive not found: {archive_path}",
            file=sys.stderr,
        )
        return 1

    if not archive_path.is_file():
        print(
            f"[ERROR] Archive path is not a file: {archive_path}",
            file=sys.stderr,
        )
        return 1

    if archive_path.suffix.lower() != ".zip":
        print(
            f"[ERROR] Expected a ZIP archive: {archive_path}",
            file=sys.stderr,
        )
        return 1

    try:
        summary, rows = build_inventory(archive_path)
        write_outputs(args.output_dir, summary, rows)
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print()
    print("[OK] Archive integrity passed.")
    print(f"[OK] Files inventoried: {summary['file_count']}")
    print(
        "[OK] Review-required entries: "
        f"{summary['review_required_count']}"
    )
    print(f"[OK] SHA-256: {summary['archive_sha256']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())