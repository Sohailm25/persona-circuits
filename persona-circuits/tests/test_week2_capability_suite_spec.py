from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_capability_suite_spec import _build_broader_suite_spec, _build_week2_proxy_spec  # noqa: E402


class Week2CapabilitySuiteSpecTests(unittest.TestCase):
    def test_build_week2_proxy_spec_uses_artifact_fields(self) -> None:
        payload = {
            "capability_proxy": {
                "available": True,
                "n_questions": 30,
                "baseline_accuracy": 0.6,
                "steered_accuracy": 0.55,
                "degradation": 0.05,
                "pass_lt_5pct_drop": True,
            }
        }
        out = _build_week2_proxy_spec(payload)
        self.assertEqual(out["implementation"]["sample_count_cap"], 30)
        self.assertTrue(out["latest_observed"]["available"])

    def test_build_broader_suite_spec_splits_unrelated_total(self) -> None:
        cfg = {"prompts": {"unrelated_task_prompts": 150}}
        out = _build_broader_suite_spec(cfg)
        targets = [b["target_n"] for b in out["benchmarks"]]
        self.assertEqual(targets, [50, 50, 50])


if __name__ == "__main__":
    unittest.main()
