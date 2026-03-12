"""Prepare trait_lanes_v2 extraction-free evaluation sets for eligible lanes."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        get_lane_config,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
    from scripts.shared.trait_lane_generation import ensure_output_path_is_new
    from scripts.week2_prepare_extraction_free_eval import (
        _build_records,
        _hash_rows,
        _load_exemplar_bank,
    )
except ModuleNotFoundError:  # pragma: no cover
    from shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        get_lane_config,
        load_trait_lane_registry,
        parse_id_csv,
        resolve_selected_lane_ids,
    )
    from shared.trait_lane_generation import ensure_output_path_is_new
    from week2_prepare_extraction_free_eval import (
        _build_records,
        _hash_rows,
        _load_exemplar_bank,
    )


ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts" / "trait_lanes_v2"
HELDOUT_DIR = PROMPTS_DIR / "heldout"
EXTRACTION_FREE_DIR = PROMPTS_DIR / "extraction_free"
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
DEFAULT_EXEMPLAR_BANK_PATH = PROMPTS_DIR / "extraction_free_exemplar_bank_sliceA.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _normalize_suffix(raw: str) -> str:
    value = str(raw).strip()
    if not value:
        return ""
    return value if value.startswith("_") else f"_{value}"


def _extraction_free_output_path(*, lane_id: str, output_suffix: str) -> Path:
    suffix = _normalize_suffix(output_suffix)
    return EXTRACTION_FREE_DIR / f"{lane_id}_eval{suffix}.jsonl"


def _heldout_input_path(*, lane_id: str, heldout_suffix: str) -> Path:
    suffix = _normalize_suffix(heldout_suffix)
    return HELDOUT_DIR / f"{lane_id}_heldout_pairs{suffix}.jsonl"


def _resolve_extraction_free_lane_ids(registry: dict[str, Any], *, lane_ids: list[str], family_ids: list[str]) -> list[str]:
    resolved = resolve_selected_lane_ids(registry, lane_ids=lane_ids, family_ids=family_ids)
    unsupported = [lane_id for lane_id in resolved if not bool(get_lane_config(registry, lane_id).get("supports_extraction_free", False))]
    if unsupported:
        raise ValueError(f"Selected lanes do not support extraction-free generation: {unsupported}")
    return resolved


def _build_plan(
    *,
    registry: dict[str, Any],
    lane_ids: list[str],
    heldout_suffix: str,
    output_suffix: str,
    n_eval_per_lane: int,
    exemplar_bank_path: Path,
) -> dict[str, Any]:
    rows = []
    for lane_id in lane_ids:
        lane_cfg = get_lane_config(registry, lane_id)
        rows.append(
            {
                "lane_id": lane_id,
                "family_id": lane_cfg["family_id"],
                "display_name": lane_cfg["display_name"],
                "input_path": str(_heldout_input_path(lane_id=lane_id, heldout_suffix=heldout_suffix)),
                "output_path": str(_extraction_free_output_path(lane_id=lane_id, output_suffix=output_suffix)),
                "n_eval_target": int(n_eval_per_lane),
            }
        )
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "exemplar_bank_path": str(exemplar_bank_path),
        "heldout_suffix": _normalize_suffix(heldout_suffix),
        "output_suffix": _normalize_suffix(output_suffix),
        "lane_rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-ids", default="", help="Comma-separated explicit lane ids.")
    parser.add_argument("--family-ids", default="", help="Comma-separated family ids.")
    parser.add_argument("--n-eval-per-lane", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--heldout-suffix", default="", help="Suffix on held-out input filenames (e.g. retry01).")
    parser.add_argument("--output-suffix", default="", help="Suffix on extraction-free output filenames.")
    parser.add_argument("--exemplar-bank-path", default=str(DEFAULT_EXEMPLAR_BANK_PATH))
    parser.add_argument("--min-examples-per-condition", type=int, default=4)
    parser.add_argument("--dry-run-plan", action="store_true")
    parser.add_argument("--output-json", default="", help="Optional explicit output path for plan/manifest.")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    lane_ids = _resolve_extraction_free_lane_ids(
        registry,
        lane_ids=parse_id_csv(args.lane_ids),
        family_ids=parse_id_csv(args.family_ids),
    )
    exemplar_bank_path = Path(args.exemplar_bank_path)

    if args.dry_run_plan:
        packet = _build_plan(
            registry=registry,
            lane_ids=lane_ids,
            heldout_suffix=args.heldout_suffix,
            output_suffix=args.output_suffix,
            n_eval_per_lane=args.n_eval_per_lane,
            exemplar_bank_path=exemplar_bank_path,
        )
        packet["launch_recommended_now"] = True
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        if args.output_json:
            out_path = Path(args.output_json)
            if not out_path.is_absolute():
                out_path = ROOT / out_path
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            out_path = RESULTS_DIR / f"week2_trait_lane_extraction_free_plan_{timestamp}.json"
        out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_json": str(out_path), "n_lanes": len(lane_ids), "dry_run": True}, indent=2))
        return

    exemplar_bank = _load_exemplar_bank(
        path=exemplar_bank_path,
        min_examples_per_condition=int(args.min_examples_per_condition),
    )
    manifest: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": int(args.seed),
        "n_eval_per_lane": int(args.n_eval_per_lane),
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "exemplar_bank_path": str(exemplar_bank_path),
        "heldout_suffix": _normalize_suffix(args.heldout_suffix),
        "output_suffix": _normalize_suffix(args.output_suffix),
        "lane_rows": [],
    }

    for lane_id in lane_ids:
        if lane_id not in exemplar_bank:
            raise KeyError(f"Lane={lane_id} missing in exemplar bank")
        lane_cfg = get_lane_config(registry, lane_id)
        input_path = _heldout_input_path(lane_id=lane_id, heldout_suffix=args.heldout_suffix)
        output_path = _extraction_free_output_path(lane_id=lane_id, output_suffix=args.output_suffix)
        ensure_output_path_is_new(output_path)
        rows = _load_jsonl(input_path)
        records, usage = _build_records(
            rows=rows,
            trait=lane_id,
            n_eval=int(args.n_eval_per_lane),
            seed=int(args.seed),
            exemplar_sets=exemplar_bank[lane_id],
        )
        for record in records:
            record["lane_id"] = lane_id
            record["family_id"] = lane_cfg["family_id"]
            record["judge_rubric_id"] = lane_cfg["judge_rubric_id"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")
        used_set_ids = sorted([key for key, value in usage.items() if value > 0])
        manifest["lane_rows"].append(
            {
                "lane_id": lane_id,
                "family_id": lane_cfg["family_id"],
                "input_path": str(input_path),
                "output_path": str(output_path),
                "n_rows": len(records),
                "sha256": _hash_rows(records),
                "n_exemplar_sets_available": len(exemplar_bank[lane_id]),
                "n_exemplar_sets_used": len(used_set_ids),
                "exemplar_set_ids_used": used_set_ids,
                "exemplar_set_usage_counts": usage,
            }
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_extraction_free_manifest_{timestamp}.json"
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest_path": str(out_path), "n_lanes": len(lane_ids), "dry_run": False}, indent=2))


if __name__ == "__main__":
    main()
