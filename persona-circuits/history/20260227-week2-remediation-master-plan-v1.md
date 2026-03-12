# Week 2 Remediation Master Plan v1

## 1) Purpose

This plan reconciles all open issues from external Reviewer 1 + Reviewer 2 and defines the minimum end-to-end remediation work required before any superseding decision to the current Week 2 `NO-GO` status.

Current governing decision:
- `DECISIONS.md` (2026-02-27T15:31:15-0600): Week 2 closeout is `NO-GO` for replication/stress launches.

## 2) Verbatim Review Inputs (Immutable)

- Reviewer 1 verbatim: `history/reviews/20260227-reviewer1-verbatim.md`
- Reviewer 2 verbatim: `history/reviews/20260227-reviewer2-verbatim.md`

These files are the source of truth for remediation scope. No paraphrase-only closure is allowed.

## 3) Remediation Guardrails

1. No replication/stress launch until a superseding decision entry is logged in `DECISIONS.md`.
2. Do not modify Week 2 acceptance criteria mid-tranche without a new decision entry.
3. Every remediation step must produce a timestamped artifact and a `known/observed/inferred/unknown` status note.
4. End-of-remediation must include a full checklist audit against every reviewer finding ID.

## 4) Authoritative Week 2 Evaluation Policy During Remediation

To address governance-drift concern while preserving hardening rigor, remediation will report both scorecards in all closeout artifacts:

- Scorecard A (`proposal_compatibility`): proposal Week 2 criterion tracking (including "continue if >=2 traits have validated steering" semantics).
- Scorecard B (`hardening_reliability`): current upgraded reliability checks (coherence/capability/specificity/cross-bleed/extraction robustness/etc.).

Decision rule for lifting NO-GO in this tranche:
- Required: explicit decision entry with both scorecards summarized and rationale for any disagreement between A vs B.

## 5) Workstreams

### WS-A: Governance Freeze + Traceability
Targets: R1-4, R2-X, R2-XII

Tasks:
1. Add explicit scorecard dual-reporting fields to ingestion/closeout outputs and docs.
2. Freeze remediation gate policy in config/docs before launching remediation runs.
3. Add end-of-tranche "criterion drift check" section to final closeout summary.

Deliverables:
- Updated `scripts/week2_primary_postrun_ingest.py` (if needed for dual-scorecard fields).
- Updated docs: `CURRENT_STATE.md`, `DECISIONS.md`, `RESULTS_INDEX.md`.

### WS-B: Extraction Position Robustness Root-Cause
Targets: R1-2, R2-IV, R2-IX (extraction root cause), R2-X(2)

Tasks:
1. Extend extraction diagnostics to compute vectors using:
   - prompt-last token,
   - response-mean tokens,
   - optional response-last token control.
2. Run per-layer (11-16) A/B robustness matrix for each trait.
3. Determine whether disagreement is layer-specific vs globally position-driven.
4. Promote response-token extraction to primary if evidence supports it; keep prompt-last as control.

Deliverables:
- Updated extraction script(s) and tests.
- New artifact: `week2_extraction_position_ablation_<timestamp>.json`.

### WS-C: Constrained Alpha Selection (Working Alpha)
Targets: R1-3, R2-III, R2-X(1), R2-X(4), R2-IX (lower-alpha validation)

Tasks:
1. Replace pure effect-max ranking with constrained optimization:
   - eligible only if quality/capability/specificity/coherence constraints pass,
   - select smallest alpha among eligible combos.
2. Add explicit lower-alpha validation pass (at minimum alpha 2.0 and 2.5 lanes for sycophancy + evil).
3. Report tradeoff curves (effect vs coherence/capability).

Deliverables:
- Updated `scripts/week2_behavioral_validation_upgrade.py` ranking path + tests.
- New artifact: `week2_alpha_constrained_selection_<timestamp>.json`.

### WS-D: Trait Scope Resolution (Hallucination + Evil Lane Split)
Targets: R1-5, R2-V, R2-VI, R2-IX (hallucination status + benchmark alignment)

Tasks:
1. Formally classify hallucination as Stage 1 negative finding unless remediation requalifies it.
2. Split evil into explicit evaluation lanes:
   - `harmful_content_lane` (current benchmark behavior),
   - `machiavellian_disposition_lane` (construct-aligned benchmark set).
3. Gate these lanes separately in closeout summaries.

Deliverables:
- Decision/doc updates with explicit trait-lane semantics.
- New artifact(s): lane-specific transfer reports.

### WS-E: Stage 2 Readiness Gate Integrity
Targets: R1-1, R2-VIII, R2-IX (cross-SAE selected-layer coverage), R2-X(3)

Tasks:
1. Rebuild Stage 2 readiness checks around selected Week 2 layers (not only default layer 16).
2. Increase probe size beyond tiny probe and require multi-seed completion.
3. Add explicit selected-layer cross-SAE coverage report; if no coverage, mark limitation as blocking/non-blocking by policy.
4. Tighten reconstruction evidence policy (reporting both threshold pass and literature-relative caveat).

Deliverables:
- Updated `scripts/week3_sae_reconstruction_audit.py` and related probe scripts.
- New artifact: `week3_sae_reconstruction_audit_<timestamp>.json` with multi-seed + selected-layer fields.

### WS-F: Stability and Calibration Extensions
Targets: R2-VII, R2-IX (multi-seed extraction, rollout stability, manual concordance power)

Tasks:
1. Multi-seed extraction replication (42, 123, 456, 789).
2. Rollout stability sensitivity beyond current default.
3. Expand manual concordance sample (or formally downweight its role versus kappa).

Deliverables:
- New stability artifacts and updated closeout summary language.

## 6) Execution Order (Strict)

1. WS-A governance freeze (no runs yet).
2. WS-B extraction-position diagnostics (small-run then full-run).
3. WS-C constrained-alpha implementation + targeted behavioral reruns.
4. WS-D trait-lane resolution (hallucination status + evil lane split).
5. WS-E Stage 2 gate integrity rerun.
6. WS-F stability extensions.
7. End-of-remediation checklist audit (all reviewer IDs accounted for).
8. Superseding decision entry (or reaffirmed NO-GO).

## 7) Exit Criteria for Remediation Tranche

Minimum required before considering a superseding decision:

1. Reviewer reconciliation checklist updated with evidence path for every finding ID.
2. Extraction-position root-cause artifact completed and interpreted.
3. Constrained alpha selection artifact completed (including lower-alpha evidence).
4. Stage 2 selected-layer, multi-seed gate artifact completed.
5. Explicit hallucination status and evil lane split decision logged.
6. Final closeout summary with dual scorecards (proposal compatibility + hardening reliability).

## 8) Final Reviewer Update Preparation (Post-Fix)

After end-to-end remediation runs complete:
1. Create `history/<timestamp>-week2-remediation-results-update-for-reviewers.md`.
2. Include only `known` claims for fixed items and explicit `unknown` for unresolved items.
3. Include a one-to-one mapping from each reviewer finding ID to final status (`resolved`, `partially_resolved`, `unresolved`) with artifact links.

