"""Unit tests for Week 2 vector diagnostics summary handling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_vector_diagnostics import _augment_summary_norm_diagnostics


class Week2VectorDiagnosticsTests(unittest.TestCase):
    def test_cosine_margin_marked_unknown_when_absent(self) -> None:
        summary = {
            "diagnostics": {
                "sycophancy": {
                    "layers": {
                        "11": {
                            "raw_vector_norm": 1.0,
                            "projection_margin_mean": 0.8,
                        }
                    }
                }
            }
        }

        diagnostics = _augment_summary_norm_diagnostics(summary)
        trait_diag = diagnostics["sycophancy"]
        layer_diag = trait_diag["layers"]["11"]

        self.assertIsNone(layer_diag["cosine_margin_mean"])
        self.assertEqual(layer_diag["cosine_margin_evidence"], "unknown")
        self.assertFalse(trait_diag["cosine_margin_data_present"])
        self.assertIsNone(trait_diag["trend_checks"]["cosine_margin_monotonic_non_decreasing"])

    def test_cosine_margin_marked_known_when_present(self) -> None:
        summary = {
            "diagnostics": {
                "evil": {
                    "layers": {
                        "12": {
                            "raw_vector_norm": 2.0,
                            "projection_margin_mean": 1.5,
                            "cosine_margin_mean": 0.42,
                        }
                    }
                }
            }
        }

        diagnostics = _augment_summary_norm_diagnostics(summary)
        trait_diag = diagnostics["evil"]
        layer_diag = trait_diag["layers"]["12"]

        self.assertAlmostEqual(layer_diag["cosine_margin_mean"], 0.42, places=6)
        self.assertEqual(layer_diag["cosine_margin_evidence"], "known")
        self.assertTrue(trait_diag["cosine_margin_data_present"])
        self.assertTrue(trait_diag["trend_checks"]["cosine_margin_monotonic_non_decreasing"])


if __name__ == "__main__":
    unittest.main()
