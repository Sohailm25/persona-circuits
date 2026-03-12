"""Week 3 SAE reconstruction audit with computed (non-placeholder) readiness gates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
INFRA_DIR = ROOT / "results" / "infrastructure"
STAGE1_DIR = ROOT / "results" / "stage1_extraction"
STAGE2_DIR = ROOT / "results" / "stage2_decomposition"
OUT_DIR = STAGE2_DIR


def _latest(base_dir: Path, path_glob: str) -> Path:
    matches = sorted(base_dir.glob(path_glob))
    if not matches:
        raise FileNotFoundError(f"No artifact matches: {base_dir}/{path_glob}")
    return matches[-1]


def _try_latest(base_dir: Path, path_glob: str) -> Path | None:
    matches = sorted(base_dir.glob(path_glob))
    return matches[-1] if matches else None


def _extract_llama_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    block = payload.get("llama_scope_and_andyrdt", {})
    return {
        "model_name": block.get("model_name"),
        "llama_scope_release": block.get("llama_scope_release"),
        "llama_scope_reconstruction_cosine_layer16": block.get("llama_scope_reconstruction_cosine_layer16"),
        "andyrdt_release": block.get("andyrdt_release"),
        "andyrdt_loaded_layers": sorted(
            int(k.split("_")[3])
            for k in block.get("andyrdt_loaded", {}).keys()
            if k.startswith("resid_post_layer_")
        ),
    }


def _extract_gemma_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    block = payload.get("gemma_scope_and_clt", {})
    return {
        "model_name": block.get("model_name"),
        "gemmascope_release": block.get("gemmascope_release"),
        "gemmascope_reconstruction_cosine_layer12": block.get("gemmascope_reconstruction_cosine_layer12"),
        "gemmascope_loaded_count": block.get("gemmascope_loaded_count"),
    }


def _status(cosine_value: float | None, *, pass_min: float = 0.9, warn_min: float = 0.8) -> str:
    if cosine_value is None:
        return "unknown"
    if cosine_value >= pass_min:
        return "pass"
    if cosine_value >= warn_min:
        return "warning"
    return "fail"


def _iter_seed_reports(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "inputs" in payload and "model_results" in payload:
        return {"single": payload}
    reports = payload.get("seed_reports")
    if isinstance(reports, dict):
        out: dict[str, dict[str, Any]] = {}
        for seed_key, report in reports.items():
            if isinstance(report, dict) and "inputs" in report and "model_results" in report:
                out[str(seed_key)] = report
        return out
    return {}


def _extract_probe_layers(payload: dict[str, Any] | None) -> list[int]:
    if not isinstance(payload, dict):
        return []
    reports = _iter_seed_reports(payload)
    layers: set[int] = set()
    for report in reports.values():
        layer = _get_nested(report, ["inputs", "layer"])
        if isinstance(layer, (int, float)):
            layers.add(int(layer))
    return sorted(layers)


def _get_nested(payload: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _resolve_claim_layers(trait_scope_payload: dict[str, Any]) -> dict[str, Any]:
    primary_claim_traits = _get_nested(
        trait_scope_payload, ["stage2_scope_recommendation", "primary_claim_traits"], []
    )
    trait_scope = trait_scope_payload.get("trait_scope", {})
    trait_to_scope_key = {
        "sycophancy": "sycophancy",
        "evil": "evil",
        "machiavellian_disposition": "evil",
        "hallucination": "hallucination",
    }

    claim_layers_by_trait: dict[str, int] = {}
    missing_traits: list[str] = []
    for claim_trait in primary_claim_traits:
        scope_key = trait_to_scope_key.get(str(claim_trait))
        if scope_key is None:
            missing_traits.append(str(claim_trait))
            continue
        layer = _get_nested(trait_scope, [scope_key, "selected_primary_combo", "layer"])
        if isinstance(layer, (int, float)):
            claim_layers_by_trait[str(claim_trait)] = int(layer)
        else:
            missing_traits.append(str(claim_trait))

    return {
        "primary_claim_traits": [str(x) for x in primary_claim_traits],
        "claim_layers_by_trait": claim_layers_by_trait,
        "claim_layers_unique": sorted(set(claim_layers_by_trait.values())),
        "missing_traits": missing_traits,
    }


def _extract_last_token_metrics(report: dict[str, Any], model_name: str) -> dict[str, Any]:
    inputs = report.get("inputs", {})
    model_results = report.get("model_results", {}).get(model_name, {})
    variants_summary = model_results.get("variants_summary", {})
    hook_name = inputs.get("configured_hook")
    if not hook_name:
        layer = inputs.get("layer")
        hook_name = f"blocks.{int(layer)}.hook_resid_post" if layer is not None else None
    if not hook_name:
        return {"available": False}
    key = f"{hook_name}::last_token"
    payload = variants_summary.get(key)
    if not isinstance(payload, dict):
        return {"available": False, "variant_key": key}
    cos = payload.get("reconstruction_cosine", {}).get("median")
    ev = payload.get("explained_variance", {}).get("median")
    l0 = payload.get("feature_l0_mean", {}).get("median")
    return {
        "available": True,
        "variant_key": key,
        "median_reconstruction_cosine": float(cos) if cos is not None else None,
        "median_explained_variance": float(ev) if ev is not None else None,
        "median_feature_l0": float(l0) if l0 is not None else None,
    }


def _compute_hook_integrity(report: dict[str, Any]) -> dict[str, Any]:
    inputs = report.get("inputs", {})
    configured_hook = inputs.get("configured_hook")
    rows = report.get("model_results", {})
    if not isinstance(rows, dict):
        return {"status": "unknown", "reason": "missing_model_results"}
    total_rows = 0
    missing_rows = 0
    for model_payload in rows.values():
        for row in model_payload.get("rows", []):
            total_rows += 1
            hook_metrics = row.get("hook_variant_metrics", {})
            if not isinstance(hook_metrics, dict):
                missing_rows += 1
                continue
            if configured_hook and configured_hook in hook_metrics:
                if hook_metrics.get(configured_hook, {}).get("missing") is True:
                    missing_rows += 1
            else:
                missing_rows += 1
    if total_rows == 0:
        return {"status": "unknown", "reason": "no_rows"}
    status = "pass" if missing_rows == 0 else "fail"
    return {
        "status": status,
        "total_rows": int(total_rows),
        "missing_hook_rows": int(missing_rows),
        "missing_fraction": float(missing_rows / total_rows),
    }


def _stage2_policy_from_config(config: dict[str, Any]) -> dict[str, bool]:
    governance = config.get("governance", {})
    if not isinstance(governance, dict):
        governance = {}
    week3_policy = governance.get("week3_stage2_policy", {})
    if not isinstance(week3_policy, dict):
        week3_policy = {}
    return {
        "decomposition_start_requires_cross_source_overlap": bool(
            week3_policy.get("decomposition_start_requires_cross_source_overlap", False)
        ),
        "cross_source_claims_require_overlap": bool(
            week3_policy.get("cross_source_claims_require_overlap", True)
        ),
    }


def main() -> None:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    llama_path = _latest(INFRA_DIR, "week1_day3_5_modal_validation_*220740Z.json")
    gemma_path = _latest(INFRA_DIR, "week1_day3_5_modal_validation_*224332Z.json")
    trait_scope_path = _try_latest(STAGE1_DIR, "week2_trait_scope_resolution_*.json")
    investigation_path = _try_latest(STAGE2_DIR, "week3_sae_reconstruction_investigation_*.json")
    root_cause_path = _try_latest(STAGE2_DIR, "week3_sae_reconstruction_root_cause_*.json")

    llama_payload = json.loads(llama_path.read_text(encoding="utf-8"))
    gemma_payload = json.loads(gemma_path.read_text(encoding="utf-8"))
    trait_scope_payload = (
        json.loads(trait_scope_path.read_text(encoding="utf-8")) if trait_scope_path else None
    )
    investigation_payload = (
        json.loads(investigation_path.read_text(encoding="utf-8")) if investigation_path else None
    )
    root_cause_payload = json.loads(root_cause_path.read_text(encoding="utf-8")) if root_cause_path else None

    llama_metrics = _extract_llama_metrics(llama_payload)
    gemma_metrics = _extract_gemma_metrics(gemma_payload)

    primary_model = str(cfg["models"]["primary"]["name"])
    primary_sae_model = str(cfg["sae"]["primary"]["model"])
    primary_sae_layers = [int(x) for x in cfg["sae"]["primary"]["layers"]]
    cross_check_layers = [int(x) for x in cfg["sae"]["cross_check"]["layers"]]
    steering_layers = [int(x) for x in cfg["models"]["primary"]["optimal_steering_layers"]]
    claim_resolution = (
        _resolve_claim_layers(trait_scope_payload)
        if isinstance(trait_scope_payload, dict)
        else {
            "primary_claim_traits": [],
            "claim_layers_by_trait": {},
            "claim_layers_unique": [],
            "missing_traits": ["trait_scope_artifact_missing"],
        }
    )

    llama_cos = (
        float(llama_metrics["llama_scope_reconstruction_cosine_layer16"])
        if llama_metrics.get("llama_scope_reconstruction_cosine_layer16") is not None
        else None
    )
    gemma_cos = (
        float(gemma_metrics["gemmascope_reconstruction_cosine_layer12"])
        if gemma_metrics.get("gemmascope_reconstruction_cosine_layer12") is not None
        else None
    )

    instruct_base_mismatch = bool(primary_model != primary_sae_model)
    overlap_primary_sae_vs_steering = sorted(set(primary_sae_layers).intersection(steering_layers))
    overlap_crosscheck_vs_steering = sorted(set(cross_check_layers).intersection(steering_layers))
    overlap_primary_sae_vs_claim_layers = sorted(
        set(primary_sae_layers).intersection(claim_resolution["claim_layers_unique"])
    )
    overlap_crosscheck_vs_claim_layers = sorted(
        set(cross_check_layers).intersection(claim_resolution["claim_layers_unique"])
    )
    investigation_probe_layers = _extract_probe_layers(investigation_payload)
    root_cause_probe_layers = _extract_probe_layers(root_cause_payload)

    # Computed gate 1: token-level reconstruction on primary model from root-cause probe.
    token_gate_details: dict[str, Any] = {"status": "unknown"}
    if root_cause_payload is not None:
        root_reports = _iter_seed_reports(root_cause_payload)
        per_seed: dict[str, Any] = {}
        for seed_key, report in root_reports.items():
            per_seed[seed_key] = _extract_last_token_metrics(report, primary_model)
        available = [
            payload
            for payload in per_seed.values()
            if payload.get("available")
            and payload.get("median_reconstruction_cosine") is not None
            and payload.get("median_explained_variance") is not None
        ]
        if available:
            cos_vals = [float(x["median_reconstruction_cosine"]) for x in available]
            ev_vals = [float(x["median_explained_variance"]) for x in available]
            pass_cond = bool(min(cos_vals) >= 0.75 and min(ev_vals) >= 0.50)
            token_gate_details = {
                "status": "pass" if pass_cond else "fail",
                "criterion": "min(last_token median_cos)>=0.75 and min(last_token median_EV)>=0.50",
                "seed_count": len(available),
                "min_median_reconstruction_cosine": float(min(cos_vals)),
                "min_median_explained_variance": float(min(ev_vals)),
                "per_seed": per_seed,
            }
        else:
            token_gate_details = {
                "status": "unknown",
                "reason": "last_token metrics unavailable",
                "per_seed": per_seed,
            }

    # Computed gate 2: hook integrity from root-cause probe rows.
    hook_gate_details: dict[str, Any] = {"status": "unknown"}
    if root_cause_payload is not None:
        root_reports = _iter_seed_reports(root_cause_payload)
        integrity_by_seed = {k: _compute_hook_integrity(v) for k, v in root_reports.items()}
        statuses = [x.get("status") for x in integrity_by_seed.values() if x.get("status") in {"pass", "fail"}]
        if statuses:
            hook_gate_details = {
                "status": "pass" if all(s == "pass" for s in statuses) else "fail",
                "per_seed": integrity_by_seed,
            }
        else:
            hook_gate_details = {
                "status": "unknown",
                "per_seed": integrity_by_seed,
            }

    # Computed gate 3: selected claim layers are available in primary SAE source.
    claim_layer_coverage_gate: dict[str, Any]
    claim_layers = claim_resolution["claim_layers_unique"]
    if claim_layers:
        missing_primary_layers = sorted(set(claim_layers) - set(primary_sae_layers))
        claim_layer_coverage_gate = {
            "status": "pass" if not missing_primary_layers else "fail",
            "criterion": "all primary-claim layers are available in primary SAE source",
            "claim_layers": claim_layers,
            "missing_primary_sae_layers": missing_primary_layers,
            "available_primary_sae_layers": primary_sae_layers,
        }
    else:
        claim_layer_coverage_gate = {
            "status": "unknown",
            "reason": "no_primary_claim_layers_resolved",
            "claim_layers": claim_layers,
            "missing_traits": claim_resolution.get("missing_traits", []),
        }

    # Computed gate 4: selected claim layers are covered by executed Stage2 probes.
    claim_probe_gate: dict[str, Any]
    if claim_layers:
        investigation_missing = sorted(set(claim_layers) - set(investigation_probe_layers))
        root_missing = sorted(set(claim_layers) - set(root_cause_probe_layers))
        claim_probe_gate = {
            "status": "pass" if (not investigation_missing and not root_missing) else "fail",
            "criterion": "investigation and root-cause probes include all primary-claim layers",
            "claim_layers": claim_layers,
            "investigation_probe_layers": investigation_probe_layers,
            "root_cause_probe_layers": root_cause_probe_layers,
            "missing_investigation_layers": investigation_missing,
            "missing_root_cause_layers": root_missing,
        }
    else:
        claim_probe_gate = {
            "status": "unknown",
            "reason": "no_primary_claim_layers_resolved",
            "investigation_probe_layers": investigation_probe_layers,
            "root_cause_probe_layers": root_cause_probe_layers,
        }

    # Computed gate 5: cross-source overlap on selected claim layers.
    cross_source_claim_layer_gate: dict[str, Any]
    if claim_layers:
        cross_source_claim_layer_gate = {
            "status": "pass" if len(overlap_crosscheck_vs_claim_layers) > 0 else "fail",
            "criterion": "cross-check SAE layers overlap selected primary-claim layers",
            "claim_layers": claim_layers,
            "cross_check_layers": cross_check_layers,
            "overlap_layers": overlap_crosscheck_vs_claim_layers,
        }
    else:
        cross_source_claim_layer_gate = {
            "status": "unknown",
            "reason": "no_primary_claim_layers_resolved",
            "overlap_layers": overlap_crosscheck_vs_claim_layers,
        }

    # Computed gate 6: investigation seed schedule consumed (if multi-seed report wrapper exists).
    seed_schedule_gate: dict[str, Any]
    if investigation_payload is None:
        seed_schedule_gate = {"status": "unknown", "reason": "investigation_artifact_missing"}
    else:
        seed_schedule = investigation_payload.get("seed_schedule")
        if isinstance(seed_schedule, list) and len(seed_schedule) > 1:
            seed_schedule_gate = {
                "status": "pass",
                "seed_schedule": [int(x) for x in seed_schedule],
            }
        elif isinstance(seed_schedule, list) and len(seed_schedule) == 1:
            seed_schedule_gate = {
                "status": "warning",
                "seed_schedule": [int(x) for x in seed_schedule],
                "reason": "single-seed run",
            }
        else:
            seed_schedule_gate = {
                "status": "warning",
                "reason": "seed schedule not present in investigation artifact",
            }

    computed_checks = [
        {
            "check": "Token-level reconstruction gate on primary model (last_token path)",
            "criterion": "min(last_token median_cos)>=0.75 and min(last_token median_EV)>=0.50",
            "status": token_gate_details["status"],
            "details": token_gate_details,
        },
        {
            "check": "Hook verification from root-cause probe rows",
            "criterion": "configured hook present for all evaluated rows",
            "status": hook_gate_details["status"],
            "details": hook_gate_details,
        },
        {
            "check": "Selected claim-layer coverage in primary SAE source",
            "criterion": "all primary-claim layers are available in primary SAE source",
            "status": claim_layer_coverage_gate["status"],
            "details": claim_layer_coverage_gate,
        },
        {
            "check": "Selected claim layers are probed by Stage2 reconstruction runs",
            "criterion": "investigation and root-cause probes include all primary-claim layers",
            "status": claim_probe_gate["status"],
            "details": claim_probe_gate,
        },
        {
            "check": "Cross-source overlap on selected claim layers",
            "criterion": "cross-check SAE layers overlap selected primary-claim layers",
            "status": cross_source_claim_layer_gate["status"],
            "details": cross_source_claim_layer_gate,
        },
        {
            "check": "Seed replication schedule consumed by investigation artifact",
            "criterion": "investigation artifact records >1 seeds when config provides replication seeds",
            "status": seed_schedule_gate["status"],
            "details": seed_schedule_gate,
        },
    ]

    required_statuses = [x["status"] for x in computed_checks]
    stage2_readiness = "pass" if all(s == "pass" for s in required_statuses) else "fail"
    stage2_policy = _stage2_policy_from_config(cfg)
    check_status_by_name = {str(item["check"]): str(item["status"]) for item in computed_checks}

    decomposition_required_checks = [
        "Token-level reconstruction gate on primary model (last_token path)",
        "Hook verification from root-cause probe rows",
        "Selected claim-layer coverage in primary SAE source",
        "Selected claim layers are probed by Stage2 reconstruction runs",
        "Seed replication schedule consumed by investigation artifact",
    ]
    if stage2_policy["decomposition_start_requires_cross_source_overlap"]:
        decomposition_required_checks.append("Cross-source overlap on selected claim layers")
    decomposition_required_statuses = [check_status_by_name.get(name, "missing") for name in decomposition_required_checks]
    decomposition_start_gate_status = (
        "pass" if all(status == "pass" for status in decomposition_required_statuses) else "fail"
    )

    cross_source_check_name = "Cross-source overlap on selected claim layers"
    cross_source_status = check_status_by_name.get(cross_source_check_name, "missing")
    cross_source_claim_gate_status = (
        "pass"
        if (
            (not stage2_policy["cross_source_claims_require_overlap"])
            or (cross_source_status == "pass")
        )
        else "fail"
    )

    audit = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "experiment_config": str(CONFIG_PATH),
            "llama_infra_artifact": str(llama_path),
            "gemma_infra_artifact": str(gemma_path),
            "trait_scope_artifact": str(trait_scope_path) if trait_scope_path else None,
            "investigation_artifact": str(investigation_path) if investigation_path else None,
            "root_cause_artifact": str(root_cause_path) if root_cause_path else None,
        },
        "evidence_status": {
            "infra_reconstruction_cosines": "known",
            "stage2_probe_artifacts": "known" if (investigation_path and root_cause_path) else "unknown",
            "trait_scope_resolution": "known" if trait_scope_path else "unknown",
            "computed_readiness_checks": "inferred",
        },
        "metrics": {
            "llama_scope_layer16_reconstruction_cosine": llama_cos,
            "llama_scope_layer16_status": _status(llama_cos),
            "gemmascope_layer12_reconstruction_cosine": gemma_cos,
            "gemmascope_layer12_status": _status(gemma_cos),
        },
        "model_sae_alignment": {
            "primary_model_name": primary_model,
            "primary_sae_model_name": primary_sae_model,
            "instruct_base_mismatch": instruct_base_mismatch,
            "primary_sae_layers": primary_sae_layers,
            "cross_check_sae_layers": cross_check_layers,
            "current_steering_layers": steering_layers,
            "overlap_primary_sae_vs_steering_layers": overlap_primary_sae_vs_steering,
            "overlap_crosscheck_vs_steering_layers": overlap_crosscheck_vs_steering,
            "primary_claim_traits": claim_resolution["primary_claim_traits"],
            "primary_claim_layers_by_trait": claim_resolution["claim_layers_by_trait"],
            "primary_claim_layers_unique": claim_resolution["claim_layers_unique"],
            "overlap_primary_sae_vs_claim_layers": overlap_primary_sae_vs_claim_layers,
            "overlap_crosscheck_vs_claim_layers": overlap_crosscheck_vs_claim_layers,
        },
        "probe_layer_coverage": {
            "investigation_probe_layers": investigation_probe_layers,
            "root_cause_probe_layers": root_cause_probe_layers,
        },
        "computed_checks_before_stage2_claims": computed_checks,
        "stage2_policy": stage2_policy,
        "stage2_decomposition_start_gate": {
            "status": decomposition_start_gate_status,
            "required_checks": decomposition_required_checks,
            "required_statuses": decomposition_required_statuses,
        },
        "stage2_cross_source_claim_gate": {
            "status": cross_source_claim_gate_status,
            "required_overlap": stage2_policy["cross_source_claims_require_overlap"],
            "overlap_check_status": cross_source_status,
            "overlap_layers": overlap_crosscheck_vs_claim_layers,
        },
        "stage2_readiness_gate": {
            "status": stage2_readiness,
            "required_checks": [x["check"] for x in computed_checks],
            "required_statuses": required_statuses,
        },
        "pre_primary_prep_actions": [
            "Run token-level reconstruction probes on all selected primary-claim layers using configured seed schedule before Stage2 claims.",
            "If cross-check overlap is empty on selected claim layers, either add overlapping SAE source/layers or scope cross-SAE agreement claims accordingly.",
            "Keep full-sequence reconstruction pathology in caveats; do not use it as primary token-level gate.",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"week3_sae_reconstruction_audit_{timestamp}.json"
    out_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "audit_path": str(out_path),
                "stage2_readiness_gate": audit["stage2_readiness_gate"]["status"],
                "llama_scope_status": audit["metrics"]["llama_scope_layer16_status"],
                "gemmascope_status": audit["metrics"]["gemmascope_layer12_status"],
                "instruct_base_mismatch": instruct_base_mismatch,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
