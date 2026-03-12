from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_cross_trait_bleed_sensitivity import (  # noqa: E402
    _entry_for_artifact,
    _infer_trait_from_label_or_payload,
    _parse_thresholds,
    _summary,
)


class Week2CrossTraitBleedSensitivityTests(unittest.TestCase):
    def test_infer_trait_prefers_payload_trait(self) -> None:
        payload = {"trait": "evil"}
        self.assertEqual(_infer_trait_from_label_or_payload("sycophancy_lane", payload), "evil")

    def test_parse_thresholds_sorts_and_deduplicates(self) -> None:
        out = _parse_thresholds("0.35,0.3,0.3,0.4")
        self.assertEqual(out, [0.3, 0.35, 0.4])

    def test_entry_for_artifact_computes_min_passing_threshold(self) -> None:
        payload = {
            "trait": "sycophancy",
            "selected": {"layer": 12, "alpha": 2.0},
            "selected_test_evaluation": {"metric": {"bidirectional_effect": 30.0}},
            "cross_trait_bleed_gate": {"off_target_to_target_ratio": 0.316, "max_allowed_fraction": 0.3},
            "quality_gates": {"cross_trait_bleed_pass": False},
        }
        entry = _entry_for_artifact("lane", payload, [0.3, 0.35, 0.4])
        self.assertEqual(entry["min_passing_threshold"], 0.35)
        self.assertFalse(entry["threshold_pass"]["0.30"])
        self.assertTrue(entry["threshold_pass"]["0.35"])

    def test_summary_aggregates_trait_counts(self) -> None:
        entries = [
            {
                "trait": "sycophancy",
                "off_target_to_target_ratio": 0.2,
                "threshold_pass": {"0.30": True, "0.40": True},
            },
            {
                "trait": "sycophancy",
                "off_target_to_target_ratio": 0.35,
                "threshold_pass": {"0.30": False, "0.40": True},
            },
        ]
        out = _summary(entries, [0.3, 0.4])
        self.assertEqual(out["traits"]["sycophancy"]["n_lanes"], 2)
        self.assertEqual(out["traits"]["sycophancy"]["passes_by_threshold"]["0.30"], 1)
        self.assertEqual(out["traits"]["sycophancy"]["passes_by_threshold"]["0.40"], 2)


if __name__ == "__main__":
    unittest.main()
