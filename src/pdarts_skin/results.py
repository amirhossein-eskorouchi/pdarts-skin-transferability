"""Loading and validating canonical publication-result records."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

PUBLICATION_PROVENANCE = "manuscript_reported_not_regenerated"


@dataclass(frozen=True)
class PublicationRecordSet:
    headline_results: tuple[Mapping[str, str], ...]
    architecture_comparisons: tuple[Mapping[str, str], ...]
    statistical_results: tuple[Mapping[str, str], ...]
    transfer_pvalues: tuple[Mapping[str, str], ...]


def load_csv_records(path: str | Path) -> tuple[dict[str, str], ...]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def require_unique(
    rows: Sequence[Mapping[str, str]],
    columns: Sequence[str],
    record_name: str,
) -> None:
    seen: set[tuple[str, ...]] = set()

    for row in rows:
        key = tuple(row.get(column, "").strip() for column in columns)

        if any(not value for value in key):
            raise ValueError(
                f"{record_name} contains an empty key component: {key}"
            )

        if key in seen:
            raise ValueError(
                f"{record_name} contains a duplicate key: {key}"
            )

        seen.add(key)


def require_publication_provenance(
    rows: Iterable[Mapping[str, str]],
    record_name: str,
) -> None:
    for row in rows:
        if row.get("provenance_status") != PUBLICATION_PROVENANCE:
            raise ValueError(
                f"{record_name} contains a noncanonical provenance status"
            )


def load_publication_record(
    directory: str | Path,
) -> PublicationRecordSet:
    root = Path(directory)

    records = PublicationRecordSet(
        headline_results=load_csv_records(
            root / "headline_results.csv"
        ),
        architecture_comparisons=load_csv_records(
            root / "architecture_comparison.csv"
        ),
        statistical_results=load_csv_records(
            root / "statistical_results.csv"
        ),
        transfer_pvalues=load_csv_records(
            root / "transfer_comparison_pvalues.csv"
        ),
    )

    require_unique(
        records.headline_results,
        ("result_id",),
        "headline results",
    )

    require_unique(
        records.architecture_comparisons,
        ("task", "target_dataset", "architecture"),
        "architecture comparisons",
    )

    require_unique(
        records.statistical_results,
        ("analysis_id",),
        "statistical results",
    )

    require_unique(
        records.transfer_pvalues,
        ("target_dataset", "evaluation_depth_m", "comparison"),
        "transfer-comparison p-values",
    )

    require_publication_provenance(
        records.headline_results,
        "headline results",
    )

    require_publication_provenance(
        records.architecture_comparisons,
        "architecture comparisons",
    )

    require_publication_provenance(
        records.statistical_results,
        "statistical results",
    )

    require_publication_provenance(
        records.transfer_pvalues,
        "transfer-comparison p-values",
    )

    return records


def numeric_value(
    row: Mapping[str, str],
    column: str,
) -> float:
    value = row.get(column, "").strip()

    if not value:
        raise ValueError(f"missing numeric value in column {column!r}")

    return float(value)


def best_by_value(
    rows: Iterable[Mapping[str, str]],
    column: str,
) -> Mapping[str, str]:
    materialized = tuple(rows)

    if not materialized:
        raise ValueError("cannot select a best result from no rows")

    return max(
        materialized,
        key=lambda row: numeric_value(row, column),
    )
