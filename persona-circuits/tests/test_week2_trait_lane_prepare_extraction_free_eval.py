from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_prepare_extraction_free_eval import (
    _build_plan,
    _extraction_free_output_path,
    _heldout_input_path,
    _resolve_extraction_free_lane_ids,
)


class TraitLanePrepareExtractionFreeEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()

    def test_resolve_extraction_free_lane_ids_rejects_unsupported(self):
        with self.assertRaises(ValueError):
            _resolve_extraction_free_lane_ids(
                self.registry,
                lane_ids=["refusal_expression"],
                family_ids=[],
            )

    def test_output_paths_include_suffix_when_present(self):
        self.assertTrue(str(_heldout_input_path(lane_id="honesty", heldout_suffix="retry01")).endswith("honesty_heldout_pairs_retry01.jsonl"))
        self.assertTrue(str(_extraction_free_output_path(lane_id="honesty", output_suffix="sliceA")).endswith("honesty_eval_sliceA.jsonl"))

    def test_build_plan_uses_trait_lane_extraction_free_namespace(self):
        packet = _build_plan(
            registry=self.registry,
            lane_ids=["assistant_likeness", "honesty"],
            heldout_suffix="retry01",
            output_suffix="",
            n_eval_per_lane=12,
            exemplar_bank_path=Path("prompts/trait_lanes_v2/extraction_free_exemplar_bank_sliceA.json"),
        )
        self.assertEqual(len(packet["lane_rows"]), 2)
        for row in packet["lane_rows"]:
            self.assertIn("prompts/trait_lanes_v2/heldout/", row["input_path"])
            self.assertIn("prompts/trait_lanes_v2/extraction_free/", row["output_path"])


if __name__ == "__main__":
    unittest.main()
