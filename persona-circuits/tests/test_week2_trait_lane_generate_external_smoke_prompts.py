"""Tests for trait-lane external-smoke prompt generation helpers."""

from __future__ import annotations

import unittest

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_generate_external_smoke_prompts import _resolve_external_lane_ids


class TraitLaneExternalSmokeGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()

    def test_resolve_external_lane_ids_accepts_supported_lanes(self) -> None:
        lane_ids = _resolve_external_lane_ids(
            self.registry,
            lane_ids=["honesty", "lying"],
            family_ids=[],
        )
        self.assertEqual(lane_ids, ["honesty", "lying"])

    def test_resolve_external_lane_ids_rejects_unsupported_lane(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_external_lane_ids(
                self.registry,
                lane_ids=["politeness"],
                family_ids=[],
            )


if __name__ == "__main__":
    unittest.main()
