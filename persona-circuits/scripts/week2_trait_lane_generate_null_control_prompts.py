"""Generate matched null-control prompt files for trait_lanes_v2 screening redesign."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.shared.trait_lane_generation import write_jsonl
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_generation import write_jsonl

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
NULL_PROMPTS_DIR = ROOT / "prompts" / "trait_lanes_v2" / "null_controls"
DEFAULT_NULL_CONTROL_GLOB = "week2_trait_lane_null_control_packet_*.json"


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
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _category_seed(seed: int, *, category: str, mode: str) -> int:
    digest = hashlib.sha256(f"{mode}:{category}".encode("utf-8")).digest()
    offset = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return int(seed) + offset


def _balanced_flip_indices(n_rows: int, *, rng: random.Random) -> set[int]:
    indices = list(range(n_rows))
    rng.shuffle(indices)
    n_flip = n_rows // 2
    return set(indices[:n_flip])


def _build_null_rows(
    *,
    rows: list[dict[str, Any]],
    control_id: str,
    source_lane_id: str,
    seed: int,
    mode: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("category", "uncategorized"))].append(row)

    output: list[dict[str, Any]] = []
    category_stats: list[dict[str, Any]] = []
    for category in sorted(grouped):
        category_rows = grouped[category]
        rng = random.Random(_category_seed(seed, category=category, mode=mode))
        flip_indices = _balanced_flip_indices(len(category_rows), rng=rng)
        flipped = 0
        for local_idx, row in enumerate(category_rows):
            row_out = dict(row)
            row_out["lane_id"] = control_id
            row_out["source_lane_id"] = source_lane_id
            row_out["null_control_id"] = control_id
            row_out["null_control_design_type"] = "category_stratified_label_permutation"
            row_out["null_control_source_mode"] = mode
            row_out["null_control_polarity_flipped"] = bool(local_idx in flip_indices)
            row_out["null_control_seed"] = int(seed)
            if local_idx in flip_indices:
                row_out["system_high"], row_out["system_low"] = row_out["system_low"], row_out["system_high"]
                flipped += 1
            output.append(row_out)
        category_stats.append(
            {
                "category": category,
                "n_rows": len(category_rows),
                "n_flipped": flipped,
                "flip_fraction": float(flipped / len(category_rows)) if category_rows else 0.0,
            }
        )
    output.sort(key=lambda row: int(row["id"]))
    return output, {
        "n_rows": len(output),
        "n_flipped": int(sum(stat["n_flipped"] for stat in category_stats)),
        "flip_fraction": float(sum(stat["n_flipped"] for stat in category_stats) / len(output)) if output else 0.0,
        "categories": category_stats,
    }


def _build_output_paths(*, control_id: str, suffix: str) -> dict[str, Path]:
    safe_suffix = f"_{suffix}" if suffix else ""
    return {
        "extraction": NULL_PROMPTS_DIR / f"{control_id}_pairs{safe_suffix}.jsonl",
        "heldout": NULL_PROMPTS_DIR / f"{control_id}_heldout_pairs{safe_suffix}.jsonl",
    }


def _ensure_new(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing null-control artifact: {path}")


def build_null_control_prompt_summary(
    *,
    null_control_packet: dict[str, Any],
    null_control_packet_path: Path,
    output_suffix: str,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    control = null_control_packet["recommended_control_design"]
    control_id = str(control["control_id"])
    source_lane_id = str(null_control_packet["source_lane_id"])
    source_paths = control["source_prompt_paths"]
    seed = int(control["permutation_policy"]["seed"])

    extraction_rows = _load_jsonl(Path(source_paths["extraction"]))
    heldout_rows = _load_jsonl(Path(source_paths["heldout"]))
    extraction_out, extraction_stats = _build_null_rows(
        rows=extraction_rows,
        control_id=control_id,
        source_lane_id=source_lane_id,
        seed=seed,
        mode="extraction",
    )
    heldout_out, heldout_stats = _build_null_rows(
        rows=heldout_rows,
        control_id=control_id,
        source_lane_id=source_lane_id,
        seed=seed,
        mode="heldout",
    )

    output_paths = _build_output_paths(control_id=control_id, suffix=output_suffix)
    return (
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "artifact_type": "week2_trait_lane_null_control_prompt_summary",
            "null_control_packet_path": str(null_control_packet_path),
            "source_lane_id": source_lane_id,
            "control_id": control_id,
            "design_type": str(control["design_type"]),
            "preserved_fields": list(control.get("preserved_fields", [])),
            "permutation_policy": dict(control.get("permutation_policy", {})),
            "source_prompt_paths": {
                "extraction": str(source_paths["extraction"]),
                "heldout": str(source_paths["heldout"]),
            },
            "output_prompt_paths": {key: str(path) for key, path in output_paths.items()},
            "output_suffix": output_suffix,
            "counts": {
                "extraction": extraction_stats,
                "heldout": heldout_stats,
            },
            "launch_recommended_now": True,
            "notes": [
                "The null control preserves user queries, rubric, and category balance while breaking coherent polarity through deterministic within-category flips.",
                "This prompt summary should be consumed by the dedicated null-control execution wrapper, not by the normal promotion packet glob path.",
            ],
        },
        {"extraction": extraction_out, "heldout": heldout_out},
    )


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--null-control-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-suffix", type=str, default="")
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    null_control_path = args.null_control_json or _latest_result_path(DEFAULT_NULL_CONTROL_GLOB)
    null_control_packet = _load_json(null_control_path)
    suffix = args.output_suffix.strip() or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary, prompt_rows = build_null_control_prompt_summary(
        null_control_packet=null_control_packet,
        null_control_packet_path=null_control_path,
        output_suffix=suffix,
    )

    output_paths = {key: Path(path) for key, path in summary["output_prompt_paths"].items()}
    for path in output_paths.values():
        _ensure_new(path)
    for key, rows in prompt_rows.items():
        write_jsonl(output_paths[key], rows)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_json = args.output_json
    if output_json is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_json = RESULTS_DIR / f"week2_trait_lane_null_control_prompt_summary_{timestamp}.json"
    elif not output_json.is_absolute():
        output_json = ROOT / output_json
    output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(output_json), "prompt_paths": summary["output_prompt_paths"]}, indent=2))


if __name__ == "__main__":
    main()
