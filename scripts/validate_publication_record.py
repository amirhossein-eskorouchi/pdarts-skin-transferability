"""Validate the canonical manuscript-reported result record."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "results" / "publication_record"

sys.path.insert(0, str(ROOT / "src"))

from pdarts_skin.results import load_publication_record


EXPECTED_COUNTS = {
    "headline_results": 10,
    "architecture_comparisons": 12,
    "statistical_results": 17,
    "transfer_pvalues": 12,
}


def fail(message: str) -> None:
    raise ValueError(message)


def find_headline(records, result_id: str):
    matches = [
        row
        for row in records.headline_results
        if row["result_id"] == result_id
    ]

    if len(matches) != 1:
        fail(f"expected one headline record for {result_id}")

    return matches[0]


def main() -> int:
    records = load_publication_record(RESULT_ROOT)

    for field, expected in EXPECTED_COUNTS.items():
        actual = len(getattr(records, field))

        if actual != expected:
            fail(f"{field}: expected {expected}, found {actual}")

    expected_ids = {
        f"HR-{number:03d}"
        for number in range(1, 11)
    }

    actual_ids = {
        row["result_id"]
        for row in records.headline_results
    }

    if actual_ids != expected_ids:
        fail("headline result IDs are incomplete")

    expected_headlines = {
        "HR-001": ("PAD-UFES-20", "62.32"),
        "HR-002": ("PAD-UFES-20", "63.70"),
        "HR-005": ("PAD-UFES-20", "97.71"),
        "HR-008": ("DermaMNIST", "79.48"),
        "HR-010": ("PAD-UFES-20", "69.06"),
    }

    for result_id, (dataset, value) in expected_headlines.items():
        row = find_headline(records, result_id)

        if row["target_dataset"] != dataset:
            fail(f"{result_id}: target dataset changed")

        if row["value_percent"] != value:
            fail(f"{result_id}: reported value changed")

    publication_root_text = " ".join(
        str(path)
        for path in RESULT_ROOT.iterdir()
    )

    if "reproduction" in publication_root_text.lower():
        fail("reproduction output entered publication_record")

    print("[OK] Headline results: 10")
    print("[OK] Architecture comparisons: 12")
    print("[OK] Statistical results: 17")
    print("[OK] Transfer-comparison p-values: 12")
    print("[OK] Canonical provenance status passed.")
    print("[OK] Key headline values passed.")
    print("[OK] Publication and reproduction namespaces remain separate.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
