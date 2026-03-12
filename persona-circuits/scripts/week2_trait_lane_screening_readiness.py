"""Aggregate real trait-lane branch artifacts into a bounded first-screen readiness packet."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        construct_card_path,
        get_lane_config,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
    from scripts.shared.trait_rubrics import supported_rubric_ids
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        construct_card_path,
        get_lane_config,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
    from scripts.shared.trait_rubrics import supported_rubric_ids

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

TRANCHE_SPECS = [
    {
        "tranche_id": "slice_a",
        "lane_ids": ["assistant_likeness", "honesty", "politeness"],
        "rationale": (
            "Initial bounded trio spanning the top-priority assistant-axis lane, a high-value truth lane, "
            "and a lower-confound style lane."
        ),
    },
    {
        "tranche_id": "slice_b",
        "lane_ids": ["persona_drift_from_assistant", "lying", "optimism"],
        "rationale": (
            "Second bounded trio with sign-flipped assistant-axis behavior, direct falsehood, and a second style lane."
        ),
    },
]


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return raw


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _ground_truth_stats(path: str | None) -> dict[str, Any]:
    if not path:
        return {"path": None, "n_rows": 0, "n_with_ground_truth": 0, "fraction_with_ground_truth": None}
    rows = _load_jsonl(Path(path))
    with_gt = 0
    for row in rows:
        value = str(row.get("ground_truth", "")).strip()
        if value and value.upper() != "N/A":
            with_gt += 1
    fraction = (with_gt / len(rows)) if rows else None
    return {
        "path": str(path),
        "n_rows": len(rows),
        "n_with_ground_truth": with_gt,
        "fraction_with_ground_truth": fraction,
    }


def _latest_generated_prompt_audit_rows() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(RESULTS_DIR.glob("week2_trait_lane_generated_prompt_audit_*.json")):
        payload = _load_json(path)
        timestamp = str(payload.get("timestamp_utc", ""))
        for row in payload.get("lane_rows", []):
            lane_id = str(row.get("lane_id", "")).strip()
            if not lane_id:
                continue
            if lane_id not in out or timestamp >= out[lane_id]["artifact_timestamp_utc"]:
                out[lane_id] = {
                    "artifact_path": str(path),
                    "artifact_timestamp_utc": timestamp,
                    "row": row,
                }
    return out


def _latest_extraction_free_rows() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(RESULTS_DIR.glob("week2_trait_lane_extraction_free_manifest_*.json")):
        payload = _load_json(path)
        timestamp = str(payload.get("timestamp_utc", ""))
        for row in payload.get("lane_rows", []):
            lane_id = str(row.get("lane_id", "")).strip()
            if not lane_id:
                continue
            if lane_id not in out or timestamp >= out[lane_id]["artifact_timestamp_utc"]:
                out[lane_id] = {
                    "artifact_path": str(path),
                    "artifact_timestamp_utc": timestamp,
                    "row": row,
                }
    return out


def _default_live_lane_ids(registry: dict[str, Any]) -> list[str]:
    audit_rows = _latest_generated_prompt_audit_rows()
    live = list(audit_rows.keys())
    ordered = resolve_selected_lane_ids(registry, lane_ids=live, family_ids=[])
    return ordered


def _screening_checks(
    *,
    lane_cfg: dict[str, Any],
    audit_row: dict[str, Any] | None,
    extraction_free_row: dict[str, Any] | None,
    extraction_gt: dict[str, Any] | None,
    heldout_gt: dict[str, Any] | None,
    extraction_free_gt: dict[str, Any] | None,
) -> dict[str, bool]:
    requires_gt = bool(lane_cfg.get("requires_ground_truth", False))
    supports_extraction_free = bool(lane_cfg.get("supports_extraction_free", False))

    checks = {
        "generated_prompt_audit_pass": bool(audit_row and audit_row.get("pass", False)),
        "extraction_pairs_present": bool(audit_row and Path(audit_row["extraction"]["path"]).exists()),
        "heldout_pairs_present": bool(audit_row and Path(audit_row["heldout"]["path"]).exists()),
        "rubric_registered": str(lane_cfg["judge_rubric_id"]) in supported_rubric_ids(),
    }
    if supports_extraction_free:
        checks["extraction_free_prepared"] = bool(
            extraction_free_row and Path(extraction_free_row["output_path"]).exists()
        )
    else:
        checks["extraction_free_prepared"] = True

    if requires_gt:
        checks["ground_truth_coverage_ok"] = bool(
            extraction_gt
            and heldout_gt
            and extraction_gt["fraction_with_ground_truth"] == 1.0
            and heldout_gt["fraction_with_ground_truth"] == 1.0
            and (
                extraction_free_gt is None
                or extraction_free_gt["fraction_with_ground_truth"] == 1.0
            )
        )
    else:
        checks["ground_truth_coverage_ok"] = True
    return checks


def build_screening_readiness_packet(
    *,
    registry: dict[str, Any],
    lane_ids: list[str],
) -> dict[str, Any]:
    audit_rows = _latest_generated_prompt_audit_rows()
    extraction_free_rows = _latest_extraction_free_rows()
    lane_rows: list[dict[str, Any]] = []
    ready_map: dict[str, bool] = {}

    for lane_id in lane_ids:
        lane_cfg = get_lane_config(registry, lane_id)
        audit_payload = audit_rows.get(lane_id)
        extraction_free_payload = extraction_free_rows.get(lane_id)
        audit_row = audit_payload["row"] if audit_payload else None
        extraction_free_row = extraction_free_payload["row"] if extraction_free_payload else None
        construct_path = construct_card_path(registry, lane_cfg["family_id"])
        extraction_gt = _ground_truth_stats(audit_row["extraction"]["path"]) if audit_row else None
        heldout_gt = _ground_truth_stats(audit_row["heldout"]["path"]) if audit_row else None
        extraction_free_gt = (
            _ground_truth_stats(extraction_free_row["output_path"]) if extraction_free_row else None
        )
        checks = _screening_checks(
            lane_cfg=lane_cfg,
            audit_row=audit_row,
            extraction_free_row=extraction_free_row,
            extraction_gt=extraction_gt,
            heldout_gt=heldout_gt,
            extraction_free_gt=extraction_free_gt,
        )
        checks["construct_card_present"] = construct_path.exists()
        screen_ready = bool(all(checks.values()))
        ready_map[lane_id] = screen_ready
        lane_rows.append(
            {
                "lane_id": lane_id,
                "family_id": lane_cfg["family_id"],
                "display_name": lane_cfg["display_name"],
                "priority_rank": int(lane_cfg["priority_rank"]),
                "persona_class": lane_cfg["persona_class"],
                "judge_rubric_id": lane_cfg["judge_rubric_id"],
                "supports_extraction_free": bool(lane_cfg.get("supports_extraction_free", False)),
                "requires_ground_truth": bool(lane_cfg.get("requires_ground_truth", False)),
                "known_confounds": list(lane_cfg.get("known_confounds", [])),
                "construct_card_path": str(construct_path),
                "audit_artifact": audit_payload["artifact_path"] if audit_payload else None,
                "extraction_free_manifest_artifact": (
                    extraction_free_payload["artifact_path"] if extraction_free_payload else None
                ),
                "prompt_quality": audit_row,
                "ground_truth_stats": {
                    "extraction": extraction_gt,
                    "heldout": heldout_gt,
                    "extraction_free": extraction_free_gt,
                },
                "checks": checks,
                "screen_ready": screen_ready,
            }
        )

    recommended_tranches: list[dict[str, Any]] = []
    for spec in TRANCHE_SPECS:
        active_ids = [lane_id for lane_id in spec["lane_ids"] if lane_id in lane_ids]
        if not active_ids:
            continue
        all_ready = all(ready_map.get(lane_id, False) for lane_id in active_ids)
        recommended_tranches.append(
            {
                "tranche_id": spec["tranche_id"],
                "lane_ids": active_ids,
                "all_ready": all_ready,
                "status": "recommended_now" if all_ready else "blocked",
                "rationale": spec["rationale"],
            }
        )
    recommended_first = next((row for row in recommended_tranches if row["all_ready"]), None)

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "selected_lane_ids": lane_ids,
        "n_live_lanes": len(lane_rows),
        "n_screen_ready_lanes": sum(1 for row in lane_rows if row["screen_ready"]),
        "lane_rows": lane_rows,
        "recommended_tranches": recommended_tranches,
        "recommended_first_tranche": recommended_first,
        "notes": [
            "This is a readiness / tranche-selection artifact, not model-behavior evidence.",
            "Recommendation order follows the bounded Slice A -> Slice B branch sequence already logged in DECISIONS.md.",
            "The next missing capability after this packet is an actual thin screening runner for vector extraction and behavioral smoke.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-ids", default="", help="Comma-separated explicit lane ids.")
    parser.add_argument("--family-ids", default="", help="Comma-separated family ids.")
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    explicit_lane_ids = parse_id_csv(args.lane_ids)
    explicit_family_ids = parse_id_csv(args.family_ids)
    if explicit_lane_ids or explicit_family_ids:
        lane_ids = resolve_selected_lane_ids(
            registry,
            lane_ids=explicit_lane_ids,
            family_ids=explicit_family_ids,
        )
    else:
        lane_ids = _default_live_lane_ids(registry)

    packet = build_screening_readiness_packet(registry=registry, lane_ids=lane_ids)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_screening_readiness_{timestamp}.json"
    out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_json": str(out_path),
                "n_live_lanes": packet["n_live_lanes"],
                "n_screen_ready_lanes": packet["n_screen_ready_lanes"],
                "recommended_first_tranche": (
                    packet["recommended_first_tranche"]["tranche_id"]
                    if packet["recommended_first_tranche"]
                    else None
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
