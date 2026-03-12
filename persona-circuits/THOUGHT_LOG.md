# THOUGHT LOG
Running log of insights, theories, surprising findings, adjacent curiosities, and follow-up research ideas.
Log freely — anything that could strengthen the paper, complicate interpretation, or open a new direction.
Format: ## [DATE] [CATEGORY] — [title]

---

## PENDING ACTIONS

Items derived from THOUGHT_LOG entries that require concrete changes before a specific phase or run.
Review this section before starting any new phase or writing any pre-run checkpoint.

- [ ] Add cross-persona selectivity control: when ablating Sherlock circuit, measure Watson behavior — should be unaffected. Required before: Phase C (Causal Validation / Week 6). See entry 2026-02-24 METHODOLOGY RISK.
- [ ] Add null-feature ablation baseline: identify features with matched activation magnitude but no persona semantics; ablate as negative control. Required before: Phase C. See entry 2026-02-24 METHODOLOGY RISK.
- [ ] Decompose Y into 3–4 orthogonal behavioral facets (lexical markers, domain knowledge, out-of-character refusal, response style) and test necessity/sufficiency for each separately. Required before: Phase B behavioral scoring design (Week 3). See entry 2026-02-24 METHODOLOGY RISK.
- [ ] Add one sentence to intro framing PSM as mechanizing Shanahan et al.'s simulator claim. Required before: paper writing (Week 9). See entry 2026-02-24 THEORY.
- [ ] Run larger-sample token-level reconstruction reliability check after root-cause probe (full-seq vs last-token divergence now known). Required before: Week 3 SAE decomposition interpretation. See entry 2026-02-25 FINDING (root-cause probe).
- [ ] Calibrate Week 2 judge reliability (rubric/prompt/parse robustness) before accepting final layer-alpha selections. Required before: Week 2 closeout. See entry 2026-02-25 FINDING.
- [ ] After primary terminalization, finalize the reframed `machiavellian_disposition` interpretation rubric (while keeping harmful-content transfer as a negative result) before Week 3 scope lock. Required before: Week 3 decomposition scope lock update. See decision 2026-02-25T11:50:12-0600 in DECISIONS.md.
- [ ] Run hallucination known-fact benchmark check (TruthfulQA-style) in upgraded Week 2 validation before closeout claim. Required before: Week 2 closeout. See entry 2026-02-25 METHODOLOGY GAP.
- [ ] Run a targeted hallucination extraction-free follow-up (alternate extraction position and/or exemplars) before locking Week 3 interpretation that hallucination is instruction-specific. Required before: Week 3 decomposition interpretation freeze. See entry 2026-02-25 FINDING.
- [ ] Before any new Week 2 launch command, verify whether active primary app IDs are still running and avoid relaunching duplicates. Required before: any additional Week 2 Modal launch. See entry 2026-02-25 HANDOFF RISK.
- [ ] Start narrative-arcs/tropes/memes extension only after core phases complete, using the formal blueprint at `history/20260225-post-core-extension-narrative-arcs-tropes-memes.md`. Required before: Post-core extension launch. See entry 2026-02-25 FUTURE-DIRECTION.
- [ ] Before freezing any future geometry-heavy interpretation for promoted trait lanes or Stage 5 refresh work, revisit Prieto et al. (2026) and run an optional geometry-only sidecar if clustered/shared feature structure is being used as evidence. Required before: next geometry-facing interpretation freeze after H3 closeout. See entry 2026-03-11 THEORY.
- [ ] Build the thin actual screening runner for the recommended `trait_lanes_v2` first tranche (`slice_a`) before widening to a third live slice or adding another prep-only sidecar. Required before: first real trait-lane screening launch. See entry 2026-03-11 FINDING (screening readiness).
- [ ] Compute `politeness` vs `sycophancy` overlap/distinctness before the next trait-lane deeper-validation launch. Required before: next `politeness` deeper-validation attempt. See entry 2026-03-12 REVIEW RECONCILIATION.
- [ ] Re-enable branch-local cross-trait bleed for at least `sycophancy` and `assistant_likeness` before the next trait-lane deeper-validation launch. Required before: next `politeness` deeper-validation attempt. See entry 2026-03-12 REVIEW RECONCILIATION.
- [ ] Freeze the response-phase persistence policy explicitly (metric investigation or preregistered relaxation) before the next trait-lane deeper-validation launch. Required before: next `politeness` deeper-validation attempt. See entry 2026-03-12 REVIEW RECONCILIATION.
- [ ] Add a branch null-lane control plan before freezing interpretation of the trait-lane branch. Required before: branch interpretation freeze. See entry 2026-03-12 REVIEW RECONCILIATION.
- [ ] Add prompt-sensitivity analysis for the lead branch lane before treating `politeness` ranking as stable. Required before: branch interpretation freeze. See entry 2026-03-12 REVIEW RECONCILIATION.
- [ ] Split extraction and upgraded validation into separate launches for the next trait-lane deeper-validation attempt. Required before: next `politeness` deeper-validation attempt. See entry 2026-03-12 REVIEW RECONCILIATION.

## RESOLVED ACTIONS

- [x] Create the lane registry + construct cards for the trait-lane expansion branch. Source: 2026-03-11 THEORY / ACTION. Resolved on 2026-03-11 via `configs/trait_lanes_v2.yaml`, `scripts/shared/trait_lane_registry.py`, and `history/construct_cards/*.md`.
- [x] Keep the active H3 core line isolated until `ap-mCOxAI9Xp7WCZoxpslD6Yi` terminalizes before any lane-expansion remote screening launch. Source: 2026-03-11 IMPLEMENTATION UPDATE. Resolved on 2026-03-11 when the bounded H3 tranche terminalized and was closed out via `week3_stage4_behavioral_sufficiency_claimgrade_trancheA_closeout_20260311T1919Z.json`.
- [x] Execute remediation workstreams WS-A through WS-F before any superseding Week 2 launch decision. Source: 2026-02-27 governance action. Resolved on 2026-03-03 with reconciliation artifacts and governance sync; superseding decision still blocked on remaining high-severity open items.
- [x] Complete `history/20260227-reviewer-reconciliation-checklist-v1.md` with artifact-backed status for every reviewer ID before reviewer response summary. Source: 2026-02-27 governance action. Resolved on 2026-03-03 after P1/P2 artifact updates (no checklist rows remain pending).
- [x] Define capability-suite boundary artifact (Week2 MMLU proxy vs broader capability-preservation claims). Source: 2026-03-03 METHODOLOGY UPDATE. Resolved on 2026-03-03 via `week2_capability_suite_spec_20260303T164726Z.json`.
- [x] Resolve manual concordance scope decision (expand sample vs explicitly de-scope to sanity-check role). Source: 2026-03-03 GOVERNANCE. Resolved on 2026-03-03 via `week2_manual_concordance_policy_closure_20260303T164726Z.json` (sanity-check-only weighting).
- [x] Run rollout-stability sensitivity check (confirm rollouts 3 vs 5) on primary-tier selected combos. Source: 2026-02-25 METHODOLOGY UPDATE. Resolved on 2026-03-03 via `week2_rollout_stability_sensitivity_20260303T132222Z.json`.
- [x] Run construct-aligned external transfer for `machiavellian_disposition` lane before superseding Week2 decision on evil-lane viability. Source: 2026-02-27 governance action. Resolved on 2026-03-02 via `week2_machiavellian_external_transfer_20260302T180239Z.json`.
- [x] Decide Stage2 cross-SAE strategy for claim layer 12 before Stage2 decomposition claims. Source: 2026-02-27 governance action. Resolved on 2026-03-03 via `week2_policy_resolution_packet_20260303T190245Z.json` (single-source decomposition at selected claim layer; cross-source claims restricted to overlap-capable sensitivity layers).
- [x] Freeze/hash prompt inputs in validation artifacts — integrated into upgraded runner + explicit plan artifact with held-out hashes. Source: 2026-02-24 METHODOLOGY RISK. Resolved on 2026-02-25 during upgrade pipeline build.
- [x] Add judge API-throttle resilience (RPM throttle + retry/backoff + jitter + retryable error handling) before large parallel launch. Source: 2026-02-25 METHODOLOGY DESIGN. Resolved on 2026-02-25 in upgraded Week 2 runner/planner.
- [x] Add coherence/directionality/random-control-strength gates to Week 2 upgraded validation. Source: 2026-02-25 LITERATURE SECOND PASS. Resolved on 2026-02-25 before launch.
- [x] Tighten Week 2 acceptance gates to include secondary parse pass, non-trait control-test threshold, specificity threshold, and strict capability-availability behavior by default. Source: 2026-02-25 METHODOLOGY GAP. Resolved on 2026-02-25 in upgraded runner/planner.
- [x] Implement hallucination known-fact (TruthfulQA-style) check in upgraded Week 2 runner and planner. Source: 2026-02-25 METHODOLOGY GAP. Resolved on 2026-02-25; execution evidence still pending.
- [x] Complete rerun smoke validation after `top_k=None` patch and verify `steering_norm_diagnostics.ratio_stats` fields in report artifact. Source: 2026-02-25 METHODOLOGY/IMPLEMENTATION. Resolved on 2026-02-25 in run `i1pg2y8c` (`week2_behavioral_validation_upgrade_sycophancy_20260225T131007Z.json`).
- [x] Choose launch tranche and concurrency cap for the upgraded Week 2 matrix (primary vs replication vs stress) before execution. Source: 2026-02-25 METHODOLOGY DESIGN. Resolved on 2026-02-25 by generating a primary-only launch plan (`week2_upgrade_parallel_plan_20260225T141045Z.json`) and deferring replication/stress until primary review.
- [x] Re-run SAE reconstruction sanity using stage-specific hooks before trusting decomposition claims. Source: 2026-02-24 INFRA OBSERVATION. Resolved on 2026-02-25 via `week3_sae_reconstruction_investigation_20260225T164322Z.json`; follow-up preprocessing controls still pending.
- [x] Make a formal keep/replace decision for the `evil` trait based on evidence. Source: 2026-02-25 FINDING (evil trait high-risk audit). Initially resolved on 2026-02-25 by replacement (`2026-02-25T11:08:23-0600`), then scope-superseded by reframed reinstatement under `machiavellian_disposition` (`2026-02-25T11:50:12-0600`) while preserving harmful-content negative findings.
- [x] Backfill cosine-margin diagnostics with non-null values across all traits/layers. Source: external review gap (cosine-margin null). Resolved on 2026-02-25 via extraction rerun `u6od5uxx` and artifact `week2_vector_diagnostics_20260225T170928Z.json`.
- [x] Run extraction-free persona validation (few-shot trait demonstrations without explicit system persona instruction) and compare steering direction/effect to system-prompt extraction. Source: 2026-02-25 METHODOLOGY RISK. Resolved on 2026-02-25 via Modal app `ap-ueBHf5QMX2Vb45ROBxySK5` and artifact `week2_extraction_free_activation_eval_20260225T173752Z.json` (`overall_pass=false`; remediation action opened).
- [x] Recalibrate extraction-free gate policy to reflect cross-induction overlap strength instead of parity with system-prompt instruction strength. Source: 2026-02-25 FINDING (trait gradient in extraction-free results). Resolved on 2026-02-25 via script updates (`week2_extraction_free_activation_eval*.py`) and reanalysis artifact `week2_extraction_free_reanalysis_20260225T174958Z.json`.
- [x] Make Week 2 alpha sweep config-authoritative (remove hardcoded default mismatch). Source: reviewer finding (alpha grid source-of-truth drift). Resolved on 2026-02-25 via `week2_behavioral_validation_upgrade.py` + tests.
- [x] Convert Stage2 reconstruction audit from placeholder pending checks to computed gates from latest probe artifacts. Source: reviewer finding (audit gate not instrumented). Resolved on 2026-02-25 via `week3_sae_reconstruction_audit_20260225T180446Z.json`.
- [x] Add Stage 3/4 local dry-run pipeline scaffold + shared concentration/effect-size primitives. Source: reviewer finding (missing execution path and reporting primitives). Resolved on 2026-02-25 via `week3_stage34_pipeline_scaffold_20260225T180446Z.json` and `scripts/circuit_metrics.py`.
- [x] Resolve Stage2 cross-source overlap precondition for Week 3 claim gating. Source: 2026-02-25 FINDING. Resolved on 2026-02-25 via config update (`sae.cross_check.layers=[11,15,19,23]`) and computed-audit artifact `week3_sae_reconstruction_audit_20260225T181955Z.json`.
- [x] After all three primaries were terminal, run deterministic closeout ingestion with explicit trait artifact map before manual edits. Source: decision 2026-02-25T12:20:49-0600 in `DECISIONS.md`. Resolved on 2026-02-27 via `week2_primary_postrun_ingestion_20260227T202336Z.json`.
- [x] Run Week 2 external benchmark transfer check for selected layer/alpha per trait and extraction-method robustness A/B before closeout lock. Source: 2026-02-25 LITERATURE SECOND PASS. Resolved on 2026-02-27 via `week2_prelaunch_gap_checks_20260227T205237Z.json`.
- [x] Perform manual 5-example judge concordance spot-check after upgraded primary runs. Source: 2026-02-25 LITERATURE SECOND PASS. Resolved on 2026-02-27 via `week2_primary_manual_concordance_ratings_20260227T202822Z.json`.
- [x] Define and log a minimal Week 2 remediation tranche before any new replication/stress launch, and lock reviewer coverage tracking. Source: 2026-02-27 closeout NO-GO governance action. Resolved on 2026-02-27 via `history/20260227-week2-remediation-master-plan-v1.md` and `history/20260227-reviewer-reconciliation-checklist-v1.md`.
- [x] Complete WS-B expanded extraction-position run (50 pairs/trait) after small-run instrumentation fix and log artifact-backed outcomes. Source: 2026-02-27 FINDING (WS-B small-run). Resolved on 2026-02-27 via app `ap-jE51jRViY2RdepUgmT3Fe4` and artifact `week2_extraction_position_ablation_20260227T225251Z.json`.
- [x] Implement WS-C constrained confirm-combo selection policy (smallest feasible alpha default) with config authority and tests. Source: reviewer alpha-selection findings. Resolved on 2026-02-27 via `scripts/week2_behavioral_validation_upgrade.py`, `configs/experiment.yaml`, and `tests/test_week2_validation_utils.py` (`Ran 74 tests ... OK`).
- [x] Lock extraction-method policy for WS-C reruns (prompt-last primary to isolate alpha effects; response-mean as deferred sensitivity lane). Source: WS-B expanded diagnostics. Resolved on 2026-02-27 via decision entry `DECISIONS.md` (2026-02-27T16:59:57-0600).
- [x] Run WS-C lower-alpha targeted reruns (sycophancy + evil) and generate constrained-selection tradeoff summary artifact. Source: WS-C remediation plan. Resolved on 2026-02-28 via `week2_behavioral_validation_upgrade_{sycophancy,evil}_20260228*.json` and `week2_alpha_constrained_selection_20260228T131217Z.json`.
- [x] Run response-mean extraction sensitivity lane after WS-C targeted results to test whether extraction-method switch improves reliability outcomes. Source: WS-B/WS-C remediation plan dependency. Resolved on 2026-02-28 via `week2_vector_extraction_summary_20260228T135004Z.json`, `week2_behavioral_validation_upgrade_{sycophancy,evil}_20260301*.json`, and synthesis artifact `week2_response_mean_sensitivity_20260301T025554Z.json`.
- [x] Formalize hallucination status and evil lane split before WS-E gate-integrity rerun. Source: WS-D remediation scope. Resolved on 2026-03-01 via `week2_trait_scope_resolution_20260301T030203Z.json`.
- [x] Freeze coherence gate policy (absolute+relative vs relative-only) with explicit mode control + diagnostic evidence before superseding Week2 decision. Source: 2026-03-03 METHODOLOGY UPDATE. Resolved on 2026-03-03 via `scripts/week2_behavioral_validation_upgrade.py`, `configs/experiment.yaml`, decision `2026-03-03T07:35:10-0600`, and artifact `week2_coherence_policy_diagnostic_20260303T132222Z.json`.
- [x] Patch rollout-stability sensitivity schema mismatch (`plus_mean`/`minus_mean` null fields) and add failing-key unit test. Source: 2026-03-03 IMPLEMENTATION RISK. Resolved on 2026-03-03 via `scripts/week2_rollout_stability_sensitivity.py`, `tests/test_week2_rollout_stability_sensitivity.py`, and artifact `week2_rollout_stability_sensitivity_20260303T132222Z.json`.
- [x] Run full-depth Stage4 evil necessity confirmation on alpha3 source (`n_random>=20`) after calibration coverage-lift evidence. Source: 2026-03-09 FINDING. Resolved on 2026-03-10 via `week3_stage4_behavioral_ablation_20260310T001903Z.json` (coverage lift confirmed; strict threshold bundle still unmet).
- [x] Compare Stage4 prompt-tranche sensitivity artifact against full-depth alpha3 reference and assess tranche-stability of threshold failures. Source: 2026-03-10 FINDING. Resolved on 2026-03-10 via `week3_stage4_tranche_comparison_20260310T141458Z.json` (coverage stable; gate failures unchanged; selectivity strength tranche-sensitive).
- [x] Finalize H2 Stage4 policy decision packet using threshold-binding + tranche-comparison artifacts. Source: 2026-03-10 FINDING. Resolved on 2026-03-10 via `week3_stage4_policy_decision_packet_20260310T142000Z.json`.
- [x] Finalize Stage5 `S5-G2`/`S5-G4` checklist closure policy after BH-hook execution (`n_rejected=0` at `alpha=0.01`). Source: 2026-03-10 FINDING. Resolved on 2026-03-10 via `week3_stage5_policy_decision_packet_20260310T200937Z.json` with exploratory-null lock recommendation.
- [x] Log explicit H2 policy lock decision and Stage4 synthesis memo after policy packet completion. Source: 2026-03-10 FINDING. Resolved on 2026-03-10 via `DECISIONS.md` entry `2026-03-10T09:24:10-0500` and `history/20260310-stage4-h2-synthesis-memo-v1.md`.

---

## 2026-02-27 [FINDING] — WS-B Small-Run Confirms Position Sensitivity Persists After Instrumentation Fix

**Type:** finding | action  
**Phase:** Week 2 remediation / WS-B  
**Relevance:** Reviewer concerns on extraction A/B robustness and method dependence

- `known`: First WS-B run failed due remote host-path dependency (`/prompts/*.jsonl` unavailable in Modal runtime); payload patch was applied and rerun succeeded.

## [2026-03-12] REVIEW RECONCILIATION — trait-lane branch review identifies distinctness and persistence as the real blockers
**Type:** action
**Phase:** Trait-lane branch / deeper-validation transition
**Relevance:** Determines whether `politeness` is a real new persona-style lane or just a tractable style/tone lead that overlaps with `sycophancy`

- `known`: the current branch evidence is strong enough to nominate `politeness` as the tractability-first lead lane, but not strong enough to establish that it is distinct from `sycophancy` or that failed response-phase persistence can be safely ignored.
- `known`: `lying` is weaker than its prior packet label implied; its external-smoke evidence now looks more like construct invalidity than like a clean conditional follow-on.
- `known`: `honesty` remains unresolved because RLHF asymmetry is a plausible explanation for its one-sided follow-on behavior.
- `inferred`: the branch should pause new deeper-validation launches until overlap/distinctness, cross-trait bleed, persistence policy, and split-launch execution are repaired.

## [2026-03-12] FINDING — politeness is low-overlap with core sycophancy but high-overlap with assistant-likeness
**Type:** finding
**Phase:** Trait-lane branch / distinctness remediation
**Relevance:** Changes the main confound from "rotated sycophancy" to "assistant-style tone lane"

- `known`: the new overlap diagnostic shows `politeness` is not strongly aligned with the core `sycophancy` vector under the requested cosine check.
- `known`: selected-pair overlap (`sycophancy L12` vs `politeness L15`) is `0.065`, and the max abs overlap anywhere in the `11..16 x 11..16` grid is only `0.181`.
- `known`: the same branch summary still shows `politeness` is strongly aligned with `assistant_likeness` (`0.432 -> 0.628` same-layer cosine).
- `inferred`: the next decisive question is no longer "is politeness just sycophancy?" but "is politeness mostly assistant-style tone transfer?".
- `known`: Artifact `results/stage1_extraction/week2_extraction_position_ablation_20260227T221817Z.json` reports `prompt_last_vs_response_mean < 0.7` for every trait/layer (11-16).
- `observed`: Mean prompt-vs-response cosine in this small run: sycophancy `0.490`, evil `0.483`, hallucination `0.343`.
- `inferred`: extraction-position sensitivity is not a single-layer bug; it appears global under current protocol, with stronger overlap for sycophancy/evil than hallucination.
- `unknown`: whether expanded sample size or response-token-primary extraction can clear robustness thresholds without harming behavioral validity.

Action: run WS-B expanded pair-count diagnostic and then lock an explicit extraction-method policy (response-primary vs prompt-primary+control) before WS-C reruns.

## 2026-02-27 [FINDING] — WS-B Expanded Run Suggests Prompt-vs-Response Phase Split for Sycophancy/Evil

**Type:** finding | action  
**Phase:** Week 2 remediation / WS-B  
**Relevance:** extraction-method policy lock before WS-C constrained-alpha reruns

- `known`: Expanded artifact `results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json` reproduces sub-threshold prompt-last vs response-mean agreement on all traits/layers (`<0.7`).
- `observed`: response-mean vs response-last agreement is high for sycophancy (`~0.75`) and evil (`~0.74`), but low for hallucination (`~0.33`).
- `inferred`: For sycophancy/evil, method instability likely concentrates in prompt-vs-response phase choice, not in response statistic choice (mean vs last). Hallucination appears unstable across both choices.
- `unknown`: Whether switching to response-token extraction as primary improves downstream behavioral reliability gates without reducing steerability.

Action: log explicit extraction-method policy decision and run WS-C constrained-alpha with that policy frozen.

## 2026-02-27 [METHODOLOGY UPDATE] — Constrained Alpha Selection Is Now Implemented but Not Yet Empirically Validated

**Type:** finding | action  
**Phase:** Week 2 remediation / WS-C  
**Relevance:** reviewer oversteer concern and alpha-selection objective alignment

- `known`: Week2 upgraded runner now supports config-driven combo selection policy and defaults to `smallest_feasible_alpha` among confirm combos that meet directional feasibility + `min_bidirectional_effect`.
- `known`: fallback behavior remains deterministic (`max_bidirectional_effect`) when no combo meets feasibility threshold.
- `known`: tests cover default policy, override policy, and fallback behavior (`tests/test_week2_validation_utils.py`).
- `unknown`: whether this change is sufficient to recover coherence/capability gates on actual reruns without sacrificing steering effect.

Action: run lower-alpha targeted reruns and generate a tradeoff artifact before claiming oversteer remediation.

## 2026-02-28 [FINDING] — Lower-Alpha Constrained Selection Reduces Effect but Does Not Clear Reliability Gates

**Type:** finding | action  
**Phase:** Week 2 remediation / WS-C  
**Relevance:** reviewer oversteer hypothesis and gate-policy interpretation

- `known`: Targeted constrained reruns selected `alpha=2.0` for both sycophancy and evil at layer 12.
- `known`: Both runs remain `overall_pass=false` under current hardening gates.
  - sycophancy fails coherence + cross-trait bleed.
  - evil fails coherence only.
- `known`: Bidirectional effect dropped materially versus prior alpha=3.0 primary runs for both traits.

## 2026-03-11 [THEORY] — Trait-Class Mismatch May Be One of the Project’s Real Bottlenecks
**Type:** theory | action  
**Phase:** Phase 4, with implications for a new Stage-1/Week-2 screening branch  
**Relevance:** determines whether future effort should go into stronger trait selection versus only deeper causal validation on the current set

- `known`: the proposal selected `sycophancy`, `evil/toxicity`, and `hallucination` largely for comparability to Chen rather than because they were proven to be the best mechanistic targets.
- `known`: project evidence now separates these sharply: `sycophancy` is still one of the cleanest lanes, `evil` improved only after reframing to `machiavellian_disposition`, and `hallucination` is currently a negative finding.
- `known`: local paper summaries plus a March 11, 2026 refresh support five credible alternative families:
  - `honesty / lying / deception`
  - `assistant_likeness`
  - `politeness / optimism / apathy / humor`
  - `agreeableness`
  - `refusal / harmfulness`
- `inferred`: the problem is probably not “all current traits are wrong.” It is more likely that the current set mixes social-behavior traits with epistemic/calibration and safety-policy behaviors under one shared persona hypothesis.
- `inferred`: the most plausible trait-level improvement is to keep `sycophancy` as an anchor, keep `machiavellian_disposition` as a reframed social-disposition lane, and treat `hallucination` as the weak target most worth replacing or demoting.
- `inferred`: this still does not eliminate other likely bottlenecks (response-phase dependence, imperfect reconstruction, distributed mechanisms), so new lanes should begin as a screening branch rather than a full pipeline reset.

Action: create a registry-backed, sidecar-style lane-expansion branch that screens all five candidate families at Stage-1/Week-2 depth before promoting any into deeper validation.
- `inferred`: lowering alpha alone is insufficient under current gate bundle; coherence failure is dominated by absolute minimum coherence threshold rather than steered-vs-baseline drop.
- `unknown`: whether response-mean extraction (or gate recalibration) can recover reliability without reintroducing oversteer artifacts.

Action: execute response-mean extraction sensitivity lane and then revisit gate-policy interpretation with dual-scorecard framing.

## 2026-03-03 [METHODOLOGY UPDATE] — Second-Pass Review Converges on Governance/Policy Bottlenecks, Not New Extraction Work

**Type:** finding | action  
**Phase:** Week 2 remediation reconciliation  
**Relevance:** determines whether additional reruns are justified before Stage2 decomposition work

- `known`: Stage2 claim-layer audit remains blocked at layer 12 because cross-check SAE overlap is empty (`overlap_layers=[]`) and token gate remains just below threshold for one seed (`min cos=0.7047`, `min EV=0.4765`).
- `known`: rollout5 coherence artifacts show baseline means are already below the absolute threshold (`syc=69.595`, `evil=58.74`, threshold `75`), while max-drop gate passes.
- `known`: seed-replication artifact uses fixed extraction inputs with `prompt_last` and `temperature=0`; pairwise cosines are identically `1.0`.
- `inferred`: immediate value is in policy freezes + targeted robustness diagnostics, not launching broader rerun matrices.
- `unknown`: whether final Week2 decision will keep absolute coherence threshold, move to relative-only, or adopt dual-scorecard interpretation.

Action: execute phased reconciliation plan (P0 policy decisions -> P1 robustness/reporting closure -> P2 pending-item closure) before any superseding launch decision.

## 2026-02-25 [FINDING] — Extraction-Free Alignment Gates Fail Across Traits

**Type:** finding | action  
**Phase:** Week 2 / Stage 1 robustness-to-conditioning check  
**Relevance:** Week 3 interpretation of "persona selection" vs "instruction following"

- `known`: Extraction-free activation evaluation completed (`results/stage1_extraction/week2_extraction_free_activation_eval_20260225T173752Z.json`, app `ap-ueBHf5QMX2Vb45ROBxySK5`) with `overall_pass=false`.
- `known`: All traits fail the `mean_cosine` gate; all traits also fail `set_std_ratio`.
- `known`: Hallucination additionally fails `positive_fraction` and `projection_delta`, with near-zero/negative mean cosine.
- `inferred`: Current few-shot conditioning setup does not recover directions sufficiently aligned with system-prompt vectors, so it does not currently support a strong persona-selection claim independent of explicit persona instructions.
- `unknown`: Whether this failure is primarily due to methodological sensitivity (last-token extraction, exemplar set variance, layer mismatch) or a true lack of shared direction between extraction-free and system-prompt regimes.

Action: diagnose failure contributors and define a remediation rerun (or explicitly downgrade interpretation claims) before Week 3 decomposition narrative lock.

## 2026-02-25 [FINDING] — Extraction-Free Overlap Is Trait-Gradient, Not Uniform Failure

**Type:** finding | action  
**Phase:** Week 2 / Stage 1 robustness-to-conditioning check  
**Relevance:** Week 3 trait framing and decomposition target selection

- `known`: Reanalysis artifact `results/stage1_extraction/week2_extraction_free_reanalysis_20260225T174958Z.json` under overlap-gradient policy yields:
  - sycophancy: weak positive overlap (`mean_cos=0.129`, `positive=0.96`, sign-test p `~2.27e-12`),
  - evil: moderate positive overlap (`mean_cos=0.223`, `positive=1.0`, sign-test p `~1.78e-15`),
  - hallucination: null overlap (`mean_cos=-0.006`, `positive=0.44`, sign-test p `~0.48`).
- `known`: Between-set mean divergence is low/moderate for sycophancy and evil (`set_mean_cv~0.27`, `~0.23`) and high for hallucination (`~3.28` due near-zero global mean).
- `inferred`: Sycophancy and machiavellian-disposition likely share cross-induction behavioral directions; hallucination appears pathway-specific under current protocol.
- `unknown`: Whether hallucination null is robust to extraction-position changes or alternate exemplar designs.

Action: maintain trait-specific Week 3 interpretation and run a targeted hallucination follow-up rather than treating all traits as a single extraction-free pass/fail outcome.

## 2026-02-25 [FINDING] — Stage2 Readiness Is Blocked by Cross-Source Layer Overlap, Not Token-Level Reconstruction

**Type:** finding | action  
**Phase:** Week 2 pre-primary hardening / Week 3 gate prep  
**Relevance:** Prevents over-claiming cross-SAE agreement when preconditions are unmet

- `known`: Computed audit artifact `results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T180446Z.json` reports:
  - token-level reconstruction gate: pass,
  - hook-integrity gate: pass,
  - cross-source overlap precondition: fail (`overlap_crosscheck_vs_steering_layers=[]`),
  - overall Stage2 readiness: fail.
- `inferred`: Immediate Stage2 blocker is now structural overlap availability, not the original token-level reconstruction viability concern.
- `unknown`: Whether overlap should be recovered by adding another SAE source/layer policy vs downgrading cross-SAE agreement claims for this tranche.

Action: resolve cross-source overlap strategy before freezing Week 3 decomposition claims.

## 2026-02-25 [FINDING] — Stage2 Overlap Blocker Cleared; Remaining Blockers Are Evidence-Arrival Tasks

**Type:** finding | action  
**Phase:** Week 2 pre-primary hardening / Week 3 gate prep  
**Relevance:** Confirms implementation readiness and isolates what must wait for terminal primary artifacts

- `known`: Updated config now includes overlap-capable andyrdt layers (`[11,15,19,23]`), and latest computed audit passes required readiness checks (`results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T181955Z.json`).
- `known`: Closeout automation script was added (`scripts/week2_primary_postrun_ingest.py`) and preflighted while primaries remain active (`week2_primary_postrun_ingestion_20260225T182017Z.json`).
- `inferred`: Before primaries finish, the highest-value remaining work is monitoring and preparing deterministic closeout execution, not additional scaffolding.
- `unknown`: Whether final trait-level §6.2.3 gate outcomes will pass once full primary artifacts land.

Action: run `week2_primary_postrun_ingest.py --apply` immediately after all three primary artifacts exist, then execute manual concordance + gap-check closeout in that order.

---

## 2026-02-24 [METHODOLOGY RISK] — The Selectivity Gap in Necessity/Sufficiency Testing

**Type:** action
**Source:** Twitter/X critique of standard MechInterp practice

**The core issue:**
Standard MechInterp evidence is:
- Necessity: ablate X → Y vanishes
- Sufficiency: insert X → Y appears

But this misses **selectivity**: does X affect other stuff? Is Y just downstream of that other stuff?

MMLU/perplexity checks don't catch this — they're too coarse and too general.

**Three specific failure modes this creates for us:**

1. **Non-selective ablation:** We ablate "Sherlock persona features" and persona-consistent behavior vanishes. But did we *selectively* remove persona representation, or did we degrade general character-maintenance ability? If ablating any coherent-character features kills Sherlock behavior, we haven't found a Sherlock circuit — we've found a general coherence circuit.

2. **Y definition mismatch:** "Persona-consistent behavior" bundles many facets — lexical choices (deductive language, "elementary"), domain knowledge (Baker Street, Watson), refusal of out-of-character requests. The subset captured by our necessity test may not be the same subset captured by our sufficiency test. If we're not testing the same Y in both directions, the evidence doesn't compose.

3. **Non-unique necessity:** We need to confirm that ablating some *other* X' (a non-persona feature of similar activation magnitude) does NOT also make Y vanish. If it does, X isn't specially necessary — it's just any disruption to that representation subspace.

**What this means for our experimental design:**

We should add selectivity controls to Phase C ablation:

a) **Cross-persona selectivity:** When we ablate the Sherlock circuit, does *Watson* behavior also degrade? It should NOT if the circuit is truly persona-specific. Selective degradation of Sherlock-only behavior is the gold standard.

b) **Null-feature ablation baseline:** Identify features with similar activation magnitudes to our target features but no persona semantic content (e.g., syntax/grammar features). Ablate those. If persona behavior degrades similarly, our effect is non-specific.

c) **Multi-facet Y decomposition:** Define persona-consistency as 3–4 orthogonal behavioral facets and measure necessity/sufficiency for *each* separately. Show the circuit is necessary/sufficient for the same facets in both directions.

d) **Perplexity alternative:** Instead of MMLU, measure behavior on a *different* persona prompt. If Sherlock circuit ablation also kills our model's ability to do Watson, that's leakage.

**Relationship to existing safeguards:**
- Our Li & Janson (2024) resample ablation partially addresses the coherence collapse failure mode (§4 of MECH_INTERP_GUIDANCE.md) but doesn't address selectivity
- Our necessity threshold ≥80% and sufficiency ≥60% are blind to whether we're measuring the *right* Y

**Paper implication:**
If we find a Sherlock circuit, the strongest paper claim would be:
> "Ablating these features selectively disrupts Sherlock-consistent behavior while leaving Watson-consistent behavior intact, establishing that the circuit is persona-specific rather than a general character-coherence mechanism."

This is a stronger and more defensible claim than "ablating X makes Sherlock behavior vanish."

**Open question:**
Can we even find a circuit that's persona-specific at this granularity, or does the PSM predict that all persona-consistent behavior routes through a shared "character simulator" substrate? If the latter, selectivity will be structurally impossible — which would itself be an interesting finding.

---

## 2026-02-24 [THEORY] — Shanahan et al. (2023): LLMs as Non-Deterministic Simulators

**Type:** theory + action (intro framing)
**Source:** Shanahan, McDonell, Reynolds, "Role play with large language models," Nature 2023

**Core claim:** An LLM is best understood not as a single agent with beliefs/goals, but as "a non-deterministic simulator capable of role-playing an infinity of characters." The assistant persona is just one character in this infinite space.

**Why this matters for our experiment:**
- Directly foundational for PSM: Marks et al. (2026) inherits and mechanizes this framing
- Our experiment is asking *where* in the network the "character selection" happens and how it's encoded
- If Shanahan's framing is correct, there should be mechanistically identifiable "character context" representations that gate which character is being simulated
- Our persona vectors and SAE feature analysis are, in effect, testing the mechanistic substrate of Shanahan's "simulator" hypothesis

**Interesting tension with PSM:**
Shanahan et al. argue the model is simultaneously multiple characters in superposition until "collapsed" by context. PSM adds a specific claim: that collapse happens via a discrete persona-selection module with identifiable geometric structure. If we find clear circuit evidence, we're advancing PSM. If the representation is diffuse/entangled, it's more consistent with pure Shanahan.

**Follow-up question for the paper:**
Worth a sentence in the intro: "The character-simulator framing (Shanahan et al., 2023) predicts that LLMs maintain latent representations of multiple simultaneous characters. The Persona Selection Model (Marks et al., 2026) makes this concrete by proposing a specific geometric structure for character selection. Our circuit analysis tests whether this structure is mechanistically grounded."

---

## 2026-02-24 [INFRA OBSERVATION] — Week 1 SAE Reconstruction Sanity Is Lower Than Expected

**Type:** action  
**Phase:** Week 1 / Infrastructure  
**Relevance:** Stage 2 decomposition reliability and interpretation validity

- `known`: During infrastructure validation, sampled encode→decode cosine values were low (`Llama layer16: 0.1278`, `Gemma layer12: 0.4526`) using straightforward residual-cache activations.
- `unknown`: Whether this is a real SAE quality issue vs a hook/preprocessing mismatch in the quick Week 1 sanity script.
- `inferred`: Stage 2 claims would be fragile if we treat these as true reconstruction metrics without re-validating with stage-appropriate hooks and expected activation normalization.

Action: before Week 3 interpretation, run the full reconstruction protocol with verified hooks and confirm >0.9 on controlled examples (or explicitly document why threshold differs for this setup).

## 2026-02-24 [FINDING] — Automated Prompt Audits Can Miss Obvious Label Contamination

**Type:** finding  
**Phase:** Week 1 / Infrastructure -> Week 2 transition  
**Relevance:** Stage 1 extraction validity depends directly on prompt-label cleanliness

- `known`: A strict regex-based audit reported pass, but manual random sampling still found an `evil` prompt asking for coercive tactics.
- `known`: After moving generation+audit to shared rule definitions and broadening coercive/instructional detection, regenerated prompts passed both automated audit and manual spot checks.
- `inferred`: For Stage 1 data quality, deterministic checks alone are insufficient; manual sampling remains necessary to catch natural-language edge cases.

## 2026-02-24 [METHODOLOGY RISK] — Mutable Prompt Files Can Break Run Traceability Mid-Execution

**Type:** action  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Evidence status for layer/alpha selection depends on reproducible run inputs

- `known`: A Week 2 behavioral validation run was active while held-out prompt files were regenerated to restore full audit coverage.
- `known`: The in-flight run had already loaded an earlier in-memory prompt set, so continuing would produce results that no longer mapped 1:1 to on-disk artifacts.
- `inferred`: Any long run that consumes mutable local prompt files is vulnerable to silent input drift unless the exact input set is frozen and hashed before launch.

Action: before each long validation run, produce a prompt manifest with hashes/counts and avoid prompt-file mutation until run completion; if mutation occurs, invalidate and rerun.

## 2026-02-25 [FINDING] — Completed Frozen Behavioral Run Still Fails Judge Reliability Gates

**Type:** action  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Final layer/alpha selection validity

- `known`: Run `8b3fp37q` completed with frozen prompts and traceable hashes; report artifact exists.
- `known`: Cross-rater kappa (Sonnet vs Opus bins) was below 0.6 for all traits (sycophancy 0.5607, evil 0.0, hallucination 0.4266).
- `known`: Hallucination exact-50 rate was 0.2743 (>0.2 fallback-risk threshold), indicating parse/format reliability risk.
- `inferred`: The selected layer/alpha combinations from this run are provisional; accepting them as validated would overstate confidence.

Action: run a judge calibration pass (manual concordance + prompt-template/parse tightening) and rerun behavioral validation before locking Week 2 optimal settings.

## 2026-02-25 [METHODOLOGY DESIGN] — Judge Reliability Failure Was Structural, Not Just Noise
**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Final layer/alpha validity gate

- `known`: In the prior accepted-input run (`8b3fp37q`), hallucination raw judge outputs were often truncated narrative text with no parseable number, producing fallback-like behavior.
- `known`: Current Week 2 acceptance criteria depended on judge outputs for all steering metrics; parse fragility therefore directly contaminates selection.
- `inferred`: Judge parsing must be promoted from a soft diagnostic to a hard gate (explicit parse-fail rate threshold), or layer/alpha ranking can be an artifact of parser behavior.

Design response implemented:
- strict JSON-first judge prompt
- parse-failure accounting per model
- explicit gate (`parse_fail_rate <= 0.05`) before acceptance
- cross-rater calibration retained as separate reliability dimension (kappa + pairwise sign agreement)

## 2026-02-25 [METHODOLOGY DESIGN] — Split Sweep and Confirm Sets to Reduce Selection Bias
**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Credible optimal layer/alpha claims

- `known`: Previous Week 2 script selected best layer/alpha on the same held-out pool used to report final effects.
- `inferred`: This creates optimistic selection bias even without prompt leakage.
- `known`: Upgraded runner now uses deterministic held-out split (`sweep` for ranking, `confirm` for final selection/effect reporting) and evaluates top-k sweep candidates on confirm.

Interpretation:
- `inferred`: This does not eliminate all bias, but materially improves evidence quality versus single-pool selection.

## 2026-02-25 [METHODOLOGY DESIGN] — Cross-Trait Bleed Is High-Signal at This Stage
**Type:** action
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Deciding whether to trust trait-specificity before Week 3 decomposition

- `known`: Local paper review (especially `bhandari2026_trait_interference.md`) emphasizes that target-trait steering can induce substantial off-target shifts, and geometric decorrelation alone does not guarantee behavioral independence.
- `inferred`: Cross-trait bleed matrix should be measured during Week 2 selection, not deferred to later phases, because a "good" target effect with high bleed changes interpretation of "optimal" settings.
- `known`: Upgraded runner now scores selected-combo outputs with all three rubrics and logs bleed matrix.

Action: before launching replication/stress tiers, inspect primary-tier bleed matrices and decide if alpha caps need tightening trait-by-trait.

## 2026-02-25 [METHODOLOGY DESIGN] — Full Parallel Matrix Is Informative but Budget-Heavy
**Type:** action
**Phase:** Week 2 / Upgrade execution planning
**Relevance:** Launch sequencing and risk control

- `known`: Generated plan artifact (`week2_upgrade_parallel_plan_20260225T113925Z.json`) includes 15 jobs (primary + replication + stress), with rough totals of ~47k primary judge calls and ~44k generations.
- `inferred`: Launching all tiers at once increases blast radius if one calibration assumption is wrong.
- `inferred`: Highest-signal rollout is stage-gated: launch primary tier first (3 jobs), review gates/bleed/capability, then conditionally launch replication and stress tiers.

Action: choose tranche policy before first upgraded launch (`primary-only` recommended as first tranche).

## 2026-02-25 [LITERATURE SECOND PASS] — Week 2 Reliability Gates Needed Tightening
**Type:** action
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Prevent false-positive layer/alpha selection before Week 3 decomposition

- `known`: Chen-style work uses behavioral layer sweeps and explicitly tracks coherence/capability tradeoffs as coefficients rise; large coefficients can degrade general quality.
- `known`: Chen and Rimsky both treat LLM-judge reliability as non-trivial and include manual/pairwise validation with documented edge cases.
- `known`: Turner and Zou both use random/shuffled baselines as robustness checks for steering-specific effects.
- `known`: Bhandari shows off-target trait bleed persists even when geometric overlap is reduced.
- `inferred`: Our prior gates (kappa + parse diagnostics + single random control) were necessary but not sufficient for high-confidence Week 2 lock-in.

Implemented response (completed before launch):
- Added judge API throttle/backoff with retryable-error handling.
- Added calibration directionality gate on known high-vs-low contrasts.
- Added coherence gate for selected combos (minimum score + bounded drop from baseline).
- Strengthened controls from one random vector to a random-control distribution with p95 separation requirement (plus shuffled vector control retained).

Remaining unresolved risks:
- `unknown`: transfer of selected settings to external benchmark prompts (outside generated held-out set).
- `unknown`: sensitivity of extraction vector quality to token-position choice (prompt-last vs response-token averaging).
- `unknown`: post-upgrade manual concordance quality on newly generated outputs.

## 2026-02-25 [METHODOLOGY GAP] — Week 2 Gate Audit Found Proposal-Mismatch Risks

**Type:** action
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Prevent overstating vector validation before Week 3 decomposition

- known: Proposal §6.2.3 specifies hallucination should be checked on known-fact questions (TruthfulQA-style), but the current upgrade runner only uses a small MMLU proxy for capability.
- known: Prior upgrade quality gate only required primary-judge parse pass; secondary-judge parse failures could occur without blocking acceptance.
- known: Non-trait control test score and neutral specificity shift were computed but not used as hard acceptance gates.
- inferred: Without these gates, a run could pass even when judge reliability/control sanity is weak, raising false-positive risk for layer/alpha lock.

Action:
1. Keep strengthened gates now implemented (secondary parse pass + control/specificity thresholds + strict capability availability by default).
2. Add an explicit hallucination known-fact benchmark check before Week 2 closeout (prefer TruthfulQA-format eval).

## 2026-02-25 [METHODOLOGY UPDATE] — Rollout Stability and Oversteer Diagnostics Added to Week 2

**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Strengthens evidence quality before layer/alpha lock-in

- known: Upgraded Week 2 runner now supports multi-rollout averaging with separate rollout controls (`sweep_rollouts_per_prompt`, `confirm_rollouts_per_prompt`, `baseline_rollouts_per_prompt`, `rollout_temperature`).
- known: Runner now logs `steering_norm_diagnostics` that compare injection magnitude (`|alpha|*||v||`) to pre-steering residual norms at the selected layer.
- inferred: This reduces variance-sensitive selection risk and gives an explicit warning channel for potential oversteering (injection magnitude approaching or exceeding residual scale).
- unknown: Empirical sensitivity of selected layer/alpha to rollout count and rollout temperature in this exact setup.

Follow-up: evaluate whether selected combos remain stable when increasing confirm rollouts (e.g., 3 -> 5) on primary-tier reruns.

## 2026-02-25 [METHODOLOGY/IMPLEMENTATION] — Gap 3/4 closure uncovered hidden generation compatibility risk
**Type:** action  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Ensures upgraded rollout/norm methodology is executable under current runtime stack

- `known`: Targeted gap closure added sweep multi-rollout defaults and expanded steering norm diagnostics (distributional ratios + exceedance rates).
- `known`: First remote smoke run failed with `AssertionError: top_k has to be greater than 0` from current `transformer_lens` when using `model.generate(..., top_k=0)`.
- `known`: Runner patched to `top_k=None` in both steered and unsteered generation paths.
- `inferred`: This failure mode could have blocked all upgraded Week 2 runs despite passing local spot checks, reinforcing that remote smoke checks are mandatory after generation-path edits.
- `unknown`: End-to-end smoke completion status for the rerun after `top_k=None` patch (currently active at time of logging).

Action: complete rerun smoke and confirm report includes `steering_norm_diagnostics.ratio_stats`/`max_ratio` before launching primary tranche.

## 2026-02-25 [IMPLEMENTATION FINDING] — `top_k=None` restored remote generation compatibility
**Type:** finding  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Confirms upgraded runner is runnable before primary tranche launch

- `known`: Rerun smoke (`i1pg2y8c`) completed successfully after patching generation from `top_k=0` to `top_k=None`.
- `known`: Output artifact contains new norm diagnostics fields (`steering_norm_diagnostics.ratio_stats`, `ratio_fraction_gt_0_5`, `ratio_fraction_gt_1_0`, `max_ratio`).
- `inferred`: The gap-closure upgrades are now implementation-valid; remaining uncertainty is scientific robustness on full-size primary runs, not code path correctness.

## [2026-02-25T13:30:12Z] [FINDING] — Null-control norm mismatch can fake selectivity
**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation upgrade
**Relevance:** Directly affects control-separation validity for final layer/alpha acceptance.

[known] The selected steering direction was used at native norm, while random/shuffled/random-text controls were unit-normalized. That asymmetry can inflate apparent superiority of selected vectors even when direction quality is similar. We patched controls to norm-match all null directions to the selected vector norm and surfaced both norms in the report.

## [2026-02-25T13:43:32Z] [OBSERVATION] — Smoke runtime should be intentionally decoupled from closeout-scale evaluation load
**Type:** observation
**Phase:** Week 2 / Stage 1 behavioral validation upgrade
**Relevance:** Affects implementation-validation cadence and risk of conflating infra latency with methodological validity.

[known] Implementation smoke accidentally inherited heavy defaults (`truthfulqa_samples=30`), creating long feedback loops that do not increase confidence in code-path correctness. [inferred] For fast iteration, smoke profiles should explicitly downshift high-cost evaluators while still traversing the same logic branches; full sample settings remain for primary/replication evidence runs.

## [2026-02-25T14:11:52Z] [METHODOLOGY TIGHTENER] — Silent calibration truncation is a hidden reliability confound
**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation upgrade
**Relevance:** Judge-calibration reliability and closeout claim defensibility.

[known] Prior v9 planning allowed `cross_rater_samples` to exceed `test_prompts`, silently reducing effective sample size via `min(...)`. [inferred] This can make calibration comparability drift across runs without explicit operator intent, weakening cross-run reliability interpretation. We now hard-fail this mismatch in both planner and runner and aligned defaults (`cross_rater_samples=20`, `test_prompts=20`).

[known] Reviewer and prelaunch artifact status still indicate open robustness risk (external transfer + extraction A/B failures), so we retained a primary-first launch policy and explicitly logged this as an open risk in the new plan artifact.

## [2026-02-25T15:11:21Z] [HANDOFF RISK] — Duplicate relaunches are a real experimental confound in long detached runs
**Type:** action
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Protects clean evidence attribution and compute budget while primary tranche is still in flight.

[known] The three primary jobs are detached and currently active, with no terminal artifacts yet. [inferred] If a new session relaunches “just to be safe,” we risk mixing evidence across duplicate runs, mis-attributing selected layer/alpha outcomes, and wasting substantial judge budget. We added explicit do-not-relaunch guardrails and canonical app IDs to CURRENT_STATE/SCRATCHPAD so the next session can resume by monitoring, not restarting.

## 2026-02-25 [FUTURE-DIRECTION] — Narrative/Trope/Meme work should be post-core, not Week 2.5
**Type:** action
**Phase:** Post-core extension planning
**Relevance:** Preserves causal clarity of preregistered claims while capturing a high-value follow-up.

- `known`: Core Week 2 work is still in active primary-tranche validation and has open closeout gates.
- `known`: A full extension blueprint now exists at `history/20260225-post-core-extension-narrative-arcs-tropes-memes.md` with implementation stages, controls, and integration paths.
- `inferred`: Running narrative/trope/meme experiments early would likely blur interpretation of core evidence and create sequencing risk.

Action: keep extension execution gated on core completion milestones and start via Stage E0 readiness checks defined in the blueprint.

## [2026-02-25T15:18:08Z] [OPS OBSERVATION] — W&B API run lookup can lag/return not-found while Modal shows active run
**Type:** observation
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Prevents false-negative status judgments during long detached runs.

[known] During active primary runs, direct links from Modal logs to W&B run pages were emitted, but local W&B API lookup by run id intermittently returned `not found`. [inferred] Next-session liveness checks should prioritize Modal app state/logs and artifact creation; treat W&B API lookup failures as non-terminal unless corroborated by app failure evidence.

## 2026-02-25 [FINDING] — Cross-trait extraction vectors are not strongly aligned in current artifact

**Type:** finding
**Phase:** Week 2 / Stage 1
**Relevance:** H4 precheck (cross-persona structure) and confound screening before Week 3 decomposition

- `known`: Local diagnostics artifact `results/stage1_extraction/week2_vector_diagnostics_20260225T152342Z.json` reports pairwise cross-trait cosine values mostly in `[-0.01, 0.30]` across layers 11-16.
- `known`: No cross-trait pair exceeded the provisional high-overlap flag threshold `|cos| >= 0.6` in this artifact.
- `inferred`: The specific concern "all trait vectors may be nearly the same direction" is not supported by this extraction artifact.
- `unknown`: Whether low geometric overlap implies behavioral independence; bleed checks from primary upgraded runs are still pending and remain the decisive evidence.

## 2026-02-25 [METHODOLOGY RISK] — System-prompt conditioning may be dominating persona-vector extraction

**Type:** action
**Phase:** Week 2 -> Week 3 boundary
**Relevance:** Validity of interpreting extracted directions as persona-selection representations rather than instruction-following vectors

- `known`: Current extraction contrasts explicit system prompts (`system_high` vs `system_low`).
- `inferred`: This setup can entangle persona-like behavior with instruction-compliance features.
- `unknown`: Whether a similar trait direction emerges when persona cues are induced without explicit system-role instructions.

Action: run an extraction-free validation condition using few-shot behavioral demonstrations under neutral system prompt, then compare directional cosine and behavioral steering effects against the current system-prompt-extracted vectors before interpreting Week 3 decomposition as persona-specific.

## 2026-02-25 [FINDING] — Evil trait pre-primary audit indicates refusal-invariant high-risk profile

**Type:** finding
**Phase:** Week 2 / Stage 1
**Relevance:** Trait validity for Week 3 decomposition scope

- `known`: Artifact `results/stage1_extraction/week2_evil_trait_audit_20260225T160326Z.json` flags 6/6 risk indicators.
- `known`: External transfer metric for evil remains non-positive (`plus_vs_minus=-0.75`, `bidirectional_effect=-0.75`).
- `known`: Manual sample refusal invariance is high (`all base/plus/minus refusal` in 80% of sampled rows).
- `inferred`: Current evil direction is likely dominated by style/disposition shifts under refusal constraints, not robust harmful-behavior steering.
- `unknown`: Whether larger alpha, different extraction method, or trait redefinition can recover a causally useful evil-like direction.

## 2026-02-25 [FINDING] — Stage2 pre-audit keeps SAE reconstruction as a hard interpretation gate

**Type:** action
**Phase:** Week 2 -> Week 3 boundary
**Relevance:** Prevent misattribution of low concentration to model rather than SAE blind spots

- `known`: Pre-audit artifact `results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T160326Z.json` classifies infra cosines as fail (`llama=0.1278`, `gemma=0.4526`) against Stage2 reliability thresholds.
- `known`: Config still applies base-model LlamaScope SAEs to an instruct model in primary path (`instruct_base_mismatch=true`).
- `inferred`: Any Stage2 concentration claim is underdetermined until dedicated reconstruction probes validate stage-appropriate hook/preprocessing behavior.
- `unknown`: Whether low infra cosine was primarily instrumentation mismatch vs intrinsic SAE transfer failure.

Action: run dedicated Stage2 reconstruction probe before trusting decomposition concentration metrics and explicitly report if interpretation remains confounded.

## 2026-02-25 [FINDING] — Layer16 Reconstruction Fails Equally on Base and Instruct Under LlamaScope SAE

**Type:** finding | action  
**Phase:** Week 2 pre-primary hardening / Week 3 gate prep  
**Relevance:** Stage 2 decomposition reliability gate

- `known`: Modal reconstruction probe artifact `results/stage2_decomposition/week3_sae_reconstruction_investigation_20260225T164322Z.json` completed successfully on app `ap-Q9eYKHJZbbY2FCW9Wha3eg`.
- `known`: Median reconstruction cosine is nearly identical and low for both models (`base~0.126`, `instruct~0.127`) at `layer=16`, `sae=l16r_32x`.
- `observed`: Explained variance is strongly negative for both models (`~ -27k`), and permutation-control median gaps are positive (~0.19), indicating the SAE path is doing non-trivial transforms but not faithful reconstruction under the current measurement path.
- `inferred`: The dominant issue is unlikely to be simple instruct-vs-base distribution shift alone; preprocessing or activation-path assumptions are probably mismatched.
- `unknown`: Which exact preprocessing step (normalization/bias handling/token selection) causes the EV collapse.

Action: add reconstruction preprocessing-path controls (input normalization variants + act-shape/token-position comparisons) before using any Stage 2 concentration/decomposition claim.

## 2026-02-25 [FINDING] — Reconstruction Failure Is Dominated by Activation Path Choice (Full Sequence vs Last Token)
**Type:** finding | action
**Phase:** Week 2 pre-primary hardening / Stage2 reliability pre-gate
**Relevance:** Determines whether Stage2 decomposition is blocked by true SAE failure or by measurement-path mismatch

- `known`: Root-cause artifact `results/stage2_decomposition/week3_sae_reconstruction_root_cause_20260225T170255Z.json` shows `raw_seq` remains catastrophic while `last_token` reconstruction is substantially better on both base and instruct models.
- `known`: For layer16 LlamaScope `l16r_32x`, `last_token` medians are roughly cosine `0.82` (base) / `0.77` (instruct), EV `0.67` / `0.57`, L0 `~31` / `~29`.
- `known`: SAE config snapshot has `normalize_activations=none` and no explicit expected hook name, so there is no direct hook-name mismatch evidence in this run.
- `inferred`: Prior catastrophic Stage2 finding overstates global SAE failure for this project's token-level extraction path; gating should be aligned to token-level reliability checks.
- `unknown`: Whether token-level reliability remains acceptable at larger sample counts and across alternate prompt distributions.

Action: rerun token-level reconstruction diagnostics with larger sample size before Stage2 interpretation claims.

## 2026-02-27 [FINDING] — Primary-Selected Gap Checks Confirm Robustness Failure Despite Stronger External Evil Delta

**Type:** finding | action  
**Phase:** Week 2 / post-primary closeout checks  
**Relevance:** Determines whether replication/stress launch is justified under existing Week 2 gate policy

- `known`: Post-primary gap-check artifact (`results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json`) fails overall (`overall_pass=false`).
- `known`: External transfer now passes for `sycophancy` and `hallucination`; `evil` still fails its external transfer gate because reversal direction remains wrong (`baseline_vs_minus < 0`) despite high `plus_vs_minus`.
- `known`: Extraction-method robustness fails for all 3 traits with low prompt-vs-response cosine similarity (`~0.376-0.406`, below `0.7` threshold).
- `known`: Manual concordance spot-check on primary outputs (`results/stage1_extraction/week2_primary_manual_concordance_ratings_20260227T202822Z.json`) is acceptable overall (`mean_trait_mae=4.744`, sign agreement mean `0.867`).
- `inferred`: Current closeout bottleneck has shifted from judge reliability to representation robustness (method sensitivity + evil reversal-direction instability).
- `unknown`: Whether adjusting extraction position or trait framing can clear robustness gates without sacrificing behavioral effect size.

Action: keep replication/stress launch blocked until an explicit decision is logged on gate policy or remediation plan for extraction-method robustness.

## 2026-02-27 [FINDING] — Week 2 Closeout Decision Locked to NO-GO for Replication/Stress

**Type:** finding | action  
**Phase:** Week 2 closeout governance  
**Relevance:** Determines whether any additional Week 2 launch is methodologically justified

- `known`: Explicit closeout decision is now recorded as `NO-GO` for replication/stress under current gate policy (`DECISIONS.md`, 2026-02-27T15:31:15-0600).
- `known`: Decision is grounded by three completed closeout artifacts:
  - ingestion summary (`week2_primary_postrun_ingestion_20260227T202336Z.json`),
  - manual concordance (`week2_primary_manual_concordance_ratings_20260227T202822Z.json`),
  - post-primary gap checks (`week2_prelaunch_gap_checks_20260227T205237Z.json`).
- `inferred`: The project now needs a narrow remediation tranche or explicit claim-scope narrowing before Week 3 narrative can remain coherent.
- `unknown`: Whether extraction-method robustness can be repaired without materially reducing observed behavioral steering effect sizes.

Action: require a superseding decision entry before any replication/stress launch command is executed.

## 2026-02-27 [FINDING] — Reviewer Inputs Are Now Frozen Verbatim and Fully Mapped to a Remediation Checklist

**Type:** finding | action  
**Phase:** Week 2 closeout governance / remediation planning  
**Relevance:** Prevents reviewer-coverage gaps and criterion drift during remediation

- `known`: Both reviewer comments are now stored verbatim in immutable artifacts:
  - `history/reviews/20260227-reviewer1-verbatim.md`
  - `history/reviews/20260227-reviewer2-verbatim.md`
- `known`: A single remediation execution plan is now frozen:
  - `history/20260227-week2-remediation-master-plan-v1.md`
- `known`: One-to-one reviewer finding coverage tracker is now in place:
  - `history/20260227-reviewer-reconciliation-checklist-v1.md`
- `inferred`: End-of-remediation "did we miss anything?" risk is now operationally controllable via checklist audit before reviewer update.
- `unknown`: Which subset of remediation tasks will materially improve robustness gates versus yielding negative but clarifying evidence.

Action: block any reviewer-facing update summary until the reconciliation checklist is fully statused with artifact-backed evidence.


## 2026-03-01 [FINDING] — WS-D Trait Scope Resolution Formalizes Hallucination as Negative and Splits Evil by Construct

**Type:** finding | action  
**Phase:** Week 2 remediation / WS-D  
**Relevance:** closes reviewer requests on hallucination formal status and evil construct mismatch framing

- `known`: Artifact `results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json` now formalizes:
  - hallucination: `negative_finding_stage1` (primary Section 6.2.3 fail + extraction-free null overlap),
  - evil harmful-content lane: `disconfirmed_bidirectional_harmful_content`,
  - evil machiavellian lane: `supported_but_week2_not_validated_due_to_coherence`.
- `inferred`: Stage2 primary-claim scope should prioritize `sycophancy + machiavellian_disposition`, with hallucination treated as exploratory instruction-following control rather than a validated persona-like direction.
- `unknown`: whether a construct-aligned external benchmark will validate bidirectionality for the machiavellian lane.

Action: run construct-aligned external transfer for machiavellian lane before any superseding Week 2 launch decision.

## 2026-03-01 [FINDING] — WS-E Claim-Layer Multi-Seed Audit Removes False-Positive Stage2 Pass Path

**Type:** finding | action  
**Phase:** Week 2 remediation / WS-E  
**Relevance:** addresses Stage2 readiness integrity concerns (selected layers, seed schedule, cross-SAE coverage)

- `known`: Multi-seed investigation artifact now records seed schedule consumption at selected claim layer 12: `results/stage2_decomposition/week3_sae_reconstruction_investigation_20260301T031743Z.json` (`[42,123,456,789]`).
- `known`: Multi-seed root-cause artifact at layer12 confirms best-variant consistency but shows instruct token-level reconstruction below prior pass threshold on some seeds: `results/stage2_decomposition/week3_sae_reconstruction_root_cause_20260301T033002Z.json`.
- `known`: Updated claim-layer audit now fails explicitly in `results/stage2_decomposition/week3_sae_reconstruction_audit_20260301T033046Z.json` due to:
  - token gate fail (`min median_cos=0.7047`, `min median_EV=0.4765`),
  - cross-source overlap fail on claim layer 12 (`cross_check overlap=[]`),
  while seed schedule and probe-layer coverage both pass.
- `inferred`: prior Stage2 `pass` was optimistic for current claim-layer scope; with stricter gating, Stage2 remains blocked.
- `unknown`: whether to recover cross-SAE overlap by adding/choosing overlapping layers or to narrow/defer cross-SAE claims for this tranche.

Action: decide cross-SAE strategy for claim layer 12 before Week 3 decomposition launch.

## [2026-03-02T17:50:00-0600] [OBSERVATION] — Detached resume is now operationally required for long Week2 upgrade runs
**Type:** observation
**Phase:** Week 2 / Stage 1 remediation
**Relevance:** execution integrity for WS-F rollout-depth evidence (prevents non-scientific interruptions from biasing closeout timing)

`known`: attached-mode long run stopped with explicit Modal reason `local client disconnected` while checkpoint state was healthy. `known`: detached resumes loaded prior state (state dictionaries preserved through controls/sweep boundaries), so remaining work can continue without discarding prior judge calls. `inferred`: for >3h Week2 upgrade jobs, detached-mode launch should be treated as default operating mode going forward to reduce avoidable compute waste.

## [2026-03-03T06:21:15-0600] [FINDING] — Rollout depth stabilizes sycophancy effect size but does not relieve coherence bottleneck
**Type:** finding
**Phase:** Week 2 / Stage 1 remediation (WS-F)
**Relevance:** informs whether closeout failure is sampling noise vs systematic gate bottleneck

`known`: rollout3 vs rollout5 comparison artifact (`week2_rollout_stability_sensitivity_20260303T121253Z.json`) shows sycophancy bidirectional effect is stable (+0.47 delta), while evil shrinks moderately (-5.25 delta). `known`: both traits remain `overall_pass=false` due coherence under rollout5. `inferred`: increasing rollout depth reduced variance concern but did not change the dominant closeout failure mode, so further stochastic-depth increases alone are unlikely to unlock a pass.

## [2026-03-03T16:50:00Z] [FINDING] — Content-robustness checks pass despite persistent prompt-vs-response A/B mismatch
**Type:** finding
**Phase:** Week 2 remediation / P1
**Relevance:** clarifies whether extraction-method concern is instability of direction content vs computational-regime dependence

- `known`: robustness artifact `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json` passes all gates for sycophancy and evil at claim layer 12.
- `known`: bootstrap subset stability is extremely high (`p05~0.999` for both traits) and train-vs-heldout cosine is also high (`~0.996`).
- `known`: prompt-vs-response A/B mismatch remains low in prior diagnostics (`~0.38-0.41`).
- `inferred`: under prompt-last extraction, vector content is stable across prompt subsets/datasets; remaining A/B issue is better interpreted as regime dependence rather than prompt-content instability.
- `unknown`: whether analogous robustness remains high for response-mean extraction under the same bootstrap/heldout protocol.

## [2026-03-03T16:52:00Z] [METHODOLOGY UPDATE] — Cross-trait bleed threshold sensitivity is lane-dependent, not universally over-tight
**Type:** finding
**Phase:** Week 2 remediation / P2
**Relevance:** closes reviewer concern on brittle single-threshold interpretation for bleed gate

- `known`: sensitivity artifact `results/stage1_extraction/week2_cross_trait_bleed_sensitivity_20260303T164726Z.json` shows only one lane is threshold-borderline: sycophancy prompt-last primary ratio `0.3165`.
- `known`: the same trait under rollout5 response-mean lane is comfortably below threshold (`0.1853`), and evil is below threshold across both lanes (`~0.162-0.168`).
- `inferred`: the `0.30` threshold is not broadly miscalibrated, but one historical lane sits near the decision boundary; policy should report this sensitivity explicitly rather than hiding it.
- `unknown`: whether future trait/layer updates preserve the same bleed margin profile.

## [2026-03-03T19:07:00Z] [GOVERNANCE] — SP-F1/SP-F3 policy ambiguity is closed with explicit packet
**Type:** finding
**Phase:** Week 2 remediation governance
**Relevance:** unblocks checklist-complete reviewer update without relaxing scientific limits

- `known`: `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json` freezes:
  - Stage2 claim-scope split (single-source decomposition allowed at selected claim layer; cross-source claims restricted to overlap-capable sensitivity layers),
  - coherence dual-scorecard policy (`absolute_and_relative` for hardening reliability, `relative_only` for proposal-compatibility interpretation).
- `inferred`: this resolves policy ambiguity while preserving existing NO-GO guardrails.
- `unknown`: whether a future superseding decision should change launch status; that still requires explicit governance action.

## [2026-03-03T14:03:10-0600] FINDING — Coherence Floor Is Model-Baseline Dominated
**Type:** finding
**Phase:** Week 2 -> Week 3 transition
**Relevance:** Governs whether Week2 hardening failure is a blocker for Stage2 H1 decomposition start.

- known: coherence diagnostic shows both traits fail absolute floor (`75`) while relative degradation passes (`sycophancy drop ~0.09`, `evil improves ~6.09`).
- inferred: absolute floor is measuring model/prompt baseline quality rather than steering-induced degradation, so it should remain a caveat scorecard rather than a Stage2-start blocker.
- action consequence: proceed to Stage2 decomposition under proposal-compatibility with explicit dual-scorecard reporting and limitation carry-forward.

## [2026-03-03T20:28:00Z] FINDING — Layer12 Stage2 decomposition-start completed; direct-vs-differential top feature overlap is very low
**Type:** finding
**Phase:** Week 3 / Stage 2 decomposition-start
**Relevance:** informs H1 concentration interpretation and feature-selection strategy for upcoming attribution/ablation.

- `known`: Stage2 artifact `results/stage2_decomposition/week3_sae_decomposition_20260303T202729Z.json` completed successfully for `sycophancy` and `evil->machiavellian_disposition` at layer 12.
- `known`: top-100 direct-projection vs top-100 differential-activation overlap is small for both traits:
  - sycophancy Jaccard `0.0309` (union count `194`),
  - machiavellian lane Jaccard `0.0256` (union count `195`).
- `inferred`: a single top-100 list from only one signal channel (direct or differential) would likely miss most candidate features; union-based candidate set is necessary for Stage3 tracing.
- `unknown`: whether low overlap persists at overlap-capable sensitivity layers (`11`, `15`) and under cross-source SAE lane.

## [2026-03-04T10:19:30-0600] FINDING — Cross-source overlap layers show higher direct-vs-differential agreement than claim layer
**Type:** finding
**Phase:** Week 3 / Stage 2 cross-source sensitivity
**Relevance:** informs whether candidate-feature selection should prioritize overlap layers for cross-source-supported claims.

- `known`: cross-source artifacts completed at layers `11` and `15`:
  - `results/stage2_decomposition/week3_sae_decomposition_20260303T203716Z.json`
  - `results/stage2_decomposition/week3_sae_decomposition_20260303T211749Z.json`
- `known`: direct-vs-differential top-100 Jaccard at claim layer12 primary run was low (`~0.031` sycophancy, `~0.026` machiavellian lane), while overlap layers are notably higher:
  - layer11 cross-source: `~0.149` sycophancy, `~0.136` machiavellian lane,
  - layer15 cross-source: `~0.149` sycophancy, `~0.111` machiavellian lane.
- `inferred`: overlap-capable layers may provide more internally consistent candidate sets for cross-source-supported interpretation than selected claim layer12.
- `unknown`: whether this higher within-layer agreement also translates to stronger Stage3 attribution selectivity and downstream causal effect concentration.

## [2026-03-04T10:32:25-0600] FINDING — Cross-layer feature-ID support is not a valid Stage3 selection signal
**Type:** finding
**Phase:** Week 3 / Stage 3 candidate selection
**Relevance:** prevents invalid cross-layer/source feature correspondence assumptions in attribution candidate policy.

- `known`: initial Stage3 v1 artifact (`week3_stage3_candidate_selection_20260304T163025Z.json`) yielded zero selected features with support>=1 when support was defined via feature-ID overlap across layers/sources.
- `inferred`: feature IDs should not be treated as directly comparable across different layers/sources for support scoring without explicit correspondence mapping.
- `known`: policy was pivoted (DECISIONS 2026-03-04T10:31:30-0600) and superseding v2 artifact (`week3_stage3_candidate_selection_20260304T163200Z.json`) now uses claim-layer selection only, with overlap lanes as context metrics.
- `unknown`: whether later representation-alignment methods can recover reliable cross-layer/source feature correspondence.

## [2026-03-04T10:37:10-0600] FINDING — First Stage3 attribution pass yields moderately concentrated, moderately stable feature maps
**Type:** finding
**Phase:** Week 3 / Stage 3 attribution
**Relevance:** provides first H1-relevant concentration/stability signal before Stage4 causal ablations.

- `known`: artifact `results/stage3_attribution/week3_stage3_activation_delta_attribution_20260304T163657Z.json` completed on app `ap-ZBqFKWyZ4fHELv9fkzWT52`.
- `known`: proxy attribution concentration is non-trivial for both active claim traits:
  - sycophancy `gini=0.5853`,
  - machiavellian disposition `gini=0.6612`.
- `known`: prompt-level top10 feature-map stability is moderate (not near-zero, not near-1):
  - sycophancy pairwise Jaccard mean `0.3296`,
  - machiavellian disposition pairwise Jaccard mean `0.3698`.
- `inferred`: there is enough concentration/stability signal to justify immediate Stage4 necessity/sufficiency ablations on claim-layer selected features instead of more Stage1/Stage2 gate iteration.
- `unknown`: whether these proxy-attribution signals reflect causal importance versus correlated activation effects until ablation results land.

## [2026-03-04T10:46:30-0600] FINDING — Stage3 depth sensitivity preserves attribution concentration/stability signal
**Type:** finding
**Phase:** Week 3 / Stage 3 attribution
**Relevance:** tests whether first-pass attribution pattern was a small-sample artifact before freezing Stage4 targets.

- `known`: depth-sensitivity artifact `results/stage3_attribution/week3_stage3_activation_delta_attribution_20260304T164549Z.json` completed with `n_prompts=50` per trait.
- `known`: metrics stay same-order versus pass1 (`n_prompts=20`):
  - sycophancy: gini `0.5853 -> 0.5771`, prompt-top10 Jaccard `0.3296 -> 0.3254`
  - machiavellian disposition: gini `0.6612 -> 0.6476`, prompt-top10 Jaccard `0.3698 -> 0.3744`
- `inferred`: attribution concentration/stability evidence is not a fragile small-sample artifact under the current proxy method.
- `unknown`: whether Stage4 necessity/sufficiency ablations will confirm the same features as causally meaningful.

## [2026-03-04T10:49:18-0600] ACTION — Stage4 target sets are now frozen from pass2 and ready for causal execution
**Type:** action
**Phase:** Week 3/4 transition (Stage3 -> Stage4)
**Relevance:** commits the exact ablation target IDs before running necessity/sufficiency tests.

- `known`: freeze artifact `results/stage4_ablation/week3_stage4_target_set_freeze_20260304T164918Z.json` is generated.
- `known`: top-10 target feature sets per trait are fixed, and random baseline requirement is pinned to `n=100` same-size sets sampled at runtime from full SAE feature space.
- `inferred`: target-freeze provenance risk is closed; remaining risk moves to ablation implementation correctness and judge/effect selectivity computation.
- `unknown`: whether necessity reductions on frozen targets will beat random baselines with strong effect sizes under resample primary mode.

## [2026-03-04T11:12:08-0600] FINDING — Stage4 proxy necessity is mixed and method-divergent; resample lane is negative
**Type:** finding | action
**Phase:** Week 4 / Stage 4 causal validation
**Relevance:** first direct Stage4 signal for H2, but currently non-claim because behavioral necessity is not measured.

- `known`: post-refactor full artifact `results/stage4_ablation/week3_stage4_necessity_proxy_ablation_20260304T171200Z.json` completed on app `ap-Ml02p5K3hbvekbO0MlsLXA`.
- `known`: primary resample method yields negative observed necessity reduction on both active traits (`syc=-0.0203`, `evil=-0.1352`).
- `known`: secondary methods disagree sharply (mean positive for both; zero positive for sycophancy and strongly negative for machiavellian lane).
- `inferred`: either the frozen top-10 sets are not necessity-driving under resample semantics, or the proxy metric does not track behavioral necessity in a claim-useful way.
- `unknown`: whether full behavioral ablation (judge-scored steering outputs) would replicate this negative pattern.

Action: choose between (A) building full behavioral Stage4 ablation runner for claim-grade H2 evidence or (B) retaining proxy lane as exploratory-only and shifting effort to stronger claim pathways.

## [2026-03-04T11:37:20-0600] observation — Stage4 import boundary failure mode repeated from Stage2
**Type:** observation
**Phase:** Week 3 / Stage 4
**Relevance:** implementation reliability for H2 causal runner

`known`: Modal detached runtime imported `week3_stage4_behavioral_ablation.py` without local package context, causing `ModuleNotFoundError: scripts`. `inferred`: for Modal-traced runners, payload-first/self-contained scripts are more reliable than workspace-package imports unless explicit mounts are validated.

## [2026-03-05T09:57:15-0600] finding — Behavioral Stage4 landed, but necessity reduction is denominator-fragile
**Type:** finding
**Phase:** Week 3 / Stage 4
**Relevance:** H2 necessity evidence quality

`known`: first behavioral Stage4 artifact exists (`week3_stage4_behavioral_ablation_20260304T192718Z.json`) and confirms end-to-end execution path after import-boundary fix. `observed`: baseline steering effect is very small/zero on part of the tranche (`syc mean abs effect=3.4`, `evil mean abs effect=0.0`). `known`: current reduction formula with near-zero denominator yields extreme magnitude outputs (`~1e8-1e9`), making aggregate necessity/selectivity summaries non-interpretable. `inferred`: this is a metric-definition issue, not necessarily a causal signal verdict; rerun after low-baseline handling patch is required.

## [2026-03-05T10:03:10-0600] finding — Hewitt (2026) residual-stream linearity note is directly relevant to our Stage1/Stage4 interpretation
**Type:** finding
**Phase:** Week 3 / Stage 4
**Relevance:** extraction-method sensitivity framing + steering-claim language discipline

`known`: Hewitt (2026) argues residual-stream additivity does not provide strong linear-propagation guarantees after interventions because downstream layers are nonlinear. `inferred`: this aligns with our observed prompt-vs-response extraction divergence and supports treating it as computational-regime dependence/limitation rather than a hard contradiction of vector utility. `known`: this also supports our claim-evidence policy: Stage4 necessity/sufficiency claims must rest on empirical gates and controls, not architectural linearity assumptions.

## [2026-03-05T00:54:10-0600] observation — Low-baseline masking yields actionable validity signal early in Stage4
**Type:** observation
**Phase:** Week 3 / Stage 4
**Relevance:** H2 necessity metric reliability

`observed`: on the patched behavioral rerun (`ap-NHmNaSEiQua5O54bXcuQ0X`), sycophancy baseline lane reports `valid_prompts=8/10` at `min_baseline_effect_for_reduction=1.0` before method aggregation. `inferred`: explicit validity accounting is likely to be a better reliability gate than forcing unstable ratio statistics when baseline steering effect is near zero.

## [2026-03-06T06:45:44-0600] finding — Low-baseline guard traded numeric stability for coverage collapse on evil lane
**Type:** finding
**Phase:** Week 3 / Stage 4
**Relevance:** H2 necessity interpretation quality

`known`: with `min_baseline_effect_for_reduction=1.0` (`week3_stage4_behavioral_ablation_20260305T091059Z.json`), denominator blowups disappeared, but validity coverage became highly asymmetric: sycophancy `8/10` valid prompts, evil `1/10`. `inferred`: current evil prompt tranche is too low-effect at baseline for reduction-based necessity summaries, so threshold sensitivity + larger prompt tranche are required before drawing H2 conclusions.

## 2026-03-09 [FINDING] — Evil Stage4 Coverage Is Source-Setting-Sensitive (alpha3 lift), Not Only Threshold-Sensitive

**Type:** finding | action  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** H2 necessity evidence viability for machiavellian lane

- `known`: calibration artifact `results/stage4_ablation/week3_stage4_behavioral_ablation_20260309T194229Z.json` (evil-only, source alpha3, threshold `0.0`) completed successfully.
- `known`: valid reduction coverage increased to `13/20` (`0.65`) vs prior alpha2-source threshold run `4/30` (`0.1333`).
- `known`: baseline steering-effect mean increased sharply (`10.75` vs `0.6333` in prior alpha2-source run).
- `known`: selectivity remains non-significant in this calibration (`p=0.1667` across methods) with reduced random depth (`n_random=5`).
- `inferred`: low coverage on evil Stage4 was substantially source-setting limited; threshold tuning alone understated this.
- `unknown`: whether coverage/selectivity gains survive claim-depth evaluation (`n_random>=20`, full bootstrap depth).

Action: run full-depth alpha3-source confirmation tranche before any H2 claim update; keep current result as calibration-only evidence.

## 2026-03-10 [FINDING] — Full-Depth Alpha3 Confirmation Solves Coverage, Exposes Threshold-Binding as Remaining H2 Bottleneck

**Type:** finding | action  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** H2 necessity interpretation quality under strict Stage4 gates

- `known`: full-depth artifact `results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T001903Z.json` landed with `n_prompts=30`, `n_random=20`.
- `known`: evil valid reduction coverage is now `21/30` (`0.70`), materially above prior alpha2-source run (`4/30`).
- `known`: selectivity p-value improved to `0.0476` across methods at full depth.
- `known`: strict threshold flags remain false across methods (`necessity_threshold_pass=false`, `selectivity_p_threshold_pass=false`, `a12_threshold_pass=false`).
- `inferred`: remaining blocker is strict threshold-policy/method-selectivity alignment rather than baseline-effect sparsity.
- `unknown`: whether failures persist across heldout tranche resampling or are slice-sensitive under the same alpha3 source.

Action: run prompt-tranche sensitivity with same source/gates and produce a threshold-binding diagnostic artifact before any H2 confidence upgrade.

## 2026-03-10 [METHODOLOGY UPDATE] — Added deterministic heldout-tranche control for Stage4 behavioral necessity

**Type:** finding | action  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** isolate prompt-slice sensitivity vs threshold-policy effects in H2

- `known`: Stage4 runner now supports `--heldout-start-index`, enabling deterministic prompt-slice offsets while preserving all other settings.
- `known`: utility tests were expanded and pass (`Ran 11 tests ... OK`) with explicit wrap/no-wrap window selection checks.
- `known`: prompt-tranche sensitivity run launched (`ap-bC1z6ABhVa7hUSNBsJ0cpe`) using `heldout_start_index=20` under the same alpha3 full-depth configuration.
- `inferred`: this closes a design gap where earlier "sensitivity" comparisons still reused the same leading heldout tranche.
- `unknown`: whether strict threshold failures remain stable across tranches or are driven by specific prompt slices.

Action: terminalize the tranche run and compare gate margins directly against `week3_stage4_behavioral_ablation_20260310T001903Z.json` before any H2 policy decision.

## 2026-03-10 [FINDING] — Prompt-Tranche Sensitivity Preserves Coverage but Destabilizes Selectivity by Method

**Type:** finding | action  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** determines whether H2 threshold failures are stable or tranche-dependent

- `known`: tranche artifact `results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T080841Z.json` completed under same source/gates as full-depth reference.
- `known`: coverage remains high (`20/30` valid prompts), comparable to reference (`21/30`).
- `known`: selectivity behavior shifts by method vs reference:
  - resample p worsened (`0.6190` vs `0.0476`)
  - mean p worsened (`0.2381` vs `0.0476`)
  - zero remained `0.0476`
- `known`: strict threshold flags remain false across methods.
- `inferred`: at least part of the remaining H2 blocker is tranche-sensitive selectivity behavior, not only global threshold stringency.
- `unknown`: whether this instability persists across additional offsets or is specific to this slice.

Action: generate explicit tranche-vs-reference comparison artifact before any threshold-policy recalibration.

## 2026-03-10 [FINDING] — Tranche-vs-Reference Comparison Stabilizes the Diagnosis: Gate State Is Robustly Failing, Effect Strength Is Slice-Sensitive

**Type:** finding | action  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** drives whether we keep strict H2 gates-only trajectory or adopt dual-scorecard interpretation

- `known`: comparison artifact `results/stage4_ablation/week3_stage4_tranche_comparison_20260310T141458Z.json` is generated from full-depth reference vs tranche runs.
- `known`: coverage remains stable/high (`0.70 -> 0.6667`, `n_valid 21 -> 20`).
- `known`: strict gate states remain unchanged (all false for all methods in both runs).
- `known`: effect strength varies by slice (p and A12 degrade on tranche for all methods; strongest degradation on resample/mean).
- `inferred`: the failure is robust at the gate-state level but unstable in margin strength; this supports policy clarification before more reruns.
- `unknown`: whether additional slices would tighten margins enough to materially change policy choice without threshold changes.

Action: finalize and log H2 policy decision packet (strict-only vs dual-scorecard narrative) before launching another Stage4 run.

## 2026-03-10 [FINDING] — Policy Packet Complete; Remaining Step Is a Single Explicit H2 Governance Lock

**Type:** finding | action  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** controls whether Stage4 proceeds with additional reruns or transitions with caveated reporting

- `known`: policy packet artifact `results/stage4_ablation/week3_stage4_policy_decision_packet_20260310T142000Z.json` is generated and indexed.
- `known`: strict gates fail across both full-depth runs while coverage remains high/stable.
- `known`: recommendation in packet is `strict_fail_with_dual_scorecard_candidate` (inferred recommendation, not yet governance-locked).
- `inferred`: the technical work for this decision tranche is complete; only governance lock remains.
- `unknown`: final chosen path (strict-only continuation vs dual-scorecard narrative lane) until explicitly logged in DECISIONS.

Action: log explicit H2 policy lock and then execute only the path-consistent next step.

## 2026-03-10 [FINDING] — Stage4 H2 Tranche Is Policy-Closed; Remaining Work Is Downstream Hypothesis Execution

**Type:** finding  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** marks transition from rerun loop risk to path-consistent next-phase planning

- `known`: H2 policy lock is now explicitly recorded in `DECISIONS.md` (`2026-03-10T09:24:10-0500`).
- `known`: Stage4 synthesis memo is now published at `history/20260310-stage4-h2-synthesis-memo-v1.md` and indexed.
- `known`: strict scorecard remains fail, while dual-scorecard interpretation lane is explicitly enabled for narrative reporting.
- `inferred`: the highest-value move is now to produce H3/Stage5 planning artifacts under the locked H2 caveat block, not launch another immediate Stage4 run.

## 2026-03-10 [FINDING] — Launch-Free H3/Stage5 Planning Artifacts Are Ready for Implementation Phase

**Type:** finding  
**Phase:** Week 7-8 transition (Stage4 -> Stage5 preparation)  
**Relevance:** converts policy-closed Stage4 status into concrete next implementation targets

- `known`: H3 planning artifact is generated at `results/stage4_ablation/week3_h3_sufficiency_execution_plan_20260310T143354Z.json` (supersedes initial `...143023Z` draft).
- `known`: Stage5 planning stub is generated at `results/stage5_cross_persona/week3_stage5_planning_stub_20260310T143354Z.json` (supersedes initial `...143023Z` draft).
- `known`: both artifacts preserve the no-new-launch constraint and mark readiness as `launch_recommended_now=false`.
- `inferred`: next efficient tranche is local implementation + tests for sufficiency/cross-persona utilities before scheduling any new remote run.

## 2026-03-10 [FINDING] — Stage5 Utility Run Shows Early>Late Overlap Trend but Not Full H4 Threshold Pattern

**Type:** finding  
**Phase:** Stage5 preparation (launch-free utility execution)  
**Relevance:** early empirical signal for H4/H5 feasibility before remote cross-persona runs

- `known`: new utility script `scripts/week3_stage5_cross_persona_analysis.py` executed successfully and produced `results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T143805Z.json`.
- `observed`: candidate-union jaccard is higher at early layers than late (`layer11=0.1696`, `layer15=0.1236`) but early overlap does not exceed the proposal heuristic `>0.2`.
- `observed`: differential-activation overlap is stronger (`layer11=0.2346`, `layer12=0.2500`, `layer15=0.1765`) with early>late trend retained.
- `observed`: router-candidate stable pool is empty across early layers 11/12 in this stub run.
- `inferred`: Stage5 can proceed as exploratory utility-hardening work, but claim-grade H4/H5 requires explicit comparability and multiple-testing controls before interpretation hardens.

## 2026-03-10 [FINDING] — H3 Dry-Run Path and Stage5 Policy Hooks Are Now Operationalized

**Type:** finding  
**Phase:** Stage4/Stage5 launch-free hardening  
**Relevance:** closes immediate tooling gaps before any new remote sufficiency/cross-persona runs

- `known`: Stage4 sufficiency preflight script/test/artifact are now landed (`week3_stage4_sufficiency_preflight_20260310T145632Z.json`), with dry-run path exercised and explicit blocker tracking.
- `observed`: synthetic full-dose preservation clears sufficiency threshold in both traits/methods under dry-run assumptions; this validates path wiring but not empirical sufficiency.
- `known`: Stage5 utility now emits comparability diagnostics by SAE source and BH-FDR hook outputs (`week3_stage5_cross_persona_analysis_20260310T145632Z.json`).
- `observed`: BH-FDR hook is unevaluated in current run due missing candidate p-value inputs (`reason=missing_router_pvalues`).
- `inferred`: next-value tranche should target real sufficiency execution and router p-value generation rather than additional planning artifacts.

## 2026-03-10 [FINDING] — Router BH Hook Is No Longer Missing; Current Launch-Free Pass Finds No FDR-Significant Candidates

**Type:** finding | action  
**Phase:** Stage5 launch-free hardening  
**Relevance:** closes implementation gap for H5 pre-run diagnostics and reframes remaining work as policy/sensitivity, not tooling

- `known`: Stage5 router p-value lane is now test-backed and executed:
  - test file: `tests/test_week3_stage5_router_candidate_pvalues.py`
  - artifacts: `week3_stage5_router_candidate_pvalues_20260310T195815Z.json` + `_map_20260310T195815Z.json`
- `known`: Stage5 cross-persona rerun consumed the map and executed BH hooks:
  - artifact: `results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T195835Z.json`
  - candidate_union hook: `n_tested=62`, `n_rejected=0`, `min_q=0.0465` at `fdr_alpha=0.01`
- `observed`: direct/differential hook lanes also show `n_rejected=0` under current alpha.
- `inferred`: the prior blocker (`missing_router_pvalues`) is resolved; what remains is interpretation policy (how to treat a no-rejection exploratory pass) and whether sensitivity lanes are worth pre-registering.
- `unknown`: whether alternate p-value models or relaxed/stratified multiple-testing policies would surface stable router candidates without inflating false positives.

Action: close `S5-G2`/`S5-G4` via a policy decision packet that explicitly states whether this remains an exploratory null lane or triggers a pre-registered sensitivity run.

## 2026-03-10 [FINDING] — Stage5 Gate Closure Is Now Policy-Locked; H3 Runner Is Remote-Capable but Unlaunched

**Type:** finding | action  
**Phase:** Stage4/Stage5 transition  
**Relevance:** turns prior tooling blockers into explicit launch-policy decisions

- `known`: Stage5 policy packet is now artifact-backed at `results/stage5_cross_persona/week3_stage5_policy_decision_packet_20260310T200937Z.json`.
- `observed`: packet classifies `S5-G2=pass_with_limitation` and `S5-G4=exploratory_null`, recommending `lock_exploratory_null_with_optional_sensitivity_lane`.
- `known`: H3 now has a remote-capable sufficiency runner plus dry-run packet artifact (`scripts/week3_stage4_behavioral_sufficiency.py`, `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T201431Z.json`).
- `observed`: dry-run packet reports `inputs_valid=true` and `launch_recommended_now=true` with no blocking items.
- `inferred`: additional launch-free scaffolding has diminishing returns; value now depends on an explicit decision to run one remote H3 sufficiency tranche or intentionally hold at dry-run readiness.
- `unknown`: whether a Stage5 sensitivity lane (alternative p-value model / FDR threshold) would materially change router-candidate conclusions without inflating false positives.

Action: decide in-governance whether to execute a single pre-registered H3 remote sufficiency run next, and whether Stage5 sensitivity is required before freezing H5 claim language.

## 2026-03-10 [FINDING] — Detached H3 Sufficiency Execution Needs Stable Run Identity, Not Just Remote Persistence

**Type:** finding  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** operational validity for judge-heavy remote sufficiency runs under Modal preemption

- `known`: the first detached H3 sufficiency retry (`ap-EvoMUuBIRRlMXBHxvtLrvB`) was stopped after worker preemption because checkpoint/final artifact identity still depended on a timestamp generated inside the remote function.
- `known`: the first token-stable retry (`ap-0G5330JQuwPuHQqTYjlWuK`) then failed operationally because `vol.reload()` ran after model load and hit a Modal open-file conflict on the mounted Hugging Face/Xet cache.
- `known`: `scripts/week3_stage4_behavioral_sufficiency.py` now threads an explicit `run_token` through local entrypoint, dry-run packet, and remote checkpoint/final artifact paths; utility tests now pass at `Ran 5 tests ... OK`.
- `known`: checkpoint reload now occurs before model loading, which removes the observed volume conflict path.
- `observed`: current detached run `ap-IhLmgFOlGMVyMfukXluGmj` is active under token `week3-stage4-h3-tranche1-20260310T2321Z`; the app has remained alive past the prior reload-failure window, but checkpoint-commit evidence has not landed yet.
- `inferred`: for long judge-heavy Stage4 runs, resumability depends more on stable artifact identity than on detached mode alone. Remote persistence without explicit run identity is not enough.
- `unknown`: whether checkpoint timing should move earlier than “post-baseline” if preemption proves frequent before first commit.

## 2026-03-10 [FINDING] — First Full H3 Sufficiency Run Executed Cleanly but Fails Selectivity/Coherence Gates Broadly

**Type:** finding  
**Phase:** Week 7-8 / Stage4 Causal Validation  
**Relevance:** first empirical H3 evidence for sufficiency, and first direct signal on whether current target sets/methods produce selective circuit-only preservation

- `known`: final artifact is now local at `results/stage4_ablation/week3_stage4_behavioral_sufficiency_remote_week3-stage4-h3-tranche1-20260310T2321Z.json`.
- `known`: execution completed for all 16 cells (`2 traits x 2 methods x 4 doses`).
- `observed`: headline gate counts are `sufficiency_threshold_pass=16/16`, `selectivity_p_threshold_pass=0/16`, `coherence_relative_max_drop_pass=0/16`, `a12_threshold_pass=1/16`.
- `observed`: many `observed_mean_preservation` values exceed `1.0`, which means the circuit-only effect can exceed the steered baseline effect under the current metric definition.
- `inferred`: before any rerun decision, we need to determine whether this is genuine “over-preservation” behavior, a metric-semantics issue, or a bug in how the denominator is being interpreted.
- `unknown`: whether H3 should be recorded as a strict fail under current gates or held in a metric-review bucket pending a targeted implementation audit.

## 2026-03-10T22:49:00-0500 FINDING — H3 pilot overclaimed twice in different ways
**Type:** finding
**Phase:** Week 7-8 / Stage 4
**Relevance:** H3 (Causal Sufficiency)

`known`: the first H3 pilot overstated sufficiency for two separate reasons: (1) uncapped preservation ratios inflated means above `1.0`, and (2) absolute-delta preservation could count sign-flipped circuit-only behavior as preserved. `inferred`: this makes the old artifact useful for operational debugging and coarse coverage checks, but not for final H3 interpretation. `known`: the patched runner now blocks both failure modes; `unknown`: whether a sign-aware rerun will leave any evil cells above the sufficiency threshold once coverage and coherence are both enforced.

## 2026-03-11T08:33:00-0500 [FINDING] — H3 is now instrumented enough that the next blocker is runtime economics, not missing controls
**Type:** finding | action
**Phase:** Week 7-8 / Stage 4
**Relevance:** H3 (Causal Sufficiency)

- `known`: the H3 runner now has explicit claim mode, full-SAE-complement support, capability-proxy diagnostics, next-token-loss diagnostics, and dose-monotonicity gating.
- `known`: the authoritative dry-run packet `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260311T132932Z.json` shows claim-grade configuration can be resolved with no code-path blockers.
- `inferred`: the next practical blocker is runtime cost. The first H3 run (`10 prompts`, `5 random sets`) already took hours; naively scaling to `30 prompts`, `100 random sets`, `2 traits x 2 methods x 4 doses` is likely too expensive/time-heavy to launch blindly.
- `inferred`: the correct next move is a bounded claim-grade execution design, not immediate full-matrix launch.
- `unknown`: whether a resample-primary or trait-staged tranche can preserve enough evidential value while keeping runtime inside a single Modal window.

Action: define a bounded H3 execution tranche before the next remote launch, rather than treating code readiness as launch readiness for the full matrix.

## [2026-03-11T09:41:00-0500] IMPLEMENTATION UPDATE — Trait-Lane Branch Is Now Real But Still Launch-Frozen
**Type:** finding
**Phase:** Week 2 screening branch / Phase 4 core isolation
**Relevance:** clarifies that the new lane-expansion branch is now executable at the planning/dry-run layer without disturbing the active H3 core path.

- `known`: the lane-expansion branch now has a real registry (`trait_lanes_v2.yaml`), family construct cards, and sidecar planning wrappers.
- `observed`: the full-family dry-run packet covers `13` candidate lanes; `10` support extraction-free overlap and `6` support external-transfer smoke.
- `observed`: the held-out namespace audit reports `0` planned prompt collisions under `prompts/trait_lanes_v2/`.
- `inferred`: this is the right stopping point before launch, because it makes the new branch concrete without changing current Week 2 defaults or interfering with the active H3 claim-grade run.

## 2026-03-11 [THEORY] — Correlated-Feature Geometry Is a Future Interpretation Check, Not a Current Method Pivot
**Type:** theory | action
**Phase:** Phase 4 closeout with direct relevance to future Stage 2 / Stage 5 interpretation and writing
**Relevance:** prevents over-reading semantic clustering or shared feature geometry as direct evidence of modular persona circuits

- `known`: Prieto et al. (2026), *From Data Statistics to Feature Geometry: How Correlations Shape Superposition* (`arXiv:2603.09972`), argues that correlated features can form semantic clusters and cyclical structure through constructive interference.
- `known`: the paper’s empirical setting is bag-of-words superposition / tied-weight autoencoders plus small value-coding tasks, not persona steering in an instruction-tuned LLM.
- `inferred`: if future promoted trait-lane work or refreshed Stage 5 analysis shows clustered/shared feature geometry, that pattern is compatible with correlated superposition and should not by itself be upgraded into H1/H4 circuit evidence.
- `inferred`: the appropriate use for this paper in this project is a low-cost geometry-only sidecar diagnostic and a discussion/interpretation citation, not a change to the active H3 or trait-lane execution path.

Action: before the next geometry-facing interpretation freeze after H3 closeout, revisit Prieto et al. and, if cluster/overlap structure is central to the argument, add a sidecar geometry diagnostic or explicit caveat.

## 2026-03-11T14:57:59-0500 [FINDING] — Full-complement H3 collapses to gibberish before it becomes claim-bearing evidence
**Type:** finding
**Phase:** Week 7-8 / Stage 4
**Relevance:** H3 (Causal Sufficiency)

- `known`: the bounded claim-grade H3 tranche on `sycophancy/resample` terminalized with a saved checkpoint and enough completed-dose evidence to interpret the lane.
- `observed`: completed doses `0.25` and `0.50` both fail sufficiency thresholding, collapse the lightweight capability proxy to `0.0`, and drop coherence by `73.2` points relative to steered outputs.
- `observed`: raw output audits at those doses are repetitive strings like `"is is is ..."` and `"::: is is ..."`, not degraded-but-interpretable task behavior.
- `observed`: the run then died at `dose=1.00` on judge parse exhaustion after `65/100` random baseline sets, which is consistent with the same non-evaluable output regime rather than a near-pass state.
- `inferred`: for the current layer/target-set/full-complement setup, the limiting factor is not subtle statistical insufficiency but operationally obvious representational destruction. This is a bounded negative feasibility signal, not just a missing last data point.

## 2026-03-11T15:10:14-0500 [FINDING] — The trait-lane branch now has a real P3 entry point, so the next risk shifts from planning drift to budget discipline
**Type:** finding | action
**Phase:** Week 2 screening branch
**Relevance:** determines how the project broadens beyond the current core lanes without turning trait-lane expansion into another uncontrolled launch surface

- `known`: the branch now has executable prompt-generation wrappers for extraction and held-out data, not just registry/planning sidecars.
- `known`: those wrappers are still namespace-isolated and preserve legacy prompt-generation defaults.
- `inferred`: the primary branch risk is no longer implementation absence; it is overspending or overexpanding too early by running all 13 lanes at once.
- `inferred`: the correct first live slice is a bounded trio spanning distinct non-safety families, so we can validate the generation path and audit quality before multiplying costs and review load.

Action: pre-register one bounded first-generation slice before any API-backed launch, and do not widen beyond that slice until prompt quality and duplicate/leakage checks are inspected.

## 2026-03-11T15:31:04-0500 [FINDING] — The first live trait-lane slice was worth doing because it revealed two branch-specific failure modes immediately
**Type:** finding | action
**Phase:** Week 2 screening branch
**Relevance:** prevents the project from mistaking “new branch exists” for “new branch is scientifically usable”

- `known`: the first live slice (`assistant_likeness`, `honesty`, `politeness`) succeeded only after two concrete corrections: retry/oversampling for category fill, and held-out anti-paraphrase guards plus append-safe filenames.
- `observed`: honesty was the main novelty risk; exact duplicate blocking alone was nowhere near enough for held-out integrity.
- `inferred`: future trait-lane widening should assume lane-specific prompt-generation pathology is normal, not exceptional. The branch needs a reusable audit artifact before it needs more families.

Action: build a reusable generated-prompt audit/manifest step for `trait_lanes_v2` before starting Slice B or promoting any lane into screening claims.

## 2026-03-11T15:33:37-0500 [FINDING] — Slice A passed once the branch had the right safeguards, which is evidence for the process more than for the lanes
**Type:** finding
**Phase:** Week 2 screening branch
**Relevance:** calibrates how much confidence to place in the new branch after the first live slice

- `known`: with retry/oversampling, append-safe reruns, and held-out anti-paraphrase guards in place, the first live slice now passes the generated-prompt audit.
- `inferred`: the strongest conclusion is procedural: the branch can now produce auditable generated inputs under bounded scope.
- `unknown`: whether these three lanes will actually steer well. Prompt-generation success is necessary infrastructure, not positive trait evidence.

## 2026-03-11T16:47:34-0500 [FINDING] — Slice B passing on the first held-out attempt is the first sign the branch process has stabilized
**Type:** finding
**Phase:** Week 2 screening branch
**Relevance:** changes the next bottleneck from “can we generate clean inputs?” to “what is the next cheapest informative screening signal?”

- `known`: Slice B (`persona_drift_from_assistant`, `lying`, `optimism`) passed the generated-prompt audit on its first held-out attempt.
- `inferred`: the retry/oversampling and novelty/no-overwrite fixes were not one-off repairs for Slice A; they generalized.
- `inferred`: the branch no longer needs another prompt-generation-only slice to prove the process works.
- `unknown`: whether extraction-free overlap or tiny behavioral screening will be the better next discriminator for deciding which lanes deserve promotion.

## 2026-03-11T16:59:57-0500 [FINDING] — Slice A extraction-free prep succeeded cleanly, so the next uncertainty is interpretive rather than infrastructural
**Type:** finding
**Phase:** Week 2 screening branch
**Relevance:** narrows the next branch question from “can we prepare extraction-free inputs at all?” to “which branch move gives the best signal per unit effort?”

- `known`: the isolated `trait_lanes_v2` extraction-free wrapper ran successfully for `assistant_likeness`, `honesty`, and `politeness`.
- `observed`: all three lanes used all four available exemplar sets across the 12 prepared rows, so the branch did not collapse into a single fixed few-shot context.
- `observed`: the `honesty` hash allocation is uneven (`7/1/2/2`), which is not a blocker for prep but is worth remembering if Slice A later shows set-sensitive overlap behavior.
- `inferred`: the branch no longer needs more wrapper work before the next real decision; the next question is whether to deepen Slice A with extraction-free evaluation or widen the exemplar-bank work to Slice B.

## 2026-03-11T17:04:36-0500 [FINDING] — With Slice B extraction-free parity in place, the branch is done proving it can prepare inputs and must now earn signal
**Type:** finding
**Phase:** Week 2 screening branch
**Relevance:** marks the transition from bounded dataset preparation to choosing the next discriminative screen for promotion decisions

- `known`: the branch now has extraction prompts, held-out prompts, generated-prompt audits, and extraction-free prep manifests for both live bounded slices (`A` and `B`).
- `observed`: all six live lanes now have extraction-free eval files under `prompts/trait_lanes_v2/extraction_free/`.
- `inferred`: another prompt-prep-only tranche would likely add more branch surface area than information.
- `inferred`: the next useful branch move should be an actual screening/evaluation layer, not a third preparation-only slice.

## 2026-03-11T17:14:05-0500 [FINDING] — The trait-lane branch is now operationally ready, so the next mistake to avoid is more readiness theater
**Type:** finding | action
**Phase:** Week 2 screening branch
**Relevance:** fixes the branch transition point from local preparation artifacts to the first bounded real screening execution

- `known`: the screening-readiness packet reports all six live lanes as `screen_ready=true`.
- `known`: the shared judge path now registers the live lane rubric IDs through `scripts/shared/trait_rubrics.py`.
- `known`: the recommended first actual screening tranche is `slice_a` (`assistant_likeness`, `honesty`, `politeness`).
- `inferred`: the branch no longer needs more preparation-only packets to justify the next move.
- `inferred`: the highest-risk failure mode now is overengineering another sidecar instead of executing a thin real screen on the recommended tranche.

Action: implement the thin actual screening runner for `slice_a` before any Slice C widening or broader branch launch.


## [2026-03-11T18:22:14-0500] finding — Slice A screen separates lane strength from response-phase persistence
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 screening branch
**Relevance:** promotion criteria for the lane-expansion branch

`known`: the first actual `slice_a` screen produced bounded positive smoke evidence for all three lanes (`assistant_likeness`, `honesty`, `politeness`), with honesty and politeness showing materially larger bidirectional effects than assistant_likeness in the 4-prompt smoke. `known`: the same artifact still shows prompt-vs-response position agreement below the legacy `0.7` threshold for all three lanes. `inferred`: the branch now has the same structural tension seen in the core Week 2 line — content-stable extraction can coexist with cross-regime position sensitivity. We need an explicit promotion policy choice on whether response-phase persistence is a hard requirement for new lanes or a tracked limitation.


## [2026-03-11T19:18:30-0500] finding — Two-slice screening makes orientation policy unavoidable
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 screening branch
**Relevance:** determines how promotion ranking should treat sign-flipped lanes

`known`: after Slice A and Slice B, all six screened lanes pass bootstrap robustness and all six have at least one coherence-passing smoke condition, but prompt-vs-response position agreement remains below the legacy `0.7` threshold across the board. `observed`: `persona_drift_from_assistant` selected a negative bidirectional effect while its paired positive-axis lane (`assistant_likeness`) selected a positive effect. `inferred`: the branch can no longer treat all lane scores as living on a single positive-is-better scale. Promotion synthesis now needs an explicit orientation-normalization rule or a pairwise axis policy before any ranking or widening claim is coherent.


## [2026-03-11T19:29:50-0500] finding — The first two-slice promotion packet favors truth/style lanes over broad assistant-axis lanes
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 screening branch
**Relevance:** determines which lanes should get the limited deeper-validation budget next

`known`: the first comparative promotion packet recommends `lying`, `politeness`, and `honesty` as the top follow-on lanes from the two completed screening slices. `known`: both assistant-axis lanes are weaker under the bounded screening criteria: `assistant_likeness` is only a weak-positive hold, while `persona_drift_from_assistant` requires explicit orientation review because its selected configuration mixes one aligned and one misaligned component. `inferred`: the branch is currently surfacing cleaner screening signal in narrower truth/style constructs than in the broader assistant-axis construct family. That matches the original plan note that assistant-likeness is likely a broad persona-space lane rather than a naive high/low trait lane.


## [2026-03-11T19:47:52-0500] finding — Extraction-free follow-on collapses the top-3 packet into one clear winner
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 screening branch
**Relevance:** determines whether the branch should keep spending budget on three lanes or narrow immediately

`known`: the targeted extraction-free follow-on on `lying`, `politeness`, and `honesty` produced only one passing lane: `politeness` (`moderate_overlap`, `mean_cosine=0.2114`, `positive_fraction=1.0`). `known`: `lying` stayed positive but sub-threshold (`mixed_or_fragile`), while `honesty` dropped to `null_overlap`. `inferred`: the original promotion packet was directionally useful but too optimistic about `honesty`; the follow-on evidence suggests the branch should now behave as if `politeness` is the lead lane, `lying` is a conditional backup pending external-smoke evidence, and `honesty` should not receive the same follow-on budget unless a new discriminator revives it. `inferred`: this is the right place to keep the branch narrow rather than widening to more families again.


## [2026-03-11T19:53:36-0500] finding — The truthfulness external-smoke lane now has balanced inputs, so the remaining uncertainty is evaluator worth, not prompt prep
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 screening branch
**Relevance:** decides whether the branch should spend more effort on truthfulness follow-on execution or cut losses after the mixed extraction-free result

`known`: the branch-local external-smoke generator produced `8` prompts each for `honesty` and `lying`, with balanced category coverage across direct factual checks, evidence-pressure prompts, social-conflict prompts, and strategic-concealment prompts. `observed`: manual spot-checks look plausible and not trivially duplicative of the earlier extraction/held-out truthfulness prompts. `inferred`: prompt preparation is no longer a reason to delay the truthfulness external-smoke decision. The remaining question is whether the branch should invest in a thin evaluator for these two lanes or accept the current evidence stack (`lying` fragile, `honesty` weak/null) and stop there.


## [2026-03-11T20:17:34-0500] finding — Truthfulness external smoke weakens the case for both truthfulness lanes rather than rescuing them
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 screening branch
**Relevance:** determines whether the branch should keep allocating follow-on budget to the truthfulness subfamily

`known`: the branch-local external-smoke evaluator failed for both `honesty` and `lying`. `known`: `honesty` still shows one-sided steering on the low-prompt side (`plus_vs_baseline=17.5`) but almost no reversal on the high-prompt side (`baseline_vs_minus=0.125`), so it fails the delta gate even though coherence is fine. `known`: `lying` shows the opposite asymmetry: reversal/suppression works (`baseline_vs_minus=18.375`), but amplification fails (`plus_vs_baseline=-3.125`). `inferred`: the truthfulness subfamily now looks structurally unstable under the branch's follow-on stack. This does not prove the lanes are meaningless, but it does mean they are weaker candidates than `politeness`, which is the only lane that strengthened when we added a second discriminator.


## [2026-03-11T22:06:12-0500] finding — The refreshed branch packet turns the lane-expansion branch from a search problem into a selection problem
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 screening branch
**Relevance:** determines whether the branch should keep screening breadth or begin deeper validation on one or two lanes

`known`: the follow-on-integrated promotion packet now ranks `politeness` as `promotion_candidate_supported`, `lying` as `conditional_followon_candidate`, and `honesty` as `deprioritized_after_followons`. `inferred`: the branch is no longer missing discriminators; it is missing a choice. Additional screening breadth would mostly be procrastination unless we have reason to believe another family can beat `politeness` on cleaner evidence. `inferred`: if the branch continues, the scientifically disciplined move is deeper Week 2 validation for `politeness` first, with `lying` only as a conditional second lane rather than a co-equal winner.

## 2026-03-11T22:18:00-0500 [FINDING] — The trait-lane branch bottleneck has shifted from lane choice to evidence depth
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 deeper-validation planning
**Relevance:** determines whether the next branch step should be another evaluation launch or prompt-depth expansion first

`known`: the deeper-validation packet now selects `politeness` alone by default and records `launch_recommended_now=false` because the lane only has `24` extraction prompts and `12` held-out prompts. `known`: the new branch-local deeper-validation sidecar profile asks for `48` extraction pairs and a `10/10/10` held-out split (`30` total), while the core full-upgrade reference remains `100/50`. `inferred`: the branch is no longer missing discriminators or ranking logic; it is missing data depth. If we launch deeper validation before expanding `politeness`, we are likely to learn more about thin held-out variance than about whether `politeness` deserves upgraded Week 2 treatment.

## [2026-03-12T08:27:00-0500] finding — The distinctness problem has narrowed from sycophancy overlap to assistant-style contamination
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 review-reconciliation tranche
**Relevance:** determines what the next `politeness` validation run can actually claim if it passes

`known`: the overlap diagnostic shows low `politeness` vs `sycophancy` cosine (`selected_pair=0.065`, max abs overlap `0.181`). `known`: the refreshed deeper-validation packet now explicitly routes cross-trait bleed against `sycophancy` and `assistant_likeness`, so the next branch-local validation contract no longer has the earlier interpretive blind spot where bleed was disabled. `inferred`: if `politeness` still looks strong after this branch-local bleed is measured, the remaining conceptual risk is not "secretly sycophancy" but "assistant-style / tone-transfer rather than persona-level structure." That is a sharper and more useful claim boundary than the branch had before the review.

## [2026-03-12T13:52:00-0500] finding — Politeness survives deeper validation behaviorally but collapses on assistant-style distinctness
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 deeper-validation branch
**Relevance:** decides whether `politeness` can be promoted as an independent persona lane or only as an assistant-style modulation lane

`known`: the split `politeness` deeper-validation rerun completed with a strong selected-test effect (`layer 13`, `alpha 2.0`, bidirectional effect `46.3333`), strong judge calibration (`kappa=0.8387`), coherence pass under the frozen relative-only policy, capability pass, and specificity pass. `known`: the same artifact fails overall because cross-trait bleed against `assistant_likeness` is slightly larger than the target-lane effect itself (`47.2333` vs `46.3333`, ratio `1.0194`), and the control-test gate stays high (`50.0`). `inferred`: the main remaining story for `politeness` is not weak steering; it is non-distinct steering. If we continue to treat it as a candidate independent persona lane, we need a stronger argument than the current branch evidence provides.

## [2026-03-12T14:28:59-0500] finding — The trait-lane branch succeeded as triage, not as promotion
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 adjudication
**Relevance:** closes the current branch question of whether any new lane should be promoted into the main persona-circuit claim path

`known`: the branch found one strong behavioral lane (`politeness`) and successfully pushed it through deeper validation, but the completed evidence stack still does not support independent promotion because assistant-style bleed and control failure dominate the final interpretation. `known`: `lying` now reads as construct-invalid under the current protocol, while `honesty` survives only as a secondary unresolved RLHF-asymmetry lane. `inferred`: the branch did useful scientific work by narrowing the search space and identifying the right confound, but it did not discover a clean new persona lane.

## [2026-03-12T14:49:47-0500] finding — The redesign tranche is now concrete enough to test the branch rather than debate it
**Type:** finding
**Phase:** Week 2 / trait_lanes_v2 redesign
**Relevance:** sets the next falsification-first branch sequence after promotion was frozen

`known`: the branch now has explicit artifacts for the two missing controls the review identified: a matched null-control screen over the `politeness` prompt family and a bounded prompt-sensitivity sidecar at the selected configuration. `inferred`: this is the right shift in posture. The branch does not need more ranking or more widening; it needs evidence about false positives and wording fragility.

## [2026-03-12T15:16:00-0500] [FINDING] — The null-control semantics only become real once polarity is flipped, not merely re-paired
**Type:** finding
**Phase:** Week 2 / Trait-lane redesign
**Relevance:** This directly affects whether the null-lane control is a valid falsification test for branch screening permissiveness.

`known`: for `politeness`, every row shares the same two system prompts, so a naive “shuffle pairings” control would have been functionally identical to the source lane. `inferred`: the only matched control that actually destroys the contrast while preserving prompt text/rubric is a row-level polarity flip within category. This is a good example of why control plans need execution-level semantics, not just design-language symmetry.

## [2026-03-12T15:32:30-0500] [FINDING] — The trait-lane screen is not generically permissive; the `politeness` null fails on stability before it ever resembles a promotable lane
**Type:** finding
**Phase:** Week 2 / Trait-lane redesign
**Relevance:** This directly sharpens the interpretation of the branch: the main remaining risk is distinctness, not a trivially easy screening pipeline.

`known`: the matched label-permutation null for `politeness` finishes with `screening_status=hold` and `overall_false_positive_alert=false`. `known`: its absolute smoke effect can still reach `14.25` on `n=4`, but that sits on top of catastrophic stability metrics (`bootstrap_p05 < 0`, `train_vs_heldout ~0.25`, response persistence ~`0.28`). `inferred`: the screening pipeline is not so permissive that any contrastive direction gets promoted; the real concern stays where the reviewer pushed us: assistant-style overlap and wording sensitivity for the real lane.
