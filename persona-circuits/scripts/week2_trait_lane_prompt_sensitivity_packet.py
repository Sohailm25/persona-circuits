"""Define a prompt-sensitivity sidecar for the lead trait-lane candidate."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
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


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _lane_packet(payload: dict[str, Any], lane_id: str) -> dict[str, Any]:
    for row in payload.get("lane_packets", []):
        if isinstance(row, dict) and str(row.get("lane_id")) == lane_id:
            return row
    raise ValueError(f"Lane {lane_id} missing from deeper-validation packet")


def _balanced_subset(rows: list[dict[str, Any]], per_category: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["category"])].append(row)
    selected: list[dict[str, Any]] = []
    for category in sorted(grouped):
        cat_rows = sorted(grouped[category], key=lambda r: int(r["id"]))
        selected.extend(cat_rows[:per_category])
    return selected


def _subset_spec(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n_rows": len(rows),
        "row_ids": [int(r["id"]) for r in rows],
        "categories": {
            category: [int(r["id"]) for r in rows if str(r["category"]) == category]
            for category in sorted({str(r["category"]) for r in rows})
        },
    }


def build_prompt_sensitivity_packet(
    *,
    deeper_packet: dict[str, Any],
    adjudication_packet: dict[str, Any],
    deeper_packet_path: Path,
    adjudication_packet_path: Path,
    lane_id: str = "politeness",
) -> dict[str, Any]:
    lane = _lane_packet(deeper_packet, lane_id)
    extraction_rows = _load_jsonl(Path(lane["current_prompt_paths"]["extraction"]))
    heldout_rows = _load_jsonl(Path(lane["current_prompt_paths"]["heldout"]))
    extraction_subset = _balanced_subset(extraction_rows, per_category=3)
    heldout_subset = _balanced_subset(heldout_rows, per_category=2)
    adjudicated_lane = adjudication_packet["lane_adjudications"]["politeness"]

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_prompt_sensitivity_packet",
        "input_paths": {
            "deeper_validation_packet_json": str(deeper_packet_path),
            "adjudication_packet_json": str(adjudication_packet_path),
        },
        "source_lane_id": lane_id,
        "status": "prompt_sensitivity_defined",
        "selected_reference_config": {
            "layer": int(adjudicated_lane["selected_layer"]),
            "alpha": float(adjudicated_lane["selected_alpha"]),
        },
        "source_prompt_paths": dict(lane["current_prompt_paths"]),
        "subset_plan": {
            "extraction": _subset_spec(extraction_subset),
            "heldout": _subset_spec(heldout_subset),
        },
        "perturbation_policy": {
            "goal": "Rephrase user queries while preserving task intent, category, and difficulty without leaking politeness wording into the prompt.",
            "operations": [
                "lexical paraphrase",
                "sentence-structure rewrite",
                "constraint-preserving reframing",
            ],
            "forbidden_changes": [
                "changing system_high/system_low",
                "changing category labels",
                "adding explicit politeness or rudeness cues to the user query",
                "changing the underlying user task",
            ],
        },
        "evaluation_plan": {
            "extraction_vector_gate": {
                "selected_layer_cosine_ge": 0.8,
                "all_layers_max_abs_drop_le": 0.2,
            },
            "behavior_retention_gate": {
                "reuse_selected_config_only": True,
                "minimum_fraction_of_original_bidirectional_effect": 0.7,
                "maximum_absolute_effect_drop": 10.0,
                "steering_and_reversal_sign_preserved": True,
            },
            "failure_interpretation": (
                "If mild prompt rewrites materially collapse the selected-layer vector or the selected configuration's effect, "
                "the branch ranking should be treated as prompt-fragile."
            ),
        },
        "branch_context": {
            "adjudicated_branch_status": adjudication_packet["status"],
            "lead_lane_final_status": adjudicated_lane["final_status"],
        },
        "recommended_next_remote_action": "generate_perturbed_prompt_subset_and_run_selected_config_retention_check",
        "notes": [
            "This packet addresses wording sensitivity, not pair-subsampling stability.",
            "The subset is intentionally category-balanced and small enough for a bounded sidecar run.",
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
    packet = build_prompt_sensitivity_packet(
        deeper_packet=_load_json(deeper_packet_path),
        adjudication_packet=_load_json(adjudication_packet_path),
        deeper_packet_path=deeper_packet_path,
        adjudication_packet_path=adjudication_packet_path,
        lane_id=args.lane_id,
    )

    output_path = args.output_json
    if output_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RESULTS_DIR / f"week2_trait_lane_prompt_sensitivity_packet_{stamp}.json"
    output_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(output_path)}, indent=2))


if __name__ == "__main__":
    main()
