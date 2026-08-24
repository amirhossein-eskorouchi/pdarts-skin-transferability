"""Deterministic patient-group assignment and leakage checks."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Iterable, Sequence

from .data import ManifestRecord, VALID_SPLITS


def _validate_ratios(
    ratios: Sequence[float],
) -> tuple[float, float, float]:
    if len(ratios) != 3:
        raise ValueError(
            "ratios must contain train, validation, and test"
        )

    normalized = tuple(float(value) for value in ratios)

    if any(value <= 0 for value in normalized):
        raise ValueError("all split ratios must be positive")

    if abs(sum(normalized) - 1.0) > 1e-9:
        raise ValueError("split ratios must sum to 1.0")

    return normalized


def _patient_fraction(patient_id: str, seed: int) -> float:
    payload = f"{seed}:{patient_id}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    integer = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )
    return integer / float(2**64)


def assign_patient_grouped(
    records: Sequence[ManifestRecord],
    *,
    seed: int,
    ratios: Sequence[float] = (0.56, 0.24, 0.20),
) -> list[ManifestRecord]:
    """Assign patients deterministically without crossing partitions.

    This baseline assignment is deterministic but not class-stratified.
    Class coverage must be evaluated after assignment.
    """

    train_ratio, validation_ratio, _ = _validate_ratios(ratios)
    train_boundary = train_ratio
    validation_boundary = train_ratio + validation_ratio

    patient_assignments: dict[str, str] = {}
    output: list[ManifestRecord] = []

    for record in records:
        if not record.patient_id:
            raise ValueError(
                "patient_grouped splitting requires patient_id"
            )

        if record.patient_id not in patient_assignments:
            fraction = _patient_fraction(record.patient_id, seed)

            if fraction < train_boundary:
                split = "train"
            elif fraction < validation_boundary:
                split = "validation"
            else:
                split = "test"

            patient_assignments[record.patient_id] = split

        output.append(
            replace(
                record,
                split=patient_assignments[record.patient_id],
                split_mode="patient_grouped",
            )
        )

    validate_patient_isolation(output)
    return output


def validate_patient_isolation(
    records: Iterable[ManifestRecord],
) -> None:
    patient_splits: dict[str, str] = {}

    for record in records:
        if record.split not in VALID_SPLITS:
            raise ValueError(f"invalid split: {record.split}")

        if not record.patient_id:
            raise ValueError(
                "patient_id is required for isolation validation"
            )

        previous = patient_splits.get(record.patient_id)

        if previous is not None and previous != record.split:
            raise ValueError(
                f"patient {record.patient_id!r} occurs in "
                f"{previous!r} and {record.split!r}"
            )

        patient_splits[record.patient_id] = record.split
