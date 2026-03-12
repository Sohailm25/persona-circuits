from __future__ import annotations

import unittest

from scripts.week3_stage3_candidate_selection import (
    _rank_map,
    _select_claim_layer_first_pass,
)


class Week3Stage3CandidateSelectionTests(unittest.TestCase):
    def test_rank_map_uses_1_indexed_positions(self) -> None:
        rows = [
            {"feature_id": 10, "combined_rank_score": 0.9},
            {"feature_id": 20, "combined_rank_score": 0.8},
            {"feature_id": 30, "combined_rank_score": 0.7},
        ]
        out = _rank_map(rows)
        self.assertEqual(out[10], 1)
        self.assertEqual(out[20], 2)
        self.assertEqual(out[30], 3)

    def test_select_claim_layer_first_pass_uses_claim_score_order(self) -> None:
        primary_rows = [
            {
                "feature_id": 1,
                "combined_rank_score": 0.90,
                "direct_rank": 3,
                "differential_rank": 2,
                "in_direct_topk": True,
                "in_differential_topk": True,
                "direct_cosine": 0.12,
                "differential_abs_mean": 0.7,
            },
            {
                "feature_id": 2,
                "combined_rank_score": 0.99,
                "direct_rank": 1,
                "differential_rank": 1,
                "in_direct_topk": True,
                "in_differential_topk": True,
                "direct_cosine": 0.21,
                "differential_abs_mean": 1.1,
            },
            {
                "feature_id": 3,
                "combined_rank_score": 0.95,
                "direct_rank": 2,
                "differential_rank": 4,
                "in_direct_topk": True,
                "in_differential_topk": False,
                "direct_cosine": 0.16,
                "differential_abs_mean": 0.4,
            },
        ]
        selected = _select_claim_layer_first_pass(
            primary_rows=primary_rows,
            first_pass_k=2,
        )
        fids = [row["feature_id"] for row in selected]
        self.assertEqual(len(fids), 2)
        self.assertEqual(fids[0], 2)
        self.assertEqual(fids[1], 3)
        self.assertIn(2, fids)
        self.assertIn(3, fids)


if __name__ == "__main__":
    unittest.main()
