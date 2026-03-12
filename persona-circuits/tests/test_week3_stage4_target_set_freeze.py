"""Unit tests for Stage4 target-set freeze helpers."""

from __future__ import annotations

import unittest

from scripts.week3_stage4_target_set_freeze import (
    _extract_target_features,
    _parse_traits,
    _random_preview_sets,
)


class ParseTraitsTests(unittest.TestCase):
    def test_parse_traits_success(self) -> None:
        self.assertEqual(_parse_traits("sycophancy,evil"), ["sycophancy", "evil"])

    def test_parse_traits_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            _parse_traits(" , ")


class ExtractTargetsTests(unittest.TestCase):
    def _stage3_payload(self) -> dict:
        return {
            "results_by_trait": {
                "sycophancy": {
                    "n_prompts": 50,
                    "attribution_method": "activation_delta_proxy",
                    "feature_attribution_summary": {
                        "prompt_top10_pairwise_jaccard_mean": 0.33,
                        "mean_abs_delta_concentration": {"gini": 0.58},
                        "top10_by_mean_abs_delta": [
                            {"feature_id": 10, "mean_delta": 0.4, "mean_abs_delta": 0.5},
                            {"feature_id": 20, "mean_delta": 0.3, "mean_abs_delta": 0.4},
                            {"feature_id": 30, "mean_delta": 0.2, "mean_abs_delta": 0.3},
                        ],
                    },
                }
            }
        }

    def _candidate_payload(self) -> dict:
        return {
            "results_by_trait": {
                "sycophancy": {
                    "selected_first_pass_features": [
                        {"feature_id": 10},
                        {"feature_id": 20},
                        {"feature_id": 30},
                        {"feature_id": 40},
                        {"feature_id": 50},
                    ]
                }
            }
        }

    def test_extract_target_features_happy_path(self) -> None:
        out = _extract_target_features(
            stage3_payload=self._stage3_payload(),
            candidate_payload=self._candidate_payload(),
            trait="sycophancy",
            top_k=2,
        )
        self.assertEqual(out["target_feature_ids"], [10, 20])
        self.assertEqual(out["candidate_pool_size"], 5)
        self.assertEqual(out["prompt_count_used"], 50)

    def test_extract_target_features_rejects_large_k(self) -> None:
        with self.assertRaises(ValueError):
            _extract_target_features(
                stage3_payload=self._stage3_payload(),
                candidate_payload=self._candidate_payload(),
                trait="sycophancy",
                top_k=4,
            )


class RandomPreviewTests(unittest.TestCase):
    def test_preview_sets_exclude_targets_and_match_size(self) -> None:
        out = _random_preview_sets(
            candidate_pool_ids=[10, 20, 30, 40, 50, 60],
            exclude_ids=[10, 20],
            set_size=2,
            n_preview=3,
            seed=42,
        )
        self.assertEqual(len(out), 3)
        for row in out:
            self.assertEqual(len(row), 2)
            self.assertTrue(all(fid not in {10, 20} for fid in row))


if __name__ == "__main__":
    unittest.main()
