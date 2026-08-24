import unittest
from pathlib import Path

from pdarts_skin.config import load_dataset_config


ROOT = Path(__file__).resolve().parents[1]


class DatasetConfigTests(unittest.TestCase):
    def test_pad_contract(self):
        config = load_dataset_config(
            ROOT / "configs" / "datasets",
            "pad_ufes_20",
        )

        self.assertEqual(
            config.label_codes[-1],
            "SCC",
        )

        self.assertIn(
            "patient_grouped",
            config.supported_split_modes,
        )

        self.assertTrue(
            config.patient_group_required
        )

    def test_dermamnist_class_five(self):
        config = load_dataset_config(
            ROOT / "configs" / "datasets",
            "dermamnist",
        )

        self.assertEqual(
            config.label_codes[-1],
            "VASC",
        )


if __name__ == "__main__":
    unittest.main()
