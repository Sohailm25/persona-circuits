"""Unit tests for the Week 2 GLP sidecar analysis helpers."""

from __future__ import annotations

import unittest

from scripts.week2_glp_sidecar_analysis import _metric_validity_summary, _summarize_trait


class Week2GLPSidecarAnalysisTests(unittest.TestCase):
    def test_metric_validity_summary_requires_family_records(self) -> None:
        summary = _metric_validity_summary({})
        self.assertEqual(summary["status"], "unavailable")

    def test_metric_validity_summary_computes_correlations_when_rows_exist(self) -> None:
        payload = {
            "family_records": {
                "selected_raw": [
                    {
                        "row_id": "a",
                        "trait_plus_score": 70.0,
                        "trait_minus_score": 30.0,
                        "coherence_plus_score": 80.0,
                        "coherence_minus_score": 78.0,
                    },
                    {
                        "row_id": "b",
                        "trait_plus_score": 60.0,
                        "trait_minus_score": 20.0,
                        "coherence_plus_score": 75.0,
                        "coherence_minus_score": 73.0,
                    },
                ],
                "selected_glp": [
                    {
                        "row_id": "a",
                        "trait_plus_score": 68.0,
                        "trait_minus_score": 26.0,
                        "coherence_plus_score": 79.0,
                        "coherence_minus_score": 77.0,
                        "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.1}],
                        "geometry_events": [{"repair_to_edit_ratio": 1.0}],
                    },
                    {
                        "row_id": "b",
                        "trait_plus_score": 55.0,
                        "trait_minus_score": 15.0,
                        "coherence_plus_score": 70.0,
                        "coherence_minus_score": 68.0,
                        "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.5}],
                        "geometry_events": [{"repair_to_edit_ratio": 2.0}],
                    },
                ],
            }
        }
        summary = _metric_validity_summary(payload)
        self.assertEqual(summary["status"], "available")
        self.assertEqual(summary["n_rows"], 2)
        self.assertIn("pearson", summary["nll_vs_coherence_delta"])
        self.assertIn("spearman", summary["repair_ratio_vs_effect_delta"])

    def test_metric_validity_summary_accepts_row_record_alias_schema(self) -> None:
        payload = {
            "row_records_by_family": {
                "selected_raw": [
                    {
                        "row_id": "a",
                        "trait_plus_score": 70.0,
                        "trait_minus_score": 30.0,
                        "coherence_plus_score": 80.0,
                        "coherence_minus_score": 78.0,
                    },
                    {
                        "row_id": "b",
                        "trait_plus_score": 60.0,
                        "trait_minus_score": 20.0,
                        "coherence_plus_score": 75.0,
                        "coherence_minus_score": 73.0,
                    },
                ],
                "selected_glp": [
                    {
                        "row_id": "a",
                        "trait_plus_score": 68.0,
                        "trait_minus_score": 26.0,
                        "coherence_plus_score": 79.0,
                        "coherence_minus_score": 77.0,
                        "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.1}],
                        "geometry_events": [{"repair_to_edit_ratio": 1.0}],
                    },
                    {
                        "row_id": "b",
                        "trait_plus_score": 55.0,
                        "trait_minus_score": 15.0,
                        "coherence_plus_score": 70.0,
                        "coherence_minus_score": 68.0,
                        "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.5}],
                        "geometry_events": [{"repair_to_edit_ratio": 2.0}],
                    },
                ],
            }
        }
        summary = _metric_validity_summary(payload)
        self.assertEqual(summary["status"], "available")
        self.assertEqual(summary["n_rows"], 2)

    def test_summarize_trait_exposes_random_draw_and_conditioning_info(self) -> None:
        payload = {
            "families": {
                "selected_raw": {
                    "bidirectional_effect_mean": -10.0,
                    "coherence_mean": 50.0,
                },
                "selected_glp": {
                    "bidirectional_effect_mean": -12.0,
                    "coherence_mean": 49.0,
                    "geometry_summary": {
                        "repair_to_edit_ratio": {"mean": 1.5},
                        "edit_retention_cosine": {"mean": 0.8},
                    },
                    "conditioning_regime_counts": {"clean_condition_edited_target": 2},
                },
                "baseline_glp_control": {
                    "bidirectional_effect_mean": -8.0,
                    "conditioning_regime_counts": {"clean_condition_clean_target": 2},
                },
                "random_glp": {
                    "bidirectional_effect_mean": -9.0,
                    "draw_distribution": {"bidirectional_effect_mean": {"mean": -9.5}},
                    "conditioning_regime_counts": {"clean_condition_edited_target": 6},
                },
            },
            "family_records": {
                "selected_raw": [],
                "selected_glp": [],
            },
            "glp_alignment": {"claim_grade_ready": True},
        }
        summary = _summarize_trait(payload)
        self.assertIn("random_glp_draw_distribution", summary)
        self.assertIn("conditioning_regimes", summary)
        self.assertEqual(
            summary["conditioning_regimes"]["selected_glp"],
            {"clean_condition_edited_target": 2},
        )


if __name__ == "__main__":
    unittest.main()
