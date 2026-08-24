import unittest
from pathlib import Path

from pdarts_skin.results import (
    best_by_value,
    load_publication_record,
    numeric_value,
)


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "results" / "publication_record"


class PublicationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_publication_record(RESULT_ROOT)

    def test_record_counts(self):
        self.assertEqual(
            len(self.records.headline_results),
            10,
        )
        self.assertEqual(
            len(self.records.architecture_comparisons),
            12,
        )
        self.assertEqual(
            len(self.records.statistical_results),
            17,
        )
        self.assertEqual(
            len(self.records.transfer_pvalues),
            12,
        )

    def test_best_binary_architecture_accuracy(self):
        rows = [
            row
            for row in self.records.architecture_comparisons
            if row["task"] == "binary"
        ]

        best = best_by_value(
            rows,
            "accuracy_percent",
        )

        self.assertEqual(
            best["architecture"],
            "P-DARTS6",
        )

        self.assertAlmostEqual(
            numeric_value(best, "accuracy_percent"),
            97.71,
        )

    def test_headline_ids_are_unique(self):
        identifiers = [
            row["result_id"]
            for row in self.records.headline_results
        ]

        self.assertEqual(
            len(identifiers),
            len(set(identifiers)),
        )


if __name__ == "__main__":
    unittest.main()
