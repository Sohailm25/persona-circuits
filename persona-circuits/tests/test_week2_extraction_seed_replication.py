"""Tests for week2_extraction_seed_replication helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_extraction_seed_replication import _normalize_csv_ints, _pairwise_seed_cosines  # noqa: E402


class Week2ExtractionSeedReplicationTests(unittest.TestCase):
    def test_normalize_csv_ints_deduplicates(self) -> None:
        self.assertEqual(_normalize_csv_ints("42,123,42,456"), [42, 123, 456])

    def test_pairwise_seed_cosines_shape(self) -> None:
        vectors = {
            42: {"sycophancy": {"12": [1.0, 0.0]}},
            123: {"sycophancy": {"12": [0.9, 0.1]}},
            456: {"sycophancy": {"12": [0.8, 0.2]}},
        }
        out = _pairwise_seed_cosines(vectors, traits=["sycophancy"], layers=[12])
        layer = out["sycophancy"]["layers"]["12"]
        self.assertEqual(layer["n_pairs"], 3)
        self.assertIsNotNone(layer["min_pairwise_cosine"])
        self.assertGreaterEqual(layer["mean_pairwise_cosine"], layer["min_pairwise_cosine"])


if __name__ == "__main__":
    unittest.main()
