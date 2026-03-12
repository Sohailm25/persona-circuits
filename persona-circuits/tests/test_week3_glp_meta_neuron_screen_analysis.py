"""Unit tests for the Week 3 GLP meta-neuron screen analysis helpers."""

from __future__ import annotations

import unittest

from scripts.week3_glp_meta_neuron_screen_analysis import _summarize_trait


class Week3GLPMetaNeuronScreenAnalysisTests(unittest.TestCase):
    def test_summarize_trait(self) -> None:
        summary = _summarize_trait(
            {
                "glp_alignment": {"claim_grade_ready": False},
                "top_meta_neurons": [
                    {"feature_identifier": "u1:c0:d2", "abs_mean_delta": 5.0},
                    {"feature_identifier": "u0:c1:d1", "abs_mean_delta": 3.0},
                ],
                "concentration_by_capture_target": [
                    {"capture_target_index": 0, "score_sum": 10.0},
                    {"capture_target_index": 1, "score_sum": 7.0},
                ],
                "concentration_by_u": [
                    {"u_index": 1, "score_sum": 8.0},
                    {"u_index": 0, "score_sum": 4.0},
                ],
                "screening_summary": {
                    "topk_abs_mean_delta_sum": 8.0,
                    "topk_abs_mean_delta_mean": 4.0,
                    "centroid_cosine_low_vs_high": 0.2,
                    "abs_mean_delta_summary": {"mean": 0.1},
                },
            }
        )
        self.assertFalse(summary["glp_alignment"]["claim_grade_ready"])
        self.assertEqual(summary["top_meta_neuron_preview"][0]["feature_identifier"], "u1:c0:d2")
        self.assertEqual(summary["top_capture_targets"][0]["capture_target_index"], 0)
        self.assertEqual(summary["top_u_values"][0]["u_index"], 1)
        self.assertEqual(summary["screening_summary"]["topk_abs_mean_delta_sum"], 8.0)


if __name__ == "__main__":
    unittest.main()
