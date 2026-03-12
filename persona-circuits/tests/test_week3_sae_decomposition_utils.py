from __future__ import annotations

import unittest

import torch

from scripts.week3_sae_decomposition import (
    _jaccard,
    _parse_trait_alias_map,
    _parse_traits,
    _rank_union_features,
    _select_topk_indices,
)


class Week3SaeDecompositionUtilsTests(unittest.TestCase):
    def test_parse_traits(self) -> None:
        self.assertEqual(_parse_traits("sycophancy, evil"), ["sycophancy", "evil"])

    def test_parse_traits_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            _parse_traits("  ,  ")

    def test_parse_trait_alias_map(self) -> None:
        mapping = _parse_trait_alias_map("evil:machiavellian_disposition,sycophancy:sycophancy")
        self.assertEqual(mapping["evil"], "machiavellian_disposition")
        self.assertEqual(mapping["sycophancy"], "sycophancy")

    def test_parse_trait_alias_map_invalid(self) -> None:
        with self.assertRaises(ValueError):
            _parse_trait_alias_map("evil")

    def test_select_topk_indices(self) -> None:
        values = torch.tensor([0.1, 0.9, 0.4, 0.2], dtype=torch.float32)
        self.assertEqual(_select_topk_indices(values, 2), [1, 2])

    def test_jaccard(self) -> None:
        self.assertAlmostEqual(_jaccard({1, 2}, {2, 3}), 1.0 / 3.0, places=7)
        self.assertEqual(_jaccard(set(), set()), 1.0)

    def test_rank_union_features_prefers_joint_signal(self) -> None:
        direct_top = [1, 2, 3]
        diff_top = [2, 4, 5]
        union_features = {1, 2, 3, 4, 5}
        direct_cos = torch.tensor([0.0, 0.8, 0.7, 0.6, 0.5, 0.4], dtype=torch.float32)
        diff_mean = torch.tensor([0.0, 0.1, 0.5, 0.3, 0.2, 0.1], dtype=torch.float32)

        ranked = _rank_union_features(
            union_features=union_features,
            direct_top=direct_top,
            diff_top=diff_top,
            direct_cos=direct_cos,
            diff_mean=diff_mean,
            top_n=5,
        )

        self.assertGreater(len(ranked), 0)
        # Feature 2 appears in both lists and should rank at or near the top.
        self.assertEqual(ranked[0]["feature_id"], 2)
        self.assertTrue(ranked[0]["in_direct_topk"])
        self.assertTrue(ranked[0]["in_differential_topk"])


if __name__ == "__main__":
    unittest.main()
