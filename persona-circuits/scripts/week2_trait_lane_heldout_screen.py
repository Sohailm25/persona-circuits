"""Build a held-out namespace and collision-audit packet for trait_lanes_v2."""

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
        ROOT,
        build_lane_screening_plan,
        build_namespace_collision_report,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        ROOT,
        build_lane_screening_plan,
        build_namespace_collision_report,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )

PROMPTS_ROOT = ROOT / "prompts"
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"


def _list_existing_prompt_files() -> list[str]:
    out: list[str] = []
    for path in sorted(PROMPTS_ROOT.rglob("*.jsonl")):
        out.append(str(path))
    return out


def build_heldout_screen_packet(
    *,
    registry: dict[str, Any],
    lane_ids: list[str],
) -> dict[str, Any]:
    plan = build_lane_screening_plan(registry, lane_ids=lane_ids)
    collision_report = build_namespace_collision_report(registry, lane_ids=lane_ids)
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "selected_lane_ids": lane_ids,
        "existing_prompt_file_count": len(_list_existing_prompt_files()),
        "existing_prompt_files": _list_existing_prompt_files(),
        "planned_heldout_files": [row["planned_prompt_files"]["heldout_pairs"] for row in plan],
        "collision_report": collision_report,
        "launch_recommended_now": False,
        "notes": [
            "Planning-only namespace audit.",
            "Use prompts/trait_lanes_v2/ to avoid collisions with current Week 1/2 prompt files.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-ids", default="")
    parser.add_argument("--family-ids", default="")
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    lane_ids = resolve_selected_lane_ids(
        registry,
        lane_ids=parse_id_csv(args.lane_ids),
        family_ids=parse_id_csv(args.family_ids),
    )
    packet = build_heldout_screen_packet(registry=registry, lane_ids=lane_ids)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_heldout_screen_{timestamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(json.dumps({"output_json": str(out_path), "collision_count": packet["collision_report"]["collision_count"]}, indent=2))


if __name__ == "__main__":
    main()
