"""Unit tests for extraction-free prompt preparation helpers."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_prepare_extraction_free_eval import (
    _build_records,
    _load_exemplar_bank,
    _select_set_index,
)


def _toy_rows(n: int = 6) -> list[dict[str, object]]:
    return [
        {
            "id": i,
            "user_query": f"query {i}",
            "category": "toy",
            "ground_truth": "N/A",
        }
        for i in range(n)
    ]


def _toy_exemplar_bank_payload() -> dict[str, object]:
    mk_examples = lambda prefix: [  # noqa: E731
        {"user": f"{prefix} user {i}", "assistant": f"{prefix} assistant {i}"}
        for i in range(4)
    ]
    return {
        "version": 1,
        "traits": {
            "sycophancy": [
                {"set_id": "s1", "high": mk_examples("h1"), "low": mk_examples("l1")},
                {"set_id": "s2", "high": mk_examples("h2"), "low": mk_examples("l2")},
                {"set_id": "s3", "high": mk_examples("h3"), "low": mk_examples("l3")},
            ]
        },
    }


class Week2PrepareExtractionFreeEvalTests(unittest.TestCase):
    def test_select_set_index_is_deterministic(self) -> None:
        idx1, digest1 = _select_set_index(trait="sycophancy", source_row_id=7, seed=42, n_sets=6)
        idx2, digest2 = _select_set_index(trait="sycophancy", source_row_id=7, seed=42, n_sets=6)
        self.assertEqual(idx1, idx2)
        self.assertEqual(digest1, digest2)

    def test_build_records_uses_multiple_sets(self) -> None:
        sets = _toy_exemplar_bank_payload()["traits"]["sycophancy"]  # type: ignore[index]
        records, usage = _build_records(
            rows=_toy_rows(8),
            trait="sycophancy",
            n_eval=8,
            seed=42,
            exemplar_sets=sets,  # type: ignore[arg-type]
        )
        used = [k for k, v in usage.items() if v > 0]
        self.assertEqual(len(records), 8)
        self.assertGreaterEqual(len(used), 2)
        self.assertTrue(all("fewshot_set_id" in rec for rec in records))

    def test_load_exemplar_bank_rejects_small_sets(self) -> None:
        bad_payload = _toy_exemplar_bank_payload()
        bad_payload["traits"]["sycophancy"][0]["high"] = bad_payload["traits"]["sycophancy"][0]["high"][:2]  # type: ignore[index]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bank.json"
            path.write_text(json.dumps(bad_payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                _load_exemplar_bank(path=path, min_examples_per_condition=4)


if __name__ == "__main__":
    unittest.main()
