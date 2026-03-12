"""Build a structured second-pass reviewer reconciliation analysis and plan artifact.

This script ingests key Week 2 and Stage 2 artifacts and emits a machine-readable
status + next-steps plan aligned to reviewer second-pass findings.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _stage2_snapshot(audit: dict[str, Any]) -> dict[str, Any]:
    checks = audit.get("computed_checks_before_stage2_claims", [])
    token = next((c for c in checks if c.get("check", "").startswith("Token-level reconstruction")), {})
    overlap = next((c for c in checks if c.get("check", "").startswith("Cross-source overlap")), {})
    seed = next((c for c in checks if c.get("check", "").startswith("Seed replication schedule")), {})

    alignment = audit.get("model_sae_alignment", {})

    return {
        "stage2_readiness_gate": audit.get("stage2_readiness_gate", {}).get("status"),
        "token_gate": {
            "status": token.get("status"),
            "min_median_reconstruction_cosine": token.get("details", {}).get("min_median_reconstruction_cosine"),
            "min_median_explained_variance": token.get("details", {}).get("min_median_explained_variance"),
        },
        "cross_source_overlap_gate": {
            "status": overlap.get("status"),
            "claim_layers": overlap.get("details", {}).get("claim_layers", []),
            "cross_check_layers": overlap.get("details", {}).get("cross_check_layers", []),
            "overlap_layers": overlap.get("details", {}).get("overlap_layers", []),
        },
        "seed_schedule_gate": {
            "status": seed.get("status"),
            "seed_schedule": seed.get("details", {}).get("seed_schedule", []),
        },
        "alignment": {
            "primary_claim_traits": alignment.get("primary_claim_traits", []),
            "primary_claim_layers_by_trait": alignment.get("primary_claim_layers_by_trait", {}),
            "primary_sae_layers": alignment.get("primary_sae_layers", []),
            "cross_check_sae_layers": alignment.get("cross_check_sae_layers", []),
            "overlap_crosscheck_vs_claim_layers": alignment.get("overlap_crosscheck_vs_claim_layers", []),
        },
    }


def _seed_replication_snapshot(seed_rep: dict[str, Any]) -> dict[str, Any]:
    pairwise = seed_rep.get("pairwise_seed_cosines", {})

    def _trait_min(trait: str) -> float | None:
        layers = pairwise.get(trait, {}).get("layers", {})
        mins: list[float] = []
        for layer_stats in layers.values():
            value = layer_stats.get("min_pairwise_cosine")
            if value is not None:
                mins.append(float(value))
        return min(mins) if mins else None

    return {
        "extraction_method": seed_rep.get("extraction_method"),
        "response_temperature": seed_rep.get("response_temperature"),
        "seed_schedule": seed_rep.get("seed_schedule", []),
        "quality_gates": seed_rep.get("quality_gates", {}),
        "min_pairwise_cosine_by_trait": {
            "sycophancy": _trait_min("sycophancy"),
            "evil": _trait_min("evil"),
        },
    }


def _ab_snapshot(gap_checks: dict[str, Any], position_ablation: dict[str, Any]) -> dict[str, Any]:
    extraction_ab = gap_checks.get("extraction_method_ab", {})

    def _method_cos(trait: str) -> float | None:
        value = extraction_ab.get(trait, {}).get("method_cosine_similarity")
        return None if value is None else float(value)

    def _response_consistency(trait: str) -> float | None:
        layers = position_ablation.get("diagnostics", {}).get(trait, {}).get("layers", {})
        values: list[float] = []
        for stats in layers.values():
            val = stats.get("pairwise_cosines", {}).get("response_mean_vs_response_last")
            if val is not None:
                values.append(float(val))
        if not values:
            return None
        return sum(values) / len(values)

    return {
        "gap_check_overall_pass": gap_checks.get("quality_gates", {}).get("overall_pass"),
        "all_traits_extraction_ab_similarity_pass": gap_checks.get("quality_gates", {}).get(
            "all_traits_extraction_ab_similarity_pass"
        ),
        "method_cosine_similarity": {
            "sycophancy": _method_cos("sycophancy"),
            "evil": _method_cos("evil"),
            "hallucination": _method_cos("hallucination"),
        },
        "response_mean_vs_response_last_mean_cosine": {
            "sycophancy": _response_consistency("sycophancy"),
            "evil": _response_consistency("evil"),
            "hallucination": _response_consistency("hallucination"),
        },
    }


def _coherence_snapshot(syc_run: dict[str, Any], evil_run: dict[str, Any]) -> dict[str, Any]:
    syc = syc_run.get("coherence", {})
    evil = evil_run.get("coherence", {})
    return {
        "sycophancy": {
            "baseline_mean": syc.get("baseline_mean"),
            "steered_mean": syc.get("steered_mean"),
            "min_score_threshold": syc.get("min_score_threshold"),
            "pass_min_score": syc.get("pass_min_score"),
            "pass_max_drop": syc.get("pass_max_drop"),
            "pass": syc.get("pass"),
        },
        "evil": {
            "baseline_mean": evil.get("baseline_mean"),
            "steered_mean": evil.get("steered_mean"),
            "min_score_threshold": evil.get("min_score_threshold"),
            "pass_min_score": evil.get("pass_min_score"),
            "pass_max_drop": evil.get("pass_max_drop"),
            "pass": evil.get("pass"),
        },
    }


def _capability_snapshot(syc_run: dict[str, Any], evil_run: dict[str, Any]) -> dict[str, Any]:
    syc = syc_run.get("capability_proxy", {})
    evil = evil_run.get("capability_proxy", {})
    return {
        "proxy_type": "mmlu_sample",
        "sycophancy": {
            "available": syc.get("available"),
            "n_questions": syc.get("n_questions"),
            "baseline_accuracy": syc.get("baseline_accuracy"),
            "steered_accuracy": syc.get("steered_accuracy"),
            "degradation": syc.get("degradation"),
        },
        "evil": {
            "available": evil.get("available"),
            "n_questions": evil.get("n_questions"),
            "baseline_accuracy": evil.get("baseline_accuracy"),
            "steered_accuracy": evil.get("steered_accuracy"),
            "degradation": evil.get("degradation"),
        },
    }


def _concordance_snapshot(concordance: dict[str, Any]) -> dict[str, Any]:
    overall = concordance.get("summary", {}).get("overall", {})
    per_trait = concordance.get("summary", {}).get("per_trait", {})
    return {
        "evaluated_examples_total": overall.get("evaluated_examples_total"),
        "mean_trait_mae": overall.get("mean_trait_mae"),
        "delta_sign_agreement_by_trait": {
            trait: stats.get("delta_sign_agreement_rate") for trait, stats in per_trait.items()
        },
        "examples_per_trait": {
            trait: stats.get("evaluated_examples") for trait, stats in per_trait.items()
        },
    }


def _rollout_schema_snapshot(rollout: dict[str, Any]) -> dict[str, Any]:
    comps = rollout.get("comparisons", {})
    syc = comps.get("sycophancy", {})
    evil = comps.get("evil", {})

    return {
        "plus_mean_fields_null": {
            "sycophancy": syc.get("metrics", {}).get("plus_mean", {}),
            "evil": evil.get("metrics", {}).get("plus_mean", {}),
        },
        "minus_mean_fields_null": {
            "sycophancy": syc.get("metrics", {}).get("minus_mean", {}),
            "evil": evil.get("metrics", {}).get("minus_mean", {}),
        },
        "bidirectional_effect_delta": {
            "sycophancy": syc.get("metrics", {}).get("bidirectional_effect", {}).get("delta_rollout5_minus_rollout3"),
            "evil": evil.get("metrics", {}).get("bidirectional_effect", {}).get("delta_rollout5_minus_rollout3"),
        },
    }


def _evil_asymmetry_snapshot(rollout: dict[str, Any], transfer: dict[str, Any]) -> dict[str, Any]:
    heldout = rollout.get("comparisons", {}).get("evil", {}).get("selected_combo_rollout5", {}).get("test_metric", {})
    metrics = transfer.get("metrics", {})
    return {
        "heldout_rollout5": {
            "steering_shift_mean": heldout.get("steering_shift_mean"),
            "reversal_shift_mean": heldout.get("reversal_shift_mean"),
            "bidirectional_effect": heldout.get("bidirectional_effect"),
        },
        "machiavellian_external_transfer": {
            "plus_vs_baseline": metrics.get("plus_vs_baseline"),
            "baseline_vs_minus": metrics.get("baseline_vs_minus"),
            "plus_vs_minus": metrics.get("plus_vs_minus"),
            "overall_pass": transfer.get("quality_gates", {}).get("overall_pass"),
        },
    }


def _build_findings(
    stage2: dict[str, Any],
    seed_rep: dict[str, Any],
    ab: dict[str, Any],
    coherence: dict[str, Any],
    capability: dict[str, Any],
    concordance: dict[str, Any],
    rollout_schema: dict[str, Any],
    evil_asymmetry: dict[str, Any],
    extraction_robustness: dict[str, Any] | None = None,
    capability_spec: dict[str, Any] | None = None,
    bleed_sensitivity: dict[str, Any] | None = None,
    manual_policy: dict[str, Any] | None = None,
    policy_resolution: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    def _has_null_metric_fields(payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        return any(v is None for v in payload.values())

    plus_fields = rollout_schema.get("plus_mean_fields_null", {})
    minus_fields = rollout_schema.get("minus_mean_fields_null", {})
    rollout_schema_issue_open = any(
        _has_null_metric_fields(plus_fields.get(trait))
        or _has_null_metric_fields(minus_fields.get(trait))
        for trait in ["sycophancy", "evil"]
    )
    robustness_pass = bool(
        extraction_robustness
        and extraction_robustness.get("quality_gates", {}).get("overall_pass", False)
    )
    capability_spec_present = bool(capability_spec)
    bleed_sensitivity_present = bool(bleed_sensitivity)
    manual_policy_present = bool(manual_policy)
    sp1_resolved = bool(
        policy_resolution
        and str(policy_resolution.get("sp_f1_resolution", {}).get("status", "")).startswith("resolved")
    )
    sp3_resolved = bool(
        policy_resolution
        and str(policy_resolution.get("sp_f3_resolution", {}).get("status", "")).startswith("resolved")
    )

    return [
        {
            "id": "SP-F1",
            "severity": "critical",
            "status": "resolved" if sp1_resolved else "open",
            "finding": "Stage 2 cross-SAE claim-layer overlap is structurally blocked at claim layer 12.",
            "evidence_status": "known",
            "evidence": {
                "claim_layers": stage2["cross_source_overlap_gate"].get("claim_layers", []),
                "cross_check_layers": stage2["cross_source_overlap_gate"].get("cross_check_layers", []),
                "overlap_layers": stage2["cross_source_overlap_gate"].get("overlap_layers", []),
                "overlap_gate_status": stage2["cross_source_overlap_gate"].get("status"),
                "policy_resolution_status": (
                    policy_resolution.get("sp_f1_resolution", {}).get("status")
                    if policy_resolution
                    else None
                ),
            },
            "action": (
                "Policy resolution captured in dedicated artifact; execute overlap-capable sensitivity lane before cross-source claims."
                if sp1_resolved
                else "Policy decision needed: move claim layer, add overlap-capable cross-check path, or scope down cross-source claim requirement."
            ),
        },
        {
            "id": "SP-F2",
            "severity": "critical",
            "status": "partial" if robustness_pass else "open",
            "finding": "Extraction A/B remains failed and currently mixes prompt-phase vs generation-phase comparisons.",
            "evidence_status": "known",
            "evidence": {
                "method_cosine_similarity": ab.get("method_cosine_similarity", {}),
                "response_regime_consistency_mean_cosine": ab.get("response_mean_vs_response_last_mean_cosine", {}),
                "content_robustness_overall_pass": (
                    extraction_robustness.get("quality_gates", {}).get("overall_pass")
                    if extraction_robustness
                    else None
                ),
            },
            "action": (
                "Retain prompt-vs-response mismatch as limitation; content-robustness tests now pass."
                if robustness_pass
                else "Replace hard blocker with content-robustness tests (bootstrap pair resampling and extraction-vs-heldout agreement)."
            ),
        },
        {
            "id": "SP-F3",
            "severity": "high",
            "status": "resolved" if sp3_resolved else "open",
            "finding": "Coherence failure is dominated by absolute min-score threshold rather than steered-vs-baseline degradation.",
            "evidence_status": "known",
            "evidence": {
                "coherence_snapshot": coherence,
                "policy_resolution_status": (
                    policy_resolution.get("sp_f3_resolution", {}).get("status")
                    if policy_resolution
                    else None
                ),
            },
            "action": (
                "Dual-scorecard coherence policy is frozen; report strict and relative interpretations together."
                if sp3_resolved
                else "Run coherence policy decision memo and evaluate relative-only gating for Week 2 closeout scorecard."
            ),
        },
        {
            "id": "SP-F4",
            "severity": "high",
            "status": "resolved" if robustness_pass else "partial",
            "finding": "Seed replication evidence demonstrates numerical determinism, not stochastic robustness under varied prompt order/sampling.",
            "evidence_status": "known",
            "evidence": {
                "extraction_method": seed_rep.get("extraction_method"),
                "response_temperature": seed_rep.get("response_temperature"),
                "seed_schedule": seed_rep.get("seed_schedule", []),
                "min_pairwise_cosine_by_trait": seed_rep.get("min_pairwise_cosine_by_trait", {}),
                "content_robustness_overall_pass": (
                    extraction_robustness.get("quality_gates", {}).get("overall_pass")
                    if extraction_robustness
                    else None
                ),
            },
            "action": (
                "Determinism evidence is now complemented by bootstrap/heldout robustness checks."
                if robustness_pass
                else "Reclassify as determinism-only evidence and add proposal-aligned robustness protocol (order perturbation + nonzero sampling or bootstrap subsets)."
            ),
        },
        {
            "id": "SP-F5",
            "severity": "medium",
            "status": "resolved" if capability_spec_present else "open",
            "finding": "Capability evidence is narrow (MMLU sample only) for stronger capability-preservation claims.",
            "evidence_status": "known",
            "evidence": {
                "capability_snapshot": capability,
                "capability_spec_artifact_present": capability_spec_present,
            },
            "action": (
                "Capability-suite boundary is now explicit (Week2 proxy vs broader suite)."
                if capability_spec_present
                else "Define capability-suite spec artifact separating Week 2 gate proxy from later-stage broader capability claims."
            ),
        },
        {
            "id": "SP-F6",
            "severity": "medium",
            "status": "open" if rollout_schema_issue_open else "resolved",
            "finding": (
                "Rollout sensitivity artifact has null plus/minus fields due metric-key mismatch."
                if rollout_schema_issue_open
                else "Rollout sensitivity schema mismatch is patched (null plus/minus fields removed)."
            ),
            "evidence_status": "known",
            "evidence": rollout_schema,
            "action": (
                "Patch comparator key mapping and add failing test for missing keys."
                if rollout_schema_issue_open
                else "No further action required for this item; keep strict metric-key test coverage."
            ),
        },
        {
            "id": "SP-F7",
            "severity": "medium",
            "status": "resolved" if bleed_sensitivity_present else "pending",
            "finding": "Cross-trait bleed threshold sensitivity remains unresolved (R1-F6).",
            "evidence_status": "known",
            "evidence": {
                "pending_checklist_id": "R1-F6",
                "bleed_sensitivity_artifact_present": bleed_sensitivity_present,
            },
            "action": (
                "Threshold sensitivity artifact exists and policy note is now explicit."
                if bleed_sensitivity_present
                else "Run threshold sensitivity analysis and lock policy before superseding Week 2 NO-GO."
            ),
        },
        {
            "id": "SP-F8",
            "severity": "medium",
            "status": "resolved" if manual_policy_present else "pending",
            "finding": "Manual concordance is still low-power (5 examples per trait).",
            "evidence_status": "known",
            "evidence": {
                "concordance_snapshot": concordance,
                "manual_policy_artifact_present": manual_policy_present,
            },
            "action": (
                "Concordance role is explicitly scoped to sanity-check-only with upgrade condition documented."
                if manual_policy_present
                else "Either expand to 15-20 per trait or explicitly scope concordance as sanity-check-only in governance docs."
            ),
        },
        {
            "id": "SP-F9",
            "severity": "medium",
            "status": "document_limitation",
            "finding": "Evil directional asymmetry differs by prompt distribution (held-out vs machiavellian transfer).",
            "evidence_status": "observed",
            "evidence": evil_asymmetry,
            "action": "Document floor/ceiling distribution limitation and avoid over-claiming symmetric bidirectionality.",
        },
    ]


def _build_plan() -> dict[str, Any]:
    return {
        "policy_freeze_required_before_new_launch": True,
        "phases": [
            {
                "phase": "P0",
                "goal": "Close critical policy contradictions that block progression.",
                "tasks": [
                    {
                        "id": "P0-T1",
                        "title": "Coherence gate decision package",
                        "deliverable": "artifact + decision entry defining absolute vs relative coherence gating for Week 2 scorecard",
                        "acceptance_criteria": [
                            "baseline and steered coherence evidence cited for sycophancy + evil",
                            "binding coherence policy explicitly frozen in DECISIONS.md",
                            "CURRENT_STATE and checklist updated with chosen policy",
                        ],
                    },
                    {
                        "id": "P0-T2",
                        "title": "Stage 2 claim-layer policy resolution",
                        "deliverable": "decision entry choosing one path: layer move, cross-check scope-down, or dual-layer sensitivity",
                        "acceptance_criteria": [
                            "cross-SAE overlap expectation explicitly tied to claim scope",
                            "audit gate criteria updated to match chosen policy",
                            "no ambiguous pass path remains",
                        ],
                    },
                ],
            },
            {
                "phase": "P1",
                "goal": "Replace misleading or incomplete robustness evidence with policy-aligned diagnostics.",
                "tasks": [
                    {
                        "id": "P1-T1",
                        "title": "Extraction robustness closure run",
                        "deliverable": "bootstrap/heldout extraction robustness artifact",
                        "acceptance_criteria": [
                            "pairwise cosine distribution across bootstrap subsets reported",
                            "train-vs-heldout extraction cosine reported",
                            "A/B regime-split metric retained as limitation, not sole blocker",
                        ],
                    },
                    {
                        "id": "P1-T2",
                        "title": "Seed-replication status correction",
                        "deliverable": "checklist/doc update reclassifying current run as determinism-only",
                        "acceptance_criteria": [
                            "R2-G6 marked partial with rationale",
                            "proposal-aligned robustness plan recorded",
                        ],
                    },
                    {
                        "id": "P1-T3",
                        "title": "Rollout sensitivity schema patch",
                        "deliverable": "code + tests + corrected artifact",
                        "acceptance_criteria": [
                            "plus_mean/minus_mean fields either computed or removed",
                            "unit tests fail on missing selected_test_evaluation metric keys",
                        ],
                    },
                ],
            },
            {
                "phase": "P2",
                "goal": "Close remaining pending reviewer items and finalize launch-readiness packet.",
                "tasks": [
                    {
                        "id": "P2-T1",
                        "title": "Capability-suite specification",
                        "deliverable": "spec artifact distinguishing Week 2 proxy gate vs broader capability claims",
                        "acceptance_criteria": [
                            "R2-G8 status updated from pending",
                            "benchmark list and thresholds frozen",
                        ],
                    },
                    {
                        "id": "P2-T2",
                        "title": "Cross-trait bleed sensitivity",
                        "deliverable": "sensitivity analysis artifact and policy note",
                        "acceptance_criteria": [
                            "R1-F6 status updated",
                            "threshold rationale documented with literature caveat",
                        ],
                    },
                    {
                        "id": "P2-T3",
                        "title": "Manual concordance policy closure",
                        "deliverable": "expanded concordance artifact or explicit de-scoping decision",
                        "acceptance_criteria": [
                            "R2-C5 status updated from pending",
                            "judge trust narrative aligns with chosen evidence weighting",
                        ],
                    },
                ],
            },
        ],
        "superseding_no_go_preconditions": [
            "Critical policy decisions P0-T1 and P0-T2 are frozen and documented.",
            "Pending reviewer checklist items R1-F6, R2-C5, R2-G8 are closed or explicitly scoped as limitations.",
            "No unresolved schema/reporting bugs remain in active closeout synthesis artifacts.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate second-pass reviewer reconciliation analysis artifact.")
    parser.add_argument(
        "--trait-scope-artifact",
        default="results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json",
    )
    parser.add_argument(
        "--stage2-audit-artifact",
        default="results/stage2_decomposition/week3_sae_reconstruction_audit_20260301T033046Z.json",
    )
    parser.add_argument(
        "--seed-replication-artifact",
        default="results/stage1_extraction/week2_extraction_seed_replication_20260302T180612Z.json",
    )
    parser.add_argument(
        "--gap-check-artifact",
        default="results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json",
    )
    parser.add_argument(
        "--position-ablation-artifact",
        default="results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json",
    )
    parser.add_argument(
        "--syc-rollout5-artifact",
        default="results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json",
    )
    parser.add_argument(
        "--evil-rollout5-artifact",
        default="results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260303T081318Z.json",
    )
    parser.add_argument(
        "--machiavellian-transfer-artifact",
        default="results/stage1_extraction/week2_machiavellian_external_transfer_20260302T180239Z.json",
    )
    parser.add_argument(
        "--rollout-sensitivity-artifact",
        default="results/stage1_extraction/week2_rollout_stability_sensitivity_20260303T132222Z.json",
    )
    parser.add_argument(
        "--manual-concordance-artifact",
        default="results/stage1_extraction/week2_primary_manual_concordance_ratings_20260227T202822Z.json",
    )
    parser.add_argument(
        "--extraction-robustness-artifact",
        default="results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json",
    )
    parser.add_argument(
        "--bleed-sensitivity-artifact",
        default="results/stage1_extraction/week2_cross_trait_bleed_sensitivity_20260303T164726Z.json",
    )
    parser.add_argument(
        "--capability-suite-spec-artifact",
        default="results/stage1_extraction/week2_capability_suite_spec_20260303T164726Z.json",
    )
    parser.add_argument(
        "--manual-policy-artifact",
        default="results/stage1_extraction/week2_manual_concordance_policy_closure_20260303T164726Z.json",
    )
    parser.add_argument(
        "--policy-resolution-artifact",
        default="results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json",
    )
    args = parser.parse_args()

    trait_scope_path = ROOT / args.trait_scope_artifact
    stage2_audit_path = ROOT / args.stage2_audit_artifact
    seed_rep_path = ROOT / args.seed_replication_artifact
    gap_check_path = ROOT / args.gap_check_artifact
    position_ablation_path = ROOT / args.position_ablation_artifact
    syc_run_path = ROOT / args.syc_rollout5_artifact
    evil_run_path = ROOT / args.evil_rollout5_artifact
    mach_transfer_path = ROOT / args.machiavellian_transfer_artifact
    rollout_sensitivity_path = ROOT / args.rollout_sensitivity_artifact
    concordance_path = ROOT / args.manual_concordance_artifact
    extraction_robustness_path = ROOT / args.extraction_robustness_artifact
    bleed_sensitivity_path = ROOT / args.bleed_sensitivity_artifact
    capability_spec_path = ROOT / args.capability_suite_spec_artifact
    manual_policy_path = ROOT / args.manual_policy_artifact
    policy_resolution_path = ROOT / args.policy_resolution_artifact

    trait_scope = _load_json(trait_scope_path)
    stage2_audit = _load_json(stage2_audit_path)
    seed_rep = _load_json(seed_rep_path)
    gap_check = _load_json(gap_check_path)
    position_ablation = _load_json(position_ablation_path)
    syc_run = _load_json(syc_run_path)
    evil_run = _load_json(evil_run_path)
    mach_transfer = _load_json(mach_transfer_path)
    rollout_sensitivity = _load_json(rollout_sensitivity_path)
    concordance = _load_json(concordance_path)
    extraction_robustness = _load_json(extraction_robustness_path)
    bleed_sensitivity = _load_json(bleed_sensitivity_path)
    capability_spec = _load_json(capability_spec_path)
    manual_policy = _load_json(manual_policy_path)
    policy_resolution = _load_json(policy_resolution_path)

    stage2_snapshot = _stage2_snapshot(stage2_audit)
    seed_snapshot = _seed_replication_snapshot(seed_rep)
    ab_snapshot = _ab_snapshot(gap_check, position_ablation)
    coherence_snapshot = _coherence_snapshot(syc_run, evil_run)
    capability_snapshot = _capability_snapshot(syc_run, evil_run)
    concordance_snapshot = _concordance_snapshot(concordance)
    rollout_schema_snapshot = _rollout_schema_snapshot(rollout_sensitivity)
    evil_asymmetry_snapshot = _evil_asymmetry_snapshot(rollout_sensitivity, mach_transfer)

    findings = _build_findings(
        stage2=stage2_snapshot,
        seed_rep=seed_snapshot,
        ab=ab_snapshot,
        coherence=coherence_snapshot,
        capability=capability_snapshot,
        concordance=concordance_snapshot,
        rollout_schema=rollout_schema_snapshot,
        evil_asymmetry=evil_asymmetry_snapshot,
        extraction_robustness=extraction_robustness,
        capability_spec=capability_spec,
        bleed_sensitivity=bleed_sensitivity,
        manual_policy=manual_policy,
        policy_resolution=policy_resolution,
    )

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_second_pass_reconciliation_analysis",
        "inputs": {
            "trait_scope_artifact": str(trait_scope_path.relative_to(ROOT)),
            "stage2_audit_artifact": str(stage2_audit_path.relative_to(ROOT)),
            "seed_replication_artifact": str(seed_rep_path.relative_to(ROOT)),
            "gap_check_artifact": str(gap_check_path.relative_to(ROOT)),
            "position_ablation_artifact": str(position_ablation_path.relative_to(ROOT)),
            "syc_rollout5_artifact": str(syc_run_path.relative_to(ROOT)),
            "evil_rollout5_artifact": str(evil_run_path.relative_to(ROOT)),
            "machiavellian_transfer_artifact": str(mach_transfer_path.relative_to(ROOT)),
            "rollout_sensitivity_artifact": str(rollout_sensitivity_path.relative_to(ROOT)),
            "manual_concordance_artifact": str(concordance_path.relative_to(ROOT)),
            "extraction_robustness_artifact": str(extraction_robustness_path.relative_to(ROOT)),
            "bleed_sensitivity_artifact": str(bleed_sensitivity_path.relative_to(ROOT)),
            "capability_suite_spec_artifact": str(capability_spec_path.relative_to(ROOT)),
            "manual_policy_artifact": str(manual_policy_path.relative_to(ROOT)),
            "policy_resolution_artifact": str(policy_resolution_path.relative_to(ROOT)),
        },
        "evidence_status": {
            "artifact_fields": "known",
            "finding_severity_assignment": "inferred",
            "recommended_plan": "inferred",
        },
        "scope_snapshot": {
            "trait_scope_status": trait_scope.get("trait_scope", {}),
            "stage2_scope_recommendation": trait_scope.get("stage2_scope_recommendation", {}),
        },
        "metrics_snapshot": {
            "stage2": stage2_snapshot,
            "seed_replication": seed_snapshot,
            "extraction_ab": ab_snapshot,
            "coherence": coherence_snapshot,
            "capability": capability_snapshot,
            "manual_concordance": concordance_snapshot,
            "rollout_schema": rollout_schema_snapshot,
            "evil_asymmetry": evil_asymmetry_snapshot,
            "extraction_robustness": extraction_robustness.get("quality_gates", {}),
            "bleed_sensitivity": bleed_sensitivity.get("summary", {}),
            "capability_suite_spec": {
                "week2_proxy_gate": capability_spec.get("week2_proxy_gate", {}).get("gate_name"),
                "broader_suite_present": bool(capability_spec.get("broader_suite_requirement")),
            },
            "manual_policy": manual_policy.get("policy_decision", {}),
            "policy_resolution": {
                "sp_f1_status": policy_resolution.get("sp_f1_resolution", {}).get("status"),
                "sp_f3_status": policy_resolution.get("sp_f3_resolution", {}).get("status"),
            },
        },
        "reconciled_findings": findings,
        "execution_plan": _build_plan(),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"week2_second_pass_reconciliation_analysis_{_timestamp()}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({"report_path": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()
