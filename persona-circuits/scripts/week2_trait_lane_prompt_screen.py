"""Build a prompt-screen planning packet for trait_lanes_v2 without generating prompts."""

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
        build_construct_card_status,
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_construct_card_status,
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"


def build_prompt_screen_packet(
    *,
    registry: dict[str, Any],
    lane_ids: list[str],
) -> dict[str, Any]:
    plan = build_lane_screening_plan(registry, lane_ids=lane_ids)
    counts = {
        "n_lanes": len(plan),
        "n_supports_extraction_free": sum(1 for row in plan if row["supports_extraction_free"]),
        "n_supports_external_transfer": sum(1 for row in plan if row["supports_external_transfer"]),
    }
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "selected_lane_ids": lane_ids,
        "construct_card_status": build_construct_card_status(registry, lane_ids=lane_ids),
        "counts": counts,
        "lane_plan": plan,
        "launch_recommended_now": False,
        "notes": [
            "Planning-only artifact; no prompt generation or remote execution occurred.",
            "Legacy Week 2 prompt files remain untouched.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-ids", default="", help="Comma-separated explicit lane ids.")
    parser.add_argument("--family-ids", default="", help="Comma-separated family ids.")
    parser.add_argument("--output-json", default="", help="Optional explicit output path.")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    lane_ids = resolve_selected_lane_ids(
        registry,
        lane_ids=parse_id_csv(args.lane_ids),
        family_ids=parse_id_csv(args.family_ids),
    )
    packet = build_prompt_screen_packet(registry=registry, lane_ids=lane_ids)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_prompt_screen_{timestamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(json.dumps({"output_json": str(out_path), "n_lanes": len(lane_ids)}, indent=2))


if __name__ == "__main__":
    main()
