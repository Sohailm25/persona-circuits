from __future__ import annotations

import unittest

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_screening_readiness import (
    _ground_truth_stats,
    build_screening_readiness_packet,
)


class Week2TraitLaneScreeningReadinessTests(unittest.TestCase):
    def test_ground_truth_stats_real_trait_lane_file(self) -> None:
        stats = _ground_truth_stats(
            "/Users/sohailmohammad/braindstorms/persona-circuits/prompts/trait_lanes_v2/honesty_pairs.jsonl"
        )
        self.assertEqual(stats["n_rows"], 24)
        self.assertEqual(stats["fraction_with_ground_truth"], 1.0)

    def test_build_screening_readiness_packet_recommends_slice_a_first(self) -> None:
        registry = load_trait_lane_registry()
        packet = build_screening_readiness_packet(
            registry=registry,
            lane_ids=[
                "assistant_likeness",
                "honesty",
                "politeness",
                "persona_drift_from_assistant",
                "lying",
                "optimism",
            ],
        )
        self.assertEqual(packet["n_live_lanes"], 6)
        self.assertEqual(packet["n_screen_ready_lanes"], 6)
        self.assertIsNotNone(packet["recommended_first_tranche"])
        self.assertEqual(packet["recommended_first_tranche"]["tranche_id"], "slice_a")


if __name__ == "__main__":
    unittest.main()
