# Reviewer Reconciliation Checklist v1

## Source-of-Truth Inputs

- Reviewer 1 verbatim: `history/reviews/20260227-reviewer1-verbatim.md`
- Reviewer 2 verbatim: `history/reviews/20260227-reviewer2-verbatim.md`
- Reviewer 1 second-pass verbatim: `history/reviews/20260303-reviewer1-second-pass-verbatim.md`
- Reviewer 2 second-pass verbatim: `history/reviews/20260303-reviewer2-second-pass-verbatim.md`
- Remediation plan: `history/20260227-week2-remediation-master-plan-v1.md`

## Status Key

- `pending`: not yet remediated
- `in_progress`: remediation started
- `resolved`: remediated with evidence
- `partial`: some evidence, gap remains
- `n/a`: superseded by explicit scope decision

## Reviewer 1 Findings

| ID | Finding (verbatim short label) | Planned workstream(s) | Required evidence | Status |
|---|---|---|---|---|
| R1-F1 | Stage2 readiness false-positive risk (layer/probe/seed mismatch) | WS-E | updated Stage2 multi-seed selected-layer audit artifact | resolved |
| R1-F2 | Extraction position likely wrong (A/B low cosine) | WS-B | extraction-position ablation artifact (layers 11-16) | partial |
| R1-F3 | Alpha selection effect-maximizing, not constrained | WS-C | constrained-alpha selection artifact + code/tests | partial |
| R1-F4 | Governance drift vs proposal criterion | WS-A | dual-scorecard closeout report + decision entry | resolved |
| R1-F5 | Evil looks like construct mismatch | WS-D | lane-split decision + lane-specific benchmark artifacts | resolved |
| R1-F6 | Cross-trait bleed threshold may be over-tight | WS-C + WS-A | sensitivity analysis + policy note in closeout | resolved |

## Reviewer 2 Critical Issues and Gaps

| ID | Finding (verbatim short label) | Planned workstream(s) | Required evidence | Status |
|---|---|---|---|---|
| R2-C1 | Alpha 3.0 oversteer risk | WS-C | alpha 2.0/2.5 rerun evidence + constrained selection outputs | partial |
| R2-C2 | A/B extraction failure is fundamental | WS-B | position/layer root-cause artifact | partial |
| R2-C3 | Hallucination null should be dropped/formalized | WS-D | formal status decision + scope updates | resolved |
| R2-C4 | Evil bidirectionality + framing tension | WS-D | harmful vs machiavellian lane transfer artifacts | resolved |
| R2-C5 | Manual concordance underpowered | WS-F | expanded sample or explicit weighting decision | resolved |
| R2-C6 | Stage2 reconstruction quality/cross-SAE limitations | WS-E | stricter selected-layer multi-seed audit + caveat report | partial |
| R2-G1 | Lower-alpha validation missing | WS-C | lower-alpha evidence artifact | partial |
| R2-G2 | Hallucination formal status missing | WS-D | decision entry + current_state update | resolved |
| R2-G3 | Evil benchmark alignment missing | WS-D | construct-aligned benchmark output | resolved |
| R2-G4 | Cross-SAE at selected layers missing | WS-E | selected-layer cross-SAE coverage report | partial |
| R2-G5 | A/B root cause missing | WS-B | diagnostic report with causal interpretation | partial |
| R2-G6 | Multi-seed extraction replication missing | WS-F | multi-seed extraction artifact(s) | partial |
| R2-G7 | Rollout stability depth missing | WS-F | rollout sensitivity artifact | resolved |
| R2-G8 | Capability benchmark suite underspecified | WS-C + WS-A | explicit benchmark definition in config/docs | resolved |

## Progress Notes (2026-02-28T20:56:20-0600)

- WS-A evidence logged:
  - `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T220017Z.json`
  - `DECISIONS.md` entry `2026-02-27T16:19:49-0600` (dual-scorecard governance freeze)
- WS-B evidence logged:
  - small-run: `results/stage1_extraction/week2_extraction_position_ablation_20260227T221817Z.json`
  - expanded-run: `results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json`
  - `DECISIONS.md` entries `2026-02-27T16:19:49-0600` and `2026-02-27T16:53:52-0600`
- WS-B response-mean sensitivity evidence logged:
  - response-mean vector extraction: `results/stage1_extraction/week2_vector_extraction_summary_20260228T135004Z.json`
  - response-mean reruns:
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260228T202943Z.json`
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260301T025504Z.json`
  - synthesis: `results/stage1_extraction/week2_response_mean_sensitivity_20260301T025554Z.json`
- WS-C implementation evidence logged:
  - `scripts/week2_behavioral_validation_upgrade.py` (config-driven constrained combo selection)
  - `configs/experiment.yaml` (`steering.combo_selection_policy`)
  - `tests/test_week2_validation_utils.py` (selection-policy tests)
  - `DECISIONS.md` entry `2026-02-27T16:55:11-0600`
- WS-C targeted rerun evidence logged:
  - `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260228T070200Z.json`
  - `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260228T131128Z.json`
  - synthesis: `results/stage1_extraction/week2_alpha_constrained_selection_20260228T131217Z.json`
- Extraction-policy lock for WS-C logged:
  - `DECISIONS.md` entry `2026-02-27T16:59:57-0600` (prompt-last primary for WS-C; response-mean sensitivity lane deferred)
- Status rationale:
  - `R1-F4` remains `partial` until end-of-tranche criterion-drift check is included in final closeout memo.
  - `R1-F2`, `R2-C2`, `R2-G5` remain `partial`: downstream response-mean rerun impact is now measured, but method-similarity gate failure (`<0.7`) persists and no full reliability recovery is demonstrated.
  - `R1-F3`, `R2-C1`, `R2-G1` remain `partial`: lower-alpha rerun evidence now exists but does not clear overall reliability failures (coherence still fails; tradeoff remains unresolved).

## Progress Notes (2026-02-28T21:31:00-0600)

- WS-D evidence logged:
  - `results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json`
  - outcome snapshot:
    - hallucination status: `negative_finding_stage1`
    - evil harmful-content lane: `disconfirmed_bidirectional_harmful_content`
    - evil machiavellian lane: `supported_but_week2_not_validated_due_to_coherence`
- WS-E evidence logged:
  - `results/stage2_decomposition/week3_sae_reconstruction_investigation_20260301T031743Z.json` (seed schedule consumed: `[42,123,456,789]`)
  - `results/stage2_decomposition/week3_sae_reconstruction_root_cause_20260301T033002Z.json` (layer12 best-variant consistency across seeds)
  - `results/stage2_decomposition/week3_sae_reconstruction_audit_20260301T033046Z.json` (claim-layer integrity audit)
- Status rationale:
  - `R1-F1` set to `resolved` because Stage2 readiness no longer has a false-positive pass path: claim-layer + multi-seed gates are computed and now fail explicitly when unmet.
  - `R2-C3`/`R2-G2` set to `resolved` due explicit hallucination formal status artifact.
  - `R2-C6`/`R2-G4` remain `partial`: stricter audit is implemented and evidence logged, but selected-claim-layer cross-SAE overlap is still empty and token gate at layer12 fails threshold.
  - `R1-F5`/`R2-C4`/`R2-G3` remain `partial`: lane split is formalized, but construct-aligned external benchmark evidence is still pending.

## Progress Notes (2026-03-03T06:15:00-0600)

- WS-D/construct-aligned benchmark evidence logged:
  - `results/stage1_extraction/week2_machiavellian_external_transfer_20260302T180239Z.json` (`overall_pass=true`, plus/base/minus directional gates all pass at `(layer=12, alpha=3.0)`).
- WS-F multi-seed extraction replication evidence logged:
  - `results/stage1_extraction/week2_extraction_seed_replication_20260302T180612Z.json` (`trait_pass`: sycophancy=true, evil=true; `overall_pass=true`).
- WS-F rollout-depth completion evidence logged:
  - rollout5 artifacts:
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json`
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260303T081318Z.json`
  - sensitivity comparison:
    - `results/stage1_extraction/week2_rollout_stability_sensitivity_20260303T121253Z.json`
- Status rationale:
  - `R1-F4` is now `resolved` via dual-scorecard governance evidence plus explicit integrated reassessment decision (`DECISIONS.md`, 2026-03-03T06:24:10-0600), removing criterion-drift ambiguity for this tranche.
  - `R1-F5`, `R2-C4`, and `R2-G3` are now `resolved` via explicit construct split + construct-aligned transfer artifact.
  - `R2-G6` was provisionally marked `resolved` and is later corrected to `partial` in the 2026-03-03 second-pass note; `R2-G7` remains `resolved`.
  - Coherence remains the dominant unresolved gate driver in both rollout3 and rollout5 lanes; this affects closeout policy but does not reopen the checklist items above.

## Progress Notes (2026-03-03T07:16:00-0600)

- Second-pass reviewer logs added verbatim:
  - `history/reviews/20260303-reviewer1-second-pass-verbatim.md`
  - `history/reviews/20260303-reviewer2-second-pass-verbatim.md`
- Structured reconciliation analysis artifact added:
  - `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T131331Z.json`
- Status correction:
  - `R2-G6` is downgraded from `resolved` -> `partial`.
    - rationale (`known`): current seed-replication run is deterministic (`prompt_last`, `response_temperature=0`, fixed extraction set), so it supports numerical determinism but does not by itself close stochastic/prompt-perturbation robustness intent.
- Scope clarification:
  - `R1-F1` remains `resolved` for its original criterion (false-positive Stage2 pass path is closed).
  - New second-pass structural blocker (claim-layer cross-SAE overlap impossibility under current policy) is tracked below as `SP-F1`.
- Additional second-pass open items are now tracked below (`SP-F1`..`SP-F9`) and mapped into a phased execution plan in the analysis artifact.

## Second-Pass Findings (2026-03-03)

| ID | Reviewer | Finding (verbatim short label) | Evidence anchor(s) | Status |
|---|---|---|---|---|
| SP-F1 | Reviewer 1 + 2 | Stage2 cross-SAE readiness structurally blocked at claim layer 12 | `week2_trait_scope_resolution_20260301T030203Z.json`, `week3_sae_reconstruction_audit_20260303T132222Z.json`, `week2_policy_resolution_packet_20260303T190245Z.json`, `configs/experiment.yaml` | resolved |
| SP-F2 | Reviewer 1 + 2 | Extraction A/B remains failed; prompt-vs-response regime confound not isolated by current hard gate | `week2_prelaunch_gap_checks_20260227T205237Z.json`, `week2_extraction_position_ablation_20260227T225251Z.json`, `week2_extraction_robustness_bootstrap_20260303T164652Z.json` | partial |
| SP-F3 | Reviewer 2 | Coherence failure appears structurally bound by absolute min-score gate | rollout5 artifacts (`20260303T082321Z`, `20260303T081318Z`), `week2_coherence_policy_diagnostic_20260303T132222Z.json`, `week2_policy_resolution_packet_20260303T190245Z.json` | resolved |
| SP-F4 | Reviewer 1 + 2 | Seed-replication evidence currently reflects determinism more than stochastic robustness | `week2_extraction_seed_replication_20260302T180612Z.json`, `week2_extraction_robustness_bootstrap_20260303T164652Z.json` | resolved |
| SP-F5 | Reviewer 1 + 2 | Capability evidence scope remains narrow for stronger claims | `week2_behavioral_validation_upgrade.py`, rollout5 `capability_proxy.n_questions=30`, `week2_capability_suite_spec_20260303T164726Z.json` | resolved |
| SP-F6 | Reviewer 1 | Rollout-sensitivity artifact has null `plus_mean`/`minus_mean` fields (schema mismatch) | `week2_rollout_stability_sensitivity_20260303T132222Z.json`, `scripts/week2_rollout_stability_sensitivity.py`, `tests/test_week2_rollout_stability_sensitivity.py` | resolved |
| SP-F7 | Reviewer 1 | Cross-trait bleed threshold sensitivity remains unresolved | `R1-F6` checklist row, `week2_cross_trait_bleed_sensitivity_20260303T164726Z.json` | resolved |
| SP-F8 | Reviewer 1 + 2 | Manual concordance remains low-power for final trust calibration | `week2_primary_manual_concordance_ratings_20260227T202822Z.json`, `week2_manual_concordance_policy_closure_20260303T164726Z.json`, `R2-C5` checklist row | resolved |
| SP-F9 | Reviewer 2 | Evil asymmetry differs by prompt distribution (held-out vs external transfer) | rollout5 + `week2_machiavellian_external_transfer_20260302T180239Z.json` | document as limitation |

## Progress Notes (2026-03-03T07:38:00-0600)

- P0 policy tranche implementation evidence:
  - coherence mode control landed in runner + config:
    - `scripts/week2_behavioral_validation_upgrade.py`
    - `configs/experiment.yaml` (`steering.coherence_gate_mode`)
  - coherence policy diagnostic artifact:
    - `results/stage1_extraction/week2_coherence_policy_diagnostic_20260303T132222Z.json`
  - explicit decision logged:
    - `DECISIONS.md` (`2026-03-03T07:35:10-0600`)
- Stage2 policy contradiction resolution evidence:
  - split-gate policy fields in config:
    - `configs/experiment.yaml` (`governance.week3_stage2_policy`)
  - updated Stage2 audit with split gates:
    - `results/stage2_decomposition/week3_sae_reconstruction_audit_20260303T132222Z.json`
  - explicit decision logged:
    - `DECISIONS.md` (`2026-03-03T07:35:40-0600`)
- Schema patch evidence:
  - rollout sensitivity comparator patched:
    - `scripts/week2_rollout_stability_sensitivity.py`
  - strict missing-key tests added:
    - `tests/test_week2_rollout_stability_sensitivity.py`
  - refreshed artifact without null plus/minus fields:
    - `results/stage1_extraction/week2_rollout_stability_sensitivity_20260303T132222Z.json`
- Reconciliation synthesis refresh:
  - `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T132329Z.json`

## Progress Notes (2026-03-03T10:48:00-0600)

- P1 extraction robustness closure evidence logged:
  - `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json` (`overall_pass=true`)
  - trait-level results:
    - sycophancy: bootstrap `p05=0.9988`, train-vs-heldout cosine `0.9957`
    - evil: bootstrap `p05=0.9991`, train-vs-heldout cosine `0.9965`
- P2 pending-item closure artifacts logged:
  - bleed threshold sensitivity:
    - `results/stage1_extraction/week2_cross_trait_bleed_sensitivity_20260303T164726Z.json`
  - capability-suite boundary spec:
    - `results/stage1_extraction/week2_capability_suite_spec_20260303T164726Z.json`
  - manual concordance scope closure:
    - `results/stage1_extraction/week2_manual_concordance_policy_closure_20260303T164726Z.json`
- Status rationale:
  - `R1-F6` set to `resolved` because threshold sensitivity is now explicit and artifact-backed (sycophancy prompt-last lane is borderline at `0.30` and passes from `0.35`).
  - `R2-C5` set to `resolved` via explicit policy closure (`manual_concordance_role=sanity_check_only`) and required upgrade condition (`>=15 examples/trait`) for stronger weight.
  - `R2-G8` set to `resolved` via capability-suite boundary artifact that freezes Week2 proxy-vs-broader-claim scope.
  - `SP-F2` remains `partial`: prompt-vs-response A/B mismatch persists, but content-robustness closure now passes.
  - `SP-F4` set to `resolved`: determinism-only seed replication is now complemented by bootstrap and heldout robustness evidence.

## Progress Notes (2026-03-03T13:03:00-0600)

- SP-F1/SP-F3 policy closure artifact logged:
  - `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`
- Status rationale:
  - `SP-F1` set to `resolved` via explicit split claim-scope policy:
    - decomposition-start at selected claim layer can proceed as single-source,
    - cross-source claims are restricted to overlap-capable sensitivity layers (`11,15`),
    - no cross-source claim is permitted on non-overlap selected claim layer (`12`).
  - `SP-F3` set to `resolved` via explicit dual-scorecard coherence policy:
    - hardening reliability remains `absolute_and_relative`,
    - proposal-compatibility interpretation uses `relative_only`,
    - both scorecards are required to be reported together.

## Progress Notes (2026-03-03T14:00:00-0600)

- External superseding recommendation logged verbatim:
  - `history/reviews/20260303-reviewer-superseding-recommendation-verbatim.md`
- Superseding governance decision logged:
  - `DECISIONS.md` (`2026-03-03T14:00:00-0600`)
- Status interpretation for phase transition:
  - `known`: no checklist rows remain `pending`.
  - `known`: remaining `partial` rows are now treated as explicit limitations/caveats, not Stage2-start blockers under proposal-compatibility scorecard.
  - `known`: `SP-F2` remains `partial` and is carried as a documented regime-mismatch limitation.
  - `known`: `SP-F9` remains `document_limitation`.

## End-of-Remediation Audit Protocol

1. For each ID above, set final status (`resolved`/`partial`/`unresolved`) and add artifact links.
2. If any item remains `pending`, remediation is not complete.
3. Before any reviewer-facing update memo, run a full pass against this checklist and include it as an appendix.
4. Before any replication/stress launch, ensure R1-F1/F2/F3/F4 and R2-C1/C2/C3/C6 are not `pending`.
