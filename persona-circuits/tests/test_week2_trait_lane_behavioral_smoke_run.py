"""Tests for the thin actual trait-lane behavioral smoke runner."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_behavioral_smoke_run import (
    _build_coherence_summary,
    _build_execution_packet,
    _rank_metric,
    _resolve_selected_lane_rows,
    SmokeMetric,
)


ROOT = Path(__file__).resolve().parents[1]
READINESS_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_screening_readiness_20260311T221405Z.json"
)


class TraitLaneBehavioralSmokeRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()
        self.readiness = __import__("json").loads(READINESS_PATH.read_text(encoding="utf-8"))

    def test_resolve_selected_lane_rows_uses_recommended_tranche(self) -> None:
        rows = _resolve_selected_lane_rows(
            readiness_payload=self.readiness,
            tranche_id="recommended",
            lane_ids_override=None,
        )
        self.assertEqual([row["lane_id"] for row in rows], ["assistant_likeness", "honesty", "politeness"])

    def test_execution_packet_builds_expected_matrix(self) -> None:
        rows = _resolve_selected_lane_rows(
            readiness_payload=self.readiness,
            tranche_id="slice_a",
            lane_ids_override=None,
        )
        packet = _build_execution_packet(
            registry=self.registry,
            readiness_payload=self.readiness,
            readiness_path=READINESS_PATH,
            selected_lane_rows=rows,
            prompt_limit=4,
            judge_model="claude-sonnet-4-6",
        )
        self.assertTrue(packet["launch_recommended_now"])
        self.assertEqual(packet["condition_matrix"]["n_rows"], 3 * 6 * 3)
        self.assertEqual(packet["selected_lane_ids"], ["assistant_likeness", "honesty", "politeness"])

    def test_coherence_summary_relative_only_passes_small_drop(self) -> None:
        summary = _build_coherence_summary(
            baseline_scores=[70.0, 72.0],
            steered_scores=[68.0, 71.0],
            coherence_gate_mode="relative_only",
            coherence_max_drop=10.0,
        )
        self.assertTrue(summary["pass"])
        self.assertAlmostEqual(summary["drop_from_baseline"], 1.5)

    def test_rank_prefers_coherence_passing_metric(self) -> None:
        passing = SmokeMetric(
            layer=12,
            alpha=1.0,
            steering_shift_mean=4.0,
            reversal_shift_mean=4.0,
            bidirectional_effect=8.0,
            coherence_baseline_mean=70.0,
            coherence_steered_mean=66.0,
            coherence_drop=4.0,
            coherence_pass=True,
            n_prompts=4,
        )
        failing = SmokeMetric(
            layer=16,
            alpha=2.0,
            steering_shift_mean=8.0,
            reversal_shift_mean=8.0,
            bidirectional_effect=16.0,
            coherence_baseline_mean=70.0,
            coherence_steered_mean=40.0,
            coherence_drop=30.0,
            coherence_pass=False,
            n_prompts=4,
        )
        self.assertGreater(_rank_metric(passing), _rank_metric(failing))


if __name__ == "__main__":
    unittest.main()
