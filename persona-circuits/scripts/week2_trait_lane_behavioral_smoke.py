"""Build a behavioral-smoke execution plan for trait_lanes_v2 without launching jobs."""

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
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"


def build_behavioral_smoke_packet(
    *,
    registry: dict[str, Any],
    lane_ids: list[str],
) -> dict[str, Any]:
    defaults = registry.get("defaults") or {}
    smoke_profile = defaults.get("behavioral_smoke_profile") or {}
    plan = build_lane_screening_plan(registry, lane_ids=lane_ids)
    matrix_rows: list[dict[str, Any]] = []
    for lane in plan:
        for layer in lane["screening_layers"]:
            for alpha in lane["screening_alpha_grid"]:
                matrix_rows.append(
                    {
                        "lane_id": lane["lane_id"],
                        "family_id": lane["family_id"],
                        "layer": int(layer),
                        "alpha": float(alpha),
                        "judge_rubric_id": lane["judge_rubric_id"],
                        "relative_coherence_only": True,
                        "supports_extraction_free": lane["supports_extraction_free"],
                        "supports_external_transfer": lane["supports_external_transfer"],
                    }
                )
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "selected_lane_ids": lane_ids,
        "behavioral_smoke_profile": smoke_profile,
        "shared_dependencies_to_reuse": [
            "scripts/shared/behavioral_eval.py",
            "scripts/week2_extraction_robustness_bootstrap.py",
            "scripts/week2_extraction_position_ablation.py",
            "scripts/week2_glp_sidecar_validation.py",
        ],
        "condition_matrix": {
            "n_rows": len(matrix_rows),
            "rows": matrix_rows,
        },
        "launch_recommended_now": False,
        "notes": [
            "Planning-only smoke matrix; no Modal job was launched.",
            "Use sidecar-style wrappers before any attempt to generalize the hardened Week 2 runner.",
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
    packet = build_behavioral_smoke_packet(registry=registry, lane_ids=lane_ids)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_behavioral_smoke_{timestamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(json.dumps({"output_json": str(out_path), "n_rows": packet["condition_matrix"]["n_rows"]}, indent=2))


if __name__ == "__main__":
    main()
