"""Unit tests for extraction-free reanalysis helper statistics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_extraction_free_reanalysis import (
    _binomial_two_sided_p_value,
    _bootstrap_mean_ci,
    _classify_overlap,
    _ttest_vs_zero_normal_approx,
)


class Week2ExtractionFreeReanalysisTests(unittest.TestCase):
    def test_binomial_two_sided_p_value_detects_extreme_sign_bias(self) -> None:
        p_value = _binomial_two_sided_p_value(50, 50, p_success=0.5)
        self.assertIsNotNone(p_value)
        self.assertLess(float(p_value), 1e-12)

    def test_ttest_vs_zero_detects_positive_signal(self) -> None:
        values = np.asarray([0.12, 0.1, 0.14, 0.11, 0.15, 0.09], dtype=np.float64)
        summary = _ttest_vs_zero_normal_approx(values)
        self.assertEqual(summary["n"], 6)
        self.assertGreater(float(summary["t_stat"]), 0.0)
        self.assertLess(float(summary["p_value_two_sided_normal_approx"]), 0.05)

    def test_bootstrap_mean_ci_returns_positive_bounds_for_positive_series(self) -> None:
        values = np.asarray([0.08, 0.1, 0.12, 0.11, 0.09, 0.13], dtype=np.float64)
        summary = _bootstrap_mean_ci(values, seed=42, n_bootstrap=500)
        ci = summary["mean_ci95"]
        self.assertIsNotNone(ci)
        self.assertGreater(ci["lower"], 0.0)
        self.assertGreater(ci["upper"], ci["lower"])

    def test_classify_overlap_returns_expected_bins(self) -> None:
        self.assertEqual(_classify_overlap(0.22, 0.98, 1e-6), "moderate_overlap")
        self.assertEqual(_classify_overlap(0.12, 0.9, 0.01), "weak_overlap")
        self.assertEqual(_classify_overlap(-0.01, 0.5, 0.9), "null_overlap")
        self.assertEqual(_classify_overlap(0.07, 0.7, 0.2), "mixed_or_fragile")


if __name__ == "__main__":
    unittest.main()
