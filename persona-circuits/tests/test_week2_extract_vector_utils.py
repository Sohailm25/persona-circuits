"""Unit tests for Week 2 vector extraction diagnostics helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_extract_persona_vectors import _compute_cross_trait_cosines, _resolve_extraction_method


class Week2ExtractVectorUtilsTests(unittest.TestCase):
    def test_cross_trait_cosines_expected_geometry(self) -> None:
        vectors = {
            "sycophancy": {
                11: [1.0, 0.0, 0.0],
                12: [1.0, 0.0, 0.0],
            },
            "evil": {
                11: [0.0, 1.0, 0.0],
                12: [1.0, 0.0, 0.0],
            },
            "hallucination": {
                11: [0.0, 0.0, 1.0],
                12: [-1.0, 0.0, 0.0],
            },
        }
        result = _compute_cross_trait_cosines(vectors=vectors, traits=["sycophancy", "evil", "hallucination"], layers=[11, 12])

        self.assertAlmostEqual(result["11"]["sycophancy"]["evil"], 0.0, places=6)
        self.assertAlmostEqual(result["11"]["sycophancy"]["hallucination"], 0.0, places=6)
        self.assertAlmostEqual(result["12"]["sycophancy"]["evil"], 1.0, places=6)
        self.assertAlmostEqual(result["12"]["sycophancy"]["hallucination"], -1.0, places=6)

    def test_cross_trait_cosines_skips_missing_layer(self) -> None:
        vectors = {
            "sycophancy": {11: [1.0, 0.0]},
            "evil": {11: [0.0, 1.0], 12: [1.0, 0.0]},
            "hallucination": {11: [0.0, 1.0], 12: [1.0, 0.0]},
        }
        result = _compute_cross_trait_cosines(vectors=vectors, traits=["sycophancy", "evil", "hallucination"], layers=[11, 12])

        self.assertIn("11", result)
        self.assertNotIn("12", result)

    def test_cross_trait_cosines_rejects_zero_norm(self) -> None:
        vectors = {
            "sycophancy": {11: [0.0, 0.0]},
            "evil": {11: [1.0, 0.0]},
            "hallucination": {11: [0.0, 1.0]},
        }
        with self.assertRaises(ValueError):
            _compute_cross_trait_cosines(vectors=vectors, traits=["sycophancy", "evil", "hallucination"], layers=[11])

    def test_resolve_extraction_method_prefers_explicit_arg(self) -> None:
        cfg = {"steering": {"extraction_method": "prompt_last"}}
        self.assertEqual(_resolve_extraction_method(cfg, "response_mean"), "response_mean")
        self.assertEqual(_resolve_extraction_method(cfg, "RESPONSE_LAST"), "response_last")

    def test_resolve_extraction_method_uses_config_default(self) -> None:
        cfg = {"steering": {"extraction_method": "response_mean"}}
        self.assertEqual(_resolve_extraction_method(cfg, ""), "response_mean")
        self.assertEqual(_resolve_extraction_method({}, ""), "prompt_last")

    def test_resolve_extraction_method_rejects_unknown(self) -> None:
        cfg = {"steering": {"extraction_method": "unknown"}}
        with self.assertRaises(ValueError):
            _resolve_extraction_method(cfg, "")
        with self.assertRaises(ValueError):
            _resolve_extraction_method({}, "foo")


if __name__ == "__main__":
    unittest.main()
