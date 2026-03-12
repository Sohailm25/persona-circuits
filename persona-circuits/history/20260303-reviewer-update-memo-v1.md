# Week 2 Remediation Update Memo (for Reviewer Re-pass)

**Prepared:** 2026-03-03 (America/Chicago)
**Scope:** Reconciliation of Reviewer 1 + Reviewer 2 first-pass and second-pass findings through the latest hardening tranche.

## 1) Evidence Base and Traceability

- **known**: Verbatim reviewer logs are preserved and indexed:
  - `history/reviews/20260227-reviewer1-verbatim.md`
  - `history/reviews/20260227-reviewer2-verbatim.md`
  - `history/reviews/20260303-reviewer1-second-pass-verbatim.md`
  - `history/reviews/20260303-reviewer2-second-pass-verbatim.md`
- **known**: Master reconciliation checklist is active and fully statused (no `pending` rows):
  - `history/20260227-reviewer-reconciliation-checklist-v1.md`
- **known**: Active structured synthesis artifact (schema-consistent refresh):
  - `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T191356Z.json`
- **known**: Policy-closure packet for second-pass critical blockers:
  - `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`

## 2) Reviewer 1 Findings Reconciliation

### R1-F1 Stage2 false-positive readiness risk
- Status: **resolved**.
- **known evidence**:
  - Stage2 claim-layer audit fail path is explicit (no accidental pass): `results/stage2_decomposition/week3_sae_reconstruction_audit_20260301T033046Z.json`
  - Split claim-scope policy is frozen: `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`

### R1-F2 Extraction position likely wrong / A-B low cosine
- Status: **partial**.
- **known evidence**:
  - A/B mismatch remains (<0.7): `results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json`
  - Position ablation confirms prompt-vs-response regime gap: `results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json`
  - Content-robustness now passes: `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json`
- **inferred**: Prompt-vs-response inconsistency is now treated as a bounded limitation, not a sole blocker for prompt-regime claims.

### R1-F3 Alpha selection objective mismatch
- Status: **partial**.
- **known evidence**:
  - Constrained-selection policy implemented in runner/config:
    - `scripts/week2_behavioral_validation_upgrade.py`
    - `configs/experiment.yaml`
    - `tests/test_week2_validation_utils.py`
  - Lower-alpha remediation runs executed but coherence remains failing:
    - `results/stage1_extraction/week2_alpha_constrained_selection_20260228T131217Z.json`

### R1-F4 Governance drift vs proposal criteria
- Status: **resolved**.
- **known evidence**:
  - Dual-scorecard governance is frozen and decision-logged:
    - `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`
    - `DECISIONS.md`

### R1-F5 Evil construct mismatch
- Status: **resolved**.
- **known evidence**:
  - Trait lane split + construct-aligned transfer:
    - `results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json`
    - `results/stage1_extraction/week2_machiavellian_external_transfer_20260302T180239Z.json`

### R1-F6 Cross-trait bleed threshold sensitivity gap
- Status: **resolved**.
- **known evidence**:
  - Sensitivity artifact produced with threshold sweep:
    - `results/stage1_extraction/week2_cross_trait_bleed_sensitivity_20260303T164726Z.json`

## 3) Reviewer 2 Findings Reconciliation

### Resolved
- **R2-C3 / R2-G2 hallucination formal closure**:
  - `results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json`
- **R2-C4 / R2-G3 evil benchmark alignment**:
  - `results/stage1_extraction/week2_machiavellian_external_transfer_20260302T180239Z.json`
- **R2-C5 manual concordance policy closure**:
  - `results/stage1_extraction/week2_manual_concordance_policy_closure_20260303T164726Z.json`
- **R2-G7 rollout-depth sensitivity executed**:
  - `results/stage1_extraction/week2_rollout_stability_sensitivity_20260303T132222Z.json`
- **R2-G8 capability-scope boundary specification**:
  - `results/stage1_extraction/week2_capability_suite_spec_20260303T164726Z.json`

### Partial
- **R2-C1 / R2-G1 lower-alpha validation**: evidence exists but does not clear strict coherence gate.
  - `results/stage1_extraction/week2_alpha_constrained_selection_20260228T131217Z.json`
- **R2-C2 / R2-G5 extraction A/B root-cause closure**: position/regime mismatch still present; content-robustness closure added.
  - `results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json`
  - `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json`
- **R2-C6 / R2-G4 Stage2 reconstruction/cross-SAE limitations**: still constrained at claim layer 12 for cross-source claims.
  - `results/stage2_decomposition/week3_sae_reconstruction_audit_20260303T132222Z.json`
- **R2-G6 seed replication**: now correctly scoped as determinism + supplemented by robustness bootstrap; not full stochastic perturbation closure.
  - `results/stage1_extraction/week2_extraction_seed_replication_20260302T180612Z.json`
  - `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json`

## 4) Second-Pass Findings (SP-F1..SP-F9)

**known (from active synthesis artifact):**
`results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T191356Z.json`

- `SP-F1`: resolved
- `SP-F2`: partial
- `SP-F3`: resolved
- `SP-F4`: resolved
- `SP-F5`: resolved
- `SP-F6`: resolved
- `SP-F7`: resolved
- `SP-F8`: resolved
- `SP-F9`: document_limitation

## 5) Implementation and Test Delta Added in This Tranche

### Scripts added/updated
- `scripts/week2_extraction_robustness_bootstrap.py`
- `scripts/week2_cross_trait_bleed_sensitivity.py`
- `scripts/week2_capability_suite_spec.py`
- `scripts/week2_manual_concordance_policy_closure.py`
- `scripts/week2_policy_resolution_packet.py`
- `scripts/week2_second_pass_reconciliation_analysis.py` (artifact-input refresh + status sync)

### Tests added
- `tests/test_week2_extraction_robustness_bootstrap.py`
- `tests/test_week2_cross_trait_bleed_sensitivity.py`
- `tests/test_week2_capability_suite_spec.py`
- `tests/test_week2_manual_concordance_policy_closure.py`
- `tests/test_week2_policy_resolution_packet.py`

### Current local validation
- **known**: full suite passes.
  - command: `python3 -m unittest discover -s tests`
  - latest observed result: `Ran 112 tests ... OK`

## 6) Current Ground Truth Status

- **known**: Week 2 remains active; replication/stress remains blocked under NO-GO.
  - `CURRENT_STATE.md`
  - `DECISIONS.md`
- **known**: Stage2 claim-readiness is still not globally claim-ready under strict cross-source interpretation; policy now separates:
  - decomposition-start (single-source at selected claim layer) vs
  - cross-source claim lane (overlap-capable sensitivity layers only).
  - `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`

## 7) Work Remaining (Explicit)

### Critical remaining item
1. **SP-F2 extraction A/B closure remains partial**.
   - Required next action: run the planned factorial closure to isolate position vs generation-phase effects, then freeze final interpretation policy.

### Documented limitations to carry forward
1. **SP-F9** evil asymmetry differs by prompt distribution (held-out vs external transfer).
2. Stage2 cross-source claims are limited to overlap-capable sensitivity layers until overlap evidence exists for selected claim layer.
3. Seed-replication evidence should be cited as determinism + content robustness, not full stochastic robustness.

### Governance before any superseding launch decision
- Maintain dual-scorecard reporting for coherence.
- Maintain explicit claim-scope split for Stage2.
- Keep NO-GO guard until superseding decision entry is written.

## 8) Reviewer Re-pass Request Package (Suggested Attachments)

1. `history/reviews/20260303-reviewer1-second-pass-verbatim.md`
2. `history/reviews/20260303-reviewer2-second-pass-verbatim.md`
3. `history/20260227-reviewer-reconciliation-checklist-v1.md`
4. `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T191356Z.json`
5. `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`
6. `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json`
7. `results/stage1_extraction/week2_cross_trait_bleed_sensitivity_20260303T164726Z.json`
8. `results/stage1_extraction/week2_capability_suite_spec_20260303T164726Z.json`
9. `results/stage1_extraction/week2_manual_concordance_policy_closure_20260303T164726Z.json`

