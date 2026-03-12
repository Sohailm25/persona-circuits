"""Build a deeper Week 2 validation packet for promoted trait-lane candidates."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.shared.trait_lane_generation import planned_output_path
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_generation import planned_output_path
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
DEFAULT_PROMOTION_PACKET_PATTERN = "week2_trait_lane_promotion_packet_*.json"
DEFAULT_TARGET_EXTRACTION_PAIRS = 48
DEFAULT_TARGET_HELDOUT_SPLIT = (10, 10, 10)
FULL_UPGRADE_REFERENCE_EXTRACTION_PAIRS = 100
FULL_UPGRADE_REFERENCE_HELDOUT_SPLIT = (15, 15, 20)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def _coerce_lane_ids(
    *,
    promotion_payload: dict[str, Any],
    lane_ids_override: list[str] | None,
    include_conditional: bool,
) -> list[str]:
    ranked_rows = promotion_payload.get("ranked_lanes")
    if not isinstance(ranked_rows, list) or not ranked_rows:
        raise ValueError("Promotion payload missing ranked_lanes.")

    if lane_ids_override:
        return lane_ids_override

    promoted = [
        str(row["lane_id"])
        for row in ranked_rows
        if isinstance(row, dict) and str(row.get("screening_status", "")) == "promotion_candidate_supported"
    ]
    if include_conditional:
        promoted.extend(
            str(row["lane_id"])
            for row in ranked_rows
            if isinstance(row, dict) and str(row.get("screening_status", "")) == "conditional_followon_candidate"
        )
    dedup: list[str] = []
    for lane_id in promoted:
        if lane_id not in dedup:
            dedup.append(lane_id)
    if not dedup:
        raise ValueError("No promoted trait-lane candidates were selected.")
    return dedup


def _heldout_profile(sweep: int, confirm: int, test: int) -> dict[str, Any]:
    return {
        "sweep_prompts_per_trait": int(sweep),
        "confirm_prompts_per_trait": int(confirm),
        "test_prompts_per_trait": int(test),
        "heldout_target_total": int(sweep + confirm + test),
    }


def _deeper_validation_profile(
    *,
    target_extraction_pairs: int,
    heldout_split: tuple[int, int, int],
) -> dict[str, Any]:
    sweep, confirm, test = heldout_split
    return {
        "profile_id": "trait_lane_deeper_week2_sidecar_v1",
        "target_extraction_pairs": int(target_extraction_pairs),
        **_heldout_profile(sweep, confirm, test),
        "cross_rater_samples": min(10, int(test)),
        "confirm_top_k": 3,
        "random_control_vectors": 16,
        "shuffled_control_permutations": 5,
        "random_control_prompts": min(10, int(test)),
        "sweep_rollouts_per_prompt": 3,
        "confirm_rollouts_per_prompt": 3,
        "baseline_rollouts_per_prompt": 3,
        "rollout_temperature": 0.7,
        "combo_selection_policy": "smallest_feasible_alpha",
        "coherence_gate_mode": "relative_only",
        "coherence_max_drop": 10.0,
        "coherence_min_score": 0.0,
        "truthfulqa_enabled": False,
        "cross_trait_bleed_enabled": True,
        "cross_trait_bleed_reference_traits": ["sycophancy", "assistant_likeness"],
        "cross_trait_bleed_max_fraction": 0.3,
        "capability_proxy_required": False,
        "notes": [
            "Branch-local deeper-validation profile: stronger than screening, lighter than the core full upgrade.",
            "This profile is intended to decide whether a promoted lane deserves full upgraded Week 2 treatment.",
            "Cross-trait bleed is enabled here against core/nearby reference rubrics rather than disabled by default.",
        ],
    }


def _full_upgrade_reference_profile() -> dict[str, Any]:
    return {
        "profile_id": "core_week2_upgrade_reference",
        "target_extraction_pairs": FULL_UPGRADE_REFERENCE_EXTRACTION_PAIRS,
        **_heldout_profile(*FULL_UPGRADE_REFERENCE_HELDOUT_SPLIT),
        "notes": [
            "Reference only: this mirrors the core Week 2 evidence depth more closely than the branch-local sidecar profile.",
            "Trait-lane candidates should not be treated as core-upgrade ready until they satisfy this reference depth or an explicit superseding decision is logged.",
        ],
    }


def _lane_followon_state(row: dict[str, Any], key: str) -> str | None:
    followon = row.get("followon_evidence")
    if not isinstance(followon, dict):
        return None
    payload = followon.get(key)
    if not isinstance(payload, dict):
        return None
    value = payload.get("state")
    return str(value) if value is not None else None


def _response_phase_policy_snapshot(promotion_payload: dict[str, Any]) -> dict[str, Any]:
    policy = promotion_payload.get("response_phase_policy")
    if not isinstance(policy, dict):
        return {
            "status": "missing",
            "rationale": "Promotion packet did not provide a response-phase persistence policy snapshot.",
        }
    return dict(policy)


def build_deeper_validation_packet(
    *,
    registry: dict[str, Any],
    promotion_payload: dict[str, Any],
    promotion_path: Path,
    lane_ids_override: list[str] | None = None,
    include_conditional: bool = False,
    target_extraction_pairs: int = DEFAULT_TARGET_EXTRACTION_PAIRS,
    heldout_split: tuple[int, int, int] = DEFAULT_TARGET_HELDOUT_SPLIT,
    output_suffix: str = "deeperv1",
    current_extraction_suffix: str = "",
    current_heldout_suffix: str = "",
) -> dict[str, Any]:
    ranked_rows = promotion_payload.get("ranked_lanes")
    if not isinstance(ranked_rows, list) or not ranked_rows:
        raise ValueError("Promotion payload missing ranked_lanes.")
    ranked_by_lane = {
        str(row["lane_id"]): row
        for row in ranked_rows
        if isinstance(row, dict) and row.get("lane_id")
    }

    selected_lane_ids = _coerce_lane_ids(
        promotion_payload=promotion_payload,
        lane_ids_override=lane_ids_override,
        include_conditional=include_conditional,
    )
    deeper_profile = _deeper_validation_profile(
        target_extraction_pairs=int(target_extraction_pairs),
        heldout_split=heldout_split,
    )
    full_reference = _full_upgrade_reference_profile()

    lane_packets: list[dict[str, Any]] = []
    for lane_id in selected_lane_ids:
        if lane_id not in ranked_by_lane:
            raise ValueError(f"Lane {lane_id} missing from promotion packet.")
        row = ranked_by_lane[lane_id]
        lane_cfg = get_lane_config(registry, lane_id)

        extraction_path = planned_output_path(
            lane_id=lane_id,
            mode="extraction",
            output_suffix=current_extraction_suffix,
        )
        heldout_path = planned_output_path(
            lane_id=lane_id,
            mode="heldout",
            output_suffix=current_heldout_suffix,
        )
        extraction_count = len(_load_jsonl(extraction_path))
        heldout_count = len(_load_jsonl(heldout_path))

        deeper_missing_extraction = max(
            0,
            int(deeper_profile["target_extraction_pairs"]) - int(extraction_count),
        )
        deeper_missing_heldout = max(
            0,
            int(deeper_profile["heldout_target_total"]) - int(heldout_count),
        )
        full_missing_extraction = max(
            0,
            int(full_reference["target_extraction_pairs"]) - int(extraction_count),
        )
        full_missing_heldout = max(
            0,
            int(full_reference["heldout_target_total"]) - int(heldout_count),
        )

        deeper_ready = bool(deeper_missing_extraction == 0 and deeper_missing_heldout == 0)
        full_ready = bool(full_missing_extraction == 0 and full_missing_heldout == 0)

        blockers: list[str] = []
        if deeper_missing_extraction > 0:
            blockers.append(
                f"extraction_pairs_below_deeper_target:{extraction_count}<{deeper_profile['target_extraction_pairs']}"
            )
        if deeper_missing_heldout > 0:
            blockers.append(
                f"heldout_pairs_below_deeper_target:{heldout_count}<{deeper_profile['heldout_target_total']}"
            )

        lane_packets.append(
            {
                "lane_id": lane_id,
                "family_id": str(row["family_id"]),
                "display_name": str(row["display_name"]),
                "persona_class": str(row["persona_class"]),
                "judge_rubric_id": str(row["judge_rubric_id"]),
                "screening_status": str(row["screening_status"]),
                "selected_layer": int(row["selected_layer"]),
                "selected_alpha": float(row["selected_alpha"]),
                "orientation_sign": int(row["orientation_sign"]),
                "response_phase_persistence": float(row["response_phase_persistence"]),
                "bootstrap_p05_cosine": float(row["bootstrap_p05_cosine"]),
                "train_vs_heldout_cosine": float(row["train_vs_heldout_cosine"]),
                "oriented_bidirectional_effect": float(row["oriented_bidirectional_effect"]),
                "coherence_pass": bool(row["coherence_pass"]),
                "requires_ground_truth": bool(lane_cfg.get("requires_ground_truth", False)),
                "supports_extraction_free": bool(lane_cfg.get("supports_extraction_free", False)),
                "supports_external_transfer": bool(lane_cfg.get("supports_external_transfer", False)),
                "followon_state": {
                    "extraction_free": _lane_followon_state(row, "extraction_free"),
                    "external_smoke": _lane_followon_state(row, "external_smoke"),
                },
                "current_prompt_paths": {
                    "extraction": str(extraction_path),
                    "heldout": str(heldout_path),
                },
                "current_prompt_counts": {
                    "extraction_pairs": int(extraction_count),
                    "heldout_pairs": int(heldout_count),
                },
                "readiness": {
                    "deeper_validation_sidecar_ready": deeper_ready,
                    "full_upgrade_reference_ready": full_ready,
                },
                "blockers": blockers,
                "expansion_requirements": {
                    "deeper_validation_sidecar": {
                        "target_extraction_pairs": int(deeper_profile["target_extraction_pairs"]),
                        "target_heldout_pairs": int(deeper_profile["heldout_target_total"]),
                        "missing_extraction_pairs": int(deeper_missing_extraction),
                        "missing_heldout_pairs": int(deeper_missing_heldout),
                        "suggested_output_suffix": str(output_suffix),
                        "suggested_output_paths": {
                            "extraction": str(
                                planned_output_path(
                                    lane_id=lane_id,
                                    mode="extraction",
                                    output_suffix=output_suffix,
                                )
                            ),
                            "heldout": str(
                                planned_output_path(
                                    lane_id=lane_id,
                                    mode="heldout",
                                    output_suffix=output_suffix,
                                )
                            ),
                        },
                    },
                    "full_upgrade_reference": {
                        "target_extraction_pairs": int(full_reference["target_extraction_pairs"]),
                        "target_heldout_pairs": int(full_reference["heldout_target_total"]),
                        "missing_extraction_pairs": int(full_missing_extraction),
                        "missing_heldout_pairs": int(full_missing_heldout),
                    },
                },
            }
        )

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_deeper_validation_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "promotion_packet_path": str(promotion_path),
        "response_phase_policy_snapshot": _response_phase_policy_snapshot(promotion_payload),
        "execution_policy": {
            "preferred_launch_mode": "split_extract_validate",
            "legacy_single_app_wrapper_allowed": False,
            "rationale": "The next deeper-validation attempt should decouple extraction and upgraded validation to reduce wrapper/handoff failure risk and narrow blast radius.",
        },
        "selected_lane_ids": selected_lane_ids,
        "selection_policy": {
            "default_behavior": "promotion_candidate_supported_only",
            "include_conditional": bool(include_conditional),
            "explicit_override_used": bool(lane_ids_override),
        },
        "current_prompt_suffixes": {
            "extraction": str(current_extraction_suffix),
            "heldout": str(current_heldout_suffix),
        },
        "profiles": {
            "deeper_validation_sidecar": deeper_profile,
            "full_upgrade_reference": full_reference,
        },
        "lane_packets": lane_packets,
        "launch_recommended_now": bool(
            lane_packets and all(bool(row["readiness"]["deeper_validation_sidecar_ready"]) for row in lane_packets)
        ),
        "notes": [
            "This is a branch-local planning/launch-readiness packet for deeper Week 2 validation.",
            "It does not claim that promoted lanes are already full-upgrade ready; it explicitly measures the current data-depth gap.",
            "Response-phase persistence policy and preferred split-launch execution mode are frozen here before the next deeper-validation evidence tranche.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promotion-packet", default="", help="Optional explicit promotion packet path.")
    parser.add_argument("--lane-ids", default="", help="Optional explicit lane ids override.")
    parser.add_argument(
        "--include-conditional",
        action="store_true",
        help="Include conditional follow-on candidates in the default selection set.",
    )
    parser.add_argument(
        "--target-extraction-pairs",
        type=int,
        default=DEFAULT_TARGET_EXTRACTION_PAIRS,
        help="Branch-local deeper-validation extraction target.",
    )
    parser.add_argument(
        "--heldout-split",
        default="10,10,10",
        help="Branch-local deeper-validation held-out split as sweep,confirm,test.",
    )
    parser.add_argument(
        "--output-suffix",
        default="deeperv1",
        help="Suggested suffix for append-safe prompt expansion artifacts.",
    )
    parser.add_argument(
        "--current-extraction-suffix",
        default="",
        help="Suffix for the extraction prompt file that should be treated as the current branch input.",
    )
    parser.add_argument(
        "--current-heldout-suffix",
        default="",
        help="Suffix for the held-out prompt file that should be treated as the current branch input.",
    )
    parser.add_argument("--output-json", default="", help="Optional explicit output path.")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    promotion_path = (
        Path(args.promotion_packet)
        if args.promotion_packet
        else _latest_result_path(DEFAULT_PROMOTION_PACKET_PATTERN)
    )
    promotion_payload = _load_json(promotion_path)
    lane_ids_override = [chunk.strip() for chunk in args.lane_ids.split(",") if chunk.strip()]
    split_raw = [chunk.strip() for chunk in args.heldout_split.split(",") if chunk.strip()]
    if len(split_raw) != 3:
        raise ValueError("--heldout-split must be sweep,confirm,test")
    heldout_split = tuple(int(chunk) for chunk in split_raw)
    packet = build_deeper_validation_packet(
        registry=registry,
        promotion_payload=promotion_payload,
        promotion_path=promotion_path,
        lane_ids_override=lane_ids_override or None,
        include_conditional=bool(args.include_conditional),
        target_extraction_pairs=int(args.target_extraction_pairs),
        heldout_split=heldout_split,
        output_suffix=str(args.output_suffix),
        current_extraction_suffix=str(args.current_extraction_suffix),
        current_heldout_suffix=str(args.current_heldout_suffix),
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_deeper_validation_packet_{timestamp}.json"
    out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_json": str(out_path),
                "selected_lane_ids": packet["selected_lane_ids"],
                "launch_recommended_now": packet["launch_recommended_now"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
