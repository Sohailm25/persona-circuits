"""Compare Week 2 targeted runs between rollout settings (e.g., 3 vs 5)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
REQUIRED_METRIC_KEYS = ("steering_shift_mean", "reversal_shift_mean", "bidirectional_effect")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _selected_metric_block(report: dict[str, Any]) -> dict[str, Any]:
    metric = report.get("selected_test_evaluation", {}).get("metric")
    if not isinstance(metric, dict):
        raise KeyError("selected_test_evaluation.metric is missing")
    missing = [key for key in REQUIRED_METRIC_KEYS if key not in metric]
    if missing:
        raise KeyError(f"selected_test_evaluation.metric missing required keys: {missing}")
    return metric


def _metric(report: dict[str, Any], key: str) -> float:
    metric = _selected_metric_block(report)
    value = metric[key]
    return float(value)


def _compare_reports(trait: str, rollout3: dict[str, Any], rollout5: dict[str, Any]) -> dict[str, Any]:
    mkeys = list(REQUIRED_METRIC_KEYS)
    metric_delta: dict[str, Any] = {}
    for key in mkeys:
        v3 = _metric(rollout3, key)
        v5 = _metric(rollout5, key)
        metric_delta[key] = {
            "rollout3": v3,
            "rollout5": v5,
            "delta_rollout5_minus_rollout3": float(v5 - v3),
        }

    g3 = rollout3.get("quality_gates", {})
    g5 = rollout5.get("quality_gates", {})
    gate_delta = {
        "overall_pass": {"rollout3": g3.get("overall_pass"), "rollout5": g5.get("overall_pass")},
        "coherence_pass": {"rollout3": g3.get("coherence_pass"), "rollout5": g5.get("coherence_pass")},
        "cross_trait_bleed_pass": {
            "rollout3": g3.get("cross_trait_bleed_pass"),
            "rollout5": g5.get("cross_trait_bleed_pass"),
        },
        "bidirectional_effect_pass": {
            "rollout3": g3.get("bidirectional_effect_pass"),
            "rollout5": g5.get("bidirectional_effect_pass"),
        },
    }

    return {
        "trait": trait,
        "selected_combo_rollout3": rollout3.get("selected", {}),
        "selected_combo_rollout5": rollout5.get("selected", {}),
        "run_metadata_rollout3": rollout3.get("run_metadata", {}),
        "run_metadata_rollout5": rollout5.get("run_metadata", {}),
        "metrics": metric_delta,
        "quality_gates": gate_delta,
        "failing_gates_rollout3": [k for k, v in g3.items() if isinstance(v, bool) and not v],
        "failing_gates_rollout5": [k for k, v in g5.items() if isinstance(v, bool) and not v],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--syc-rollout3", required=True)
    parser.add_argument("--syc-rollout5", required=True)
    parser.add_argument("--evil-rollout3", required=True)
    parser.add_argument("--evil-rollout5", required=True)
    args = parser.parse_args()

    syc3 = _load(Path(args.syc_rollout3))
    syc5 = _load(Path(args.syc_rollout5))
    evil3 = _load(Path(args.evil_rollout3))
    evil5 = _load(Path(args.evil_rollout5))

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_rollout_stability_sensitivity",
        "comparisons": {
            "sycophancy": _compare_reports("sycophancy", syc3, syc5),
            "evil": _compare_reports("evil", evil3, evil5),
        },
        "evidence_status": {
            "input_artifacts": "known",
            "stability_interpretation": "inferred",
        },
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_rollout_stability_sensitivity_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({"report_path": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()
