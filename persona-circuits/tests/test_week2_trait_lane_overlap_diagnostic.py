from __future__ import annotations

import unittest
import sys
from pathlib import Path

import torch

try:
    from scripts.week2_trait_lane_overlap_diagnostic import (
        _branch_reference_overlap,
        _cross_layer_cosines,
        _max_abs_entry,
        _same_layer_cosines,
        _selected_pair,
        _threshold_flags,
    )
except ModuleNotFoundError:  # pragma: no cover - direct test execution fallback
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.week2_trait_lane_overlap_diagnostic import (
        _branch_reference_overlap,
        _cross_layer_cosines,
        _max_abs_entry,
        _same_layer_cosines,
        _selected_pair,
        _threshold_flags,
    )


class TraitLaneOverlapDiagnosticTests(unittest.TestCase):
    def test_same_and_cross_layer_overlap(self) -> None:
        core = {11: torch.tensor([1.0, 0.0]), 12: torch.tensor([0.0, 1.0])}
        branch = {11: torch.tensor([1.0, 0.0]), 12: torch.tensor([1.0, 0.0])}
        same = _same_layer_cosines(core_vectors=core, branch_vectors=branch)
        self.assertAlmostEqual(same["11"], 1.0, places=6)
        self.assertAlmostEqual(same["12"], 0.0, places=6)

        cross = _cross_layer_cosines(core_vectors=core, branch_vectors=branch)
        best = _max_abs_entry(cross)
        self.assertEqual(best["core_layer"], 11)
        self.assertEqual(best["branch_layer"], 11)
        self.assertAlmostEqual(best["cosine"], 1.0, places=6)

    def test_selected_pair_and_threshold_flags(self) -> None:
        core = {12: torch.tensor([1.0, 0.0])}
        branch = {15: torch.tensor([0.3, 0.4])}
        pair = _selected_pair(core_vectors=core, branch_vectors=branch, core_layer=12, branch_layer=15)
        self.assertAlmostEqual(pair["cosine"], 0.6, places=6)

        flags = _threshold_flags(
            same_layer={"12": 0.2},
            cross_layer_max={"abs_cosine": 0.41},
            selected_pair=pair,
            threshold=0.4,
        )
        self.assertFalse(flags["same_layer_max_abs_exceeds_threshold"])
        self.assertTrue(flags["cross_layer_max_abs_exceeds_threshold"])
        self.assertTrue(flags["selected_pair_abs_exceeds_threshold"])

    def test_branch_reference_overlap(self) -> None:
        summary = {
            "cross_trait_vector_cosines_by_layer": {
                "11": {"politeness": {"assistant_likeness": 0.3}},
                "12": {"politeness": {"assistant_likeness": 0.55}},
            }
        }
        result = _branch_reference_overlap(
            branch_summary=summary,
            branch_trait="politeness",
            reference_trait="assistant_likeness",
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["max_abs_same_layer_overlap"]["layer"], 12)
        self.assertAlmostEqual(result["max_abs_same_layer_overlap"]["cosine"], 0.55, places=6)


if __name__ == "__main__":
    unittest.main()
