#!/usr/bin/env python3
"""Diagnose which Stage4 thresholds are binding by trait/method/run."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE4_DIR = ROOT / "results" / "stage4_ablation"


def _latest_paths(pattern: str, limit: int) -> list[Path]:
    paths = sorted(STAGE4_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not paths:
        raise FileNotFoundError(f"No artifacts found for pattern: {pattern}")
    return paths[: int(limit)]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _method_binding_snapshot(
    method_payload: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any]:
    obs_reduction = method_payload.get("observed_mean_reduction")
    p_value = (
        method_payload.get("selectivity_vs_random", {}) or {}
    ).get("p_value_one_sided_ge")
    a12 = (
        method_payload.get("effect_sizes_vs_random_prompt_distribution", {}) or {}
    ).get("a12")

    necessity_thr = float(thresholds["necessity"])
    sig_thr = float(thresholds["significance"])
    a12_thr = float(thresholds["a12_minimum"])

    necessity_margin = None if obs_reduction is None else float(obs_reduction) - necessity_thr
    significance_margin = None if p_value is None else sig_thr - float(p_value)
    a12_margin = None if a12 is None else float(a12) - a12_thr

    gates = {
        "necessity": bool(method_payload.get("necessity_threshold_pass", False)),
        "significance": bool(method_payload.get("selectivity_p_threshold_pass", False)),
        "a12": bool(method_payload.get("a12_threshold_pass", False)),
    }
    failed_gates = [name for name, ok in gates.items() if not ok]

    # Distances below threshold; lower (more negative margin) means tighter blocker.
    distances = {
        "necessity": None if necessity_margin is None else max(0.0, -necessity_margin),
        "significance": None if significance_margin is None else max(0.0, -significance_margin),
        "a12": None if a12_margin is None else max(0.0, -a12_margin),
    }
    binding_gate = None
    binding_distance = None
    present = {k: v for k, v in distances.items() if v is not None}
    if present:
        binding_gate = max(present, key=lambda k: present[k])
        binding_distance = float(present[binding_gate])

    return {
        "observed": {
            "mean_reduction": obs_reduction,
            "p_value_one_sided_ge": p_value,
            "a12": a12,
        },
        "thresholds": {
            "necessity": necessity_thr,
            "significance": sig_thr,
            "a12_minimum": a12_thr,
        },
        "margins": {
            "necessity_margin": necessity_margin,
            "significance_margin": significance_margin,
            "a12_margin": a12_margin,
        },
        "gates": gates,
        "failed_gates": failed_gates,
        "binding_gate": binding_gate,
        "binding_distance": binding_distance,
    }


def _analyze_artifact(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    thresholds = payload.get("thresholds", {})
    results_by_trait = payload.get("results_by_trait", {})
    out_traits: dict[str, Any] = {}

    for trait, trait_payload in results_by_trait.items():
        methods = trait_payload.get("methods", {})
        method_rows: dict[str, Any] = {}
        for method_name, method_payload in methods.items():
            method_rows[method_name] = _method_binding_snapshot(method_payload, thresholds)
        out_traits[trait] = {
            "validity": {
                "n_prompts": trait_payload.get("n_prompts"),
                "baseline_effect_abs_summary": (
                    trait_payload.get("behavioral_score_baseline", {}) or {}
                ).get("steered_effect_abs_summary"),
            },
            "methods": method_rows,
        }

    return {
        "artifact_path": str(path),
        "artifact_timestamp_utc": payload.get("timestamp_utc"),
        "thresholds": thresholds,
        "traits": out_traits,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Stage4 threshold-binding diagnostic from behavioral-ablation artifacts."
    )
    parser.add_argument(
        "--artifacts",
        type=str,
        default="",
        help=(
            "Comma-separated artifact paths. If omitted, latest N matching artifacts are used from "
            "results/stage4_ablation."
        ),
    )
    parser.add_argument(
        "--latest-limit",
        type=int,
        default=4,
        help="How many latest artifacts to include when --artifacts is omitted (default: 4).",
    )
    args = parser.parse_args()

    if args.artifacts.strip():
        paths = [Path(x.strip()) for x in args.artifacts.split(",") if x.strip()]
    else:
        paths = _latest_paths("week3_stage4_behavioral_ablation_*.json", limit=int(args.latest_limit))

    analyses = [_analyze_artifact(path.resolve()) for path in paths]

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "artifacts": [str(p.resolve()) for p in paths],
            "latest_limit": int(args.latest_limit),
        },
        "evidence_status": {
            "artifact_contents": "known",
            "binding_gate_labels": "inferred",
        },
        "analyses": analyses,
    }

    out_path = STAGE4_DIR / (
        f"week3_stage4_threshold_binding_diagnostic_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "n_analyzed": len(analyses)}, indent=2))


if __name__ == "__main__":
    main()

