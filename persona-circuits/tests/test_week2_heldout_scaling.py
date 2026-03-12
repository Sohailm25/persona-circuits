"""Unit tests for Week 2 held-out generation scaling helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from generate_week2_heldout_prompts import CategorySpec, _scaled_specs


class Week2HeldoutScalingTests(unittest.TestCase):
    def test_scale_factor_multiplies_counts(self) -> None:
        specs = [
            CategorySpec("a", "desc", 10),
            CategorySpec("b", "desc", 5),
        ]
        scaled = _scaled_specs(specs, scale_factor=3.0)
        self.assertEqual([s.n for s in scaled], [30, 15])

    def test_target_total_preserves_sum_and_relative_mix(self) -> None:
        specs = [
            CategorySpec("a", "desc", 2),
            CategorySpec("b", "desc", 1),
            CategorySpec("c", "desc", 1),
        ]
        scaled = _scaled_specs(specs, target_total=10)
        counts = [s.n for s in scaled]

        self.assertEqual(sum(counts), 10)
        self.assertGreaterEqual(counts[0], counts[1])
        self.assertGreaterEqual(counts[0], counts[2])

    def test_invalid_scale_or_target_raises(self) -> None:
        specs = [CategorySpec("a", "desc", 2)]
        with self.assertRaises(ValueError):
            _scaled_specs(specs, scale_factor=0.0)
        with self.assertRaises(ValueError):
            _scaled_specs(specs, target_total=0)


if __name__ == "__main__":
    unittest.main()
