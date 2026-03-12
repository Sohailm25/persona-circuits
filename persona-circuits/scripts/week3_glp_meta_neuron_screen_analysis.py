"""Aggregate Week 3 GLP meta-neuron screen artifacts into a compact comparison report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "results" / "glp_sidecar"
OUTPUT_DIR = ROOT / "results" / "glp_sidecar"


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _latest_artifacts(limit: int) -> list[Path]:
    artifacts = sorted(INPUT_DIR.glob("week3_glp_meta_neuron_screen_*.json"))
    if not artifacts:
        raise FileNotFoundError(f"No Week 3 GLP meta-neuron artifacts found in {INPUT_DIR}")
    return artifacts[-int(limit) :]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summarize_trait(payload: dict[str, Any]) -> dict[str, Any]:
    top_rows = payload.get("top_meta_neurons", []) if isinstance(payload.get("top_meta_neurons"), list) else []
    capture_rows = payload.get("concentration_by_capture_target", []) if isinstance(payload.get("concentration_by_capture_target"), list) else []
    u_rows = payload.get("concentration_by_u", []) if isinstance(payload.get("concentration_by_u"), list) else []
    screening = payload.get("screening_summary", {}) if isinstance(payload.get("screening_summary"), dict) else {}
    return {
        "glp_alignment": payload.get("glp_alignment", {}),
        "top_meta_neuron_preview": top_rows[:5],
        "top_capture_targets": capture_rows[:5],
        "top_u_values": u_rows[:5],
        "screening_summary": {
            "topk_abs_mean_delta_sum": screening.get("topk_abs_mean_delta_sum"),
            "topk_abs_mean_delta_mean": screening.get("topk_abs_mean_delta_mean"),
            "centroid_cosine_low_vs_high": screening.get("centroid_cosine_low_vs_high"),
            "abs_mean_delta_summary": screening.get("abs_mean_delta_summary"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="*", help="Optional explicit artifact paths")
    parser.add_argument("--latest", type=int, default=0, help="Load the latest N artifacts if none are passed")
    args = parser.parse_args()

    if args.artifacts:
        artifact_paths = [_resolve_path(path) for path in args.artifacts]
    else:
        artifact_paths = _latest_artifacts(limit=max(1, int(args.latest or 1)))

    payloads = [(path, _load_json(path)) for path in artifact_paths]
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_glp_meta_neuron_screen_analysis",
        "inputs": [str(path) for path, _ in payloads],
        "summary_by_artifact": {},
    }

    for path, payload in payloads:
        by_trait = payload.get("results_by_trait", {}) if isinstance(payload.get("results_by_trait"), dict) else {}
        report["summary_by_artifact"][str(path)] = {
            "results_by_trait": {
                trait: _summarize_trait(trait_payload)
                for trait, trait_payload in sorted(by_trait.items())
            },
            "cross_trait_overlap": payload.get("cross_trait_overlap", {}),
        }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"week3_glp_meta_neuron_screen_analysis_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "inputs": report["inputs"]}, indent=2))


if __name__ == "__main__":
    main()
