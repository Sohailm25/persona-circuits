"""Evaluate Week 2 coherence gate behavior under alternate policy modes.

This script does not run generation. It reads completed Week 2 artifacts and
re-scores coherence pass/fail under:
- absolute_and_relative
- relative_only
- absolute_only
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _evaluate_mode(coherence_block: dict[str, Any], mode: str) -> bool:
    pass_min = bool(coherence_block.get("pass_min_score", False))
    pass_drop = bool(coherence_block.get("pass_max_drop", False))
    if mode == "absolute_and_relative":
        return bool(pass_min and pass_drop)
    if mode == "relative_only":
        return pass_drop
    if mode == "absolute_only":
        return pass_min
    raise ValueError(f"Unsupported mode: {mode}")


def _trait_snapshot(trait: str, payload: dict[str, Any]) -> dict[str, Any]:
    coherence = payload.get("coherence", {})
    modes = {
        mode: _evaluate_mode(coherence, mode)
        for mode in ["absolute_and_relative", "relative_only", "absolute_only"]
    }
    return {
        "trait": trait,
        "selected": payload.get("selected", {}),
        "coherence": {
            "baseline_mean": coherence.get("baseline_mean"),
            "steered_mean": coherence.get("steered_mean"),
            "drop_from_baseline": coherence.get("drop_from_baseline"),
            "min_score_threshold": coherence.get("min_score_threshold"),
            "max_drop_threshold": coherence.get("max_drop_threshold"),
            "pass_min_score": coherence.get("pass_min_score"),
            "pass_max_drop": coherence.get("pass_max_drop"),
            "pass_current_artifact": coherence.get("pass"),
        },
        "mode_pass": modes,
        "current_quality_gate_coherence_pass": payload.get("quality_gates", {}).get("coherence_pass"),
        "current_quality_gate_overall_pass": payload.get("quality_gates", {}).get("overall_pass"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--syc-artifact",
        default="results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json",
    )
    parser.add_argument(
        "--evil-artifact",
        default="results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260303T081318Z.json",
    )
    args = parser.parse_args()

    syc_path = ROOT / args.syc_artifact
    evil_path = ROOT / args.evil_artifact

    syc = _load(syc_path)
    evil = _load(evil_path)

    trait_snapshots = {
        "sycophancy": _trait_snapshot("sycophancy", syc),
        "evil": _trait_snapshot("evil", evil),
    }

    mode_summary: dict[str, Any] = {}
    for mode in ["absolute_and_relative", "relative_only", "absolute_only"]:
        passes = [bool(trait_snapshots[t]["mode_pass"][mode]) for t in ["sycophancy", "evil"]]
        mode_summary[mode] = {
            "n_traits_pass": int(sum(passes)),
            "n_traits": len(passes),
            "all_pass": bool(all(passes)),
        }

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_coherence_policy_diagnostic",
        "inputs": {
            "sycophancy_artifact": str(syc_path.relative_to(ROOT)),
            "evil_artifact": str(evil_path.relative_to(ROOT)),
        },
        "evidence_status": {
            "source_coherence_metrics": "known",
            "policy_reinterpretation": "inferred",
        },
        "trait_snapshots": trait_snapshots,
        "mode_summary": mode_summary,
        "recommendation": {
            "known": "absolute min-score threshold is currently binding for both traits while max-drop passes for both.",
            "inferred": "if the objective is to prevent steering-induced degradation, relative-only gating is the more targeted criterion.",
            "unknown": "whether changing coherence gate policy should supersede existing hardening NO-GO without parallel governance approval.",
        },
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"week2_coherence_policy_diagnostic_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({"report_path": str(out)}, indent=2))


if __name__ == "__main__":
    main()
