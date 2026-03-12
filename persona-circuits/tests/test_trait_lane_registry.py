"""Tests for the trait-lane registry helpers."""

from __future__ import annotations

import unittest

from scripts.shared.trait_lane_registry import (
    build_construct_card_status,
    build_lane_screening_plan,
    load_trait_lane_registry,
    resolve_selected_lane_ids,
)


class TraitLaneRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()

    def test_resolve_selected_lane_ids_defaults_to_all_candidate_lanes(self) -> None:
        lane_ids = resolve_selected_lane_ids(self.registry)
        self.assertIn("assistant_likeness", lane_ids)
        self.assertIn("honesty", lane_ids)
        self.assertIn("refusal_expression", lane_ids)
        self.assertNotIn("sycophancy", lane_ids)

    def test_resolve_selected_lane_ids_allows_family_selection(self) -> None:
        lane_ids = resolve_selected_lane_ids(self.registry, family_ids=["assistant_axis"])
        self.assertEqual(lane_ids, ["assistant_likeness", "persona_drift_from_assistant"])

    def test_build_lane_screening_plan_contains_expected_paths(self) -> None:
        plan = build_lane_screening_plan(self.registry, lane_ids=["honesty"])
        self.assertEqual(len(plan), 1)
        lane = plan[0]
        self.assertTrue(lane["planned_prompt_files"]["extraction_pairs"].endswith("prompts/trait_lanes_v2/honesty_pairs.jsonl"))
        self.assertEqual(lane["screening_counts"]["heldout_pairs"], 12)

    def test_construct_cards_present_for_selected_family(self) -> None:
        status = build_construct_card_status(self.registry, lane_ids=["agreeableness"])
        self.assertTrue(status["all_present"])
        self.assertEqual(len(status["missing"]), 0)


if __name__ == "__main__":
    unittest.main()
