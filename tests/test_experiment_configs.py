import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "experiments"


class ExperimentConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in CONFIG_DIR.glob("*.json")
        }

    def test_expected_experiment_count(self):
        self.assertEqual(
            len(self.configs),
            3,
        )

    def test_reproduction_namespace(self):
        self.assertTrue(
            all(
                config["result_namespace"] == "reproduction"
                for config in self.configs.values()
            )
        )

    def test_new_target_weights(self):
        self.assertTrue(
            all(
                config["evaluation"]["initialization"]
                == "new_weights_on_target"
                for config in self.configs.values()
            )
        )

    def test_upstream_policy(self):
        self.assertTrue(
            all(
                config["upstream_core_policy"]
                == "external_authorized_dependency_required"
                for config in self.configs.values()
            )
        )

    def test_e1_progressive_depths(self):
        config = self.configs["e1_pdarts6_depth_transfer"]

        self.assertEqual(
            config["search"]["progressive_stage_depths"],
            [2, 4, 6],
        )

        self.assertEqual(
            config["search"]["epochs_per_stage"],
            25,
        )


if __name__ == "__main__":
    unittest.main()
