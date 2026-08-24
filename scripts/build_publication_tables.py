"""Build deterministic Markdown tables from canonical result CSV files."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "results" / "publication_record"
TABLE_ROOT = RESULT_ROOT / "tables"

TABLES = (
    (
        "headline_results.csv",
        "headline-results.md",
        "Headline publication results",
        (
            "result_id",
            "task",
            "target_dataset",
            "evaluation_depth_m",
            "resolution",
            "metric",
            "value_percent",
            "dispersion",
            "aggregation",
            "publication_location",
        ),
    ),
    (
        "architecture_comparison.csv",
        "architecture-comparison.md",
        "Architecture comparison",
        (
            "task",
            "target_dataset",
            "architecture",
            "training_initialization",
            "accuracy_percent",
            "publication_location",
        ),
    ),
    (
        "statistical_results.csv",
        "statistical-results.md",
        "Statistical results",
        (
            "analysis_id",
            "analysis_type",
            "method_or_target",
            "resolution",
            "comparison",
            "n",
            "estimate",
            "dispersion",
            "median",
            "p_value",
            "effect_size",
            "publication_location",
        ),
    ),
    (
        "transfer_comparison_pvalues.csv",
        "transfer-comparison-pvalues.md",
        "Transfer-comparison p-values",
        (
            "target_dataset",
            "evaluation_depth_m",
            "comparison",
            "test",
            "p_value",
            "publication_location",
        ),
    ),
)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def cell(value: object) -> str:
    return str(value).replace("|", r"\|").replace("\n", " ").replace("\r", " ")


def render_table(
    title: str,
    source_name: str,
    rows: Iterable[dict[str, str]],
    columns: Sequence[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        (
            "_Generated from "
            f"`results/publication_record/{source_name}`. "
            "Do not edit manually._"
        ),
        "",
        "| " + " | ".join(cell(column) for column in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(cell(row.get(column, "")) for column in columns)
            + " |"
        )

    return "\n".join(lines) + "\n"


def build(check: bool) -> None:
    TABLE_ROOT.mkdir(parents=True, exist_ok=True)
    mismatches: list[str] = []

    for source_name, output_name, title, columns in TABLES:
        expected = render_table(
            title,
            source_name,
            load_rows(RESULT_ROOT / source_name),
            columns,
        )

        destination = TABLE_ROOT / output_name

        if check:
            if not destination.exists():
                mismatches.append(f"missing: {destination}")
            elif destination.read_text(encoding="utf-8") != expected:
                mismatches.append(f"out of date: {destination}")
        else:
            destination.write_text(expected, encoding="utf-8")

    if mismatches:
        raise ValueError("; ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if committed tables differ from canonical CSV files.",
    )
    args = parser.parse_args()

    build(check=args.check)

    if args.check:
        print("[OK] Publication Markdown tables are current.")
    else:
        print("[OK] Publication Markdown tables generated.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
