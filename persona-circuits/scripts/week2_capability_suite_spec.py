"""Week 2 capability-suite boundary specification artifact.

Defines what is gated in Week 2 versus what is required for stronger capability-preservation claims.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
RESULTS_DIR = ROOT / "results" / "stage1_extraction"


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_week2_proxy_spec(artifact: dict[str, Any]) -> dict[str, Any]:
    cap = artifact.get("capability_proxy", {})
    available = bool(cap.get("available", False))
    return {
        "gate_name": "week2_capability_proxy",
        "benchmark": "MMLU sample",
        "implementation": {
            "sample_count_cap": int(cap.get("n_questions", 30) or 30),
            "metric": "accuracy drop (baseline_accuracy - steered_accuracy)",
            "pass_threshold": "<= 0.05",
            "availability_required_by_default": True,
            "override_flag": "--allow-missing-capability-proxy",
        },
        "latest_observed": {
            "available": available,
            "n_questions": cap.get("n_questions"),
            "baseline_accuracy": cap.get("baseline_accuracy"),
            "steered_accuracy": cap.get("steered_accuracy"),
            "degradation": cap.get("degradation"),
            "pass_lt_5pct_drop": cap.get("pass_lt_5pct_drop"),
        },
        "evidence_status": {
            "implementation_fields": "known",
            "latest_observed_values": "known",
            "claim_strength": "inferred",
        },
    }


def _build_broader_suite_spec(config: dict[str, Any]) -> dict[str, Any]:
    unrelated_total = int(config.get("prompts", {}).get("unrelated_task_prompts", 150))
    per_benchmark_target = int(unrelated_total // 3)
    return {
        "suite_name": "capability_preservation_broader_suite",
        "benchmarks": [
            {"name": "TriviaQA", "target_n": per_benchmark_target, "status": "pending_implementation"},
            {"name": "GSM8K", "target_n": per_benchmark_target, "status": "pending_implementation"},
            {"name": "HumanEval", "target_n": per_benchmark_target, "status": "pending_implementation"},
        ],
        "intended_use": "Stronger capability-preservation claims beyond Week 2 interim gate.",
        "evidence_status": {
            "benchmark_targets": "known",
            "execution_status": "known",
            "future_claim_support": "inferred",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--week2-artifact",
        default="results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json",
        help="Week2 behavioral artifact used to extract current capability-proxy implementation evidence.",
    )
    args = parser.parse_args()

    config = _load_yaml(CONFIG_PATH)
    week2_artifact_path = ROOT / args.week2_artifact
    week2_payload = _load_json(week2_artifact_path)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_capability_suite_spec",
        "inputs": {
            "config": str(CONFIG_PATH.relative_to(ROOT)),
            "week2_artifact": str(week2_artifact_path.relative_to(ROOT)),
        },
        "week2_proxy_gate": _build_week2_proxy_spec(week2_payload),
        "broader_suite_requirement": _build_broader_suite_spec(config),
        "governance_note": {
            "week2_closeout_use": "MMLU proxy is sufficient for interim Week2 gate under frozen policy.",
            "strong_claim_boundary": "Do not claim broad capability preservation until the broader suite is implemented and run.",
        },
        "evidence_status": {
            "config_fields": "known",
            "week2_artifact_fields": "known",
            "policy_interpretation": "inferred",
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_capability_suite_spec_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "output_path": str(out_path),
                "artifact_type": report["artifact_type"],
                "week2_proxy_gate": report["week2_proxy_gate"]["gate_name"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
