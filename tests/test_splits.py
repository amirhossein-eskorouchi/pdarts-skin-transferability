import unittest

from pdarts_skin.data import ManifestRecord
from pdarts_skin.splits import (
    assign_patient_grouped,
    validate_patient_isolation,
)


class SplitTests(unittest.TestCase):
    def test_assignment_is_deterministic_and_patient_safe(self):
        records = [
            ManifestRecord(
                f"sample_{index}",
                f"images/{index}.jpg",
                index % 6,
                f"patient_{index // 2}",
                "pad_ufes_20",
                "",
                "",
            )
            for index in range(20)
        ]

        first = assign_patient_grouped(
            records,
            seed=17,
        )

        second = assign_patient_grouped(
            records,
            seed=17,
        )

        self.assertEqual(
            first,
            second,
        )

        validate_patient_isolation(
            first
        )

        patient_splits = {}

        for record in first:
            patient_splits.setdefault(
                record.patient_id,
                set(),
            ).add(record.split)

        self.assertTrue(
            all(
                len(splits) == 1
                for splits in patient_splits.values()
            )
        )


if __name__ == "__main__":
    unittest.main()
