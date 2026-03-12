from __future__ import annotations

import unittest

from scripts.shared.trait_lane_generation import (
    TEMPLATE_CATEGORY_SPECS,
    allocate_category_specs,
    build_generation_plan,
    build_system_prompts,
    collect_valid_unique_items,
    ensure_output_path_is_new,
    max_query_similarity,
    planned_output_path,
    request_batch_size,
    split_construct,
)
from scripts.shared.trait_lane_registry import load_trait_lane_registry, resolve_selected_lane_ids


class TraitLaneGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()

    def test_split_construct_requires_vs_separator(self):
        high, low = split_construct("warm cooperation vs cold antagonism")
        self.assertEqual(high, "warm cooperation")
        self.assertEqual(low, "cold antagonism")
        with self.assertRaises(ValueError):
            split_construct("missing separator")

    def test_template_registry_covers_all_registry_templates(self):
        template_ids = set(TEMPLATE_CATEGORY_SPECS.keys())
        for lane_id in resolve_selected_lane_ids(self.registry):
            lane_cfg = None
            for family in self.registry["families"].values():
                lanes = family["lanes"]
                if lane_id in lanes:
                    lane_cfg = lanes[lane_id]
                    break
            self.assertIsNotNone(lane_cfg)
            self.assertIn(lane_cfg["prompt_generator_template"], template_ids)
            self.assertIn(lane_cfg["heldout_template"], template_ids)

    def test_allocate_category_specs_hits_target_total(self):
        specs = allocate_category_specs("assistant_axis_v1", mode="extraction", target_total=24)
        self.assertEqual(sum(spec.weight for spec in specs), 24)
        heldout_specs = allocate_category_specs("assistant_axis_v1", mode="heldout", target_total=12)
        self.assertEqual(sum(spec.weight for spec in heldout_specs), 12)

    def test_build_system_prompts_uses_construct_split(self):
        lane_cfg = {
            "high_vs_low_construct": "assistant-like helpful persona vs off-axis persona drift"
        }
        prompts = build_system_prompts(lane_cfg)
        self.assertIn("assistant-like helpful persona", prompts["high"])
        self.assertIn("off-axis persona drift", prompts["low"])

    def test_build_generation_plan_uses_trait_lane_namespace(self):
        packet = build_generation_plan(
            registry=self.registry,
            lane_ids=["assistant_likeness", "agreeableness"],
            mode="extraction",
        )
        self.assertEqual(packet["mode"], "extraction")
        self.assertEqual(len(packet["lane_rows"]), 2)
        for row in packet["lane_rows"]:
            self.assertIn("prompts/trait_lanes_v2/", row["output_path"])
            self.assertEqual(row["target_total"], 24)

    def test_build_generation_plan_supports_external_smoke(self):
        packet = build_generation_plan(
            registry=self.registry,
            lane_ids=["honesty", "lying"],
            mode="external_smoke",
        )
        self.assertEqual(packet["mode"], "external_smoke")
        self.assertEqual(len(packet["lane_rows"]), 2)
        for row in packet["lane_rows"]:
            self.assertIn("prompts/trait_lanes_v2/external_smoke/", row["output_path"])
            self.assertEqual(row["target_total"], 8)

    def test_build_generation_plan_accepts_target_total_override(self):
        packet = build_generation_plan(
            registry=self.registry,
            lane_ids=["politeness"],
            mode="heldout",
            target_total_override=30,
            output_suffix="deeperv1",
        )
        self.assertEqual(packet["lane_rows"][0]["target_total"], 30)
        self.assertTrue(packet["lane_rows"][0]["output_path"].endswith("politeness_heldout_pairs_deeperv1.jsonl"))
        self.assertEqual(
            sum(category["n"] for category in packet["lane_rows"][0]["categories"]),
            30,
        )

    def test_request_batch_size_oversamples_target(self):
        self.assertEqual(request_batch_size(1), 3)
        self.assertEqual(request_batch_size(3), 5)
        self.assertEqual(request_batch_size(6), 9)

    def test_collect_valid_unique_items_filters_duplicates_and_invalid(self):
        lane_cfg = {
            "requires_ground_truth": True,
        }
        seen = {"existing prompt"}
        items = [
            {"user_query": "Existing prompt", "ground_truth": "True."},
            {"user_query": "New prompt one", "ground_truth": "Maybe true."},
            {"user_query": "New prompt two", "ground_truth": "A short factual answer."},
            {"user_query": "New prompt three", "ground_truth": "Another short factual answer."},
        ]
        accepted = collect_valid_unique_items(
            lane_id="honesty",
            lane_cfg=lane_cfg,
            items=items,
            seen=seen,
            target_n=2,
        )
        self.assertEqual([item["user_query"] for item in accepted], ["New prompt two", "New prompt three"])
        self.assertIn("new prompt two", seen)
        self.assertIn("new prompt three", seen)

    def test_planned_output_path_supports_suffix(self):
        path = planned_output_path(lane_id="honesty", mode="heldout", output_suffix="retry01")
        self.assertTrue(str(path).endswith("honesty_heldout_pairs_retry01.jsonl"))
        ext_path = planned_output_path(lane_id="lying", mode="external_smoke", output_suffix="retry01")
        self.assertTrue(str(ext_path).endswith("lying_external_smoke_retry01.jsonl"))

    def test_max_query_similarity_flags_near_paraphrase(self):
        sim = max_query_similarity(
            "I heard the Great Wall of China is visible from space with the naked eye. Is that true?",
            ["Is the Great Wall of China visible from space with the naked eye?"],
        )
        self.assertGreaterEqual(sim, 0.8)
        self.assertLess(
            max_query_similarity("How do I prepare for a job interview?", ["What are good indoor plants for beginners?"]),
            0.5,
        )


if __name__ == "__main__":
    unittest.main()
