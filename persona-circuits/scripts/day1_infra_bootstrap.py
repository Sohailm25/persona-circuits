"""Day 1 infrastructure bootstrap checks (Week 1 Days 1-2 checklist support)."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import wandb

ROOT = Path(__file__).resolve().parents[1]
SCRATCH_DIR = ROOT / "scratch"
VENDOR_DIR = SCRATCH_DIR / "vendor"

MODULES = [
    "sae_lens",
    "transformer_lens",
    "circuit_tracer",
    "transformers",
    "modal",
    "wandb",
]

WANDB_STRUCTURE = {
    "project": "persona-circuits",
    "entity_key": "WANDB_ENTITY",
    "run_group_conventions": {
        "extraction/sycophancy": "Stage 1 sycophancy extraction and validation runs",
        "extraction/evil": "Stage 1 evil extraction and validation runs",
        "extraction/hallucination": "Stage 1 hallucination extraction and validation runs",
        "decomposition": "Stage 2 SAE decomposition runs",
        "attribution": "Stage 3 attribution/circuit tracing runs",
        "ablation": "Stage 4 causal ablation runs",
        "cross-persona": "Stage 5 cross-persona/routing analysis runs",
        "gemma2b-validation": "Week 6 CLT hybrid-vs-full pipeline runs",
    },
}


def module_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in MODULES:
        module = importlib.import_module(name)
        versions[name] = getattr(module, "__version__", "version_attr_missing")
    return versions


def vendor_repos() -> dict[str, str]:
    repos: dict[str, str] = {}
    for repo in ["SAELens", "TransformerLens", "circuit-tracer"]:
        git_dir = VENDOR_DIR / repo / ".git"
        repos[repo] = "present" if git_dir.exists() else "missing"
    return repos


def write_local_report(report: dict) -> Path:
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = SCRATCH_DIR / f"day1_infra_report_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out_path


def log_wandb(structure_path: Path, versions: dict[str, str], repos: dict[str, str]) -> str:
    entity = (os.environ.get("WANDB_ENTITY") or "sohailm").strip()
    run_name = f"week1-day1-bootstrap-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    run = wandb.init(
        project="persona-circuits",
        entity=entity,
        job_type="infrastructure",
        name=run_name,
        config={
            "phase": "week1_day1_day2",
            "check_type": "infrastructure_bootstrap",
            "module_versions": versions,
            "vendor_repos": repos,
        },
    )
    artifact = wandb.Artifact("day1-infra-structure", type="infrastructure")
    artifact.add_file(str(structure_path))
    run.log_artifact(artifact)
    wandb.log({"infrastructure/bootstrap_complete": 1})
    run.finish()
    return run_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-wandb",
        action="store_true",
        help="Skip W&B initialization/logging and only write local report.",
    )
    args = parser.parse_args()

    versions = module_versions()
    repos = vendor_repos()

    structure_path = SCRATCH_DIR / "wandb_project_structure.json"
    structure_path.write_text(json.dumps(WANDB_STRUCTURE, indent=2), encoding="utf-8")

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "module_versions": versions,
        "vendor_repo_status": repos,
        "wandb_structure_file": str(structure_path),
    }
    report_path = write_local_report(report)
    print(f"local_report={report_path}")

    if args.skip_wandb:
        print("wandb_run=skipped")
        return

    run_name = log_wandb(structure_path, versions, repos)
    print(f"wandb_run={run_name}")


if __name__ == "__main__":
    main()
