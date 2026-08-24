import unittest
from pathlib import Path

from pdarts_skin.config import load_dataset_config
from pdarts_skin.data import ManifestRecord, validate_manifest


ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.config = load_dataset_config(
            ROOT / "configs" / "datasets",
            "pad_ufes_20",
        )

    def test_valid_grouped_manifest(self):
        records = [
            ManifestRecord(
                "sample_1",
                "images/sample_1.jpg",
                0,
                "patient_1",
                "pad_ufes_20",
                "train",
                "patient_grouped",
            ),
            ManifestRecord(
                "sample_2",
                "images/sample_2.jpg",
                5,
                "patient_2",
                "pad_ufes_20",
                "test",
                "patient_grouped",
            ),
        ]

        validate_manifest(
            records,
            self.config,
        )

    def test_absolute_path_rejected(self):
        records = [
            ManifestRecord(
                "sample_1",
                "C:/private/sample.jpg",
                0,
                "patient_1",
                "pad_ufes_20",
                "train",
                "patient_grouped",
            )
        ]

        with self.assertRaises(ValueError):
            validate_manifest(
                records,
                self.config,
            )

    def test_patient_leakage_rejected(self):
        records = [
            ManifestRecord(
                "sample_1",
                "images/a.jpg",
                0,
                "patient_1",
                "pad_ufes_20",
                "train",
                "patient_grouped",
            ),
            ManifestRecord(
                "sample_2",
                "images/b.jpg",
                0,
                "patient_1",
                "pad_ufes_20",
                "test",
                "patient_grouped",
            ),
        ]

        with self.assertRaises(ValueError):
            validate_manifest(
                records,
                self.config,
            )


if __name__ == "__main__":
    unittest.main()
