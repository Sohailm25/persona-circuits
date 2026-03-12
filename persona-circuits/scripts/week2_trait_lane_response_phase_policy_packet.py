"""Freeze the response-phase persistence policy for the trait-lane branch."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
DEFAULT_PROMOTION_PACKET_PATTERN = "week2_trait_lane_promotion_packet_*.json"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def build_response_phase_policy_packet(
    *,
    promotion_payload: dict[str, Any],
    promotion_path: Path,
) -> dict[str, Any]:
    ranked_rows = promotion_payload.get("ranked_lanes")
    if not isinstance(ranked_rows, list) or not ranked_rows:
        raise ValueError("Promotion payload missing ranked_lanes.")

    lane_rows: list[dict[str, Any]] = []
    for row in ranked_rows:
        if not isinstance(row, dict) or not row.get("lane_id"):
            continue
        lane_rows.append(
            {
                "lane_id": str(row["lane_id"]),
                "screening_status": str(row["screening_status"]),
                "response_phase_persistence": float(row["response_phase_persistence"]),
                "response_phase_persistence_pass": bool(row["response_phase_persistence_pass"]),
                "selected_layer": int(row["selected_layer"]),
                "selected_alpha": float(row["selected_alpha"]),
                "oriented_bidirectional_effect": float(row["oriented_bidirectional_effect"]),
            }
        )
    if not lane_rows:
        raise ValueError("Promotion payload contained no usable ranked lane rows.")

    response_phase_pass_count = int(sum(1 for row in lane_rows if row["response_phase_persistence_pass"]))
    candidate_like = [
        row
        for row in lane_rows
        if row["screening_status"]
        in {
            "promotion_candidate_supported",
            "promotion_candidate_strong",
            "conditional_followon_candidate",
            "followon_candidate_with_limitation",
        }
    ]

    legacy_policy = {
        "threshold": 0.7,
        "screening_role": "hard_gate",
        "rationale": "Original branch promotion logic treated prompt-vs-response persistence >=0.7 as a required screening pass.",
    }
    frozen_policy = {
        "status": "pre_registered_superseding_policy",
        "screening_role": "tracked_limitation_not_hard_gate",
        "deeper_validation_launch_role": "must_report_not_blocking",
        "claim_role": "explicit_limitation_not_positive_evidence",
        "threshold_retained_for_reporting": 0.7,
        "hard_gate_counterfactual_candidate_count": response_phase_pass_count,
        "screening_candidate_count_without_hard_gate": len(candidate_like),
        "rationale": (
            "All screened lanes miss the legacy 0.7 prompt-vs-response persistence threshold, while branch screening also "
            "shows strong bootstrap/train-vs-heldout robustness and the core line already established that prompt-end vs "
            "response-generation disagreement can be a computational-regime property rather than a content-stability failure. "
            "Therefore persistence stays mandatory to report and interpret, but is frozen as a tracked limitation rather than "
            "a branch-killing hard gate before the next deeper-validation evidence tranche."
        ),
        "required_reporting": [
            "Always report response_phase_persistence and pass/fail against the legacy 0.7 threshold.",
            "Do not use persistence alone as positive evidence for persona-level generation control.",
            "Carry persistence failure forward as a limitation in any deeper-validation interpretation.",
        ],
    }

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_response_phase_policy_packet",
        "promotion_packet_path": str(promotion_path),
        "n_screened_lanes": len(lane_rows),
        "n_response_phase_pass": response_phase_pass_count,
        "legacy_policy": legacy_policy,
        "frozen_policy": frozen_policy,
        "lane_rows": lane_rows,
        "status": "policy_frozen_before_next_deeper_validation",
        "notes": [
            "This artifact freezes the branch response-phase persistence policy before collecting the next deeper-validation evidence.",
            "It does not assert that persistence is unimportant; it fixes how persistence is treated in screening/launch governance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promotion-packet", default="", help="Optional explicit promotion packet path.")
    parser.add_argument("--output-json", default="", help="Optional explicit output path.")
    args = parser.parse_args()

    promotion_path = (
        Path(args.promotion_packet).resolve()
        if args.promotion_packet.strip()
        else _latest_result_path(DEFAULT_PROMOTION_PACKET_PATTERN)
    )
    promotion_payload = _load_json(promotion_path)
    packet = build_response_phase_policy_packet(
        promotion_payload=promotion_payload,
        promotion_path=promotion_path,
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json.strip():
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_response_phase_policy_packet_{timestamp}.json"
    out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_json": str(out_path),
                "status": packet["status"],
                "n_response_phase_pass": packet["n_response_phase_pass"],
                "frozen_policy_status": packet["frozen_policy"]["status"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
