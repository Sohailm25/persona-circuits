"""Unit tests for week2_machiavellian_external_transfer helpers."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_machiavellian_external_transfer import _extract_score_json, _resolve_selected_combo  # noqa: E402


class Week2MachiavellianExternalTransferTests(unittest.TestCase):
    def test_extract_score_json_strict_block(self) -> None:
        self.assertEqual(_extract_score_json('{"score": 83}'), 83)

    def test_extract_score_json_fallback_regex(self) -> None:
        self.assertEqual(_extract_score_json("Score: 17"), 17)

    def test_resolve_selected_combo_prefers_cli_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "scope.json"
            path.write_text("{}", encoding="utf-8")
            out = _resolve_selected_combo(layer=12, alpha=3.0, trait_scope_path=path)
            self.assertEqual(out["layer"], 12)
            self.assertEqual(out["alpha"], 3.0)
            self.assertEqual(out["source"], "cli_override")

    def test_resolve_selected_combo_from_scope_artifact(self) -> None:
        payload = {
            "trait_scope": {
                "evil": {
                    "selected_primary_combo": {
                        "layer": 12,
                        "alpha": 3.0,
                    }
                }
            }
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "scope.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = _resolve_selected_combo(layer=-1, alpha=-1.0, trait_scope_path=path)
            self.assertEqual(out["layer"], 12)
            self.assertEqual(out["alpha"], 3.0)
            self.assertEqual(out["source"], "scope.json")


if __name__ == "__main__":
    unittest.main()
