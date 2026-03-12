"""Week 2 manual concordance policy closure artifact.

Converts low-power manual concordance into an explicit governance interpretation.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
DEFAULT_CONCORDANCE = ROOT / "results" / "stage1_extraction" / "week2_primary_manual_concordance_ratings_20260227T202822Z.json"
DEFAULT_SYC = ROOT / "results" / "stage1_extraction" / "week2_behavioral_validation_upgrade_sycophancy_20260227T191157Z.json"
DEFAULT_EVIL = ROOT / "results" / "stage1_extraction" / "week2_behavioral_validation_upgrade_evil_20260227T171643Z.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("n must be positive")
    phat = successes / n
    denom = 1 + (z**2 / n)
    center = (phat + (z**2 / (2 * n))) / denom
    margin = (z / denom) * math.sqrt((phat * (1 - phat) / n) + (z**2 / (4 * n**2)))
    return float(max(0.0, center - margin)), float(min(1.0, center + margin))


def _count_sign_matches(entries: list[dict[str, Any]]) -> tuple[int, int]:
    successes = 0
    n = 0
    for entry in entries:
        judge_plus = entry.get("judge_plus_score")
        judge_minus = entry.get("judge_minus_score")
        manual_plus = entry.get("manual_plus_score")
        manual_minus = entry.get("manual_minus_score")
        if any(v is None for v in (judge_plus, judge_minus, manual_plus, manual_minus)):
            continue
        judge_delta = float(judge_plus) - float(judge_minus)
        manual_delta = float(manual_plus) - float(manual_minus)
        judge_sign = 1 if judge_delta > 0 else (-1 if judge_delta < 0 else 0)
        manual_sign = 1 if manual_delta > 0 else (-1 if manual_delta < 0 else 0)
        successes += int(judge_sign == manual_sign)
        n += 1
    return successes, n


def _judge_kappa_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    cal = payload.get("judge_calibration", {})
    return {
        "n_pairs": cal.get("n_pairs"),
        "kappa": cal.get("kappa"),
        "kappa_pass": cal.get("kappa_pass"),
        "pairwise_sign_agreement": cal.get("pairwise_sign_agreement"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concordance-artifact", default=str(DEFAULT_CONCORDANCE))
    parser.add_argument("--sycophancy-week2-artifact", default=str(DEFAULT_SYC))
    parser.add_argument("--evil-week2-artifact", default=str(DEFAULT_EVIL))
    parser.add_argument("--claim_ready_min_examples_per_trait", type=int, default=15)
    args = parser.parse_args()

    concordance = _load_json(Path(args.concordance_artifact))
    syc = _load_json(Path(args.sycophancy_week2_artifact))
    evil = _load_json(Path(args.evil_week2_artifact))

    ratings = concordance.get("ratings", {})
    summary = concordance.get("summary", {})
    per_trait_summary = summary.get("per_trait", {})

    trait_rows: dict[str, Any] = {}
    for trait, entries in ratings.items():
        successes, n = _count_sign_matches(entries)
        ci = _wilson_interval(successes, n) if n > 0 else (None, None)
        trait_rows[trait] = {
            "n_examples": int(n),
            "sign_agreement_successes": int(successes),
            "sign_agreement_rate": float(successes / n) if n > 0 else None,
            "sign_agreement_wilson95": list(ci) if ci[0] is not None else None,
            "mean_abs_error": per_trait_summary.get(trait, {}).get("mean_abs_error"),
        }

    min_examples = min((row["n_examples"] for row in trait_rows.values()), default=0)
    claim_ready = bool(min_examples >= int(args.claim_ready_min_examples_per_trait))

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_manual_concordance_policy_closure",
        "inputs": {
            "concordance_artifact": str(Path(args.concordance_artifact).relative_to(ROOT)),
            "sycophancy_week2_artifact": str(Path(args.sycophancy_week2_artifact).relative_to(ROOT)),
            "evil_week2_artifact": str(Path(args.evil_week2_artifact).relative_to(ROOT)),
            "claim_ready_min_examples_per_trait": int(args.claim_ready_min_examples_per_trait),
        },
        "manual_concordance": {
            "overall": summary.get("overall", {}),
            "per_trait": trait_rows,
            "claim_ready_for_primary_reliability": claim_ready,
        },
        "judge_calibration_reference": {
            "sycophancy": _judge_kappa_snapshot(syc),
            "evil": _judge_kappa_snapshot(evil),
        },
        "policy_decision": {
            "manual_concordance_role": "sanity_check_only",
            "primary_reliability_signal": "judge_calibration_kappa",
            "upgrade_condition_for_manual_claim_weight": f"Increase to >= {int(args.claim_ready_min_examples_per_trait)} examples per trait.",
            "r2_c5_status_recommendation": "resolved_via_explicit_scope_decision",
        },
        "evidence_status": {
            "manual_counts": "known",
            "wilson_intervals": "known",
            "policy_scope_decision": "inferred",
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_manual_concordance_policy_closure_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "output_path": str(out_path),
                "manual_claim_ready": claim_ready,
                "policy_role": report["policy_decision"]["manual_concordance_role"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
