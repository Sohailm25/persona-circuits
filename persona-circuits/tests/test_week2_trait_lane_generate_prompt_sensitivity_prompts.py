from __future__ import annotations

import unittest

from scripts.week2_trait_lane_generate_prompt_sensitivity_prompts import _validate_perturbation


class PromptSensitivityGenerationTests(unittest.TestCase):
    def test_rejects_near_duplicate(self) -> None:
        ok, meta = _validate_perturbation(
            source_query="Can you help me rewrite this email to sound more professional?",
            perturbed_query="Can you help me rewrite this email to sound more professional?",
            seen=set(),
        )
        self.assertFalse(ok)
        self.assertIn("unchanged", meta["reasons"])

    def test_rejects_added_style_cue(self) -> None:
        ok, meta = _validate_perturbation(
            source_query="Can you review this note to my landlord?",
            perturbed_query="Can you politely review this note to my landlord?",
            seen=set(),
        )
        self.assertFalse(ok)
        self.assertIn("added_explicit_style_cue", meta["reasons"])

    def test_accepts_distinct_noncue_rewrite(self) -> None:
        ok, meta = _validate_perturbation(
            source_query="I need help turning this update into a clearer project summary for my team.",
            perturbed_query="Could you help me turn this project update into a summary my team can scan quickly?",
            seen=set(),
        )
        self.assertTrue(ok)
        self.assertLess(meta["similarity"], 0.92)


if __name__ == "__main__":
    unittest.main()
