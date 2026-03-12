"""Week 3 Stage 3 candidate-selection pass from Stage2 decomposition artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "stage3_attribution"
DEFAULT_PRIMARY = (
    "results/stage2_decomposition/week3_sae_decomposition_20260303T202729Z.json"
)
DEFAULT_CROSS_11 = (
    "results/stage2_decomposition/week3_sae_decomposition_20260303T203716Z.json"
)
DEFAULT_CROSS_15 = (
    "results/stage2_decomposition/week3_sae_decomposition_20260303T211749Z.json"
)


def _parse_traits(raw: str) -> list[str]:
    traits = [x.strip() for x in raw.split(",") if x.strip()]
    if not traits:
        raise ValueError("Trait list cannot be empty.")
    return traits


def _resolve(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _feature_rows(artifact: dict[str, Any], trait: str) -> list[dict[str, Any]]:
    rows = (
        artifact.get("results_by_trait", {})
        .get(trait, {})
        .get("candidate_union", {})
        .get("ranked_candidates_topk", [])
    )
    if not isinstance(rows, list):
        raise ValueError(f"ranked_candidates_topk is not a list for trait={trait}")
    return rows


def _rank_map(rows: list[dict[str, Any]]) -> dict[int, int]:
    out: dict[int, int] = {}
    for i, row in enumerate(rows, start=1):
        fid = int(row["feature_id"])
        out[fid] = i
    return out


def _select_claim_layer_first_pass(
    *,
    primary_rows: list[dict[str, Any]],
    first_pass_k: int,
) -> list[dict[str, Any]]:
    ordered = sorted(
        primary_rows,
        key=lambda r: float(r["combined_rank_score"]),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    for row in ordered[:first_pass_k]:
        selected.append(
            {
                "feature_id": int(row["feature_id"]),
                "claim_combined_rank_score": float(row["combined_rank_score"]),
                "direct_rank": (
                    None if row.get("direct_rank") is None else int(row["direct_rank"])
                ),
                "differential_rank": (
                    None
                    if row.get("differential_rank") is None
                    else int(row["differential_rank"])
                ),
                "in_direct_topk": bool(row.get("in_direct_topk", False)),
                "in_differential_topk": bool(row.get("in_differential_topk", False)),
                "direct_cosine": float(row.get("direct_cosine", 0.0)),
                "differential_abs_mean": float(row.get("differential_abs_mean", 0.0)),
            }
        )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traits", type=str, default="sycophancy,evil")
    parser.add_argument("--primary-artifact", type=str, default=DEFAULT_PRIMARY)
    parser.add_argument("--cross-layer11-artifact", type=str, default=DEFAULT_CROSS_11)
    parser.add_argument("--cross-layer15-artifact", type=str, default=DEFAULT_CROSS_15)
    parser.add_argument("--first-pass-k", type=int, default=50)
    args = parser.parse_args()

    traits = _parse_traits(args.traits)
    if int(args.first_pass_k) <= 0:
        raise ValueError("--first-pass-k must be positive")

    primary_path = _resolve(args.primary_artifact)
    cross11_path = _resolve(args.cross_layer11_artifact)
    cross15_path = _resolve(args.cross_layer15_artifact)

    primary = _load_json(primary_path)
    cross11 = _load_json(cross11_path)
    cross15 = _load_json(cross15_path)

    by_trait: dict[str, Any] = {}
    for trait in traits:
        p_rows = _feature_rows(primary, trait)
        c11_rows = _feature_rows(cross11, trait)
        c15_rows = _feature_rows(cross15, trait)

        selected = _select_claim_layer_first_pass(
            primary_rows=p_rows,
            first_pass_k=int(args.first_pass_k),
        )

        claim_name = (
            primary.get("results_by_trait", {})
            .get(trait, {})
            .get("claim_trait_name", trait)
        )

        by_trait[trait] = {
            "claim_trait_name": claim_name,
            "selected_feature_count": int(len(selected)),
            "selected_first_pass_features": selected,
            "source_summary": {
                "primary_candidate_count": int(len(p_rows)),
                "cross_layer11_candidate_count": int(len(c11_rows)),
                "cross_layer15_candidate_count": int(len(c15_rows)),
                "primary_layer": int(primary.get("inputs", {}).get("layer")),
                "cross_layer11": int(cross11.get("inputs", {}).get("layer")),
                "cross_layer15": int(cross15.get("inputs", {}).get("layer")),
            },
            "overlap_context_metrics": {
                "direct_vs_differential_jaccard": {
                    "primary_layer12": float(
                        primary.get("results_by_trait", {})
                        .get(trait, {})
                        .get("candidate_union", {})
                        .get("direct_vs_differential_jaccard", 0.0)
                    ),
                    "cross_layer11": float(
                        cross11.get("results_by_trait", {})
                        .get(trait, {})
                        .get("candidate_union", {})
                        .get("direct_vs_differential_jaccard", 0.0)
                    ),
                    "cross_layer15": float(
                        cross15.get("results_by_trait", {})
                        .get(trait, {})
                        .get("candidate_union", {})
                        .get("direct_vs_differential_jaccard", 0.0)
                    ),
                }
            },
            "evidence_status": {
                "selection_inputs": "known",
                "selection_outputs": "observed",
                "selection_optimality": "unknown",
                "cross_layer_feature_id_correspondence": "unknown",
            },
        }

    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_stage3_candidate_selection",
        "selection_policy": {
            "policy_id": "stage3_v2_claim_layer_primary_only_with_overlap_context",
            "policy_description": (
                "Select first-pass Stage3 features from claim-layer (layer12 primary-source) "
                "ranked candidates only. Use overlap-layer (11/15 cross-source) outputs as "
                "lane-level context metrics, not per-feature support, because cross-layer/source "
                "feature-ID correspondence is not established."
            ),
            "first_pass_k": int(args.first_pass_k),
            "evidence_status": {
                "policy_definition": "known",
                "policy_effectiveness": "unknown",
            },
        },
        "inputs": {
            "traits": traits,
            "primary_artifact": str(primary_path),
            "cross_layer11_artifact": str(cross11_path),
            "cross_layer15_artifact": str(cross15_path),
        },
        "results_by_trait": by_trait,
        "global_notes": {
            "known": [
                "Selection uses claim-layer primary lane (layer12) ranked candidates for first-pass features.",
                "Overlap-layer cross-source lanes (11,15) are included as context metrics only."
            ],
            "inferred": [
                "This avoids unsupported feature correspondence assumptions across layers/sources while preserving overlap-lane sensitivity context."
            ],
            "unknown": [
                "Feature-level correspondence across layers/sources remains unresolved.",
                "Causal necessity/sufficiency of selected features is not established until Stage3/4 interventions run."
            ],
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"week3_stage3_candidate_selection_{ts}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "traits": traits}, indent=2))


if __name__ == "__main__":
    main()
