#!/usr/bin/env python3
"""Stage5 cross-persona analysis utility (launch-free/local).

Consumes one or more Stage2 decomposition artifacts and computes:
- cross-trait Jaccard overlap per layer for multiple feature sources
- simple early-vs-late overlap gradient diagnostics
- early-layer shared-feature router-candidate pools (stub)
- source/layer comparability policy diagnostics
- optional multiple-testing correction hooks for router candidates
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set


FEATURE_SOURCE_TO_FIELD = {
    "candidate_union": ("candidate_union", "ranked_candidates_topk"),
    "direct_projection": ("direct_projection", "top_feature_ids"),
    "differential_activation": ("differential_activation", "top_feature_ids"),
}
GRADIENT_MODES = {"combined", "source_consistent_only"}


@dataclass(frozen=True)
class LayerOverlap:
    layer: int
    source_signature: str
    artifact_path: str
    trait_a_count: int
    trait_b_count: int
    shared_count: int
    jaccard: float


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _jaccard(a: Set[int], b: Set[int]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _artifact_source_signature(artifact: Dict[str, Any]) -> str:
    inputs = artifact.get("inputs", {})
    sae_source = str(inputs.get("sae_source", "unknown_source"))
    sae_release = str(inputs.get("sae_release", "unknown_release"))
    return f"{sae_source}|{sae_release}"


def _extract_layer(artifact: Dict[str, Any]) -> int:
    layer = artifact.get("inputs", {}).get("layer")
    if layer is None:
        raise ValueError("Artifact missing inputs.layer")
    if isinstance(layer, str):
        return int(layer)
    return int(layer)


def _extract_feature_set(
    trait_payload: Dict[str, Any], feature_source: str
) -> Set[int]:
    source_key, value_key = FEATURE_SOURCE_TO_FIELD[feature_source]
    source_payload = trait_payload[source_key]
    values = source_payload[value_key]
    if feature_source == "candidate_union":
        return {int(item["feature_id"]) for item in values}
    return {int(x) for x in values}


def _compute_layer_overlap(
    artifact: Dict[str, Any],
    *,
    artifact_path: Path,
    trait_a: str,
    trait_b: str,
    feature_source: str,
) -> LayerOverlap:
    results = artifact["results_by_trait"]
    if trait_a not in results or trait_b not in results:
        raise ValueError(f"Artifact missing required traits: {trait_a}, {trait_b}")

    set_a = _extract_feature_set(results[trait_a], feature_source)
    set_b = _extract_feature_set(results[trait_b], feature_source)
    shared = set_a & set_b
    return LayerOverlap(
        layer=_extract_layer(artifact),
        source_signature=_artifact_source_signature(artifact),
        artifact_path=str(artifact_path),
        trait_a_count=len(set_a),
        trait_b_count=len(set_b),
        shared_count=len(shared),
        jaccard=_jaccard(set_a, set_b),
    )


def _gradient_summary(points: Sequence[LayerOverlap]) -> Dict[str, Any]:
    if not points:
        return {"available": False}
    ordered = sorted(points, key=lambda x: x.layer)
    early = ordered[0]
    late = ordered[-1]
    return {
        "available": True,
        "early_layer": early.layer,
        "late_layer": late.layer,
        "early_source_signature": early.source_signature,
        "late_source_signature": late.source_signature,
        "early_jaccard": early.jaccard,
        "late_jaccard": late.jaccard,
        "delta_early_minus_late": early.jaccard - late.jaccard,
        "proposal_pattern_pass": bool(early.jaccard >= 0.2 and late.jaccard <= 0.1),
    }


def _gradient_summary_by_source(points: Sequence[LayerOverlap]) -> Dict[str, Any]:
    grouped: Dict[str, List[LayerOverlap]] = {}
    for row in points:
        grouped.setdefault(row.source_signature, []).append(row)

    out: Dict[str, Any] = {}
    for signature, rows in grouped.items():
        summary = _gradient_summary(rows)
        summary["n_layers"] = int(len(rows))
        if len(rows) < 2:
            summary = {
                "available": False,
                "reason": "insufficient_layers_for_gradient",
                "n_layers": int(len(rows)),
                "single_layer": int(rows[0].layer),
                "source_signature": signature,
            }
        out[signature] = summary
    return out


def _comparability_policy(points: Sequence[LayerOverlap], *, gradient_mode: str) -> Dict[str, Any]:
    signatures = sorted({row.source_signature for row in points})
    layers = sorted({int(row.layer) for row in points})
    mixed = len(signatures) > 1
    per_signature_counts: Dict[str, int] = {}
    for sig in signatures:
        per_signature_counts[sig] = int(sum(1 for row in points if row.source_signature == sig))

    return {
        "gradient_mode": gradient_mode,
        "layers_present": layers,
        "source_signatures": signatures,
        "mixed_source_detected": mixed,
        "within_layer_feature_id_comparability": "known_same_artifact_source",
        "cross_layer_gradient_interpretation": (
            "limited_mixed_source"
            if mixed and gradient_mode == "source_consistent_only"
            else "combined"
        ),
        "source_layer_counts": per_signature_counts,
        "source_consistent_gradient_available": bool(
            any(count >= 2 for count in per_signature_counts.values())
        ),
    }


def _router_candidate_summary(
    artifacts: Iterable[Dict[str, Any]],
    trait_a: str,
    trait_b: str,
    feature_source: str,
    early_layer_max: int,
) -> Dict[str, Any]:
    per_layer_shared: Dict[int, Set[int]] = {}

    for artifact in artifacts:
        layer = _extract_layer(artifact)
        if layer > early_layer_max:
            continue
        results = artifact["results_by_trait"]
        if trait_a not in results or trait_b not in results:
            continue
        set_a = _extract_feature_set(results[trait_a], feature_source)
        set_b = _extract_feature_set(results[trait_b], feature_source)
        per_layer_shared[layer] = set_a & set_b

    if not per_layer_shared:
        return {
            "available": False,
            "early_layer_max": early_layer_max,
            "reason": "no_eligible_layers",
        }

    ordered_layers = sorted(per_layer_shared)
    shared_sets = [per_layer_shared[layer] for layer in ordered_layers]
    union_pool = set().union(*shared_sets) if shared_sets else set()
    stable_pool = set.intersection(*shared_sets) if shared_sets else set()

    return {
        "available": True,
        "early_layer_max": early_layer_max,
        "layers_used": ordered_layers,
        "candidate_union_count": len(union_pool),
        "candidate_stable_count": len(stable_pool),
        "candidate_union_ids": sorted(union_pool),
        "candidate_stable_ids": sorted(stable_pool),
        "candidate_union_preview": sorted(union_pool)[:20],
        "candidate_stable_preview": sorted(stable_pool)[:20],
    }


def _normalize_router_pvalues(raw: Dict[str, Any]) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for key, value in raw.items():
        try:
            feature_id = int(key)
        except (TypeError, ValueError):
            continue
        pval: float | None
        if isinstance(value, (float, int)):
            pval = float(value)
        elif isinstance(value, dict):
            raw_p = value.get("p_value")
            if isinstance(raw_p, (float, int)):
                pval = float(raw_p)
            else:
                pval = None
        else:
            pval = None
        if pval is None:
            continue
        if 0.0 <= pval <= 1.0:
            out[feature_id] = pval
    return out


def _benjamini_hochberg(pvals: Sequence[float], alpha: float) -> tuple[list[bool], list[float]]:
    m = len(pvals)
    if m == 0:
        return [], []
    order = sorted(range(m), key=lambda i: pvals[i])
    sorted_p = [float(pvals[i]) for i in order]

    max_pass_rank = 0
    for rank, pval in enumerate(sorted_p, start=1):
        threshold = float(alpha) * (float(rank) / float(m))
        if pval <= threshold:
            max_pass_rank = rank

    rejected_sorted = [False] * m
    if max_pass_rank > 0:
        for i in range(max_pass_rank):
            rejected_sorted[i] = True

    q_sorted = [0.0] * m
    running = 1.0
    for i in range(m - 1, -1, -1):
        rank = i + 1
        raw_q = sorted_p[i] * float(m) / float(rank)
        running = min(running, raw_q)
        q_sorted[i] = min(1.0, running)

    rejected = [False] * m
    q_vals = [1.0] * m
    for sorted_idx, original_idx in enumerate(order):
        rejected[original_idx] = rejected_sorted[sorted_idx]
        q_vals[original_idx] = q_sorted[sorted_idx]

    return rejected, q_vals


def _router_multiple_testing_hook(
    *,
    router_summary: Dict[str, Any],
    router_pvalues: Dict[int, float] | None,
    fdr_alpha: float,
) -> Dict[str, Any]:
    if not router_summary.get("available", False):
        return {
            "available": False,
            "reason": "router_summary_unavailable",
            "method": "benjamini_hochberg_fdr",
            "fdr_alpha": float(fdr_alpha),
        }
    if router_pvalues is None:
        return {
            "available": False,
            "reason": "missing_router_pvalues",
            "method": "benjamini_hochberg_fdr",
            "fdr_alpha": float(fdr_alpha),
        }

    candidate_ids = [int(x) for x in router_summary.get("candidate_union_ids", [])]
    tested_ids = [fid for fid in candidate_ids if fid in router_pvalues]
    if not tested_ids:
        return {
            "available": False,
            "reason": "no_matching_candidate_pvalues",
            "method": "benjamini_hochberg_fdr",
            "fdr_alpha": float(fdr_alpha),
            "n_candidates": int(len(candidate_ids)),
        }

    pvals = [float(router_pvalues[fid]) for fid in tested_ids]
    rejected, qvals = _benjamini_hochberg(pvals, alpha=float(fdr_alpha))
    rejected_ids = [int(fid) for fid, keep in zip(tested_ids, rejected) if keep]
    q_map = {int(fid): float(qv) for fid, qv in zip(tested_ids, qvals)}

    return {
        "available": True,
        "method": "benjamini_hochberg_fdr",
        "fdr_alpha": float(fdr_alpha),
        "n_candidates": int(len(candidate_ids)),
        "n_tested": int(len(tested_ids)),
        "n_rejected": int(len(rejected_ids)),
        "rejected_feature_preview": rejected_ids[:20],
        "min_q_value": float(min(q_map.values())) if q_map else None,
        "q_value_preview": [
            {"feature_id": int(fid), "q_value": float(q_map[fid])}
            for fid in sorted(q_map.keys())[:20]
        ],
    }


def run_analysis(
    artifact_paths: Sequence[Path],
    trait_a: str,
    trait_b: str,
    early_layer_max: int,
    *,
    gradient_mode: str = "source_consistent_only",
    router_pvalues: Dict[int, float] | None = None,
    router_fdr_alpha: float = 0.01,
) -> Dict[str, Any]:
    if gradient_mode not in GRADIENT_MODES:
        raise ValueError(
            f"Unsupported gradient_mode={gradient_mode!r}. Allowed={sorted(GRADIENT_MODES)}"
        )
    if not (0.0 < float(router_fdr_alpha) <= 1.0):
        raise ValueError("router_fdr_alpha must be in (0, 1].")

    artifacts = [_load_json(path) for path in artifact_paths]
    overlap_by_source: Dict[str, List[LayerOverlap]] = {}

    for source in FEATURE_SOURCE_TO_FIELD:
        points = [
            _compute_layer_overlap(
                artifact,
                artifact_path=artifact_path,
                trait_a=trait_a,
                trait_b=trait_b,
                feature_source=source,
            )
            for artifact, artifact_path in zip(artifacts, artifact_paths)
        ]
        overlap_by_source[source] = sorted(points, key=lambda x: x.layer)

    router_stubs = {
        source: _router_candidate_summary(
            artifacts=artifacts,
            trait_a=trait_a,
            trait_b=trait_b,
            feature_source=source,
            early_layer_max=early_layer_max,
        )
        for source in FEATURE_SOURCE_TO_FIELD
    }

    gradient_source_consistent = {
        source: _gradient_summary_by_source(points)
        for source, points in overlap_by_source.items()
    }

    output = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_stage5_cross_persona_analysis",
        "inputs": {
            "artifacts": [str(path) for path in artifact_paths],
            "trait_a": trait_a,
            "trait_b": trait_b,
            "router_early_layer_max": early_layer_max,
            "gradient_mode": gradient_mode,
            "router_fdr_alpha": float(router_fdr_alpha),
            "router_pvalues_provided": bool(router_pvalues is not None),
        },
        "layerwise_overlap": {
            source: [
                {
                    "layer": p.layer,
                    "source_signature": p.source_signature,
                    "artifact_path": p.artifact_path,
                    "trait_a_count": p.trait_a_count,
                    "trait_b_count": p.trait_b_count,
                    "shared_count": p.shared_count,
                    "jaccard": p.jaccard,
                }
                for p in points
            ]
            for source, points in overlap_by_source.items()
        },
        "gradient_summary": {
            source: _gradient_summary(points) for source, points in overlap_by_source.items()
        },
        "gradient_summary_source_consistent": gradient_source_consistent,
        "comparability_policy": {
            source: _comparability_policy(points, gradient_mode=gradient_mode)
            for source, points in overlap_by_source.items()
        },
        "router_candidate_stub": router_stubs,
        "router_multiple_testing_hooks": {
            source: _router_multiple_testing_hook(
                router_summary=router_stubs[source],
                router_pvalues=router_pvalues,
                fdr_alpha=float(router_fdr_alpha),
            )
            for source in FEATURE_SOURCE_TO_FIELD
        },
        "evidence_status": {
            "input_artifacts": "known",
            "layerwise_overlap_metrics": "known",
            "comparability_policy": "known",
            "multiple_testing_hooks": "known",
            "router_candidate_stub_interpretation": "inferred",
        },
    }
    return output


def _default_output_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(
        f"results/stage5_cross_persona/week3_stage5_cross_persona_analysis_{timestamp}.json"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute launch-free Stage5 cross-persona overlap and router-candidate stubs."
    )
    parser.add_argument(
        "--artifacts",
        nargs="+",
        required=True,
        help="Stage2 decomposition artifact paths (can include multiple layers/sources).",
    )
    parser.add_argument("--trait-a", default="sycophancy")
    parser.add_argument("--trait-b", default="evil")
    parser.add_argument("--router-early-layer-max", type=int, default=12)
    parser.add_argument(
        "--gradient-mode",
        choices=sorted(GRADIENT_MODES),
        default="source_consistent_only",
    )
    parser.add_argument(
        "--router-pvalues-json",
        default=None,
        help="Optional JSON file containing feature_id->p_value mappings for router BH-FDR hook.",
    )
    parser.add_argument("--router-fdr-alpha", type=float, default=0.01)
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path (default: timestamped file in results/stage5_cross_persona).",
    )
    args = parser.parse_args()

    artifact_paths = [Path(path) for path in args.artifacts]
    router_pvalues: Dict[int, float] | None = None
    if args.router_pvalues_json:
        raw = _load_json(Path(args.router_pvalues_json))
        router_pvalues = _normalize_router_pvalues(raw)
    result = run_analysis(
        artifact_paths=artifact_paths,
        trait_a=args.trait_a,
        trait_b=args.trait_b,
        early_layer_max=args.router_early_layer_max,
        gradient_mode=args.gradient_mode,
        router_pvalues=router_pvalues,
        router_fdr_alpha=args.router_fdr_alpha,
    )
    output_path = Path(args.output) if args.output else _default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
