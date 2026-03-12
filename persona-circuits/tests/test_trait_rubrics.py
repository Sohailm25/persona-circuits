from __future__ import annotations

import unittest

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.shared.trait_rubrics import RUBRICS, supported_rubric_ids


class TraitRubricsTests(unittest.TestCase):
    def test_registry_judge_rubrics_are_registered(self) -> None:
        registry = load_trait_lane_registry()
        expected = set()
        for family in registry["families"].values():
            for lane in family["lanes"].values():
                expected.add(str(lane["judge_rubric_id"]))
        self.assertTrue(expected.issubset(supported_rubric_ids()))

    def test_core_rubrics_remain_available(self) -> None:
        for rubric_id in ("sycophancy", "evil", "hallucination", "coherence"):
            self.assertIn(rubric_id, RUBRICS)

    def test_new_lane_rubric_text_mentions_construct(self) -> None:
        self.assertIn("assistant-like", RUBRICS["assistant_likeness"].lower())
        self.assertIn("truthful", RUBRICS["honesty"].lower())
        self.assertIn("falsehood", RUBRICS["lying"].lower())
        self.assertIn("optimistic", RUBRICS["optimism"].lower())


if __name__ == "__main__":
    unittest.main()
