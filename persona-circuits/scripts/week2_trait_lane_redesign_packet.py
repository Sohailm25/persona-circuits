"""Assemble the post-adjudication redesign tranche for the trait-lane branch."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

DEFAULT_ADJUDICATION_GLOB = "week2_trait_lane_adjudication_packet_*.json"
DEFAULT_NULL_CONTROL_GLOB = "week2_trait_lane_null_control_packet_*.json"
DEFAULT_PROMPT_SENSITIVITY_GLOB = "week2_trait_lane_prompt_sensitivity_packet_*.json"


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


def build_redesign_packet(
    *,
    adjudication_payload: dict[str, Any],
    null_control_payload: dict[str, Any],
    prompt_sensitivity_payload: dict[str, Any],
    input_paths: dict[str, str],
) -> dict[str, Any]:
    lead = adjudication_payload["lane_adjudications"]["politeness"]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_redesign_packet",
        "input_paths": input_paths,
        "status": "redesign_tranche_defined",
        "branch_status_snapshot": adjudication_payload["status"],
        "lead_lane": {
            "lane_id": "politeness",
            "current_final_status": lead["final_status"],
            "current_promotion_decision": lead["promotion_decision"],
            "binding_confound": "assistant_likeness_distinctness",
        },
        "redesign_objectives": [
            "estimate branch false-positive rate with a matched null control",
            "measure wording sensitivity of the lead lane under bounded prompt perturbations",
            "avoid any new promotion claim until assistant-style distinctness is better characterized",
        ],
        "ordered_work_items": [
            {
                "step": 1,
                "item": "run_null_control_screen",
                "artifact_dependency": null_control_payload["artifact_type"],
                "why": "A branch-specific false-positive estimate is missing today.",
            },
            {
                "step": 2,
                "item": "run_prompt_sensitivity_sidecar",
                "artifact_dependency": prompt_sensitivity_payload["artifact_type"],
                "why": "Bootstrap stability does not answer wording sensitivity.",
            },
            {
                "step": 3,
                "item": "decide_if_assistant_likeness_specific_distinctness_run_is_still_worthwhile",
                "why": "Only revisit further `politeness` work if the null-control and prompt-sensitivity lanes do not already freeze the branch.",
            },
        ],
        "launch_policy": {
            "launch_recommended_now": True,
            "forbidden_now": [
                "another blind politeness deeper-validation rerun",
                "independent lane promotion into the main persona-circuit claim path",
                "slice_c_widening",
            ],
            "next_remote_priority": "run_null_control_screen",
        },
        "notes": [
            "This packet opens redesign work without undoing the adjudicated no-promotion verdict.",
            "The redesign tranche is for falsification support and confound measurement, not for quietly re-promoting the branch.",
        ],
    }


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adjudication-json", type=Path, default=None)
    parser.add_argument("--null-control-json", type=Path, default=None)
    parser.add_argument("--prompt-sensitivity-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    adjudication_path = args.adjudication_json or _latest_result_path(DEFAULT_ADJUDICATION_GLOB)
    null_control_path = args.null_control_json or _latest_result_path(DEFAULT_NULL_CONTROL_GLOB)
    prompt_sensitivity_path = args.prompt_sensitivity_json or _latest_result_path(DEFAULT_PROMPT_SENSITIVITY_GLOB)

    packet = build_redesign_packet(
        adjudication_payload=_load_json(adjudication_path),
        null_control_payload=_load_json(null_control_path),
        prompt_sensitivity_payload=_load_json(prompt_sensitivity_path),
        input_paths={
            "adjudication_json": str(adjudication_path),
            "null_control_json": str(null_control_path),
            "prompt_sensitivity_json": str(prompt_sensitivity_path),
        },
    )

    output_path = args.output_json
    if output_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RESULTS_DIR / f"week2_trait_lane_redesign_packet_{stamp}.json"
    output_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(output_path)}, indent=2))


if __name__ == "__main__":
    main()
