"""Unit tests for GLP sidecar geometry metrics."""

from __future__ import annotations

import unittest

from scripts.shared.glp_metrics import (
    aggregate_geometry_metrics,
    aggregate_numeric_metrics,
    compute_geometry_metrics,
    compute_next_token_loss_metrics,
    cosine_similarity,
)


class GLPMetricsTests(unittest.TestCase):
    def test_cosine_similarity_basic(self) -> None:
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [2.0, 0.0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [-2.0, 0.0]), -1.0)
        self.assertIsNone(cosine_similarity([0.0, 0.0], [1.0, 0.0]))

    def test_compute_geometry_metrics(self) -> None:
        metrics = compute_geometry_metrics(
            original=[0.0, 0.0],
            edited=[3.0, 4.0],
            projected=[3.0, 0.0],
        )
        self.assertAlmostEqual(metrics["edit_norm"], 5.0)
        self.assertAlmostEqual(metrics["projected_shift_norm"], 3.0)
        self.assertAlmostEqual(metrics["repair_norm"], 4.0)
        self.assertAlmostEqual(metrics["repair_to_edit_ratio"], 0.8)
        self.assertIsNotNone(metrics["edit_retention_cosine"])

    def test_compute_geometry_metrics_zero_edit_sets_ratios_none(self) -> None:
        metrics = compute_geometry_metrics(
            original=[1.0, 2.0],
            edited=[1.0, 2.0],
            projected=[2.0, 3.0],
        )
        self.assertEqual(metrics["edit_norm"], 0.0)
        self.assertIsNone(metrics["repair_to_edit_ratio"])
        self.assertIsNone(metrics["projected_to_edit_ratio"])

    def test_aggregate_geometry_metrics(self) -> None:
        rows = [
            {"edit_norm": 1.0, "repair_to_edit_ratio": 0.1},
            {"edit_norm": 3.0, "repair_to_edit_ratio": 0.3},
            {"edit_norm": 2.0, "repair_to_edit_ratio": None},
            {"edit_norm": 4.0, "reference_mode": "raw"},
        ]
        summary = aggregate_geometry_metrics(rows)
        self.assertEqual(summary["edit_norm"]["n"], 4)
        self.assertAlmostEqual(summary["edit_norm"]["mean"], 2.5)
        self.assertEqual(summary["repair_to_edit_ratio"]["n"], 2)
        self.assertAlmostEqual(summary["repair_to_edit_ratio"]["median"], 0.2)
        self.assertNotIn("reference_mode", summary)

    def test_compute_next_token_loss_metrics(self) -> None:
        metrics = compute_next_token_loss_metrics(
            clean_logits=[3.0, 1.0, 0.0],
            hooked_logits=[2.0, 2.5, 0.0],
        )
        self.assertGreater(metrics["delta_target_nll_vs_clean"], 0.0)
        self.assertGreater(metrics["kl_clean_to_hooked"], 0.0)
        self.assertLess(metrics["hooked_target_prob"], metrics["clean_target_prob"])

    def test_compute_next_token_loss_metrics_handles_extreme_logits(self) -> None:
        metrics = compute_next_token_loss_metrics(
            clean_logits=[1000.0, -1000.0, -1000.0],
            hooked_logits=[-1000.0, 1000.0, -1000.0],
        )
        self.assertTrue(metrics["kl_clean_to_hooked"] > 0.0)
        self.assertFalse(str(metrics["kl_clean_to_hooked"]).lower() == "nan")

    def test_aggregate_numeric_metrics(self) -> None:
        summary = aggregate_numeric_metrics(
            [
                {"delta_target_nll_vs_clean": 0.1, "kl_clean_to_hooked": 0.2},
                {"delta_target_nll_vs_clean": 0.3, "kl_clean_to_hooked": None},
            ]
        )
        self.assertEqual(summary["delta_target_nll_vs_clean"]["n"], 2)
        self.assertAlmostEqual(summary["delta_target_nll_vs_clean"]["mean"], 0.2)
        self.assertEqual(summary["kl_clean_to_hooked"]["n"], 1)


if __name__ == "__main__":
    unittest.main()
