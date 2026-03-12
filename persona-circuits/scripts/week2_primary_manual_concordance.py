"""Manual 5-example judge concordance check on primary Week2 outputs."""

from __future__ import annotations

import argparse
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
DEFAULT_TRAITS = ("sycophancy", "evil", "hallucination")


def _parse_artifact_map(spec: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for chunk in [c.strip() for c in spec.split(",") if c.strip()]:
        if "=" not in chunk:
            raise ValueError(f"Invalid artifact map chunk: {chunk}")
        trait, path = chunk.split("=", 1)
        trait = trait.strip()
        if trait not in DEFAULT_TRAITS:
            raise ValueError(f"Unsupported trait in artifact map: {trait}")
        out[trait] = Path(path.strip())
    missing = [t for t in DEFAULT_TRAITS if t not in out]
    if missing:
        raise ValueError(f"Missing trait artifacts in map: {missing}")
    return out


def _sample_rows(rows: list[dict[str, Any]], sample_count: int, seed: int) -> list[dict[str, Any]]:
    if len(rows) < sample_count:
        raise ValueError(f"Not enough rows for concordance sample (need {sample_count}, have {len(rows)})")
    rng = random.Random(seed)
    picked_idx = sorted(rng.sample(range(len(rows)), sample_count))
    return [rows[i] for i in picked_idx]


def _to_float(value: Any) -> float:
    return float(value) if value is not None else math.nan


def _sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def _build_template_entry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "user_query": row["user_query"],
        "plus_response": row["plus_response"],
        "minus_response": row["minus_response"],
        "judge_plus_score": _to_float(row.get("plus_score")),
        "judge_minus_score": _to_float(row.get("minus_score")),
        "manual_plus_score": None,
        "manual_minus_score": None,
        "notes": "",
    }


def _compute_trait_metrics(entries: list[dict[str, Any]]) -> dict[str, Any]:
    plus_abs: list[float] = []
    minus_abs: list[float] = []
    sign_match = 0
    evaluated = 0
    for e in entries:
        manual_plus = e.get("manual_plus_score")
        manual_minus = e.get("manual_minus_score")
        if manual_plus is None or manual_minus is None:
            continue
        judge_plus = _to_float(e.get("judge_plus_score"))
        judge_minus = _to_float(e.get("judge_minus_score"))
        plus_abs.append(abs(float(manual_plus) - judge_plus))
        minus_abs.append(abs(float(manual_minus) - judge_minus))
        judge_delta = judge_plus - judge_minus
        manual_delta = float(manual_plus) - float(manual_minus)
        sign_match += 1 if _sign(judge_delta) == _sign(manual_delta) else 0
        evaluated += 1

    if evaluated == 0:
        return {
            "evaluated_examples": 0,
            "mean_abs_error": None,
            "mean_plus_abs_error": None,
            "mean_minus_abs_error": None,
            "delta_sign_agreement_rate": None,
        }
    return {
        "evaluated_examples": int(evaluated),
        "mean_abs_error": float((sum(plus_abs) + sum(minus_abs)) / (2 * evaluated)),
        "mean_plus_abs_error": float(sum(plus_abs) / evaluated),
        "mean_minus_abs_error": float(sum(minus_abs) / evaluated),
        "delta_sign_agreement_rate": float(sign_match / evaluated),
    }


def _build_template(
    artifact_map: dict[str, Path],
    sample_count: int,
    seed: int,
) -> dict[str, Any]:
    traits_payload: dict[str, Any] = {}
    for trait, path in artifact_map.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("selected_test_evaluation", {}).get("rows", [])
        sampled = _sample_rows(rows=rows, sample_count=sample_count, seed=seed)
        traits_payload[trait] = [_build_template_entry(row) for row in sampled]
    return {
        "metadata": {
            "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sample_count_per_trait": int(sample_count),
            "sample_seed": int(seed),
            "artifact_map": {k: str(v) for k, v in artifact_map.items()},
        },
        "ratings": traits_payload,
    }


def _compute_summary(template_or_ratings: dict[str, Any]) -> dict[str, Any]:
    trait_metrics: dict[str, Any] = {}
    all_mae: list[float] = []
    all_sign: list[float] = []
    total_examples = 0

    ratings = template_or_ratings.get("ratings", {})
    for trait in DEFAULT_TRAITS:
        entries = ratings.get(trait, [])
        metrics = _compute_trait_metrics(entries)
        trait_metrics[trait] = metrics
        if metrics["mean_abs_error"] is not None:
            all_mae.append(float(metrics["mean_abs_error"]))
            all_sign.append(float(metrics["delta_sign_agreement_rate"]))
            total_examples += int(metrics["evaluated_examples"])

    overall = {
        "evaluated_examples_total": int(total_examples),
        "mean_trait_mae": float(sum(all_mae) / len(all_mae)) if all_mae else None,
        "mean_trait_delta_sign_agreement_rate": float(sum(all_sign) / len(all_sign)) if all_sign else None,
        "concordance_pass_mae_le_20": bool(all_mae and (sum(all_mae) / len(all_mae)) <= 20.0),
    }
    return {"per_trait": trait_metrics, "overall": overall}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-map", required=True, help="trait=path CSV for 3 trait primary artifacts")
    parser.add_argument("--sample-count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--ratings-path",
        default="",
        help="Optional path to filled ratings JSON. If omitted, emits a template only.",
    )
    parser.add_argument(
        "--output-path",
        default="",
        help="Optional explicit output path. Defaults to timestamped stage1_extraction artifact.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_map = _parse_artifact_map(args.artifact_map)
    template = _build_template(
        artifact_map=artifact_map,
        sample_count=int(args.sample_count),
        seed=int(args.seed),
    )

    if args.ratings_path:
        ratings_path = Path(args.ratings_path)
        loaded = json.loads(ratings_path.read_text(encoding="utf-8"))
        if "ratings" not in loaded:
            raise ValueError("ratings_path JSON missing top-level 'ratings' key.")
        report = loaded
        report["metadata"] = {
            **template["metadata"],
            **loaded.get("metadata", {}),
            "evaluated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        report["summary"] = _compute_summary(report)
    else:
        report = template
        report["summary"] = _compute_summary(report)

    if args.output_path:
        out_path = Path(args.output_path)
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        suffix = "ratings" if args.ratings_path else "template"
        out_path = RESULTS_DIR / f"week2_primary_manual_concordance_{suffix}_{timestamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output_path": str(out_path), "summary": report["summary"]["overall"]}, indent=2))


if __name__ == "__main__":
    main()
