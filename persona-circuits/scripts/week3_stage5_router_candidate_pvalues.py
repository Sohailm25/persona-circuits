#!/usr/bin/env python3
"""Compute heuristic feature-level router candidate p-values from decomposition ranks."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Sequence

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "stage5_cross_persona"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_layer(artifact: Dict[str, Any]) -> int:
    layer = artifact.get("inputs", {}).get("layer")
    if layer is None:
        raise ValueError("Artifact missing inputs.layer")
    return int(layer)


def _rank_map_from_candidates(trait_payload: Dict[str, Any]) -> Dict[int, int]:
    rows = trait_payload["candidate_union"]["ranked_candidates_topk"]
    out: Dict[int, int] = {}
    for idx, row in enumerate(rows, start=1):
        out[int(row["feature_id"])] = int(idx)
    return out


def _exact_rank_sum_pvalue(rank_a: int, rank_b: int, *, k_a: int, k_b: int) -> float:
    threshold = int(rank_a) + int(rank_b)
    favorable = 0
    for i in range(1, int(k_a) + 1):
        j_max = min(int(k_b), threshold - i)
        if j_max >= 1:
            favorable += j_max
    total = int(k_a) * int(k_b)
    if total <= 0:
        return 1.0
    return float(favorable / total)


def build_router_pvalues(
    *,
    artifact_paths: Sequence[Path],
    trait_a: str,
    trait_b: str,
    early_layer_max: int,
) -> Dict[str, Any]:
    feature_records: Dict[int, Dict[str, Any]] = {}

    for path in artifact_paths:
        artifact = _load_json(path)
        layer = _extract_layer(artifact)
        if layer > int(early_layer_max):
            continue
        results = artifact.get("results_by_trait", {})
        if trait_a not in results or trait_b not in results:
            continue
        rank_a = _rank_map_from_candidates(results[trait_a])
        rank_b = _rank_map_from_candidates(results[trait_b])
        shared = sorted(set(rank_a) & set(rank_b))
        if not shared:
            continue

        k_a = max(1, len(rank_a))
        k_b = max(1, len(rank_b))
        for fid in shared:
            ra = int(rank_a[fid])
            rb = int(rank_b[fid])
            rank_sum = int(ra + rb)
            p_val = _exact_rank_sum_pvalue(ra, rb, k_a=k_a, k_b=k_b)
            rec = feature_records.setdefault(
                int(fid),
                {
                    "support_layers": [],
                    "rank_sums": [],
                    "raw_p_values": [],
                },
            )
            rec["support_layers"].append(int(layer))
            rec["rank_sums"].append(int(rank_sum))
            rec["raw_p_values"].append(float(p_val))

    combined: Dict[int, Dict[str, Any]] = {}
    for fid, rec in feature_records.items():
        n = max(1, len(rec["raw_p_values"]))
        min_p = float(min(rec["raw_p_values"]))
        bonf_p = float(min(1.0, min_p * n))
        combined[int(fid)] = {
            "p_value": bonf_p,
            "p_value_method": "exact_rank_sum_minp_bonferroni",
            "n_support_layers": int(n),
            "support_layers": sorted(int(x) for x in set(rec["support_layers"])),
            "best_rank_sum": int(min(rec["rank_sums"])),
            "min_raw_p_value": min_p,
        }

    pvalue_map = {str(fid): float(payload["p_value"]) for fid, payload in combined.items()}
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_stage5_router_candidate_pvalues",
        "inputs": {
            "artifacts": [str(path) for path in artifact_paths],
            "trait_a": trait_a,
            "trait_b": trait_b,
            "early_layer_max": int(early_layer_max),
        },
        "feature_pvalues": {str(fid): payload for fid, payload in sorted(combined.items())},
        "router_pvalues_map": pvalue_map,
        "summary": {
            "n_features": int(len(combined)),
            "min_p_value": (float(min(pvalue_map.values())) if pvalue_map else None),
            "median_p_value": (
                float(sorted(pvalue_map.values())[len(pvalue_map) // 2]) if pvalue_map else None
            ),
        },
        "evidence_status": {
            "rank_inputs": "known",
            "feature_pvalues": "inferred",
            "causal_router_interpretation": "unknown",
        },
    }


def _default_output_paths() -> tuple[Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_path = OUT_DIR / f"week3_stage5_router_candidate_pvalues_{timestamp}.json"
    map_path = OUT_DIR / f"week3_stage5_router_candidate_pvalues_map_{timestamp}.json"
    return artifact_path, map_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", nargs="+", required=True)
    parser.add_argument("--trait-a", default="sycophancy")
    parser.add_argument("--trait-b", default="evil")
    parser.add_argument("--early-layer-max", type=int, default=12)
    parser.add_argument("--output", default=None)
    parser.add_argument("--map-output", default=None)
    args = parser.parse_args()

    artifact_paths = [Path(path) for path in args.artifacts]
    report = build_router_pvalues(
        artifact_paths=artifact_paths,
        trait_a=args.trait_a,
        trait_b=args.trait_b,
        early_layer_max=int(args.early_layer_max),
    )

    default_artifact_path, default_map_path = _default_output_paths()
    out_path = Path(args.output) if args.output else default_artifact_path
    map_path = Path(args.map_output) if args.map_output else default_map_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    map_path.write_text(json.dumps(report["router_pvalues_map"], indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"artifact": str(out_path), "map": str(map_path)}, indent=2))


if __name__ == "__main__":
    main()
