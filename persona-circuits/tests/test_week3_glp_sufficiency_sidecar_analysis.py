"""Unit tests for the Week 3 GLP sufficiency sidecar analysis helpers."""

from __future__ import annotations

import unittest

from scripts.week3_glp_sufficiency_sidecar_analysis import _best_dose, _summarize_method


class Week3GLPSufficiencySidecarAnalysisTests(unittest.TestCase):
    def test_best_dose_prefers_higher_glp_preservation(self) -> None:
        payload = {
            "dose_fraction_reports": {
                "0.50": {
                    "preserved_fraction_target": 0.5,
                    "conditions": {
                        "circuit_only_raw": {"preservation_vs_raw_full_mean": 0.35, "coherence_mean": 78.0},
                        "circuit_only_glp": {"preservation_vs_raw_full_mean": 0.55, "coherence_mean": 79.0},
                    },
                },
                "1.00": {
                    "preserved_fraction_target": 1.0,
                    "conditions": {
                        "circuit_only_raw": {"preservation_vs_raw_full_mean": 0.60, "coherence_mean": 74.0},
                        "circuit_only_glp": {"preservation_vs_raw_full_mean": 0.72, "coherence_mean": 76.0},
                    },
                },
            }
        }
        best = _best_dose(payload)
        self.assertEqual(best["dose_key"], "1.00")
        self.assertAlmostEqual(best["glp_minus_raw_preservation_vs_raw_full"], 0.12)

    def test_summarize_method_includes_deltas(self) -> None:
        payload = {
            "dose_fraction_reports": {
                "1.00": {
                    "preserved_fraction_target": 1.0,
                    "conditions": {
                        "circuit_only_raw": {
                            "preservation_vs_raw_full_mean": 0.6,
                            "coherence_mean": 74.0,
                        },
                        "circuit_only_glp": {
                            "preservation_vs_raw_full_mean": 0.72,
                            "coherence_mean": 76.0,
                        },
                        "random_same_size_circuit_raw": {
                            "selectivity_vs_observed": {"p_value_one_sided_ge": 0.2}
                        },
                        "random_same_size_circuit_glp": {
                            "selectivity_vs_observed": {"p_value_one_sided_ge": 0.05}
                        },
                    },
                    "condition_records": {
                        "circuit_only_raw": [
                            {
                                "coherence_score": 70.0,
                                "preservation_vs_raw_full": 0.4,
                                "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.1}],
                                "geometry_events": [{"repair_to_edit_ratio": 1.0}],
                            },
                            {
                                "coherence_score": 75.0,
                                "preservation_vs_raw_full": 0.6,
                                "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.2}],
                                "geometry_events": [{"repair_to_edit_ratio": 1.2}],
                            },
                        ],
                        "circuit_only_glp": [
                            {
                                "coherence_score": 68.0,
                                "preservation_vs_raw_full": 0.5,
                                "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.3}],
                                "geometry_events": [{"repair_to_edit_ratio": 1.5}],
                            },
                            {
                                "coherence_score": 72.0,
                                "preservation_vs_raw_full": 0.7,
                                "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.4}],
                                "geometry_events": [{"repair_to_edit_ratio": 1.8}],
                            },
                        ],
                    },
                }
            }
        }
        summary = _summarize_method(payload)
        dose = summary["dose_fraction_reports"]["1.00"]
        self.assertAlmostEqual(dose["glp_minus_raw_preservation_vs_raw_full"], 0.12)
        self.assertAlmostEqual(dose["glp_minus_raw_coherence"], 2.0)
        self.assertEqual(dose["random_glp_selectivity_p"], 0.05)
        self.assertEqual(dose["metric_validity"]["circuit_only_glp"]["status"], "available")


if __name__ == "__main__":
    unittest.main()
