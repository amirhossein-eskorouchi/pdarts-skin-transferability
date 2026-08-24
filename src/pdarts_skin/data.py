"""Portable image-manifest records and validation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Iterable, Mapping, Sequence

from .config import DatasetConfig

VALID_SPLITS = frozenset({"train", "validation", "test"})


@dataclass(frozen=True)
class ManifestRecord:
    sample_id: str
    image_path: str
    label_id: int
    patient_id: str
    dataset_id: str
    split: str
    split_mode: str


def read_manifest(path: str) -> list[ManifestRecord]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return [
            ManifestRecord(
                sample_id=row["sample_id"],
                image_path=row["image_path"],
                label_id=int(row["label_id"]),
                patient_id=row["patient_id"],
                dataset_id=row["dataset_id"],
                split=row["split"],
                split_mode=row["split_mode"],
            )
            for row in rows
        ]


def _is_absolute_portable_path(value: str) -> bool:
    return (
        PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
    )


def validate_manifest(
    records: Sequence[ManifestRecord],
    config: DatasetConfig,
) -> None:
    if not records:
        raise ValueError("manifest contains no records")

    sample_ids: set[str] = set()
    patient_splits: dict[str, str] = {}
    observed_modes: set[str] = set()

    for record in records:
        if not record.sample_id:
            raise ValueError("sample_id must not be empty")

        if record.sample_id in sample_ids:
            raise ValueError(f"duplicate sample_id: {record.sample_id}")

        sample_ids.add(record.sample_id)

        if record.dataset_id != config.dataset_id:
            raise ValueError(
                f"record dataset_id {record.dataset_id!r} does not match "
                f"{config.dataset_id!r}"
            )

        if record.label_id not in config.valid_label_ids:
            raise ValueError(f"invalid label_id: {record.label_id}")

        if record.split not in VALID_SPLITS:
            raise ValueError(f"invalid split: {record.split}")

        if record.split_mode not in config.supported_split_modes:
            raise ValueError(
                f"unsupported split mode for {config.dataset_id}: "
                f"{record.split_mode}"
            )

        if not record.image_path:
            raise ValueError("image_path must not be empty")

        if _is_absolute_portable_path(record.image_path):
            raise ValueError(
                f"image_path must be relative: {record.image_path}"
            )

        observed_modes.add(record.split_mode)

        if record.split_mode == "patient_grouped":
            if not record.patient_id:
                raise ValueError(
                    "patient_grouped records require patient_id"
                )

            previous_split = patient_splits.get(record.patient_id)

            if previous_split is not None and previous_split != record.split:
                raise ValueError(
                    f"patient {record.patient_id!r} crosses partitions"
                )

            patient_splits[record.patient_id] = record.split

    if len(observed_modes) != 1:
        raise ValueError(
            f"one manifest must use one split mode, "
            f"found {sorted(observed_modes)}"
        )


def records_by_split(
    records: Iterable[ManifestRecord],
) -> Mapping[str, tuple[ManifestRecord, ...]]:
    grouped: dict[str, list[ManifestRecord]] = {
        split: [] for split in sorted(VALID_SPLITS)
    }

    for record in records:
        grouped[record.split].append(record)

    return {
        split: tuple(items)
        for split, items in grouped.items()
    }
