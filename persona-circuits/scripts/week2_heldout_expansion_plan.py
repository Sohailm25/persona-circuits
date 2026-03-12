"""Plan artifact for held-out prompt expansion (Week 2 pre-primary prep)."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-total", type=int, default=50)
    parser.add_argument("--proposed-total", type=int, default=150)
    parser.add_argument("--current-sweep", type=int, default=15)
    parser.add_argument("--current-confirm", type=int, default=15)
    parser.add_argument("--current-test", type=int, default=20)
    parser.add_argument("--proposed-sweep", type=int, default=50)
    parser.add_argument("--proposed-confirm", type=int, default=50)
    parser.add_argument("--proposed-test", type=int, default=50)
    parser.add_argument("--layers", type=int, default=6)
    parser.add_argument("--alphas", type=int, default=10)
    args = parser.parse_args()

    if min(
        args.current_total,
        args.proposed_total,
        args.current_sweep,
        args.current_confirm,
        args.current_test,
        args.proposed_sweep,
        args.proposed_confirm,
        args.proposed_test,
        args.layers,
        args.alphas,
    ) <= 0:
        raise ValueError("All counts must be > 0")

    current_split_total = args.current_sweep + args.current_confirm + args.current_test
    proposed_split_total = args.proposed_sweep + args.proposed_confirm + args.proposed_test

    combos = args.layers * args.alphas

    plan = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "current_total": args.current_total,
            "proposed_total": args.proposed_total,
            "current_split": {
                "sweep": args.current_sweep,
                "confirm": args.current_confirm,
                "test": args.current_test,
                "sum": current_split_total,
            },
            "proposed_split": {
                "sweep": args.proposed_sweep,
                "confirm": args.proposed_confirm,
                "test": args.proposed_test,
                "sum": proposed_split_total,
            },
            "grid": {
                "layers": args.layers,
                "alphas": args.alphas,
                "combos": combos,
            },
        },
        "diagnostics": {
            "split_sum_matches_current_total": bool(current_split_total == args.current_total),
            "split_sum_matches_proposed_total": bool(proposed_split_total == args.proposed_total),
            "sweep_prompt_per_combo_current": float(args.current_sweep),
            "sweep_prompt_per_combo_proposed": float(args.proposed_sweep),
            "sweep_standard_error_reduction_factor": float(
                math.sqrt(args.current_sweep / args.proposed_sweep)
            ),
            "test_standard_error_reduction_factor": float(
                math.sqrt(args.current_test / args.proposed_test)
            ),
            "relative_total_judge_load_multiplier": float(args.proposed_total / args.current_total),
            "relative_sweep_load_multiplier": float(args.proposed_sweep / args.current_sweep),
        },
        "recommendation": {
            "status": "ready_for_post_primary_execution",
            "generator_command": (
                "python3 scripts/generate_week2_heldout_prompts.py "
                "--traits sycophancy evil hallucination "
                "--target-per-trait 150"
            ),
            "notes": [
                "Do not regenerate held-out prompts while primary runs are in-flight if it risks file mutation for active jobs.",
                "Run after primary artifact closeout and before replication/stress launch if budget allows.",
            ],
        },
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_heldout_expansion_plan_{ts}.json"
    out_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "plan_path": str(out_path),
                "sweep_se_reduction_factor": plan["diagnostics"]["sweep_standard_error_reduction_factor"],
                "test_se_reduction_factor": plan["diagnostics"]["test_standard_error_reduction_factor"],
                "load_multiplier": plan["diagnostics"]["relative_total_judge_load_multiplier"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
