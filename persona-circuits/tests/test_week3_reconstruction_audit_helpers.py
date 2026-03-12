"""Unit tests for Week 3 reconstruction audit helper functions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week3_sae_reconstruction_audit import (  # noqa: E402
    _extract_probe_layers,
    _resolve_claim_layers,
    _stage2_policy_from_config,
)


class Week3ReconstructionAuditHelpersTests(unittest.TestCase):
    def test_extract_probe_layers_from_seed_reports_wrapper(self) -> None:
        payload = {
            "seed_reports": {
                "42": {"inputs": {"layer": 12}, "model_results": {}},
                "123": {"inputs": {"layer": 15}, "model_results": {}},
                "456": {"inputs": {"layer": 12}, "model_results": {}},
            }
        }
        self.assertEqual(_extract_probe_layers(payload), [12, 15])

    def test_extract_probe_layers_from_single_report(self) -> None:
        payload = {"inputs": {"layer": 14}, "model_results": {}}
        self.assertEqual(_extract_probe_layers(payload), [14])

    def test_resolve_claim_layers_maps_machiavellian_to_evil_scope(self) -> None:
        payload = {
            "stage2_scope_recommendation": {
                "primary_claim_traits": ["sycophancy", "machiavellian_disposition"]
            },
            "trait_scope": {
                "sycophancy": {"selected_primary_combo": {"layer": 12}},
                "evil": {"selected_primary_combo": {"layer": 12}},
            },
        }
        out = _resolve_claim_layers(payload)
        self.assertEqual(out["claim_layers_by_trait"]["sycophancy"], 12)
        self.assertEqual(out["claim_layers_by_trait"]["machiavellian_disposition"], 12)
        self.assertEqual(out["claim_layers_unique"], [12])
        self.assertEqual(out["missing_traits"], [])

    def test_stage2_policy_defaults_and_overrides(self) -> None:
        defaults = _stage2_policy_from_config({})
        self.assertFalse(defaults["decomposition_start_requires_cross_source_overlap"])
        self.assertTrue(defaults["cross_source_claims_require_overlap"])

        cfg = {
            "governance": {
                "week3_stage2_policy": {
                    "decomposition_start_requires_cross_source_overlap": True,
                    "cross_source_claims_require_overlap": False,
                }
            }
        }
        overridden = _stage2_policy_from_config(cfg)
        self.assertTrue(overridden["decomposition_start_requires_cross_source_overlap"])
        self.assertFalse(overridden["cross_source_claims_require_overlap"])


if __name__ == "__main__":
    unittest.main()
