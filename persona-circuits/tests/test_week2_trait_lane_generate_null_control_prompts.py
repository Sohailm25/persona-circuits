from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.week2_trait_lane_generate_null_control_prompts import (
    build_null_control_prompt_summary,
)


class TraitLaneNullControlPromptGenerationTests(unittest.TestCase):
    def test_build_summary_balances_flips_within_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            extraction_path = tmp / "extraction.jsonl"
            heldout_path = tmp / "heldout.jsonl"
            extraction_rows = [
                {
                    "id": idx,
                    "lane_id": "politeness",
                    "category": "a" if idx < 4 else "b",
                    "user_query": f"q{idx}",
                    "system_high": "HIGH",
                    "system_low": "LOW",
                    "judge_rubric_id": "politeness",
                }
                for idx in range(7)
            ]
            heldout_rows = [
                {
                    "id": idx,
                    "lane_id": "politeness",
                    "category": "a" if idx < 3 else "b",
                    "user_query": f"h{idx}",
                    "system_high": "HIGH",
                    "system_low": "LOW",
                    "judge_rubric_id": "politeness",
                }
                for idx in range(5)
            ]
            extraction_path.write_text("\n".join(json.dumps(r) for r in extraction_rows) + "\n", encoding="utf-8")
            heldout_path.write_text("\n".join(json.dumps(r) for r in heldout_rows) + "\n", encoding="utf-8")
            packet = {
                "source_lane_id": "politeness",
                "recommended_control_design": {
                    "control_id": "politeness_label_permutation_null_v1",
                    "design_type": "category_stratified_label_permutation",
                    "source_prompt_paths": {
                        "extraction": str(extraction_path),
                        "heldout": str(heldout_path),
                    },
                    "preserved_fields": ["id", "category", "user_query", "judge_rubric_id", "system_high", "system_low"],
                    "permutation_policy": {"seed": 42},
                },
            }
            summary, prompt_rows = build_null_control_prompt_summary(
                null_control_packet=packet,
                null_control_packet_path=tmp / "packet.json",
                output_suffix="unit",
            )

        self.assertEqual(summary["control_id"], "politeness_label_permutation_null_v1")
        self.assertEqual(summary["counts"]["extraction"]["n_rows"], 7)
        self.assertEqual(summary["counts"]["heldout"]["n_rows"], 5)
        extraction_by_category = {row["category"]: row for row in summary["counts"]["extraction"]["categories"]}
        heldout_by_category = {row["category"]: row for row in summary["counts"]["heldout"]["categories"]}
        self.assertEqual(extraction_by_category["a"]["n_flipped"], 2)
        self.assertEqual(extraction_by_category["b"]["n_flipped"], 1)
        self.assertEqual(heldout_by_category["a"]["n_flipped"], 1)
        self.assertEqual(heldout_by_category["b"]["n_flipped"], 1)
        self.assertTrue(any(row["null_control_polarity_flipped"] for row in prompt_rows["extraction"]))
        flipped = next(row for row in prompt_rows["extraction"] if row["null_control_polarity_flipped"])
        self.assertEqual(flipped["system_high"], "LOW")
        self.assertEqual(flipped["system_low"], "HIGH")
        self.assertTrue(all(row["lane_id"] == "politeness_label_permutation_null_v1" for row in prompt_rows["heldout"]))


if __name__ == "__main__":
    unittest.main()
