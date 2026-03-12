"""Unit tests for concentration and causal-effect metric helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from circuit_metrics import (
    concentration_summary,
    cohens_d,
    effect_size_summary,
    gini_coefficient,
    normalized_shannon_entropy,
    random_baseline_selectivity,
    top_p_mass,
    vargha_delaney_a12,
)


class CircuitMetricsTests(unittest.TestCase):
    def test_gini_uniform_zero(self) -> None:
        self.assertAlmostEqual(float(gini_coefficient([1, 1, 1, 1])), 0.0, places=6)

    def test_gini_concentrated_high(self) -> None:
        self.assertAlmostEqual(float(gini_coefficient([1, 0, 0, 0])), 0.75, places=6)

    def test_entropy_uniform_one(self) -> None:
        self.assertAlmostEqual(float(normalized_shannon_entropy([1, 1, 1, 1])), 1.0, places=6)

    def test_entropy_concentrated_zero(self) -> None:
        self.assertAlmostEqual(float(normalized_shannon_entropy([1, 0, 0, 0])), 0.0, places=6)

    def test_top_p_mass(self) -> None:
        self.assertAlmostEqual(float(top_p_mass([4, 3, 2, 1], 0.25)), 0.4, places=6)
        self.assertAlmostEqual(float(top_p_mass([4, 3, 2, 1], 0.5)), 0.7, places=6)

    def test_a12_extremes(self) -> None:
        self.assertAlmostEqual(float(vargha_delaney_a12([2, 3], [0, 1])), 1.0, places=6)
        self.assertAlmostEqual(float(vargha_delaney_a12([0, 1], [2, 3])), 0.0, places=6)

    def test_cohens_d_zero_when_identical(self) -> None:
        self.assertAlmostEqual(float(cohens_d([1, 2, 3], [1, 2, 3])), 0.0, places=6)

    def test_effect_size_summary_contains_bootstrap_cis(self) -> None:
        summary = effect_size_summary(
            [0.7, 0.8, 0.9, 1.0, 1.1],
            [0.1, 0.2, 0.3, 0.4, 0.5],
            seed=42,
            n_bootstrap=200,
        )
        self.assertIsNotNone(summary["cohens_d"])
        self.assertIsNotNone(summary["a12"])
        self.assertIsNotNone(summary["cohens_d_ci95"])
        self.assertIsNotNone(summary["a12_ci95"])

    def test_random_baseline_selectivity(self) -> None:
        rng = np.random.default_rng(42)
        random_vals = rng.uniform(low=0.1, high=0.6, size=100)
        observed = 0.95
        out = random_baseline_selectivity(observed, random_vals)
        self.assertEqual(out["n_random"], 100)
        self.assertGreater(float(out["percentile_rank"]), 0.99)
        self.assertTrue(bool(out["top_1pct_pass"]))
        self.assertLess(float(out["p_value_one_sided_ge"]), 0.02)

    def test_concentration_summary_keys_present(self) -> None:
        out = concentration_summary([1, 2, 3, 4, 5])
        self.assertIn("gini", out)
        self.assertIn("entropy_normalized", out)
        self.assertIn("top_1pct_mass", out)
        self.assertIn("top_5pct_mass", out)
        self.assertIn("top_10pct_mass", out)


if __name__ == "__main__":
    unittest.main()
