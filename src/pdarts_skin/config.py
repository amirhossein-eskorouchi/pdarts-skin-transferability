"""Dataset-configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class DatasetConfig:
    dataset_id: str
    display_name: str
    label_codes: tuple[str, ...]
    supported_split_modes: frozenset[str]
    patient_group_required: bool
    raw: Mapping[str, Any]

    @property
    def valid_label_ids(self) -> frozenset[int]:
        return frozenset(range(len(self.label_codes)))


def _validate_raw_config(raw: Mapping[str, Any], source: Path) -> None:
    if raw.get("schema_version") != 1:
        raise ValueError(f"{source}: unsupported schema_version")

    if raw.get("data_in_repository") is not False:
        raise ValueError(f"{source}: data_in_repository must be false")

    dataset_id = raw.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError(f"{source}: missing dataset_id")

    labels = raw.get("label_schema")
    if not isinstance(labels, list) or not labels:
        raise ValueError(f"{source}: label_schema must be a nonempty list")

    label_ids = [item.get("label_id") for item in labels]
    if label_ids != list(range(len(labels))):
        raise ValueError(f"{source}: label IDs must be contiguous from zero")

    codes = [item.get("code") for item in labels]
    if any(not isinstance(code, str) or not code for code in codes):
        raise ValueError(f"{source}: every label requires a code")

    if len(set(codes)) != len(codes):
        raise ValueError(f"{source}: label codes must be unique")

    modes = raw.get("supported_split_modes")
    if not isinstance(modes, list) or not modes:
        raise ValueError(f"{source}: supported_split_modes must be nonempty")

    for record in raw.get("partition_records", []):
        calculated = (
            int(record["train"])
            + int(record["validation"])
            + int(record["test"])
        )
        if calculated != int(record["total"]):
            raise ValueError(f"{source}: inconsistent partition total")


def load_dataset_config(
    config_directory: str | Path,
    dataset_id: str,
) -> DatasetConfig:
    source = Path(config_directory) / f"{dataset_id}.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    _validate_raw_config(raw, source)

    if raw["dataset_id"] != dataset_id:
        raise ValueError(
            f"{source}: dataset_id {raw['dataset_id']!r} does not match filename"
        )

    return DatasetConfig(
        dataset_id=raw["dataset_id"],
        display_name=raw["display_name"],
        label_codes=tuple(
            item["code"] for item in raw["label_schema"]
        ),
        supported_split_modes=frozenset(raw["supported_split_modes"]),
        patient_group_required=bool(
            raw.get("patient_group_required", False)
        ),
        raw=raw,
    )
