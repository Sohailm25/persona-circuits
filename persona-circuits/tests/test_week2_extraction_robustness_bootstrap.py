from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_extraction_robustness_bootstrap import (
    _bootstrap_indices,
    _normalize_trait_key,
    _pairwise_cosine_summary,
    _parse_trait_layer_map_spec,
    _resolve_trait_layer_map,
)


class Week2ExtractionRobustnessBootstrapTests(unittest.TestCase):
    def test_parse_trait_layer_map_spec_supports_machiavellian_alias(self) -> None:
        parsed = _parse_trait_layer_map_spec("sycophancy:12,machiavellian_disposition:11")
        self.assertEqual(parsed["sycophancy"], 12)
        self.assertEqual(parsed["evil"], 11)

    def test_normalize_trait_key_maps_machiavellian_to_evil(self) -> None:
        self.assertEqual(_normalize_trait_key("machiavellian_disposition"), "evil")
        self.assertEqual(_normalize_trait_key("sycophancy"), "sycophancy")

    def test_resolve_trait_layer_map_from_scope_payload(self) -> None:
        payload = {
            "trait_scope": {
                "sycophancy": {"selected_primary_combo": {"layer": 12}},
                "evil": {"selected_primary_combo": {"layer": 11}},
            }
        }
        resolved = _resolve_trait_layer_map(
            trait_scope_payload=payload,
            traits=["sycophancy", "evil"],
            override_map=None,
        )
        self.assertEqual(resolved, {"sycophancy": 12, "evil": 11})

    def test_bootstrap_indices_have_expected_shape(self) -> None:
        draws = _bootstrap_indices(n_rows=10, subset_size=4, n_bootstrap=6, seed=42)
        self.assertEqual(len(draws), 6)
        for row in draws:
            self.assertEqual(len(row), 4)
            self.assertEqual(len(set(row)), 4)
            self.assertTrue(all(0 <= idx < 10 for idx in row))

    def test_pairwise_cosine_summary_returns_expected_keys(self) -> None:
        vectors = [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.8, 0.2, 0.0],
        ]
        summary = _pairwise_cosine_summary(vectors)  # type: ignore[arg-type]
        self.assertEqual(summary["n_vectors"], 3)
        self.assertEqual(summary["n_pairs"], 3)
        self.assertIsNotNone(summary["p05"])
        self.assertGreaterEqual(summary["max"], summary["min"])


if __name__ == "__main__":
    unittest.main()
