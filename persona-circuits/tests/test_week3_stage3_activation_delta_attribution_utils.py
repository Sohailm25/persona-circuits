from __future__ import annotations

import unittest

import numpy as np

from scripts.week3_stage3_activation_delta_attribution import (
    _concentration_summary,
    _jaccard,
    _mean_pairwise_jaccard,
    _parse_traits,
)


class Week3Stage3ActivationDeltaAttributionUtilsTests(unittest.TestCase):
    def test_parse_traits(self) -> None:
        self.assertEqual(_parse_traits("sycophancy, evil"), ["sycophancy", "evil"])
        with self.assertRaises(ValueError):
            _parse_traits(" , ")

    def test_jaccard(self) -> None:
        self.assertAlmostEqual(_jaccard({1, 2}, {2, 3}), 1.0 / 3.0, places=7)
        self.assertEqual(_jaccard(set(), set()), 1.0)

    def test_mean_pairwise_jaccard(self) -> None:
        sets = [{1, 2, 3}, {2, 3, 4}, {3, 4, 5}]
        out = _mean_pairwise_jaccard(sets)
        self.assertIsNotNone(out)
        self.assertGreater(out, 0.0)
        self.assertLess(out, 1.0)

    def test_concentration_summary(self) -> None:
        vals = np.array([0.1, 0.2, 0.3, 2.0], dtype=np.float64)
        out = _concentration_summary(vals)
        self.assertIn("gini", out)
        self.assertIn("entropy_normalized", out)
        self.assertIn("top_10pct_mass", out)
        self.assertIn("top_20pct_mass", out)
        self.assertGreaterEqual(out["gini"], 0.0)
        self.assertLessEqual(out["entropy_normalized"], 1.0)


if __name__ == "__main__":
    unittest.main()

