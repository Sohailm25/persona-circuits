from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.week2_trait_lane_generated_prompt_audit import _file_stats, _overlap_stats


class TraitLaneGeneratedPromptAuditTests(unittest.TestCase):
    def test_file_stats_counts_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.jsonl"
            rows = [
                {"user_query": "One"},
                {"user_query": "Two"},
                {"user_query": "one"},
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            stats = _file_stats(path)
            self.assertEqual(stats["count"], 3)
            self.assertEqual(stats["duplicate_count"], 1)

    def test_overlap_stats_reports_high_similarity_for_paraphrase(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            extraction_path = Path(tmpdir) / "extraction.jsonl"
            heldout_path = Path(tmpdir) / "heldout.jsonl"
            extraction_path.write_text(
                json.dumps({"user_query": "Is the Great Wall of China visible from space with the naked eye?"}) + "\n",
                encoding="utf-8",
            )
            heldout_path.write_text(
                json.dumps({"user_query": "I heard the Great Wall of China is visible from space with the naked eye. Is that true?"}) + "\n",
                encoding="utf-8",
            )
            stats = _overlap_stats(extraction_path, heldout_path)
            self.assertGreaterEqual(stats["max_similarity"], 0.8)


if __name__ == "__main__":
    unittest.main()
