"""Parity checks ensuring trait-lane scaffolding does not mutate legacy Week 2 defaults."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from generate_prompt_datasets import CATEGORIES as TRAIN_CATEGORIES
from generate_week2_heldout_prompts import HELDOUT_CATEGORIES
from week2_extract_persona_vectors import DEFAULT_TRAITS as EXTRACTION_DEFAULT_TRAITS
from week2_extraction_position_ablation import DEFAULT_TRAITS as POSITION_DEFAULT_TRAITS
from week2_extraction_robustness_bootstrap import DEFAULT_TRAITS as ROBUSTNESS_DEFAULT_TRAITS


class Week2TraitLaneParityTests(unittest.TestCase):
    def test_legacy_prompt_generation_traits_unchanged(self) -> None:
        self.assertEqual(sorted(TRAIN_CATEGORIES.keys()), ["evil", "hallucination", "sycophancy"])
        self.assertEqual(sorted(HELDOUT_CATEGORIES.keys()), ["evil", "hallucination", "sycophancy"])

    def test_legacy_extraction_defaults_unchanged(self) -> None:
        self.assertEqual(EXTRACTION_DEFAULT_TRAITS, ["sycophancy", "evil", "hallucination"])
        self.assertEqual(POSITION_DEFAULT_TRAITS, ("sycophancy", "evil", "hallucination"))
        self.assertEqual(ROBUSTNESS_DEFAULT_TRAITS, ("sycophancy", "evil"))


if __name__ == "__main__":
    unittest.main()
