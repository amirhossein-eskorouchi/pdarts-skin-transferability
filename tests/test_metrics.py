import unittest

from pdarts_skin.metrics import (
    accuracy,
    confusion_matrix,
    weighted_f1,
)


class MetricTests(unittest.TestCase):
    def test_accuracy(self):
        self.assertAlmostEqual(
            accuracy(
                [0, 1, 2, 2],
                [0, 1, 0, 2],
            ),
            0.75,
        )

    def test_confusion_matrix(self):
        self.assertEqual(
            confusion_matrix(
                [0, 1, 1],
                [0, 0, 1],
                2,
            ),
            [
                [1, 0],
                [1, 1],
            ],
        )

    def test_weighted_f1_perfect(self):
        self.assertAlmostEqual(
            weighted_f1(
                [0, 1, 2],
                [0, 1, 2],
                3,
            ),
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
