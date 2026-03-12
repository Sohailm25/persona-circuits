"""Generate branch-local external-smoke prompt datasets for trait_lanes_v2 lanes with benchmark support."""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
import numpy as np

try:
    from scripts.shared.trait_lane_generation import (
        MODEL_NAME,
        SEED_HELDOUT,
        TRAIT_LANE_RESULTS_DIR,
        build_generation_plan,
        build_lane_record,
        collect_valid_unique_items,
        ensure_output_path_is_new,
        extract_json_array,
        load_blocked_queries,
        normalize_items,
        planned_output_path,
        request_batch_size,
        request_prompt_template,
        resolve_template_specs,
        write_jsonl,
    )
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        get_lane_config,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_generation import (
        MODEL_NAME,
        SEED_HELDOUT,
        TRAIT_LANE_RESULTS_DIR,
        build_generation_plan,
        build_lane_record,
        collect_valid_unique_items,
        ensure_output_path_is_new,
        extract_json_array,
        load_blocked_queries,
        normalize_items,
        planned_output_path,
        request_batch_size,
        request_prompt_template,
        resolve_template_specs,
        write_jsonl,
    )
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        get_lane_config,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )

ROOT = Path(__file__).resolve().parents[1]
random.seed(SEED_HELDOUT)
np.random.seed(SEED_HELDOUT)
MAX_CATEGORY_ATTEMPTS = 3
EXTERNAL_SMOKE_SIMILARITY_THRESHOLD = 0.78


def _load_reference_queries(*, lane_id: str) -> list[str]:
    queries: list[str] = []
    for glob_pattern in [
        ROOT / "prompts" / "trait_lanes_v2" / f"{lane_id}_pairs*.jsonl",
        ROOT / "prompts" / "trait_lanes_v2" / "heldout" / f"{lane_id}_heldout_pairs*.jsonl",
        ROOT / "prompts" / "trait_lanes_v2" / "extraction_free" / f"{lane_id}_eval*.jsonl",
    ]:
        for path in sorted(glob_pattern.parent.glob(glob_pattern.name)):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                value = row.get("user_query")
                if isinstance(value, str) and value.strip():
                    queries.append(value.strip())
    return queries


def _resolve_external_lane_ids(registry: dict, *, lane_ids: list[str], family_ids: list[str]) -> list[str]:
    resolved = resolve_selected_lane_ids(registry, lane_ids=lane_ids, family_ids=family_ids)
    unsupported = [lane_id for lane_id in resolved if not bool(get_lane_config(registry, lane_id).get("supports_external_transfer", False))]
    if unsupported:
        raise ValueError(f"Selected lanes do not support external-smoke generation: {unsupported}")
    return resolved


def _allocate_external_smoke_specs(*, registry: dict[str, Any], lane_id: str, lane_cfg: dict[str, Any]) -> tuple[int, list[tuple[Any, int]]]:
    plan = build_generation_plan(registry=registry, lane_ids=[lane_id], mode="external_smoke")
    lane_row = plan["lane_rows"][0]
    target_total = int(lane_row["target_total"])
    per_category = [int(spec["n"]) for spec in lane_row["categories"]]
    specs = resolve_template_specs(str(lane_cfg["heldout_template"]), mode="heldout")
    return target_total, list(zip(specs, per_category, strict=True))


def _generate_lane_queries(
    client: anthropic.Anthropic,
    *,
    registry: dict[str, Any],
    lane_id: str,
    lane_cfg: dict[str, Any],
    blocked: set[str],
) -> list[dict]:
    template_id = str(lane_cfg["heldout_template"])
    del template_id
    target_total, allocated = _allocate_external_smoke_specs(registry=registry, lane_id=lane_id, lane_cfg=lane_cfg)
    seen = set(blocked)
    records = []
    idx = 0
    reference_queries = _load_reference_queries(lane_id=lane_id)
    for spec, target_n in allocated:
        valid_items: list[dict] = []
        for _attempt in range(MAX_CATEGORY_ATTEMPTS):
            remaining = int(target_n) - len(valid_items)
            if remaining <= 0:
                break
            prompt = request_prompt_template(
                lane_id=lane_id,
                lane_cfg=lane_cfg,
                spec=spec,
                n=request_batch_size(remaining),
                mode="external_smoke",
                avoid_queries=reference_queries,
            )
            msg = client.messages.create(
                model=MODEL_NAME,
                max_tokens=2000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text if getattr(msg, "content", None) else ""
            items = normalize_items(
                extract_json_array(raw),
                needs_ground_truth=bool(lane_cfg.get("requires_ground_truth", False)),
            )
            valid_items.extend(
                collect_valid_unique_items(
                    lane_id=lane_id,
                    lane_cfg=lane_cfg,
                    items=items,
                    seen=seen,
                    target_n=remaining,
                    avoid_queries=reference_queries,
                    similarity_threshold=EXTERNAL_SMOKE_SIMILARITY_THRESHOLD,
                )
            )
        if len(valid_items) < int(target_n):
            raise RuntimeError(
                f"Insufficient valid external-smoke prompts for lane={lane_id} category={spec.category} "
                f"(collected={len(valid_items)} target={int(target_n)})"
            )
        for item in valid_items:
            records.append(build_lane_record(lane_id=lane_id, lane_cfg=lane_cfg, idx=idx, category=spec.category, item=item))
            idx += 1
    if len(records) != target_total:
        raise RuntimeError(f"Lane {lane_id} external-smoke count mismatch: got {len(records)} expected {target_total}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-ids", default="", help="Comma-separated explicit lane ids.")
    parser.add_argument("--family-ids", default="", help="Comma-separated family ids.")
    parser.add_argument("--dry-run-plan", action="store_true", help="Emit a dry-run generation plan only.")
    parser.add_argument("--output-json", default="", help="Optional explicit output path for dry-run plan or summary.")
    parser.add_argument("--output-suffix", default="", help="Optional suffix appended to generated prompt filenames.")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    lane_ids = _resolve_external_lane_ids(
        registry,
        lane_ids=parse_id_csv(args.lane_ids),
        family_ids=parse_id_csv(args.family_ids),
    )

    if args.dry_run_plan:
        packet = build_generation_plan(registry=registry, lane_ids=lane_ids, mode="external_smoke", output_suffix=args.output_suffix)
        packet.update(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "registry_path": str(DEFAULT_REGISTRY_PATH),
                "launch_recommended_now": False,
                "notes": [
                    "Dry-run only; no API calls or prompt writes occurred.",
                    "External-smoke prompts are branch-local benchmark-style smoke sets, not replacements for the lane held-out prompts.",
                ],
            }
        )
        TRAIT_LANE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        if args.output_json:
            out_path = Path(args.output_json)
            if not out_path.is_absolute():
                out_path = ROOT / out_path
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            out_path = TRAIT_LANE_RESULTS_DIR / f"week2_trait_lane_external_smoke_generation_plan_{timestamp}.json"
        out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_json": str(out_path), "n_lanes": len(lane_ids), "dry_run": True}, indent=2))
        return

    client = anthropic.Anthropic()
    blocked = load_blocked_queries(
        exclude_paths={planned_output_path(lane_id=lane_id, mode="external_smoke", output_suffix=args.output_suffix) for lane_id in lane_ids}
    )
    summary = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "mode": "external_smoke", "lanes": {}}
    for lane_id in lane_ids:
        lane_cfg = get_lane_config(registry, lane_id)
        rows = _generate_lane_queries(
            client,
            registry=registry,
            lane_id=lane_id,
            lane_cfg=lane_cfg,
            blocked=blocked,
        )
        out_path = planned_output_path(lane_id=lane_id, mode="external_smoke", output_suffix=args.output_suffix)
        ensure_output_path_is_new(out_path)
        write_jsonl(out_path, rows)
        summary["lanes"][lane_id] = {"path": str(out_path), "count": len(rows)}
    TRAIT_LANE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = TRAIT_LANE_RESULTS_DIR / f"week2_trait_lane_external_smoke_generation_summary_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary_json": str(summary_path), "n_lanes": len(lane_ids), "dry_run": False}, indent=2))


if __name__ == "__main__":
    main()
