"""Critical prompt-audit checks for Week 1 extraction datasets."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from prompt_quality_rules import HALLUC_GT_HEDGE, SYCO_EXPLICIT_AGREE, evil_violation_type

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
OUT_PATH = ROOT / "results" / "infrastructure" / "week1_prompt_audit_report.json"


EXPECTED = {
    "sycophancy": {
        "count": 100,
        "categories": {
            "factually_wrong": 20,
            "political_opinion": 20,
            "personal_advice": 20,
            "aesthetic_claim": 20,
            "self_assessment": 20,
        },
    },
    "evil": {
        "count": 100,
        "categories": {
            "open_ended": 20,
            "advice_seeking": 20,
            "moral_dilemma": 20,
            "power_dynamics": 20,
            "hypotheticals": 20,
        },
    },
    "hallucination": {
        "count": 100,
        "categories": {
            "obscure_facts": 25,
            "false_premise": 25,
            "post_cutoff": 25,
            "reasoning_trap": 25,
        },
    },
}


def sentence_count(text: str) -> int:
    return len([x for x in re.split(r"[.!?]+", text) if x.strip()])


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def audit_trait(trait: str) -> dict[str, Any]:
    path = PROMPTS_DIR / f"{trait}_pairs.jsonl"
    rows = load_rows(path)
    expected = EXPECTED[trait]
    failures: list[dict[str, Any]] = []

    if len(rows) != expected["count"]:
        failures.append({"type": "count_mismatch", "expected": expected["count"], "actual": len(rows)})

    category_counts = Counter(r.get("category") for r in rows)
    if dict(category_counts) != expected["categories"]:
        failures.append(
            {
                "type": "category_mismatch",
                "expected": expected["categories"],
                "actual": dict(category_counts),
            }
        )

    seen = {}
    for idx, row in enumerate(rows):
        rid = row.get("id", idx)
        q = (row.get("user_query") or "").strip()
        if not q:
            failures.append({"type": "empty_query", "id": rid})
            continue

        key = re.sub(r"\s+", " ", q.lower())
        if key in seen:
            failures.append({"type": "duplicate_query", "id": rid, "duplicate_of": seen[key]})
        else:
            seen[key] = rid

        s_count = sentence_count(q)
        if s_count < 1 or s_count > 3:
            failures.append({"type": "sentence_count_out_of_bounds", "id": rid, "sentences": s_count})

        if not row.get("system_high") or not row.get("system_low"):
            failures.append({"type": "missing_system_prompt", "id": rid})

        if trait == "sycophancy" and SYCO_EXPLICIT_AGREE.search(q):
            failures.append({"type": "explicit_agreement_phrase", "id": rid, "query": q})

        if trait == "evil":
            violation_type = evil_violation_type(q)
            if violation_type is not None:
                failures.append(
                    {
                        "type": violation_type,
                        "id": rid,
                        "query": q,
                    }
                )

        if trait == "hallucination":
            cat = row.get("category")
            gt = row.get("ground_truth")
            needs_gt = cat in {"obscure_facts", "false_premise"}
            if needs_gt and not gt:
                failures.append({"type": "missing_ground_truth", "id": rid, "category": cat})
            if not needs_gt and gt is not None:
                failures.append({"type": "unexpected_ground_truth", "id": rid, "category": cat})
            if needs_gt and gt:
                if len(gt.split()) > 35:
                    failures.append({"type": "ground_truth_too_long", "id": rid, "word_count": len(gt.split())})
                if HALLUC_GT_HEDGE.search(gt):
                    failures.append({"type": "ground_truth_hedged", "id": rid, "ground_truth": gt})

    return {
        "trait": trait,
        "path": str(path),
        "count": len(rows),
        "category_counts": dict(category_counts),
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    report = {"audits": {}, "overall_pass": True}
    for trait in ["sycophancy", "evil", "hallucination"]:
        audit = audit_trait(trait)
        report["audits"][trait] = audit
        if audit["failure_count"] > 0:
            report["overall_pass"] = False

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_path": str(OUT_PATH), "overall_pass": report["overall_pass"]}, indent=2))
    return 0 if report["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
