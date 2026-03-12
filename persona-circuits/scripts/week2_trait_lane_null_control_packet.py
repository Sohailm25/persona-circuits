"""Define a branch-local null-lane control plan for trait-lane screening."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

DEFAULT_DEEPER_PACKET_GLOB = "week2_trait_lane_deeper_validation_packet_*.json"
DEFAULT_ADJUDICATION_GLOB = "week2_trait_lane_adjudication_packet_*.json"


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _lane_packet(payload: dict[str, Any], lane_id: str) -> dict[str, Any]:
    rows = payload.get("lane_packets")
    if not isinstance(rows, list):
        raise ValueError("Deeper-validation packet missing lane_packets")
    for row in rows:
        if isinstance(row, dict) and str(row.get("lane_id")) == lane_id:
            return row
    raise ValueError(f"Lane {lane_id} missing from deeper-validation packet")


def build_null_control_packet(
    *,
    deeper_packet: dict[str, Any],
    adjudication_packet: dict[str, Any],
    deeper_packet_path: Path,
    adjudication_packet_path: Path,
    lane_id: str = "politeness",
) -> dict[str, Any]:
    lane = _lane_packet(deeper_packet, lane_id)
    current_paths = lane["current_prompt_paths"]
    screening_shift_threshold = 10.0
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_null_control_packet",
        "input_paths": {
            "deeper_validation_packet_json": str(deeper_packet_path),
            "adjudication_packet_json": str(adjudication_packet_path),
        },
        "source_lane_id": lane_id,
        "status": "null_control_defined",
        "recommended_control_design": {
            "control_id": f"{lane_id}_label_permutation_null_v1",
            "design_type": "category_stratified_label_permutation",
            "rationale": (
                "Use the same prompt family and rubric as the promoted lane, but destroy the coherent "
                "high-vs-low contrast by stratified polarity permutation. This estimates the screening "
                "pipeline's false-positive rate without needing a new rubric or prompt family."
            ),
            "source_prompt_paths": {
                "extraction": current_paths["extraction"],
                "heldout": current_paths["heldout"],
            },
            "source_prompt_counts": dict(lane["current_prompt_counts"]),
            "preserved_fields": [
                "id",
                "category",
                "user_query",
                "judge_rubric_id",
                "system_high",
                "system_low",
            ],
            "permutation_policy": {
                "unit": "within_category",
                "seed": 42,
                "shuffle_target": "high_low_pairing",
                "preserve_category_balance": True,
                "preserve_prompt_text": True,
                "preserve_rubric": True,
            },
        },
        "secondary_control_design": {
            "control_id": f"{lane_id}_mechanistically_implausible_even_number_preference_v1",
            "design_type": "new_prompt_family_if_needed",
            "rationale": (
                "Optional higher-cost falsification lane if label-permutation is inconclusive. Use a concept "
                "with low mechanistic plausibility for persona-circuit claims."
            ),
        },
        "evaluation_plan": {
            "reuse_runner": "week2_trait_lane_behavioral_smoke_run.py",
            "runner_mode": "single_control_lane_screen",
            "minimum_required_outputs": [
                "bootstrap_robustness",
                "position_ablation",
                "behavioral_smoke",
            ],
            "false_positive_alerts": {
                "promotion_status_not_hold": True,
                "oriented_bidirectional_effect_ge": screening_shift_threshold,
                "bootstrap_p05_cosine_ge": 0.8,
                "response_phase_persistence_ge": 0.7,
            },
            "pass_condition": (
                "Null control should remain below the branch promotion frontier; any hold-or-better status with "
                "promotion-scale behavioral shift is evidence that the screening pipeline may be overly permissive."
            ),
        },
        "branch_context": {
            "adjudicated_branch_status": adjudication_packet["status"],
            "lead_lane_final_status": adjudication_packet["lane_adjudications"]["politeness"]["final_status"],
        },
        "recommended_next_remote_action": "run_label_permutation_null_control_before_any_new_lane_promotion_attempt",
        "notes": [
            "This packet defines a low-cost false-positive control that reuses the promoted lane's prompt family.",
            "It is designed to run at screening depth, not deeper-validation depth.",
        ],
    }


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deeper-packet-json", type=Path, default=None)
    parser.add_argument("--adjudication-json", type=Path, default=None)
    parser.add_argument("--lane-id", type=str, default="politeness")
    parser.add_argument("--output-json", type=Path, default=None)
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    deeper_packet_path = args.deeper_packet_json or _latest_result_path(DEFAULT_DEEPER_PACKET_GLOB)
    adjudication_packet_path = args.adjudication_json or _latest_result_path(DEFAULT_ADJUDICATION_GLOB)
    packet = build_null_control_packet(
        deeper_packet=_load_json(deeper_packet_path),
        adjudication_packet=_load_json(adjudication_packet_path),
        deeper_packet_path=deeper_packet_path,
        adjudication_packet_path=adjudication_packet_path,
        lane_id=args.lane_id,
    )

    output_path = args.output_json
    if output_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RESULTS_DIR / f"week2_trait_lane_null_control_packet_{stamp}.json"
    output_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(output_path)}, indent=2))


if __name__ == "__main__":
    main()
