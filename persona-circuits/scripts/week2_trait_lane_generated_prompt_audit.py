"""Audit generated trait_lanes_v2 prompt files for counts, duplicates, and held-out overlap."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.shared.trait_lane_generation import load_blocked_queries, max_query_similarity, planned_output_path
    from scripts.shared.trait_lane_registry import load_trait_lane_registry, parse_id_csv, resolve_selected_lane_ids
except ModuleNotFoundError:  # pragma: no cover
    from shared.trait_lane_generation import load_blocked_queries, max_query_similarity, planned_output_path
    from shared.trait_lane_registry import load_trait_lane_registry, parse_id_csv, resolve_selected_lane_ids

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"


def _load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _file_stats(path: Path) -> dict[str, Any]:
    rows = _load_rows(path)
    queries = [str(row["user_query"]).strip() for row in rows]
    unique_queries = {query.lower() for query in queries}
    return {
        "path": str(path),
        "count": len(rows),
        "unique_count": len(unique_queries),
        "duplicate_count": len(rows) - len(unique_queries),
        "sample_queries": queries[:3],
    }


def _overlap_stats(extraction_path: Path, heldout_path: Path) -> dict[str, Any]:
    extraction_rows = _load_rows(extraction_path)
    heldout_rows = _load_rows(heldout_path)
    extraction_queries = [str(row["user_query"]).strip() for row in extraction_rows]
    heldout_queries = [str(row["user_query"]).strip() for row in heldout_rows]
    best_matches = []
    scores = []
    for query in heldout_queries:
        scored = sorted(
            (
                (max_query_similarity(query, [candidate]), candidate)
                for candidate in extraction_queries
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        score, candidate = scored[0]
        scores.append(score)
        best_matches.append({
            "heldout_query": query,
            "best_extraction_query": candidate,
            "similarity": score,
        })
    best_matches.sort(key=lambda item: item["similarity"], reverse=True)
    return {
        "max_similarity": max(scores) if scores else 0.0,
        "mean_similarity": (sum(scores) / len(scores)) if scores else 0.0,
        "top_matches": best_matches[:3],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-ids", default="", help="Comma-separated explicit lane ids.")
    parser.add_argument("--heldout-suffix", default="", help="Suffix for held-out files to audit.")
    parser.add_argument("--extraction-suffix", default="", help="Suffix for extraction files to audit.")
    parser.add_argument("--output-json", default="", help="Optional explicit output path.")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    lane_ids = resolve_selected_lane_ids(registry, lane_ids=parse_id_csv(args.lane_ids))

    current_paths = {
        planned_output_path(lane_id=lane_id, mode="extraction", output_suffix=args.extraction_suffix)
        for lane_id in lane_ids
    } | {
        planned_output_path(lane_id=lane_id, mode="heldout", output_suffix=args.heldout_suffix)
        for lane_id in lane_ids
    }
    blocked_queries = load_blocked_queries(exclude_paths=current_paths)

    lane_rows = []
    overall_pass = True
    for lane_id in lane_ids:
        extraction_path = planned_output_path(lane_id=lane_id, mode="extraction", output_suffix=args.extraction_suffix)
        heldout_path = planned_output_path(lane_id=lane_id, mode="heldout", output_suffix=args.heldout_suffix)
        extraction_stats = _file_stats(extraction_path)
        heldout_stats = _file_stats(heldout_path)
        overlap_stats = _overlap_stats(extraction_path, heldout_path)
        exact_repo_collisions = [
            query for query in (row["user_query"] for row in _load_rows(extraction_path) + _load_rows(heldout_path))
            if query.strip().lower() in blocked_queries
        ]
        lane_pass = (
            extraction_stats["duplicate_count"] == 0
            and heldout_stats["duplicate_count"] == 0
            and overlap_stats["max_similarity"] < 0.80
            and not exact_repo_collisions
        )
        overall_pass = overall_pass and lane_pass
        lane_rows.append({
            "lane_id": lane_id,
            "extraction": extraction_stats,
            "heldout": heldout_stats,
            "heldout_vs_extraction_overlap": overlap_stats,
            "exact_repo_collision_count": len(exact_repo_collisions),
            "exact_repo_collision_examples": exact_repo_collisions[:5],
            "pass": lane_pass,
            "manual_review_required": True,
        })

    packet = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "lane_ids": lane_ids,
        "extraction_suffix": args.extraction_suffix,
        "heldout_suffix": args.heldout_suffix,
        "overall_pass": overall_pass,
        "lane_rows": lane_rows,
        "notes": [
            "Pass criteria here are screening-level only: no within-file duplicates, no exact repo collisions, and held-out/extraction max lexical similarity < 0.80.",
            "Manual review is still required before promotion or broader screening claims.",
        ],
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_generated_prompt_audit_{timestamp}.json"
    out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(out_path), "overall_pass": overall_pass, "n_lanes": len(lane_ids)}, indent=2))


if __name__ == "__main__":
    main()
