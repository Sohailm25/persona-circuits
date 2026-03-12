"""Freeze Stage4 ablation target sets from Stage3 attribution outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
OUT_DIR = ROOT / "results" / "stage4_ablation"
DEFAULT_STAGE3_ARTIFACT = (
    "results/stage3_attribution/week3_stage3_activation_delta_attribution_20260304T164549Z.json"
)
DEFAULT_CANDIDATE_ARTIFACT = (
    "results/stage3_attribution/week3_stage3_candidate_selection_20260304T163200Z.json"
)
DEFAULT_TRAITS = "sycophancy,evil"


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _parse_traits(raw: str) -> list[str]:
    traits = [x.strip() for x in raw.split(",") if x.strip()]
    if not traits:
        raise ValueError("Trait list cannot be empty.")
    return traits


def _trait_label(trait: str) -> str:
    return "machiavellian_disposition" if trait == "evil" else trait


def _extract_target_features(
    *,
    stage3_payload: dict[str, Any],
    candidate_payload: dict[str, Any],
    trait: str,
    top_k: int,
) -> dict[str, Any]:
    stage3_trait = stage3_payload.get("results_by_trait", {}).get(trait, {})
    top_rows = (
        stage3_trait.get("feature_attribution_summary", {}).get("top10_by_mean_abs_delta", [])
    )
    if not top_rows:
        raise ValueError(f"No top10 attribution rows found for trait={trait}.")
    if int(top_k) < 1:
        raise ValueError("top_k must be >= 1.")
    if int(top_k) > len(top_rows):
        raise ValueError(
            f"Requested top_k={top_k} exceeds available attribution ranking length={len(top_rows)} for trait={trait}."
        )

    ranked_target_rows = [
        {
            "rank": i + 1,
            "feature_id": int(row["feature_id"]),
            "mean_delta": float(row["mean_delta"]),
            "mean_abs_delta": float(row["mean_abs_delta"]),
        }
        for i, row in enumerate(top_rows[: int(top_k)])
    ]
    target_ids = [int(r["feature_id"]) for r in ranked_target_rows]

    selected_rows = (
        candidate_payload.get("results_by_trait", {})
        .get(trait, {})
        .get("selected_first_pass_features", [])
    )
    if not selected_rows:
        raise ValueError(f"No selected_first_pass_features found for trait={trait}.")
    candidate_pool = [int(r["feature_id"]) for r in selected_rows]

    missing = [fid for fid in target_ids if fid not in set(candidate_pool)]
    if missing:
        raise ValueError(
            f"Target feature IDs not present in candidate pool for trait={trait}: {missing}"
        )

    return {
        "trait": trait,
        "claim_trait_name": _trait_label(trait),
        "target_feature_ids": target_ids,
        "target_ranked_rows": ranked_target_rows,
        "candidate_pool_size": int(len(candidate_pool)),
        "candidate_pool_feature_ids": candidate_pool,
        "prompt_count_used": int(stage3_trait.get("n_prompts", 0)),
        "attribution_method": str(stage3_trait.get("attribution_method", "unknown")),
        "prompt_top10_pairwise_jaccard_mean": stage3_trait.get(
            "feature_attribution_summary", {}
        ).get("prompt_top10_pairwise_jaccard_mean"),
        "mean_abs_delta_concentration": stage3_trait.get(
            "feature_attribution_summary", {}
        ).get("mean_abs_delta_concentration", {}),
    }


def _random_preview_sets(
    *,
    candidate_pool_ids: list[int],
    exclude_ids: list[int],
    set_size: int,
    n_preview: int,
    seed: int,
) -> list[list[int]]:
    pool = [int(x) for x in candidate_pool_ids if int(x) not in set(int(y) for y in exclude_ids)]
    if len(pool) < int(set_size):
        raise ValueError(
            f"Insufficient candidate pool for preview random sets: pool={len(pool)} set_size={set_size}"
        )
    rng = np.random.default_rng(int(seed))
    out: list[list[int]] = []
    for _ in range(int(n_preview)):
        draw = rng.choice(np.asarray(pool, dtype=np.int64), size=int(set_size), replace=False)
        out.append([int(x) for x in draw.tolist()])
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage3-artifact", type=str, default=DEFAULT_STAGE3_ARTIFACT)
    parser.add_argument("--candidate-artifact", type=str, default=DEFAULT_CANDIDATE_ARTIFACT)
    parser.add_argument("--traits", type=str, default=DEFAULT_TRAITS)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--preview-random-sets",
        type=int,
        default=5,
        help="Small deterministic preview only; Stage4 full random baselines are sampled at runtime from full SAE feature space.",
    )
    args = parser.parse_args()

    cfg = _load_config()
    stage3_path = _resolve_path(args.stage3_artifact)
    cand_path = _resolve_path(args.candidate_artifact)
    traits = _parse_traits(args.traits)

    stage3_payload = _load_json(stage3_path)
    cand_payload = _load_json(cand_path)

    random_baseline_samples = int(cfg.get("thresholds", {}).get("random_baseline_samples", 100))

    by_trait: dict[str, Any] = {}
    for trait in traits:
        target = _extract_target_features(
            stage3_payload=stage3_payload,
            candidate_payload=cand_payload,
            trait=trait,
            top_k=int(args.top_k),
        )
        preview_sets = _random_preview_sets(
            candidate_pool_ids=target["candidate_pool_feature_ids"],
            exclude_ids=target["target_feature_ids"],
            set_size=int(args.top_k),
            n_preview=int(args.preview_random_sets),
            seed=int(args.seed),
        )
        by_trait[trait] = {
            **target,
            "random_baseline_sampling": {
                "full_run_mode": "runtime_sae_full_feature_space",
                "n_sets_required": random_baseline_samples,
                "set_size": int(args.top_k),
                "exclude_target_ids": True,
                "preview_sets_from_candidate_pool": preview_sets,
            },
        }

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": {
            "target_feature_ranking": "known",
            "stage4_runtime_selectivity": "unknown",
            "causal_necessity": "unknown",
            "causal_sufficiency": "unknown",
        },
        "inputs": {
            "config_path": str(CONFIG_PATH),
            "stage3_artifact": str(stage3_path),
            "candidate_artifact": str(cand_path),
            "traits": traits,
            "top_k": int(args.top_k),
            "seed": int(args.seed),
            "random_baseline_samples_required": random_baseline_samples,
        },
        "policy": {
            "target_freeze_source": "stage3_pass2_depth_sensitivity",
            "top_k_selection": "top_k_by_mean_abs_delta_from_stage3_artifact",
            "random_baseline_policy": "sample_same_size_sets_at_runtime_from_full_sae_feature_space",
        },
        "targets_by_trait": by_trait,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"week3_stage4_target_set_freeze_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "artifact": str(out_path),
                "traits": traits,
                "top_k": int(args.top_k),
                "random_baseline_samples_required": random_baseline_samples,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
