"""Generate held-out prompt datasets for trait_lanes_v2 without mutating legacy Week 2 files."""

from __future__ import annotations

import argparse
import json
import random
import sys
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import numpy as np

try:
    from scripts.shared.trait_lane_generation import (
        MODEL_NAME,
        SEED_HELDOUT,
        TRAIT_LANE_RESULTS_DIR,
        allocate_category_specs,
        build_generation_plan,
        build_lane_record,
        collect_valid_unique_items,
        ensure_output_path_is_new,
        extract_json_array,
        load_blocked_queries,
        max_query_similarity,
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
        allocate_category_specs,
        build_generation_plan,
        build_lane_record,
        collect_valid_unique_items,
        ensure_output_path_is_new,
        extract_json_array,
        load_blocked_queries,
        max_query_similarity,
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
HELDOUT_SIMILARITY_THRESHOLD = 0.80


def _load_reference_extraction_queries(*, lane_id: str) -> list[str]:
    queries: list[str] = []
    for path in sorted((ROOT / "prompts" / "trait_lanes_v2").glob(f"{lane_id}_pairs*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            value = row.get("user_query")
            if isinstance(value, str) and value.strip():
                queries.append(value.strip())
    return queries


def _generate_lane_queries(
    client: anthropic.Anthropic,
    *,
    lane_id: str,
    lane_cfg: dict,
    blocked: set[str],
    target_total: int | None = None,
) -> list[dict]:
    template_id = str(lane_cfg["heldout_template"])
    if target_total is None:
        specs = resolve_template_specs(template_id, mode="heldout")
    else:
        specs = allocate_category_specs(template_id, mode="heldout", target_total=int(target_total))
    seen = set(blocked)
    records = []
    idx = 0
    reference_queries = _load_reference_extraction_queries(lane_id=lane_id)
    for spec in specs:
        target_n = int(spec.weight)
        valid_items: list[dict] = []
        for _attempt in range(MAX_CATEGORY_ATTEMPTS):
            remaining = target_n - len(valid_items)
            if remaining <= 0:
                break
            prompt = request_prompt_template(
                lane_id=lane_id,
                lane_cfg=lane_cfg,
                spec=spec,
                n=request_batch_size(remaining),
                mode="heldout",
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
                    similarity_threshold=HELDOUT_SIMILARITY_THRESHOLD,
                )
            )
        if len(valid_items) < target_n:
            raise RuntimeError(
                f"Insufficient valid held-out prompts for lane={lane_id} category={spec.category} "
                f"(collected={len(valid_items)} target={target_n})"
            )
        for item in valid_items:
            records.append(build_lane_record(lane_id=lane_id, lane_cfg=lane_cfg, idx=idx, category=spec.category, item=item))
            idx += 1
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-ids", default="", help="Comma-separated explicit lane ids.")
    parser.add_argument("--family-ids", default="", help="Comma-separated family ids.")
    parser.add_argument("--dry-run-plan", action="store_true", help="Emit a dry-run generation plan only.")
    parser.add_argument("--output-json", default="", help="Optional explicit output path for dry-run plan.")
    parser.add_argument("--output-suffix", default="", help="Optional suffix appended to generated prompt filenames.")
    parser.add_argument(
        "--target-total",
        type=int,
        default=0,
        help="Optional override for held-out prompts per selected lane. Uses proportional category allocation.",
    )
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    lane_ids = resolve_selected_lane_ids(
        registry,
        lane_ids=parse_id_csv(args.lane_ids),
        family_ids=parse_id_csv(args.family_ids),
    )

    target_total_override = int(args.target_total) if int(args.target_total) > 0 else None

    if args.dry_run_plan:
        packet = build_generation_plan(
            registry=registry,
            lane_ids=lane_ids,
            mode="heldout",
            output_suffix=args.output_suffix,
            target_total_override=target_total_override,
        )
        packet.update({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "registry_path": str(DEFAULT_REGISTRY_PATH),
            "launch_recommended_now": False,
            "notes": [
                "Dry-run only; no API calls or prompt writes occurred.",
                "Legacy Week 2 held-out files remain untouched.",
            ],
        })
        TRAIT_LANE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        if args.output_json:
            out_path = Path(args.output_json)
            if not out_path.is_absolute():
                out_path = ROOT / out_path
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            out_path = TRAIT_LANE_RESULTS_DIR / f"week2_trait_lane_heldout_generation_plan_{timestamp}.json"
        out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_json": str(out_path), "n_lanes": len(lane_ids), "dry_run": True}, indent=2))
        return

    client = anthropic.Anthropic()
    blocked = load_blocked_queries(
        exclude_paths={planned_output_path(lane_id=lane_id, mode="heldout", output_suffix=args.output_suffix) for lane_id in lane_ids}
    )
    summary = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "mode": "heldout", "lanes": {}}
    for lane_id in lane_ids:
        lane_cfg = get_lane_config(registry, lane_id)
        rows = _generate_lane_queries(
            client,
            lane_id=lane_id,
            lane_cfg=lane_cfg,
            blocked=blocked,
            target_total=target_total_override,
        )
        out_path = planned_output_path(lane_id=lane_id, mode="heldout", output_suffix=args.output_suffix)
        ensure_output_path_is_new(out_path)
        write_jsonl(out_path, rows)
        summary["lanes"][lane_id] = {
            "path": str(out_path),
            "count": len(rows),
            "target_total": len(rows),
        }
    TRAIT_LANE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = TRAIT_LANE_RESULTS_DIR / f"week2_trait_lane_heldout_generation_summary_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary_json": str(summary_path), "n_lanes": len(lane_ids), "dry_run": False}, indent=2))


if __name__ == "__main__":
    main()
