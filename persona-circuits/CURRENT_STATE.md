# Current State

**Last updated:** 2026-03-12T14:49:47-0500
**Updated by:** codex-gpt5 (session024, continuation)  
**Status:** in_progress  
**Current phase:** Phase 4 — Causal Validation (Week 7-8)

## Active Phase

Phase 4 is active. Week 1 infrastructure milestone is closed with a pass, Week 2 is closed under proposal-compatibility with explicit caveats recorded in `DECISIONS.md` (2026-03-03T14:00:00-0600), Stage3 attribution runs are completed for initial target freeze, and Stage4 behavioral necessity follow-up now includes calibration/full-depth/tranche sensitivity plus a policy lock to dual-scorecard interpretation while preserving strict-fail status as primary.

- `known`: the bounded H3 claim-grade sufficiency tranche is terminalized:
  - app: `ap-mCOxAI9Xp7WCZoxpslD6Yi`
  - lane: bounded H3 claim-grade sufficiency tranche (`sycophancy`, `resample`, `full_sae_complement`)
  - terminal state: `stopped`
  - scoped closeout artifact: `results/stage4_ablation/week3_stage4_behavioral_sufficiency_claimgrade_trancheA_closeout_20260311T1919Z.json`
- `known`: the bounded H3 tranche is now closed as a scoped negative feasibility signal, not a positive claim-bearing H3 result:
  - completed doses `0.25` and `0.50` both fail sufficiency thresholding and collapse coherence/capability
  - raw output audits show degenerate repetitive text under full-complement circuit-only execution
  - `dose=1.00` did not finish; the runner stopped on judge parse exhaustion after `65/100` random baseline sets
  - default next action is `no immediate rerun`
- `known`: sequencing is now explicitly locked as follows:
  - bounded H3 tranche is considered scoped-closed without widening into a larger matrix by default
  - the next active execution branch becomes the trait-lane expansion screening line (`trait_lanes_v2`)
- `known`: the trait-lane expansion plan has now been re-read against existing Week 2 infrastructure and active-run state; no structural duplication or unsafe core-path mutation was found in the planned first tranche.
- `known`: the first non-invasive trait-lane implementation tranche is complete and remains local-only:
  - registry/config: `configs/trait_lanes_v2.yaml`, `scripts/shared/trait_lane_registry.py`
  - construct cards: `history/construct_cards/*.md`
  - dry-run sidecars: `week2_trait_lane_{prompt_screen,heldout_screen,behavioral_smoke,promotion_packet}_20260311T143658Z.json`
  - branch status: ready for first real screening execution; no lane-expansion Modal job has been launched yet
- `known`: the second local-only trait-lane implementation tranche is now complete:
  - shared generation helper: `scripts/shared/trait_lane_generation.py`
  - extraction generator wrapper: `scripts/week2_trait_lane_generate_extraction_prompts.py`
  - held-out generator wrapper: `scripts/week2_trait_lane_generate_heldout_prompts.py`
  - validation test: `tests/test_trait_lane_generation.py`
  - dry-run generation artifacts:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_plan_20260311T200659Z.json`
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_plan_20260311T200659Z.json`
  - branch status: real prompt-generation is now tooling-ready under the new namespace, with legacy Week 1/2 prompt files still untouched
- `known`: the first live `trait_lanes_v2` P3 slice has now executed for the bounded trio `assistant_likeness`, `honesty`, `politeness`:
  - extraction summary artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_summary_20260311T201829Z.json`
  - held-out summary artifact (provisional): `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_summary_20260311T202524Z.json`
  - held-out summary artifact (retry01, superseding): `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_summary_20260311T203019Z.json`
  - extraction prompt files: `prompts/trait_lanes_v2/{assistant_likeness,honesty,politeness}_pairs.jsonl`
  - held-out prompt files now preferred for review/use: `prompts/trait_lanes_v2/heldout/*_heldout_pairs_retry01.jsonl`
- `observed`: exact duplicate counts are zero within all six generated files in the bounded slice.
- `observed`: held-out lexical-overlap audit improved materially after the retry01 patch:
  - `assistant_likeness`: `max~0.586`, `mean~0.428`
  - `honesty`: `max~0.693`, `mean~0.516` (down from provisional `max~0.99`, `mean~0.65`)
  - `politeness`: `max~0.465`, `mean~0.386`
- `known`: Slice A now has a formal generated-prompt audit artifact:
  - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_generated_prompt_audit_20260311T203324Z.json`
  - `overall_pass=true` under the slice-level screening checks (no within-file duplicates, no exact repo collisions, held-out/extraction max lexical similarity `<0.80`)
- `known`: Slice B is now also complete and formally audited for the bounded trio `persona_drift_from_assistant`, `lying`, `optimism`:
  - extraction summary: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_summary_20260311T214555Z.json`
  - held-out summary: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_summary_20260311T214716Z.json`
  - audit artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_generated_prompt_audit_20260311T214720Z.json`
- `observed`: Slice B passes on the first held-out attempt with no corrective rerun:
  - `persona_drift_from_assistant`: `max~0.529`, `mean~0.404`
  - `lying`: `max~0.577`, `mean~0.429`
  - `optimism`: `max~0.646`, `mean~0.473`
- `inferred`: the generation + novelty/audit path now appears stable across more than one slice, which lowers the risk of widening the branch further.
- `known`: a new trait-lane expansion branch is now defined at planning level only:
  - literature refresh: `history/20260311-trait-lane-literature-refresh-v1.md`
  - execution plan: `history/20260311-trait-lane-expansion-plan-v1.md`
  - launch policy: H3 terminalization condition is now satisfied; branch advancement can proceed without reopening the bounded H3 tranche
- `known`: Prieto et al. (2026) / `correlations-feature-geometry` has now been assessed and logged as an interpretation-sidecar reference only:
  - no change to active H3 sequencing, thresholds, or the post-H3 `trait_lanes_v2` branch order
  - future revisit point: after H3 closeout, if promoted trait-lane or Stage5 interpretation begins relying on clustered/shared feature geometry

### Week 1 Milestone Closeout (proposal §10.2)

- Milestone: `Infrastructure ready` (models load, SAEs work, prompts ready)
- Final decision: `GO / PASS`
- Evidence:
  - Strict prompt audit report: `results/infrastructure/week1_prompt_audit_report.json` (`overall_pass=true`, `known`)
  - Manual random prompt spot-checks performed after re-generation (`known`)
  - Prompt-generation and audit filters hardened via shared rule module (`scripts/prompt_quality_rules.py`) and re-run (`known`)

### Week 2 checklist status (proposal §10.1)

**Days 1–3:**
- [x] Implement contrastive extraction pipeline
  - Script: `scripts/week2_extract_persona_vectors.py`
- [x] Extract persona vectors for all 3 traits on Llama-3.1-8B-Instruct
  - Runs: `https://wandb.ai/sohailm/persona-circuits/runs/mud40b2t` (initial), `https://wandb.ai/sohailm/persona-circuits/runs/u6od5uxx` (cosine-margin backfill rerun)
  - Artifacts: `results/stage1_extraction/week2_vector_extraction_summary_20260225T170852Z.json`, `results/stage1_extraction/week2_persona_vectors_20260225T170852Z.pt`
- [x] Identify optimal layers per trait (behavioral criterion)
  - Final Week2 selected primary claim layers: sycophancy=`12`, evil/machiavellian=`12`; hallucination=`13` is retained only as exploratory negative-control lane.
  - Evidence: `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T220017Z.json`, `results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json`

**Days 4–7:**
- [x] Implement behavioral validation suite (Claude Sonnet 4.6 judge)
  - Script: `scripts/week2_behavioral_validation.py`
  - Includes: steering+reversal alpha sweep, cross-rater kappa, specificity/control checks, prompt-hash traceability
- [x] Implement upgraded Week 2 validation pipeline (strict calibration + broad sweep planning)
  - Runner: `scripts/week2_behavioral_validation_upgrade.py`
  - Planner: `scripts/week2_upgrade_parallel_plan.py`
  - Adds: strict JSON judge parsing + parse-fail gate, directionality calibration, coherence gate, sweep/confirm split, full-layer broad alpha sweep support, multi-random/shuffled controls with p95 separation, cross-trait bleed matrix, API throttle+retry backoff, seed override for replications
  - Latest hardening (2026-02-25): secondary parse-pass is now required, non-trait control-test and specificity now have hard gates, capability proxy is required by default unless explicitly overridden (`--allow-missing-capability-proxy`), hallucination includes both TruthfulQA known-fact directional and objective MC checks, lockbox split is now sweep/confirm/test with headline gates on test, controls use larger null distributions (`random_control_vectors>=64`, `shuffled>=10` in primary plan), and rollout-stability support is added via multi-rollout averaging (`sweep=3`, `confirm=3`, `baseline=3`, `rollout_temperature=0.7` defaults)
  - Added steering magnitude diagnostics: `steering_norm_diagnostics` now includes ratio distributions (`mean/median/p90/p95/max/min`), threshold exceedance fractions, and max-ratio warnings (injection norm vs residual norm at selected layer/alpha)
  - Additional control-validity patch: null controls are now norm-matched to selected steering-vector magnitude and logged (`controls.selected_direction_norm`, `controls.control_direction_norm`)
  - Additional pre-launch tightening patch: enforce `cross_rater_samples <= test_prompts` (no silent calibration truncation), default cross-rater now aligned to test split (`20`), and launch-script phase filter defaults to `primary`
  - Planning artifacts: `results/stage1_extraction/week2_upgrade_parallel_plan_20260225T141045Z.json`, `scratch/week2_upgrade_launch_commands.sh`, `scratch/week2_upgrade_rerun_commands_20260226.sh`
- [ ] Validate all 3 persona vectors (steering works)
  - Status: primary rerun tranche completed and ingested deterministically.
  - `known` primary artifacts:
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260227T191157Z.json`
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260227T171643Z.json`
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_hallucination_20260227T164544Z.json`
  - `known` ingestion summary: `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T202336Z.json`
    - sycophancy selected `(12, 3.0)`, `section623_pass=true`, `runner_overall_pass=false`
    - evil selected `(12, 3.0)`, `section623_pass=true`, `runner_overall_pass=false`
    - hallucination selected `(13, 3.0)`, `section623_pass=false`, `runner_overall_pass=false`
  - `known` post-primary closeout checks completed:
    - manual concordance: `results/stage1_extraction/week2_primary_manual_concordance_ratings_20260227T202822Z.json` (`mean_trait_mae=4.744`, pass vs 20-point guideline)
    - gap checks rerun on primary-selected combos: `results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json` (`overall_pass=false`)
  - Current blocker for advancing replication/stress: extraction-method robustness A/B gate remains failed for all traits; evil external transfer directional gate still fails.
- [ ] Document optimal steering coefficients
- [ ] Log all vectors and metrics to W&B
  - Partial: extraction vectors logged in `mud40b2t`; behavioral metrics logged in `8b3fp37q` but not accepted for closeout

### Week 2 data-quality and traceability status

- Held-out prompt sets regenerated and fully audited for all traits:
  - `results/stage1_extraction/week2_heldout_prompt_audit_report.json` (`overall_pass=true`)
- Extraction-vs-heldout overlap check: 0 exact normalized overlaps for all traits (`known`)
- Prompt manifest created:
  - `results/stage1_extraction/week2_heldout_prompt_manifest_20260225T040156Z.json`
- One behavioral run (`f41g19g9`) was intentionally invalidated after prompt-file mutation mid-run; rerun launched on frozen audited set.
- Frozen rerun completed (`8b3fp37q`) with traceable prompt hashes, but validation quality gates failed (judge consistency + hallucination parseability).
- Exhaustive second-pass methodology review completed and archived:
  - `results/stage1_extraction/week2_literature_second_pass_20260225T120710Z.md`
- Third-pass critical methodology audit completed and archived:
  - `results/stage1_extraction/week2_literature_third_pass_20260225T123439Z.md`
- Gap-focused literature addendum (rollout stability + norm diagnostics) completed and archived:
  - `results/stage1_extraction/week2_gap34_literature_addendum_20260225T130737Z.md`
- Prelaunch Week 2 gap-check run (external transfer + extraction-method A/B) completed after remote path fix:
  - Completed artifact: `results/stage1_extraction/week2_prelaunch_gap_checks_20260225T131521Z.json`
  - Outcome: overall gate fail (`all_traits_external_transfer_pass=false`, `all_traits_extraction_ab_similarity_pass=false`)
- Parallel-safe review-feedback hardening completed while primary tranche remained in-flight:
  - Added extraction-time diagnostics in `scripts/week2_extract_persona_vectors.py`: cross-trait cosine matrix by layer, norm-aware margin diagnostics (`projection_margin_mean_normalized_by_pair_avg_activation_norm`, `cosine_margin_mean`), and alternate `prelim_best_layer_by_cosine_margin`.
  - Added local diagnostics runner `scripts/week2_vector_diagnostics.py`.
  - Backfill artifact generated from existing vectors: `results/stage1_extraction/week2_vector_diagnostics_20260225T152342Z.json` (`known`: no cross-trait pair exceeded `|cos| >= 0.6` threshold in this artifact).
  - Added Week 2 utility tests: `tests/test_week2_extract_vector_utils.py`, `tests/test_week2_validation_utils.py`.
- Additional pre-primary review tranche completed (no primary relaunch):
  - Evil validity audit artifact: `results/stage1_extraction/week2_evil_trait_audit_20260225T160326Z.json` (`known`: high-risk profile, `n_flags=6`, external `plus_vs_minus=-0.75`, manual refusal-invariance `0.8`).
  - Extraction-free prompt prep artifact: `results/stage1_extraction/week2_extraction_free_prompt_manifest_20260225T160326Z.json` (50 eval rows/trait, neutral system prompt + few-shot high/low contexts).
  - Held-out expansion plan artifact: `results/stage1_extraction/week2_heldout_expansion_plan_20260225T160326Z.json` (proposed 150/trait split with estimated SE reduction/load multiplier).
  - Week3 SAE reconstruction pre-audit artifact: `results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T160326Z.json` (`known`: reconstruction cosines below threshold in infra checks; instruct/base mismatch confirmed).
  - Added held-out generation scaling controls in `scripts/generate_week2_heldout_prompts.py` (`--scale-factor`, `--target-per-trait`, `--dry-run-plan`) with plan emitted at `scratch/week2_heldout_prompt_generation_plan.json`.
  - Expanded local tests to 23 passing (`python3 -m unittest discover -s tests`), including new held-out scaling coverage (`tests/test_week2_heldout_scaling.py`) and steering-sign/retry helper checks.
- Continued hardening pass completed (no primary relaunch):
  - Extraction-free prompt prep now supports versioned output files (no overwrite): `scripts/week2_prepare_extraction_free_eval.py --output-suffix ...`.
  - New rotated-set manifest generated: `results/stage1_extraction/week2_extraction_free_prompt_manifest_20260225T163517Z.json` with prompt files `prompts/heldout/*_extraction_free_eval_v2_rotating_20260225.jsonl`.
  - New execution-grade extraction-free evaluator added: `scripts/week2_extraction_free_activation_eval.py` (few-shot high/low activation deltas compared to existing system-prompt vectors; set-variance gates included).
  - Evil audit refusal classification upgraded from prefix regex to full-response profiling with mixed refusal+compliance detection; refreshed artifact: `results/stage1_extraction/week2_evil_trait_audit_20260225T163523Z.json`.
  - Week3 SAE reconstruction investigation script added and executed via Modal (`scripts/week3_sae_reconstruction_investigation.py`; app `ap-Q9eYKHJZbbY2FCW9Wha3eg`), producing artifact `results/stage2_decomposition/week3_sae_reconstruction_investigation_20260225T164322Z.json`.
  - Observed reconstruction outcome (`known`): both base and instruct fail at layer16 with very similar median reconstruction cosine (`~0.126` vs `~0.127`); extreme negative explained variance suggests a preprocessing/normalization mismatch risk beyond simple instruct/base distribution shift.
  - Local tests expanded to 31 passing (`python3 -m unittest discover -s tests`) with new coverage for extraction-free prep and evil refusal profiling (`tests/test_week2_prepare_extraction_free_eval.py`, `tests/test_week2_evil_trait_audit.py`).
- Follow-up hardening lane completed (no primary relaunch):
  - Root-cause reconstruction probe executed via Modal (`scripts/week3_sae_reconstruction_root_cause.py`; app `ap-mTwL7r4snV4BQd7C5btNFt`), artifact: `results/stage2_decomposition/week3_sae_reconstruction_root_cause_20260225T170255Z.json`.
  - `known`: SAE cfg snapshot reports `expected_hook_name=null`, `normalize_activations=none`; no hook-name delta evidence was available.
  - `known`: reconstruction is strongly path-dependent:
    - `raw_seq` remains catastrophic (`median_cos~0.126/0.127`, `EV<<0`, `L0~1517/1889`).
    - `last_token` is substantially better (`median_cos~0.82/0.77`, `EV~0.67/0.57`, `L0~31/29`).
  - `known`: cosine-margin null gap is resolved by rerunning extraction (`run=u6od5uxx`, app `ap-zgOoSUWY6gDqdHGQfH5KCd`), producing:
    - `results/stage1_extraction/week2_vector_extraction_summary_20260225T170852Z.json`
    - `results/stage1_extraction/week2_persona_vectors_20260225T170852Z.pt`
    - `results/stage1_extraction/week2_vector_diagnostics_20260225T170928Z.json` (`cosine_margin_from_summary=known`).
  - `known`: initial `evil` replacement decision (2026-02-25T11:08:23-0600) is now scope-superseded by 2026-02-25T11:50:12-0600 reframing: harmful-content claims remain disconfirmed, while `machiavellian/manipulative disposition` is reopened as a Week 3 candidate axis.
  - `known`: primary app IDs remain active after these runs; no replacement primary launches were performed.
  - `known`: extraction-free activation eval was executed via Modal app `ap-ueBHf5QMX2Vb45ROBxySK5`, artifact `results/stage1_extraction/week2_extraction_free_activation_eval_20260225T173752Z.json`, with `overall_pass=false`.
  - `known`: extraction-free gate outcomes by trait:
    - sycophancy: fails `mean_cosine` and `set_std_ratio`; passes `positive_fraction` and `projection_delta`.
    - evil: fails `mean_cosine` and `set_std_ratio`; passes `positive_fraction` and `projection_delta`.
    - hallucination: fails `mean_cosine`, `positive_fraction`, `projection_delta`, and `set_std_ratio`.
  - `known`: extraction-free reanalysis using overlap-gradient policy completed via `scripts/week2_extraction_free_reanalysis.py`, artifact `results/stage1_extraction/week2_extraction_free_reanalysis_20260225T174958Z.json`.
  - `known`: reanalysis trait gradient:
    - sycophancy: weak positive overlap (`mean_cos=0.129`, `positive=0.96`, sign-test p `~2.27e-12`, pass under recalibrated policy).
    - evil: moderate positive overlap (`mean_cos=0.223`, `positive=1.00`, sign-test p `~1.78e-15`, pass under recalibrated policy).
    - hallucination: null overlap (`mean_cos=-0.006`, `positive=0.44`, sign-test p `~0.48`, fail under recalibrated policy).
  - `known`: extraction-free evaluator gate policy was upgraded in both local + Modal scripts (`v2_overlap_gradient`): `mean_cosine>=0.1` + required `set_mean_cv<=0.8`; legacy `set_std_ratio` is now diagnostic only.
  - `known`: `evil` is reopened for Week3 candidacy under reframed axis `machiavellian/manipulative disposition`; harmful-content transfer remains a negative finding for the old framing.
  - `known`: Week2/Week3 config-authority + reproducibility hardening completed locally:
    - alpha defaults are now config-authoritative in upgraded Week2 runner (`steering.coefficients` from `experiment.yaml`).
    - Week3 reconstruction scripts now consume config seed schedule (`primary + replication`) by default when no explicit seed override is provided.
  - `known`: Stage2 audit was upgraded from placeholder `pending` checks to computed gate outputs and rerun:
    - prior artifact (superseded): `results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T180446Z.json` (overlap precondition fail).
    - intermediate artifact (superseded): `results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T181955Z.json` (legacy pass before claim-layer tightening).
    - current artifact: `results/stage2_decomposition/week3_sae_reconstruction_audit_20260301T033046Z.json`.
    - gate summary (current): claim-layer multi-seed policy now fails (`token_gate=fail`, `cross_source_claim_layer_overlap=fail`, `seed_schedule=pass`).
  - `known`: Stage3/4 dry-run scaffold artifact now exists:
    - `results/stage3_attribution/week3_stage34_pipeline_scaffold_20260225T180446Z.json`
    - includes required ablation modalities (`resample/mean/zero`), random same-size baseline sample count wiring (`100`), and concentration/effect-size/selectivity schema targets.
  - `known`: Week2 post-run closeout automation script added:
    - script: `scripts/week2_primary_postrun_ingest.py`
    - preflight artifact: `results/stage1_extraction/week2_primary_postrun_ingestion_20260225T182017Z.json` (`resolved_traits=[sycophancy]`, pending primary artifacts for `evil/hallucination`).
  - `known`: New shared metrics utility added (`scripts/circuit_metrics.py`) covering concentration (Gini/entropy/top-p mass) and causal-effect stats (Cohen's d, A12, bootstrap CIs, random-baseline selectivity), with unit tests.
  - `known`: local test suite now passes at `52` tests.
- Post-patch smoke check for upgraded runner (after `top_k=None` generation fix) completed successfully:
  - Modal app: `ap-12Do4tY1DwxrIafMY9lWtr`
  - W&B run: `i1pg2y8c`
  - Artifact: `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260225T131007Z.json` (execution smoke only; tiny-sample gates not used for scientific closeout)
- Post-reviewer patch smoke check (strict parser + lockbox + bleed gate + control norm matching) completed successfully:
  - Modal app: `ap-ICdOlw6drTUL50qWgc6edW`
  - W&B run: `j48ylybc`
  - Artifact: `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260225T135828Z.json` (execution smoke only; tiny-sample gates not used for scientific closeout)
## Primary Closeout Snapshot

- [2026-02-27T14:23:36-0600] `known`: deterministic ingestion applied with explicit trait map:
  - `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T202336Z.json`
  - `section623_all_pass=false`, `runner_overall_all_pass=false`
- [2026-02-27T14:53:37-0600] `known`: manual 5-example/trait judge concordance spot-check completed:
  - `results/stage1_extraction/week2_primary_manual_concordance_ratings_20260227T202822Z.json`
  - `mean_trait_mae=4.744`, `mean_trait_delta_sign_agreement_rate=0.867`, guideline pass (`<=20`)
- [2026-02-27T14:53:37-0600] `known`: prelaunch gap checks rerun on primary-selected combos completed:
  - `results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json`
  - `overall_pass=false`
  - external transfer: pass for `sycophancy` + `hallucination`, fail for `evil` directional criterion
  - extraction method A/B similarity: fail for all three traits (`method_cosine_similarity < 0.7`)
- [2026-02-27T15:31:15-0600] `known`: explicit closeout decision logged:
  - `DECISIONS.md` entry `DECISION: Week 2 closeout is NO-GO for replication/stress launches under current gate policy`
  - replication/stress launches are blocked pending remediation evidence and a new decision entry.
- [2026-02-27T15:32:52-0600] `known`: reviewer reconciliation scaffolding is now logged and frozen before remediation:
  - verbatim review logs:
    - `history/reviews/20260227-reviewer1-verbatim.md`
    - `history/reviews/20260227-reviewer2-verbatim.md`
  - remediation plan:
    - `history/20260227-week2-remediation-master-plan-v1.md`
  - completion checklist:
    - `history/20260227-reviewer-reconciliation-checklist-v1.md`
- [2026-02-27T15:57:18-0600] `known`: WS-A governance freeze implementation completed:
  - dual-scorecard ingestion artifact: `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T220017Z.json`
  - scorecards disagree (`proposal_continue=true`, `hardening_runner_all=false`, `scorecard_disagreement=true`).
- [2026-02-27T16:19:49-0600] `known`: WS-B extraction-position small-run completed after remote payload fix:
  - app: `ap-TpixiBPB3LEILoVRUZiV77`
  - artifact: `results/stage1_extraction/week2_extraction_position_ablation_20260227T221817Z.json` (superseded by expanded run below)
  - `observed` summary: no trait/layer reaches `prompt_last_vs_response_mean >= 0.7`; means are `sycophancy=0.490`, `evil=0.483`, `hallucination=0.343`.
- [2026-02-27T16:53:52-0600] `known`: WS-B extraction-position expanded run completed (`50` pairs/trait):
  - app: `ap-jE51jRViY2RdepUgmT3Fe4`
  - artifact: `results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json`
  - `observed` summary:
    - prompt-last vs response-mean remains below `0.7` for all traits/layers
      - sycophancy mean `0.496`, evil mean `0.507`, hallucination mean `0.420`
    - response-mean vs response-last is high for sycophancy/evil (`~0.75/~0.74`) but low for hallucination (`~0.33`).
- [2026-02-27T16:55:11-0600] `known`: WS-C constrained-selection implementation is now in code:
  - config policy added: `configs/experiment.yaml` -> `steering.combo_selection_policy=smallest_feasible_alpha`
  - runner now selects smallest feasible alpha on confirm set (fallback to max bidirectional only when no combo meets feasibility threshold): `scripts/week2_behavioral_validation_upgrade.py`
  - unit coverage added for selection-policy parsing/behavior in `tests/test_week2_validation_utils.py`.
- [2026-02-27T16:59:57-0600] `known`: extraction-method policy for WS-C reruns is frozen to prompt-last vectors (response-mean extraction deferred as separate sensitivity lane) to avoid alpha+extraction confounding in the same tranche.
- [2026-02-28T07:12:29-0600] `known`: WS-C targeted lower-alpha reruns completed for sycophancy + evil:
  - sycophancy artifact: `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260228T070200Z.json`
    - selected `(layer=12, alpha=2.0)`, `overall_pass=false` (failed: coherence, cross-trait bleed)
  - evil artifact: `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260228T131128Z.json`
    - selected `(layer=12, alpha=2.0)`, `overall_pass=false` (failed: coherence only)
  - combined summary: `results/stage1_extraction/week2_alpha_constrained_selection_20260228T131217Z.json`
    - `observed`: lower alpha reduces bidirectional effect substantially for both traits and does not clear coherence gate.
- [2026-02-28T20:56:20-0600] `known`: WS-B response-mean sensitivity lane completed (sycophancy + evil at layer12):
  - response-mean extraction artifacts:
    - `results/stage1_extraction/week2_vector_extraction_summary_20260228T135004Z.json`
    - `results/stage1_extraction/week2_persona_vectors_20260228T135004Z.pt`
  - response-mean behavioral reruns:
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260228T202943Z.json`
      - selected `(12, 2.0)`, `overall_pass=false` (failed: coherence only; cross-trait bleed now passes)
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260301T025504Z.json`
      - selected `(12, 2.0)`, `overall_pass=false` (failed: coherence only; bidirectional effect increased vs prompt-last constrained)
  - synthesis artifact:
    - `results/stage1_extraction/week2_response_mean_sensitivity_20260301T025554Z.json`
    - `known`: method switch improves some gate/effect metrics, but coherence remains failing for both traits.
- [2026-02-28T21:32:52-0600] `known`: WS-D trait-scope resolution artifact completed:
  - `results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json`
  - outcome summary:
    - hallucination status: `negative_finding_stage1`
    - evil harmful-content lane: `disconfirmed_bidirectional_harmful_content`
    - evil machiavellian lane: `supported_but_week2_not_validated_due_to_coherence`
  - stage2 scope recommendation in artifact: primary claim traits `sycophancy + machiavellian_disposition`; hallucination retained as exploratory control.
- [2026-02-28T21:32:53-0600] `known`: WS-E claim-layer + multi-seed Stage2 gate-integrity tranche executed:
  - multi-seed investigation artifact: `results/stage2_decomposition/week3_sae_reconstruction_investigation_20260301T031743Z.json`
  - multi-seed root-cause artifact: `results/stage2_decomposition/week3_sae_reconstruction_root_cause_20260301T033002Z.json`
  - updated audit artifact: `results/stage2_decomposition/week3_sae_reconstruction_audit_20260301T033046Z.json`
  - updated audit outcome: `stage2_readiness_gate=fail` with required checks now including claim-layer coverage/probe coverage/cross-source overlap/seed-schedule consumption.
  - failure details:
    - token gate fail at layer12 (`min median_cos=0.7047`, `min median_EV=0.4765`),
    - cross-source overlap fail on claim layer12 (`overlap=[]`),
    - seed schedule consumed pass (`[42,123,456,789]`).
- [2026-03-02T12:02:39-0600] `known`: construct-aligned external transfer lane executed for `evil` (machiavellian disposition framing):
  - app: `ap-WpFtvzibtVhyAgKCH582XN`
  - artifact: `results/stage1_extraction/week2_machiavellian_external_transfer_20260302T180239Z.json`
  - outcome: `overall_pass=true` with plus/base/minus directional gates all passing at selected `(layer=12, alpha=3.0)`.
- [2026-03-02T12:26:12-0600] `known`: WS-F extraction seed replication completed (prompt-last, layer12, seeds `[42,123,456,789]`):
  - app: `ap-slznNP0DpuJxj3imvg6M0r`
  - artifact: `results/stage1_extraction/week2_extraction_seed_replication_20260302T180612Z.json`
  - outcome: `trait_pass={sycophancy:true, evil:true}`, `overall_pass=true` at min pairwise cosine threshold `0.7`.
- [2026-03-02T17:46:10-0600] `known`: WS-F rollout-depth runs were pivoted to detached-resume mode after attached-session interruption risk was observed:
  - sycophancy attached app `ap-CU86fvnqVzHNTiECWoKd4m` stopped due local client disconnect (partial checkpoint at `controls_random_progress`).
  - detached resume apps now active:
    - sycophancy: `ap-j87Kw5fwW1yYn6WmxvAd6z`
    - evil: `ap-vJsFv6H7b0X5vof3Dm36xb`
  - checkpoint evidence indicates resume state is loaded (not restarted): sycophancy contains `controls` state; evil contains `sweep` state.
- [2026-03-03T06:13:20-0600] `known`: WS-F rollout-depth reruns reached terminal checkpoint stage (`final_report_written`) and comparison artifact is complete:
  - rollout5 artifacts:
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json`
    - `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260303T081318Z.json`
  - rollout3 vs rollout5 comparison:
    - `results/stage1_extraction/week2_rollout_stability_sensitivity_20260303T121253Z.json`
  - `observed` summary:
    - sycophancy: bidirectional effect is stable (`33.68 -> 34.15`), `overall_pass` remains false due coherence.
    - evil: bidirectional effect decreases (`47.80 -> 42.55`), `overall_pass` remains false due coherence.
- [2026-03-03T06:20:30-0600] `known`: documentation reconciliation for WS-D/WS-F tranche is synced:
  - `results/RESULTS_INDEX.md` now registers:
    - rollout5 sycophancy artifact (`20260303T082321Z`)
    - rollout5 evil artifact (`20260303T081318Z`)
    - rollout stability sensitivity artifact (`20260303T121253Z`)
  - reviewer checklist updated: `history/20260227-reviewer-reconciliation-checklist-v1.md`
    - resolved: `R1-F5`, `R2-C4`, `R2-G3`, `R2-G6`, `R2-G7`
  - governance update logged: `DECISIONS.md` entry `2026-03-03T06:18:30-0600` (WS-F complete, NO-GO not superseded automatically).
- [2026-03-03T06:24:10-0600] `known`: integrated remediation reassessment decision is now logged and reaffirms Week2 NO-GO:
  - decision entry: `DECISIONS.md` (`DECISION: Reaffirm Week2 NO-GO after WS-D/WS-F completion`)
  - summary: WS-D/WS-F evidence is complete but insufficient for gate supersession; replication/stress remains blocked.
- [2026-03-03T07:16:00-0600] `known`: second-pass reviewer reconciliation is now logged with raw-source preservation and a structured plan artifact:
  - verbatim logs:
    - `history/reviews/20260303-reviewer1-second-pass-verbatim.md`
    - `history/reviews/20260303-reviewer2-second-pass-verbatim.md`
  - reconciliation analysis artifact:
    - `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T131331Z.json`
  - checklist status correction:
    - `R2-G6` downgraded from resolved -> partial (determinism evidence confirmed; stochastic robustness still open)
- [2026-03-03T07:39:20-0600] `known`: P0 policy tranche + schema bugfix tranche are now implemented with fresh artifacts:
  - coherence policy mode instrumentation + diagnostic:
    - config: `configs/experiment.yaml` (`steering.coherence_gate_mode`)
    - artifact: `results/stage1_extraction/week2_coherence_policy_diagnostic_20260303T132222Z.json`
    - summary: strict mode (`absolute_and_relative`) passes `0/2`; relative-only passes `2/2`.
  - Stage2 split-gate policy instrumentation:
    - config: `configs/experiment.yaml` (`governance.week3_stage2_policy`)
    - artifact: `results/stage2_decomposition/week3_sae_reconstruction_audit_20260303T132222Z.json`
    - summary: `stage2_decomposition_start_gate=fail` (token gate), `stage2_cross_source_claim_gate=fail` (overlap).
  - rollout-sensitivity schema patch:
    - refreshed artifact: `results/stage1_extraction/week2_rollout_stability_sensitivity_20260303T132222Z.json`
    - `known`: null `plus_mean/minus_mean` fields are removed; strict required-metric test added.
  - refreshed reconciliation synthesis:
    - `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T132329Z.json`
- [2026-03-03T10:48:00-0600] `known`: P1/P2 closure artifacts are now generated and indexed:
  - extraction robustness closure run:
    - app `ap-I8m0e5l5pGK1UeRbcD4oqe`, W&B `bzu4kdxo`
    - artifact: `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json`
    - summary: `overall_pass=true`; sycophancy/evil both pass bootstrap and train-vs-heldout cosine gates.
  - cross-trait bleed sensitivity artifact:
    - `results/stage1_extraction/week2_cross_trait_bleed_sensitivity_20260303T164726Z.json`
    - summary: sycophancy prompt-last primary lane is borderline (`0.3165` fails at `0.30`, passes at `0.35`); rollout5 response-mean lanes pass at `0.30`.
  - capability-suite boundary artifact:
    - `results/stage1_extraction/week2_capability_suite_spec_20260303T164726Z.json`
  - manual concordance scope-closure artifact:
    - `results/stage1_extraction/week2_manual_concordance_policy_closure_20260303T164726Z.json` (`manual_concordance_role=sanity_check_only`).
  - checklist impact:
    - pending items `R1-F6`, `R2-C5`, `R2-G8` moved to resolved in `history/20260227-reviewer-reconciliation-checklist-v1.md`.
  - verification:
    - full local suite passes after this tranche: `Ran 112 tests ... OK`.
- [2026-03-03T13:03:00-0600] `known`: high-severity second-pass policy blockers SP-F1 and SP-F3 are now closed via explicit policy packet:
  - artifact: `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`
  - SP-F1 closure:
    - decomposition-start is allowed as single-source at selected claim layer,
    - cross-source claims are explicitly restricted to overlap-capable sensitivity layers (`11,15`),
    - no cross-source claim is allowed on non-overlap selected claim layer (`12`).
  - SP-F3 closure:
    - coherence dual-scorecard policy is explicit and frozen:
      - hardening reliability: `absolute_and_relative`
    - proposal-compatibility interpretation: `relative_only`
    - dual reporting required.
- [2026-03-03T13:13:56-0600] `known`: second-pass synthesis artifact is refreshed with latest closure state (schema-consistent rollout sensitivity input):
  - artifact: `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T191356Z.json`
  - status summary:
    - resolved: `SP-F1`, `SP-F3`, `SP-F4`, `SP-F5`, `SP-F6`, `SP-F7`, `SP-F8`
    - partial: `SP-F2` (prompt-vs-response regime mismatch retained as limitation)
    - limitation: `SP-F9` (evil asymmetry by prompt distribution)
- [2026-03-03T13:15:00-0600] `known`: reviewer-facing exhaustive update memo is generated for next external pass:
  - `history/20260303-reviewer-update-memo-v1.md`
- [2026-03-03T14:00:00-0600] `known`: superseding-decision review is logged and Week2 NO-GO is superseded for phase transition (proposal-compatibility path):
  - review log: `history/reviews/20260303-reviewer-superseding-recommendation-verbatim.md`
  - decision entry: `DECISIONS.md` (2026-03-03T14:00:00-0600)
  - transition scope:
    - proceed Stage2 decomposition for `sycophancy` + `machiavellian_disposition`,
    - keep cross-source claims restricted to overlap-capable sensitivity layers (`11`, `15`),
    - retain explicit limitation block (`SP-F2`, `SP-F9`, layer12 cross-SAE limitation, determinism-vs-stochastic robustness caveat).
- [2026-03-03T14:27:45-0600] `known`: Stage2 decomposition-start primary lane run succeeded at selected claim layer:
  - app: `ap-fA5SmEmYa8AfRxorlWLFNy`
  - artifact: `results/stage2_decomposition/week3_sae_decomposition_20260303T202729Z.json`
  - scope: `sycophancy` + `evil` (aliased to `machiavellian_disposition`), primary SAE source, layer `12`, `100` pairs per trait
  - observed summary: direct-vs-differential top-100 overlap is low for both traits (`jaccard~0.031` sycophancy, `~0.026` machiavellian lane), supporting union-based candidate feature set for downstream Stage3 tracing.
- [2026-03-03T14:37:24-0600] `known`: Stage2 cross-source sensitivity run for overlap layer `11` completed:
  - app: `ap-UqPi08anfVEFE6cXpPkPzZ`
  - artifact: `results/stage2_decomposition/week3_sae_decomposition_20260303T203716Z.json`
  - observed summary: direct-vs-differential top-100 overlap increased vs claim-layer run (`jaccard~0.149` sycophancy, `~0.136` machiavellian lane).
- [2026-03-03T15:17:49-0600] `known`: Stage2 cross-source sensitivity run for overlap layer `15` completed:
  - app: `ap-FvTuR1w1XXqkqosNVkuV52`
  - artifact: `results/stage2_decomposition/week3_sae_decomposition_20260303T211749Z.json`
  - observed summary: direct-vs-differential overlap remains higher than claim-layer run (`jaccard~0.149` sycophancy, `~0.111` machiavellian lane).
- [2026-03-04T10:20:02-0600] `known`: Stage2 decomposition cross-lane sensitivity summary artifact generated:
  - artifact: `results/stage2_decomposition/week3_sae_decomposition_sensitivity_summary_20260304T162002Z.json`
  - observed summary:
    - sycophancy Jaccard delta vs primary layer12: `+0.1185` at layer11 and `+0.1185` at layer15
    - machiavellian lane Jaccard delta vs primary layer12: `+0.1107` at layer11 and `+0.0855` at layer15
  - unknown: whether these overlap gains improve Stage3 attribution selectivity/causal concentration.
- [2026-03-04T10:31:30-0600] `known`: Stage3 candidate-selection policy was pivoted after first-pass artifact sanity check:
  - decision: `DECISIONS.md` entry `2026-03-04T10:31:30-0600`
  - reason: cross-layer/source feature-ID support assumption is not established and produced zero supported features in v1 artifact.
  - impact: selection policy changed to claim-layer primary-only with overlap lanes treated as context metrics.
- [2026-03-04T10:32:00-0600] `known`: Stage3 candidate-selection v2 artifact completed:
  - artifact: `results/stage3_attribution/week3_stage3_candidate_selection_20260304T163200Z.json`
  - policy id: `stage3_v2_claim_layer_primary_only_with_overlap_context`
  - selected features: `50` per trait (`sycophancy`, `machiavellian_disposition`) from claim-layer12 ranked candidates.
- [2026-03-04T10:37:10-0600] `known`: first Stage3 executable attribution pass completed:
  - app: `ap-ZBqFKWyZ4fHELv9fkzWT52`
  - artifact: `results/stage3_attribution/week3_stage3_activation_delta_attribution_20260304T163657Z.json`
  - method: `activation_delta_proxy` at claim layer `12` using `50` selected features per trait on `20` held-out prompts per trait.
  - observed summary:
    - sycophancy: mean-abs-delta concentration `gini=0.5853`; prompt top10 stability `pairwise_jaccard_mean=0.3296`
    - machiavellian lane: mean-abs-delta concentration `gini=0.6612`; prompt top10 stability `pairwise_jaccard_mean=0.3698`
  - unknown: whether these proxy-attribution concentration patterns correspond to true causal-importance edges before Stage4 ablation.
- [2026-03-04T10:46:30-0600] `known`: Stage3 attribution depth-sensitivity pass completed at larger prompt coverage:
  - app: `ap-oW62P2TsDS7TMlLw0BHIHw`
  - artifact: `results/stage3_attribution/week3_stage3_activation_delta_attribution_20260304T164549Z.json`
  - scope: claim layer12, selected top-50 features/trait, `n_prompts=50`/trait.
  - observed summary (vs pass1 `n=20`):
    - sycophancy: `gini 0.5853 -> 0.5771`, prompt-top10 Jaccard `0.3296 -> 0.3254`
    - machiavellian lane: `gini 0.6612 -> 0.6476`, prompt-top10 Jaccard `0.3698 -> 0.3744`
  - inferred: first-pass concentration/stability signal is robust to prompt-depth increase and is suitable for Stage4 target-set freeze.
- [2026-03-04T10:47:30-0600] `known`: Stage4 target-freeze source is explicitly locked to Stage3 pass2 artifact:
  - decision entry: `DECISIONS.md` (`2026-03-04T10:47:30-0600`)
  - freeze source: `results/stage3_attribution/week3_stage3_activation_delta_attribution_20260304T164549Z.json`
  - implication: next critical-path execution is Stage4 necessity/sufficiency ablations using frozen top-k trait feature sets plus random same-size baselines.
- [2026-03-04T10:49:18-0600] `known`: Stage4 pre-execution target-freeze artifact generated:
  - artifact: `results/stage4_ablation/week3_stage4_target_set_freeze_20260304T164918Z.json`
  - scope: traits `sycophancy` + `evil` (claim alias `machiavellian_disposition`), top-10 feature targets/trait frozen from Stage3 pass2 ranking.
  - random-baseline policy: full Stage4 run must sample `100` same-size random sets at runtime from full SAE feature space (`set_size=10`, target IDs excluded).
- [2026-03-04T10:58:56-0600] `known`: first full Stage4 proxy-necessity run completed:
  - app: `ap-gHK92aLmkJL17rPowStV2V`
  - artifact: `results/stage4_ablation/week3_stage4_necessity_proxy_ablation_20260304T165848Z.json` (superseded by post-refactor rerun)
  - observed summary: method disagreement + negative resample reductions (`syc=-0.0203`, `evil=-0.1352`) triggered implementation-spot-check loop before interpretation.
- [2026-03-04T11:06:00-0600] `known`: post-refactor implementation smoke run succeeded:
  - app: `ap-AONqoFo4wGidAF0FXCdD23`
  - artifact: `results/stage4_ablation/week3_stage4_necessity_proxy_ablation_20260304T170551Z.json`
  - purpose: validate runtime and method-population path after helper refactor.
- [2026-03-04T11:12:08-0600] `known`: full post-refactor Stage4 proxy rerun completed:
  - app: `ap-Ml02p5K3hbvekbO0MlsLXA`
  - artifact: `results/stage4_ablation/week3_stage4_necessity_proxy_ablation_20260304T171200Z.json`
  - observed summary:
    - resample reductions remain negative for both traits (`syc=-0.0203`, `evil=-0.1352`)
    - mean reductions positive (`syc=0.2820`, `evil=0.3388`)
    - zero ablation diverges strongly by trait (`syc=0.5365`, `evil=-1.4563`)
  - inferred: proxy Stage4 signal is mixed/negative and not claim-ready for H2; behavioral ablation path remains required for causal claims.
- [2026-03-04T11:36:51-0600] `known`: first behavioral Stage4 launch failed at Modal module import boundary:
  - app: `ap-qGsg9jGO9PWD709AjrcLhm`
  - failure: `ModuleNotFoundError: No module named 'scripts'` from `from scripts.shared.behavioral_eval import ...`
  - impact: no Stage4 behavioral artifact produced; run is non-claim failed attempt.
  - mitigation: runner was made self-contained and validated locally via targeted tests before relaunch.
- [2026-03-04T11:37:21-0600] `known`: behavioral Stage4 small-tranche rerun launched after import fix:
  - app: `ap-OcpIPgzEsMcFCs968fCyxW`
  - observed startup evidence: model load completed (`Loaded pretrained model meta-llama/Llama-3.1-8B-Instruct into HookedTransformer`).
- [2026-03-05T09:56:00-0600] `known`: first behavioral Stage4 artifact is present and timestamp-aligned with the rerun window:
  - artifact: `results/stage4_ablation/week3_stage4_behavioral_ablation_20260304T192718Z.json`
  - observed baseline steering-effect means: `sycophancy=3.4`, `evil=0.0`
  - observed anomaly: reduction means explode at low-baseline prompts (order `1e8-1e9`) under current denominator rule.
  - inferred: execution path is validated, but artifact is not claim-ready for H2 until low-baseline reduction handling is stabilized and rerun.
- [2026-03-05T00:30:50-0600] `known`: low-baseline-stability rerun launched with explicit validity masking:
  - app: `ap-NHmNaSEiQua5O54bXcuQ0X`
  - config delta: `min_baseline_effect_for_reduction=1.0`
  - observed progress checkpoints:
    - `trait=sycophancy baseline done=10/10`
    - `reduction_validity trait=sycophancy valid_prompts=8/10`
    - `random_baseline_progress trait=sycophancy method=resample sets_done=10/20`
- [2026-03-05T09:10:59Z] `known`: low-baseline-stability rerun completed and wrote superseding artifact:
  - artifact: `results/stage4_ablation/week3_stage4_behavioral_ablation_20260305T091059Z.json`
  - observed summary:
    - sycophancy baseline effect mean `3.6`; reduction-valid prompts `8/10`
    - evil baseline effect mean `0.5`; reduction-valid prompts `1/10`
    - no method passes full necessity/selectivity threshold bundle in this tranche.
  - inferred: denominator instability is mitigated, but low baseline effect coverage (especially evil) now dominates interpretability limits.
- [2026-03-06T06:45:44-0600] `known`: no active Stage4 behavioral app remains in current Modal app-list window (`tasks=0` for remaining listed historical app), and closeout is now artifact-driven for this tranche.
- [2026-03-06T08:01:03-0600] `known`: first threshold-sensitivity follow-up launched for evil lane with larger prompt tranche:
  - app: `ap-6cyPCePw9R4wIkimKetVXp`
  - config: `traits=evil`, `n_prompts=30`, `min_baseline_effect_for_reduction=0.0`, `random_baseline_samples=20`
  - observed startup: `[2026-03-06T14:02:39Z] model_loaded model=meta-llama/Llama-3.1-8B-Instruct`
  - outcome: failed (no artifact) with `ZeroDivisionError` in `_reduction_fraction` when baseline effect hit `0.0` at threshold `0.0`.
- [2026-03-06T08:53:41-0600] `known`: rerun launched after zero-baseline guard patch under identical config:
  - app: `ap-LJQ0sKpAXckEL26C1h3bSE`
  - observed startup: `[2026-03-06T14:55:26Z] model_loaded model=meta-llama/Llama-3.1-8B-Instruct`
- [2026-03-06T17:35:23Z] `known`: patched rerun completed and wrote artifact:
  - artifact: `results/stage4_ablation/week3_stage4_behavioral_ablation_20260306T173523Z.json`
  - observed summary (`evil`, `n_prompts=30`, threshold `0.0`):
    - baseline effect mean `0.6333`
    - valid prompts `4/30` (`valid_fraction=0.1333`)
    - observed mean reductions: resample `-1.625`, mean `-1.625`, zero `-2.125`
    - selectivity `p=0.9048` across methods; no full necessity/selectivity pass.
  - inferred: zero-division failure is fixed, but low baseline-effect prevalence remains the dominant blocker for interpretable H2 evidence on this lane.
- [2026-03-09T19:42:29Z] `known`: evil source-sensitivity calibration run completed with alpha3 source and wrote artifact:
  - app: `ap-NaWK7AJnmjQXVPU3NivMKr`
  - artifact: `results/stage4_ablation/week3_stage4_behavioral_ablation_20260309T194229Z.json`
  - config delta vs prior threshold run:
    - source artifact switched to `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260227T171643Z.json` (`selected layer=12, alpha=3.0`)
    - calibration depth: `n_prompts=20`, `random_baseline_samples=5`, `n_bootstrap=100`, `min_baseline_effect_for_reduction=0.0`
  - observed summary:
    - baseline effect mean `10.75` (prior alpha2 source run `0.6333`)
    - valid prompts `13/20` (`valid_fraction=0.65`)
    - observed mean reductions: resample `0.3094`, mean `0.3061`, zero `0.7471`
    - selectivity `p=0.1667` across methods (`n_random=5`)
  - inferred: source-setting switch appears to resolve the low-coverage blocker, but this calibration is underpowered for claim-grade selectivity.
- [2026-03-09T14:54:54-0500] `observed`: first full-depth alpha3 attempt (`ap-AEoOP0w8tMcfAJklW5BauZ`) reached terminal state without a landed local artifact in this workspace.
  - known: no new `week3_stage4_behavioral_ablation_*.json` file was produced by this attempt.
  - unknown: exact stop cause is not recoverable from current CLI log output.
- [2026-03-10T00:19:03Z] `known`: full-depth alpha3 relaunch completed and wrote artifact:
  - app: `ap-dpUywEUrE2CNDn9cXPzEpG`
  - artifact: `results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T001903Z.json`
  - observed summary (`evil`, `n_prompts=30`, `random_baseline_samples=20`, threshold `0.0`):
    - baseline effect mean `12.3333`
    - valid prompts `21/30` (`valid_fraction=0.70`)
    - observed mean reductions: resample `0.2585`, mean `0.1783`, zero `0.5627`
    - selectivity `p=0.0476` for all methods, but strict threshold flags remain unmet (`necessity/selectivity/A12=false` across methods).
  - inferred: coverage blocker is materially reduced, but H2 remains interpretation-limited under the current strict Stage4 threshold bundle.
- [2026-03-10T04:46:38Z] `known`: threshold-binding diagnostic artifact generated from latest Stage4 behavioral runs:
  - artifact: `results/stage4_ablation/week3_stage4_threshold_binding_diagnostic_20260310T044638Z.json`
  - observed (latest full-depth run): necessity margin is the dominant negative gap across methods (`~ -0.24 to -0.62`), with significance (`~ -0.038`) and A12 (`~ -0.007 to -0.173`) as secondary binders.
  - inferred: next policy discussion should focus first on necessity-threshold alignment, not only p-value tuning.
- [2026-03-10T08:08:41Z] `known`: prompt-tranche sensitivity run completed and wrote artifact:
  - app: `ap-bC1z6ABhVa7hUSNBsJ0cpe`
  - artifact: `results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T080841Z.json`
  - observed summary (`evil`, alternate heldout slice, `n_prompts=30`, `n_random=20`):
    - baseline effect mean `14.7`
    - valid prompts `20/30` (`valid_fraction=0.6667`)
    - observed mean reductions: resample `0.2549`, mean `0.2853`, zero `0.5280`
    - selectivity p-values: resample `0.6190`, mean `0.2381`, zero `0.0476`
    - strict threshold flags remain unmet (`necessity/selectivity/A12=false` across methods).
  - observed: artifact currently does not persist `heldout_start_index` in `inputs`; tranche provenance is tracked in SCRATCHPAD launch records.
  - inferred: strict-threshold failures persist and at least some selectivity signals are tranche-sensitive (not uniformly stable across methods).
- [2026-03-10T14:14:58Z] `known`: tranche-vs-reference comparison artifact generated:
  - artifact: `results/stage4_ablation/week3_stage4_tranche_comparison_20260310T141458Z.json`
  - comparison scope: reference `week3_stage4_behavioral_ablation_20260310T001903Z.json` vs tranche `week3_stage4_behavioral_ablation_20260310T080841Z.json`
  - observed summary:
    - coverage stability preserved (`valid_fraction 0.70 -> 0.6667`, label=`stable`)
    - gate states unchanged (all strict gates still fail for all methods in both runs)
    - tranche deltas show selectivity/A12 degradation across methods (`resample p +0.5714`, `mean p +0.1905`, `zero p +0.0`; all A12 deltas negative)
  - inferred: H2 failure pattern is stable at the gate level and tranche-sensitive in strength, supporting policy review over further immediate reruns.
- [2026-03-10T14:20:00Z] `known`: Stage4 policy decision packet generated from reference + tranche + threshold diagnostics:
  - artifact: `results/stage4_ablation/week3_stage4_policy_decision_packet_20260310T142000Z.json`
  - observed summary:
    - strict summary: no method passes full strict gate bundle in either run
    - coverage: stable/high (`0.70` reference, `0.6667` tranche)
    - recommendation (inferred): `strict_fail_with_dual_scorecard_candidate`
  - inferred: evidence package is now complete for a policy-lock decision without launching additional Stage4 runs first.
- [2026-03-10T09:24:10-0500] `known`: explicit H2 policy lock is now logged in `DECISIONS.md`:
  - selected path: dual-scorecard interpretation lane enabled for narrative reporting, while strict Stage4 status remains `fail` as primary governance signal.
  - launch policy: additional Stage4 runs are frozen until a new, explicitly-scoped strict-threshold remediation question is defined.


## Completed Phases

- Phase 0 — Infrastructure (Week 1) completed on 2026-02-24.

## Blocking Issues

- `known`: no global blocker remains for Stage2 decomposition start under proposal-compatibility scorecard.
- `known`: Week2 replication/stress expansion remains non-critical-path and should stay deferred unless explicitly required by a future decision.

## Current Risks / Notes

- `known`: reconstruction failure mode is now narrowed: catastrophic values occur on full-sequence activation evaluation; token-level (`last_token`) reconstruction is much better but still below preferred thresholds.
- `inferred`: Stage2 reliability gating should align with token-level extraction target; full-sequence flatten metrics are not a faithful proxy for this project's extraction path.
- `known`: Full upgraded parallel plan is broad and expensive if launched all-at-once (15 jobs; latest estimate ~53k primary judge calls after stricter controls); should be launched in tranches.
- `known`: Post-primary prelaunch gap-check rerun still fails external transfer + extraction A/B robustness gates (`week2_prelaunch_gap_checks_20260227T205237Z.json`); this remains a documented Week2 limitation lane, not a Stage2 start blocker under the superseding decision.
- `known`: the prior Week2 `NO-GO` decision (2026-02-27T15:31:15-0600) is superseded for phase transition by the decision at 2026-03-03T14:00:00-0600; hardening scorecard caveats remain mandatory in reporting.
- `known`: WS-B small-run extraction-position diagnostics remain below robustness threshold (`0.7`) for every trait/layer on prompt-last vs response-mean agreement (`week2_extraction_position_ablation_20260227T221817Z.json`).
- `known`: WS-B expanded run confirms the same gate failure pattern at larger sample size (`week2_extraction_position_ablation_20260227T225251Z.json`).
- `inferred`: method disagreement appears trait-dependent in magnitude (sycophancy/evil higher overlap than hallucination), and disagreement is likely prompt-vs-response phase driven for sycophancy/evil because response-only variants align strongly.
- `known`: WS-C selection policy is now constrained by design (smallest feasible alpha default), and lower-alpha targeted evidence is collected for sycophancy+evil.
- `known`: response-mean sensitivity lane is now executed for sycophancy+evil; extraction-method switch alone does not recover overall pass under current coherence gate.
- `known`: WS-C targeted reruns now show that constrained low-alpha selection (alpha 2.0) does not recover overall pass for sycophancy/evil under current gates.
- `inferred`: coherence failure appears dominated by absolute `coherence_min_score=75` threshold (steered coherence improves vs baseline but remains below threshold).
- `known`: harmful-content interpretation for `evil` remains a negative finding, but the same direction is reopened for a reframed `machiavellian/manipulative disposition` axis based on extraction-free overlap evidence.
- `known`: cosine-margin diagnostics are now populated in current artifacts (`week2_vector_extraction_summary_20260225T170852Z.json`, `week2_vector_diagnostics_20260225T170928Z.json`).
- `known`: extraction-free evidence is trait-dependent after reanalysis: sycophancy/evil show positive overlap above chance; hallucination remains null.
- `inferred`: Hallucination likely tracks instruction-conditioned calibration/refusal dynamics rather than a stable persona-like direction under current protocol.
- `known`: Stage2 computed readiness still fails under claim-layer + multi-seed policy (`week3_sae_reconstruction_audit_20260303T132222Z.json`): token gate fails at layer12 (`min cos=0.7047`, `min EV=0.4765`) and cross-source overlap on claim layer12 is empty.
- `known`: Seed-schedule consumption is now resolved (`seed_schedule=[42,123,456,789]` in `week3_sae_reconstruction_investigation_20260301T031743Z.json`).
- `known`: extraction seed-replication artifact (`week2_extraction_seed_replication_20260302T180612Z.json`) supports deterministic reproducibility under fixed inputs, and is now complemented by direct content-robustness evidence in `week2_extraction_robustness_bootstrap_20260303T164652Z.json`.
- `inferred`: Stage2 false-positive pass path is closed; decomposition-start and overlap-layer cross-source sensitivity lanes are now executed, enabling explicit cross-layer/source comparison reporting in the next synthesis artifact.
- `known`: Post-core extension blueprint for narrative arcs/tropes/memes is documented at `history/20260225-post-core-extension-narrative-arcs-tropes-memes.md`; execution is explicitly deferred until core phases are complete.
- `known`: WS-F rollout-depth artifacts are now terminalized and compared; both traits remain coherence-gate limited under rollout5.
- `known`: coherence gate remains bound by absolute minimum score threshold under current policy (rollout5 coherence baseline means: sycophancy `69.595`, evil `58.74`, both below threshold `75`).
- `known`: legacy rollout-sensitivity artifact (`week2_rollout_stability_sensitivity_20260303T121253Z.json`) contained null `plus_mean/minus_mean` fields due key mismatch; this is now superseded by patched output.
- `known`: rollout-sensitivity schema mismatch is patched in refreshed artifact (`week2_rollout_stability_sensitivity_20260303T132222Z.json`); prior null-field artifact is superseded.
- `known`: cross-layer/source feature-ID correspondence is not established for direct support scoring; Stage3 v2 policy avoids this assumption and uses overlap lanes as context only.
- `known`: Stage4 proxy necessity artifacts are method-divergent and primary resample lane is negative for both traits (`week3_stage4_necessity_proxy_ablation_20260304T171200Z.json`); proxy outputs are exploratory-only and cannot support claim-grade H2.
- `known`: first behavioral Stage4 attempt failed on Modal import packaging (`ap-qGsg9jGO9PWD709AjrcLhm`) and was followed by a successful execution artifact lane.
- `known`: `week3_stage4_behavioral_ablation.py` now includes granular runtime progress checkpoints (trait/method/random-set progress) for subsequent reruns.
- `known`: zero-baseline reduction instability is patched (`MIN_REDUCTION_DENOMINATOR` + aligned validity masking), and recent runs no longer exhibit denominator blowups.
- `known`: low-baseline guard patch removed numeric blowups in superseding artifact (`week3_stage4_behavioral_ablation_20260305T091059Z.json`), but evil coverage is sparse (`1/10` valid prompts at threshold `1.0`) and remains underpowered for H2 interpretation.
- `known`: threshold-sensitivity rerun (`week3_stage4_behavioral_ablation_20260306T173523Z.json`) confirms that even at threshold `0.0`, evil-lane valid coverage remains low (`4/30`) and method selectivity is weak.
- `known`: source-sensitivity calibration with alpha3 source (`week3_stage4_behavioral_ablation_20260309T194229Z.json`) lifts evil-lane valid coverage to `13/20`, but selectivity remains non-significant under reduced random depth (`p=0.1667`, `n_random=5`).
- `known`: full-depth alpha3 confirmation (`week3_stage4_behavioral_ablation_20260310T001903Z.json`) further lifts coverage to `21/30` with selectivity `p=0.0476`, but strict necessity/selectivity/A12 threshold flags remain unmet.
- `known`: prompt-tranche sensitivity full-depth run (`week3_stage4_behavioral_ablation_20260310T080841Z.json`) keeps coverage high (`20/30`) but shows method-level selectivity instability (resample/mean p-values degrade vs reference; zero remains near prior `p=0.0476`).
- `known`: runner code now includes `heldout_start_index` in run-level `inputs`, but the just-completed tranche artifact predates that remote-parameter patch and therefore still shows `null` metadata.
- `known`: policy packet now exists for Stage4 H2 governance lock (`week3_stage4_policy_decision_packet_20260310T142000Z.json`).
- `known`: policy ambiguity is resolved (dual-scorecard lane locked); strict gate status for H2 remains fail under current thresholds.
- `known`: Stage4 synthesis memo is now recorded with explicit strict-fail + dual-scorecard lock status:
  - `history/20260310-stage4-h2-synthesis-memo-v1.md`
- `known`: H3 sufficiency execution planning artifact is now created without launching new runs:
  - `results/stage4_ablation/week3_h3_sufficiency_execution_plan_20260310T143354Z.json` (supersedes `...143023Z`)
- `known`: Stage4 sufficiency runner path now has an executable launch-free preflight/dry-run checkpoint:
  - script: `scripts/week3_stage4_sufficiency_preflight.py`
  - test: `tests/test_week3_stage4_sufficiency_preflight.py`
  - artifact: `results/stage4_ablation/week3_stage4_sufficiency_preflight_20260310T145632Z.json`
  - observed: `inputs_valid=true`, `dryrun_path_exercised=true`, `launch_recommended_now=false`, blocker remains `remote_circuit_only_execution_not_run_dryrun_only`.
- `known`: Stage4 sufficiency now has an explicit remote-capable behavioral runner with dry-run packet mode:
  - script: `scripts/week3_stage4_behavioral_sufficiency.py`
  - tests: `tests/test_week3_stage4_behavioral_sufficiency_utils.py`
  - artifact: `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T201431Z.json`
  - observed: dry-run packet reports `inputs_valid=true`, `launch_recommended_now=true`, `blocking_items=[]`.
- `known`: Stage4 sufficiency runner now also has token-stable checkpoint/final artifact plumbing for detached retries:
  - script patch: `scripts/week3_stage4_behavioral_sufficiency.py` (`run_token` threaded through local entrypoint, dry-run packet, and remote checkpoint/final paths)
  - tests: `tests/test_week3_stage4_behavioral_sufficiency_utils.py` (`Ran 5 tests ... OK`)
  - verification artifacts:
    - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T231437Z.json`
    - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T232102Z.json`
- `observed`: the first tokenized detached retry (`ap-0G5330JQuwPuHQqTYjlWuK`) failed operationally on `vol.reload()` after model load and is now closed as infrastructure failure.
- `known`: H3 detached retry `ap-IhLmgFOlGMVyMfukXluGmj` has terminalized successfully and the final remote artifact has been recovered locally:
  - final artifact: `results/stage4_ablation/week3_stage4_behavioral_sufficiency_remote_week3-stage4-h3-tranche1-20260310T2321Z.json`
  - deterministic inputs: target-freeze `week3_stage4_target_set_freeze_20260304T164918Z.json`, vectors `week2_persona_vectors_seed42_20260302T180612Z.pt`, source artifacts `week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json` + `week2_behavioral_validation_upgrade_evil_20260303T081318Z.json`
  - observed remote artifacts on Modal volume:
    - `persona-circuits/results/stage4_ablation/week3_stage4_behavioral_sufficiency_remote_checkpoint_week3-stage4-h3-tranche1-20260310T2321Z.json`
    - `persona-circuits/results/stage4_ablation/week3_stage4_behavioral_sufficiency_remote_week3-stage4-h3-tranche1-20260310T2321Z.json`
  - observed execution coverage: all 16 trait/method/dose cells are populated (`2 traits x 2 methods x 4 doses`).
  - observed gate snapshot from the final artifact: `sufficiency_threshold_pass=16/16`, `selectivity_p_threshold_pass=0/16`, `coherence_relative_max_drop_pass=0/16`, `a12_threshold_pass=1/16` (sole A12 pass: `evil/resample/0.50`).
- `known`: Stage5 cross-persona planning stub is now created with explicit H4/H5 gate checklist:
  - `results/stage5_cross_persona/week3_stage5_planning_stub_20260310T143354Z.json` (supersedes `...143023Z`)
- `known`: Stage5 launch-free overlap utility is now implemented and executed on current decomposition artifacts:
  - script: `scripts/week3_stage5_cross_persona_analysis.py`
  - test: `tests/test_week3_stage5_cross_persona_analysis.py`
  - artifact: `results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T195835Z.json` (supersedes `...145632Z`)
  - observed: mixed-source comparability is explicitly flagged, source-consistent gradient summaries are emitted by SAE source, and BH-FDR router-testing hook is now executed (`n_tested=62`, `n_rejected=0`, `candidate_union`, `fdr_alpha=0.01`).
- `known`: Stage5 router-candidate p-value artifact + map are now generated from current decomposition artifacts:
  - script: `scripts/week3_stage5_router_candidate_pvalues.py`
  - test: `tests/test_week3_stage5_router_candidate_pvalues.py`
  - artifacts:
    - `results/stage5_cross_persona/week3_stage5_router_candidate_pvalues_20260310T195815Z.json`
    - `results/stage5_cross_persona/week3_stage5_router_candidate_pvalues_map_20260310T195815Z.json`
  - observed: `n_features=62`, `min_p_value=0.001`, `median_p_value=0.3486`.
- `known`: Stage5 gate-closure policy packet is now generated from executed BH evidence:
  - script: `scripts/week3_stage5_policy_decision_packet.py`
  - test: `tests/test_week3_stage5_policy_decision_packet.py`
  - artifact: `results/stage5_cross_persona/week3_stage5_policy_decision_packet_20260310T200937Z.json`
  - observed: `S5-G2=pass_with_limitation`, `S5-G4=exploratory_null`, recommendation=`lock_exploratory_null_with_optional_sensitivity_lane`.
- `inferred`: remaining H2 gap is now synthesis/reporting alignment and path-consistent next-phase execution, not additional immediate Stage4 data collection.

## Next Action

1. Add an extraction-free generation wrapper for eligible `trait_lanes_v2` lanes and run it first on Slice A or Slice B before widening to a third live trio.
2. Decide whether the next breadth move should be Slice C (`deception` or `agreeableness`) only after the extraction-free path exists.
3. Keep safety-like lanes deferred until the extraction-free or broader screening path has succeeded on at least one additional slice beyond A/B.

## Handoff Resume Protocol (if session restarts now)

1. Re-open the latest closeout artifacts:
   - `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T220017Z.json`
   - `results/stage1_extraction/week2_primary_manual_concordance_ratings_20260227T202822Z.json`
   - `results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json`
   - `results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json`
   - `history/20260227-week2-closeout-deep-summary-for-review.md`
   - `history/reviews/20260227-reviewer1-verbatim.md`
   - `history/reviews/20260227-reviewer2-verbatim.md`
   - `history/reviews/20260303-reviewer1-second-pass-verbatim.md`
   - `history/reviews/20260303-reviewer2-second-pass-verbatim.md`
   - `history/reviews/20260303-reviewer-superseding-recommendation-verbatim.md`
   - `history/20260227-week2-remediation-master-plan-v1.md`
   - `history/20260227-reviewer-reconciliation-checklist-v1.md`
   - `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T191356Z.json`
   - `history/20260303-reviewer-update-memo-v1.md`
   - `results/stage1_extraction/week2_coherence_policy_diagnostic_20260303T132222Z.json`
   - `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`
   - `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json`
   - `results/stage1_extraction/week2_cross_trait_bleed_sensitivity_20260303T164726Z.json`
   - `results/stage1_extraction/week2_capability_suite_spec_20260303T164726Z.json`
   - `results/stage1_extraction/week2_manual_concordance_policy_closure_20260303T164726Z.json`
   - `results/stage2_decomposition/week3_sae_reconstruction_audit_20260303T132222Z.json`
   - `results/stage2_decomposition/week3_sae_decomposition_20260303T202729Z.json`
   - `history/20260310-stage4-h2-synthesis-memo-v1.md`
   - `results/stage4_ablation/week3_h3_sufficiency_execution_plan_20260310T143354Z.json`
   - `results/stage4_ablation/week3_stage4_sufficiency_preflight_20260310T145632Z.json`
   - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T201431Z.json`
   - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T231437Z.json`
   - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T232102Z.json`
   - `results/stage5_cross_persona/week3_stage5_planning_stub_20260310T143354Z.json`
   - `results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T195835Z.json`
   - `results/stage5_cross_persona/week3_stage5_router_candidate_pvalues_20260310T195815Z.json`
   - `results/stage5_cross_persona/week3_stage5_router_candidate_pvalues_map_20260310T195815Z.json`
   - `results/stage5_cross_persona/week3_stage5_policy_decision_packet_20260310T200937Z.json`
   - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_summary_20260311T201829Z.json`
   - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_summary_20260311T203019Z.json`
   - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_generated_prompt_audit_20260311T203324Z.json`
2. If resuming H3 sufficiency work, first inspect `SCRATCHPAD.md` entries at `2026-03-10T18:15:15-0500` and `2026-03-10T18:21:02-0500`, then check Modal app `ap-IhLmgFOlGMVyMfukXluGmj` and run token `week3-stage4-h3-tranche1-20260310T2321Z` before launching anything else.
3. Confirm docs are synchronized:
   - `CURRENT_STATE.md`, `SCRATCHPAD.md`, `THOUGHT_LOG.md`, `results/RESULTS_INDEX.md`
4. Verify closeout decision remains in force (`DECISIONS.md`, 2026-02-27T15:31:15-0600) before any new Week 2 launch.
5. For Stage2 work, follow the superseding decision entry (`DECISIONS.md`, 2026-03-03T14:00:00-0600) and keep the explicit limitation block attached to all decomposition outputs.

---

## Phase Tracker

| Phase | Status | Start Date | End Date | Key Result |
|-------|--------|------------|----------|------------|
| 0. Infrastructure | completed | 2026-02-24 | 2026-02-24 | Modal/W&B/model/SAE/CLT setup validated; prompt datasets regenerated and strict-audit passed |
| 1. Persona Extraction | completed | 2026-02-24 | 2026-03-03 | Week2 closed under proposal-compatibility with explicit caveats; superseding decision logged for Stage2 transition |
| 2. SAE Decomposition | completed | 2026-03-03 | 2026-03-04 | Decomposition-start + overlap-layer sensitivity artifacts completed with explicit cross-SAE/claim-layer caveats (`week3_sae_decomposition_20260303T202729Z.json`, `week3_sae_decomposition_sensitivity_summary_20260304T162002Z.json`) |
| 3. Circuit Tracing | in_progress | 2026-03-04 | | Stage3 candidate-selection + two executable attribution passes completed (`week3_stage3_activation_delta_attribution_20260304T163657Z.json`, `week3_stage3_activation_delta_attribution_20260304T164549Z.json`) |
| 4. Causal Validation | in_progress | 2026-03-04 | | Stage4 target-freeze + proxy runs + behavioral follow-ups completed; first full H3 sufficiency execution artifact is now landed (`week3_stage4_target_set_freeze_20260304T164918Z.json`, `week3_stage4_necessity_proxy_ablation_20260304T171200Z.json`, `week3_stage4_behavioral_ablation_20260305T091059Z.json`, `week3_stage4_behavioral_ablation_20260306T173523Z.json`, `week3_stage4_behavioral_ablation_20260309T194229Z.json`, `week3_stage4_behavioral_ablation_20260310T001903Z.json`, `week3_stage4_behavioral_ablation_20260310T080841Z.json`, `week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T201431Z.json`, `week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T231437Z.json`, `week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T232102Z.json`, `week3_stage4_behavioral_sufficiency_remote_week3-stage4-h3-tranche1-20260310T2321Z.json`) |
| 5. Cross-Persona Analysis | in_progress | 2026-03-10 | | Launch-free utility + planning artifacts landed; BH-FDR hook executed and policy closure packet added (`week3_stage5_planning_stub_20260310T143354Z.json`, `week3_stage5_router_candidate_pvalues_20260310T195815Z.json`, `week3_stage5_cross_persona_analysis_20260310T195835Z.json`, `week3_stage5_policy_decision_packet_20260310T200937Z.json`) |
| 6. Gemma-2-2B Validation | not_started | | | |
| 7. Writing | not_started | | | |

## Hypothesis Status

| Hypothesis | Status | Current Evidence | Confidence |
|------------|--------|-----------------|------------|
| H1 (Coherence) | in_progress | Stage1 vectors extracted; Stage2 decomposition-start + sensitivity artifacts completed (`week3_sae_decomposition_20260303T202729Z.json`, `week3_sae_decomposition_sensitivity_summary_20260304T162002Z.json`); Stage3 proxy-attribution concentration/stability is observed and depth-stable across two runs (`week3_stage3_activation_delta_attribution_20260304T163657Z.json`, `week3_stage3_activation_delta_attribution_20260304T164549Z.json`) | low |
| H2 (Necessity) | in_progress | Stage4 behavioral necessity path executed through full-depth alpha3 confirmation + tranche sensitivity (`week3_stage4_behavioral_ablation_20260305T091059Z.json`, `week3_stage4_behavioral_ablation_20260306T173523Z.json`, `week3_stage4_behavioral_ablation_20260309T194229Z.json`, `week3_stage4_behavioral_ablation_20260310T001903Z.json`, `week3_stage4_behavioral_ablation_20260310T080841Z.json`); policy diagnostics and synthesis are now closed (`week3_stage4_threshold_binding_diagnostic_20260310T044638Z.json`, `week3_stage4_tranche_comparison_20260310T141458Z.json`, `week3_stage4_policy_decision_packet_20260310T142000Z.json`, `history/20260310-stage4-h2-synthesis-memo-v1.md`); strict threshold flags remain unmet with dual-scorecard interpretation lock active | low |
| H3 (Sufficiency) | in_progress | Launch-free sufficiency preflight plus remote-capable runner packets are artifact-backed, and the first full remote execution artifact is now landed (`week3_stage4_sufficiency_preflight_20260310T145632Z.json`, `week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T201431Z.json`, `week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T231437Z.json`, `week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T232102Z.json`, `week3_stage4_behavioral_sufficiency_remote_week3-stage4-h3-tranche1-20260310T2321Z.json`); execution completed for all 16 cells, but selectivity/coherence gates fail broadly (`sel=0/16`, `coh=0/16`, `a12=1/16`) and interpretation review is now required | low |
| H4 (Cross-Persona) | in_progress | Launch-free overlap utility now emits layerwise overlap + source-consistent gradient diagnostics with executed BH hook (`week3_stage5_cross_persona_analysis_20260310T195835Z.json`); claim thresholds not yet met/closed | low |
| H5 (Router) | in_progress | Router-candidate p-value lane + BH hook are executed and policy packet is logged (`week3_stage5_router_candidate_pvalues_20260310T195815Z.json`, `week3_stage5_cross_persona_analysis_20260310T195835Z.json`, `week3_stage5_policy_decision_packet_20260310T200937Z.json`); no FDR-significant candidates at `alpha=0.01` in current launch-free pass | low |


## Continuation Update (22:50-0500)

- [x] H3 runner claim-facing semantics patched and locally revalidated:
  - bounded preservation for thresholding + raw-ratio diagnostic retained
  - sign-aware preservation (`signed circuit delta / signed steered delta`)
  - minimum valid-prompt floor (`count>=5`, `fraction>=0.5`) required before H3 thresholds can pass
  - selectivity feasibility guard now requires enough random baselines to realize configured alpha (`>=99` for `p<0.01`)
  - raw circuit-only output audit samples now persist per cell for coherence inspection
- [x] Local validation status:
  - `python3 -m py_compile scripts/week3_stage4_behavioral_sufficiency.py`
  - `python3 -m unittest discover -s tests -p 'test_week3_stage4_behavioral_sufficiency_utils.py'` -> `Ran 9 tests ... OK`
  - `python3 -m unittest discover -s tests -p 'test_week3_stage4_*py'` -> `Ran 44 tests ... OK`
- [x] Fresh dry-run packet from final patched code:
  - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260311T024350Z.json`
  - `known`: `random_baseline_samples=100`, `minimum_random_sets_required_for_significance=99`, `launch_recommended_now=true` for this diagnostic runner configuration
- [ ] Important caveat before any new H3 launch:
  - `known`: this runner still executes candidate-pool-complement sufficiency, not full-SAE-complement `circuit alone` sufficiency.
  - `known`: on-run capability/perplexity checks and monotonicity gating are still absent.
  - `inferred`: next H3 decision should choose explicitly between (a) diagnostic rerun on the patched runner, or (b) additional claim-grade hardening before any proposal-facing H3 claim.

## Continuation Update (08:35-0500)

- [x] H3 claim-grade hardening tranche completed in the primary runner:
  - `scripts/week3_stage4_behavioral_sufficiency.py` now supports explicit `claim_mode` + `ablation_scope`
  - `full_sae_complement` path implemented for true circuit-only preservation scope
  - on-run capability-proxy and next-token-loss diagnostics added
  - method-level dose-monotonicity gate added
- [x] Validation state:
  - `python3 -m py_compile scripts/week3_stage4_behavioral_sufficiency.py`
  - `python3 -m unittest discover -s tests -p 'test_week3_stage4_behavioral_sufficiency_utils.py'` -> `Ran 11 tests ... OK`
  - `python3 -m unittest discover -s tests -p 'test_week3_stage4_*py'` -> `Ran 46 tests ... OK`
- [x] Fresh authoritative claim-grade dry-run packet:
  - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260311T132932Z.json`
  - `known`: packet records `claim_mode=claim_grade`, `ablation_scope=full_sae_complement`, `next_token_loss_diagnostics_enabled=true`, and `launch_recommended_now=true` for code-path readiness
- [x] H3 blocker shift:
  - `known`: prior implementation blockers (candidate-pool-only scope, absent capability/perplexity-style controls, absent monotonicity gate) are now resolved in code.
  - `inferred`: the remaining blocker is runtime/economic feasibility of a full judge-heavy claim-grade matrix, not missing instrumentation.
- [ ] Next H3 action:
  - keep the active bounded claim-grade tranche isolated until it reaches a scoped H3 closeout.
  - after that closeout is written, transition the next active execution branch to `trait_lanes_v2` screening rather than widening the current H3 matrix by default.
- `known`: bounded claim-grade H3 tranche is now active on Modal:
  - app: `ap-mCOxAI9Xp7WCZoxpslD6Yi`
  - run token: `week3-stage4-h3-claimgrade-syc-resample-trancheA-20260311T0844-0500`
  - scope: `trait=sycophancy`, `method=resample`, `dose_response={0.25,0.50,1.00}`, `n_prompts=10`, `random_baseline_samples=100`, `claim_mode=claim_grade`, `ablation_scope=full_sae_complement`
  - `observed`: `modal app list --json` shows `Tasks=1`.

## Live Run Update (10:27-0500)

- [x] Bounded H3 claim-grade tranche launched:
  - app: `ap-mCOxAI9Xp7WCZoxpslD6Yi`
  - run token: `week3-stage4-h3-claimgrade-syc-resample-trancheA-20260311T0844-0500`
  - scope: `trait=sycophancy`, `method=resample`, `dose_response={0.25,0.50,1.00}`, `n_prompts=10`, `random_baseline_samples=100`, `claim_mode=claim_grade`, `ablation_scope=full_sae_complement`
- [x] Observed runtime status from Modal logs:
  - worker preemption occurred once, but checkpoint reload succeeded on restart
  - baseline cache was reused (`baseline_resume_cache_hit`)
  - dose `0.25` is already checkpointed and the run is actively progressing through dose `0.50`
- [x] Operational inference:
  - resumability path is working under full-complement claim-grade execution, not just the earlier diagnostic lane.
- [ ] Next monitoring target:
  - wait for the first completed bounded claim-grade artifact, then classify H3 feasibility based on coherence, preservation, capability proxy, next-token-loss, and monotonicity together.

## Closeout Update (14:58-0500)

- [x] Bounded H3 claim-grade tranche terminalized:
  - app: `ap-mCOxAI9Xp7WCZoxpslD6Yi`
  - run token: `week3-stage4-h3-claimgrade-syc-resample-trancheA-20260311T0844-0500`
  - terminal state: `stopped`
  - observed terminal failure: `Judge returned unparseable output after 6 attempts (model=claude-sonnet-4-6, trait=sycophancy).`
- [x] Recovery evidence captured:
  - remote checkpoint exists on Modal volume and was copied locally:
    - `scratch/h3_recovery/week3_stage4_behavioral_sufficiency_remote_checkpoint_week3-stage4-h3-claimgrade-syc-resample-trancheA-20260311T0844-0500.json`
  - checkpoint stage confirms completed doses `0.25` and `0.50`
  - `known`: this runner does not checkpoint mid-dose random-baseline progress, so a rerun would restart `dose=1.00` from scratch rather than from `65/100`
- [x] Scoped H3 closeout artifacts landed:
  - machine-readable closeout packet:
    - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_claimgrade_trancheA_closeout_20260311T1919Z.json`
  - narrative memo:
    - `history/20260311-stage4-h3-bounded-trancheA-closeout-v1.md`
- [x] Scoped interpretation:
  - `observed`: completed doses `0.25` and `0.50` both have `sufficiency_threshold_pass=false`
  - `observed`: completed doses `0.25` and `0.50` both have catastrophic coherence-drop mean `73.2` and capability proxy `0.0`
  - `observed`: raw circuit-only audit samples are repetitive degenerate text (`\"is is is...\"`, `\"::: is is...\"`)
  - `inferred`: this bounded tranche is sufficient to close as a negative feasibility signal for claim-grade full-complement H3 on the sycophancy/resample lane
- [x] Next active branch:
  - move into the `trait_lanes_v2` screening branch rather than widening H3 by default

## Continuation Update (15:10-0500)

- [x] Advanced the `trait_lanes_v2` branch from dry-run sidecars into generation-ready tooling without touching legacy Week 1/2 defaults:
  - added shared helper: `scripts/shared/trait_lane_generation.py`
  - added real-generation wrappers:
    - `scripts/week2_trait_lane_generate_extraction_prompts.py`
    - `scripts/week2_trait_lane_generate_heldout_prompts.py`
  - added validation test: `tests/test_trait_lane_generation.py`
- [x] Local validation passed:
  - `python3 -m py_compile scripts/shared/trait_lane_generation.py scripts/week2_trait_lane_generate_extraction_prompts.py scripts/week2_trait_lane_generate_heldout_prompts.py tests/test_trait_lane_generation.py`
  - `python3 -m unittest discover -s tests -p 'test_trait_lane_generation.py'` -> `Ran 5 tests ... OK`
- [x] Dry-run generation artifacts landed:
  - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_plan_20260311T200659Z.json`
  - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_plan_20260311T200659Z.json`
- [x] Branch interpretation:
  - `known`: the branch is no longer limited to planning packets; it now has executable prompt-generation wrappers that write only into the `trait_lanes_v2` namespace.
  - `known`: no API-backed generation run has occurred yet in this tranche.
  - `inferred`: the next defensible execution step is a bounded first P3 generation slice rather than an all-13-lane launch.

## Continuation Update (15:31-0500)

- [x] Executed the first bounded live `trait_lanes_v2` P3 slice for `assistant_likeness`, `honesty`, and `politeness`.
- [x] Extraction generation succeeded:
  - summary: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_summary_20260311T201829Z.json`
  - files:
    - `prompts/trait_lanes_v2/assistant_likeness_pairs.jsonl`
    - `prompts/trait_lanes_v2/honesty_pairs.jsonl`
    - `prompts/trait_lanes_v2/politeness_pairs.jsonl`
- [x] Held-out generation required one corrective rerun:
  - provisional summary: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_summary_20260311T202524Z.json`
  - corrective patch: append-safe `output_suffix` support + held-out anti-paraphrase guard against existing extraction queries
  - superseding summary: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_summary_20260311T203019Z.json`
  - preferred files:
    - `prompts/trait_lanes_v2/heldout/assistant_likeness_heldout_pairs_retry01.jsonl`
    - `prompts/trait_lanes_v2/heldout/honesty_heldout_pairs_retry01.jsonl`
    - `prompts/trait_lanes_v2/heldout/politeness_heldout_pairs_retry01.jsonl`
- [x] Audit snapshot:
  - exact duplicates within each generated file: `0`
  - provisional honesty held-out overlap was too high; retry01 lowered max lexical overlap from `~0.99` to `~0.693`
  - retry01 spot-check looks materially healthier for all three lanes
- [ ] Remaining branch gap:
  - no extraction-free or external-smoke generation wrapper exists yet for the new branch

## Continuation Update (15:33-0500)

- [x] Added and ran a reusable generated-prompt audit for Slice A:
  - script: `scripts/week2_trait_lane_generated_prompt_audit.py`
  - test: `tests/test_week2_trait_lane_generated_prompt_audit.py` (`Ran 2 tests ... OK`)
  - artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_generated_prompt_audit_20260311T203324Z.json`
- [x] Audit outcome:
  - `overall_pass=true`
  - no within-file duplicates
  - no exact repo prompt collisions
  - held-out/extraction lexical-overlap threshold passes for all three lanes under retry01
- [x] Branch state:
  - Slice A is now formally registered as a completed first live generated-input slice
  - next branch decision is about widening, not repairing Slice A

## Continuation Update (16:47-0500)

- [x] Executed and audited Slice B for `persona_drift_from_assistant`, `lying`, and `optimism`.
- [x] Slice B artifacts landed:
  - extraction summary: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_summary_20260311T214555Z.json`
  - held-out summary: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_summary_20260311T214716Z.json`
  - audit: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_generated_prompt_audit_20260311T214720Z.json`
- [x] Slice B outcome:
  - `overall_pass=true`
  - no held-out corrective rerun was required
  - branch fixes from Slice A appear to generalize
- [x] Branch state:
  - two bounded live slices are now complete (`A` and `B`)
  - the next highest-value work is no longer more prompt-generation breadth by default; it is adding the extraction-free generation path for promoted/active slices

## Continuation Update (16:59-0500)

- [x] Validated and executed the isolated `trait_lanes_v2` extraction-free preparation path for Slice A (`assistant_likeness`, `honesty`, `politeness`).
  - local validation:
    - `python3 -m py_compile scripts/week2_trait_lane_prepare_extraction_free_eval.py tests/test_week2_trait_lane_prepare_extraction_free_eval.py`
    - `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_prepare_extraction_free_eval.py'` -> `Ran 3 tests ... OK`
  - dry-run plan artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_free_plan_20260311T215940Z.json`
  - live manifest artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_free_manifest_20260311T215957Z.json`
  - live prompt outputs:
    - `prompts/trait_lanes_v2/extraction_free/assistant_likeness_eval.jsonl`
    - `prompts/trait_lanes_v2/extraction_free/honesty_eval.jsonl`
    - `prompts/trait_lanes_v2/extraction_free/politeness_eval.jsonl`
- [x] Slice A extraction-free outcome:
  - `known`: all three lanes generated `12` eval rows in the isolated trait-lane namespace.
  - `observed`: each lane uses all four available exemplar sets (`n_exemplar_sets_used=4/4`), meeting the bounded diversity target for this preparation stage.
  - `observed`: set usage is somewhat uneven for `honesty` (`7/1/2/2`), but no lane collapsed to a single-set path.
- [x] Branch implication:
  - the extraction-free path now exists as a real exercised branch component, not just a planned follow-on.
  - the next branch decision is no longer “build the wrapper” but “extend extraction-free depth to Slice B or add the next screening/eval layer on top of Slice A first.”

## Continuation Update (17:04-0500)

- [x] Extended extraction-free prep parity to Slice B (`persona_drift_from_assistant`, `lying`, `optimism`) with a dedicated exemplar bank.
  - new exemplar bank:
    - `prompts/trait_lanes_v2/extraction_free_exemplar_bank_sliceB.json`
  - dry-run plan artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_free_plan_20260311T220419Z.json`
  - live manifest artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_free_manifest_20260311T220436Z.json`
  - live prompt outputs:
    - `prompts/trait_lanes_v2/extraction_free/persona_drift_from_assistant_eval.jsonl`
    - `prompts/trait_lanes_v2/extraction_free/lying_eval.jsonl`
    - `prompts/trait_lanes_v2/extraction_free/optimism_eval.jsonl`
- [x] Slice B extraction-free outcome:
  - `known`: all three lanes generated `12` eval rows under the isolated trait-lane namespace.
  - `observed`: each lane uses all four available exemplar sets (`n_exemplar_sets_used=4/4`).
  - `observed`: `persona_drift_from_assistant` set usage is slightly skewed (`4/5/2/1`), but the lane still spans the full bank.
- [x] Branch implication:
  - bounded extraction-free prompt-prep parity now exists for both live generated slices (`A` and `B`).
  - the next bottleneck is no longer prompt generation or extraction-free prep; it is choosing the next discriminative screening layer on top of the prepared data.

## Continuation Update (17:14-0500)

- [x] Added generic judge-rubric registration for the live `trait_lanes_v2` lane set without changing legacy core-trait behavior:
  - new shared registry: `scripts/shared/trait_rubrics.py`
  - `scripts/shared/behavioral_eval.py` now imports the shared rubric registry
  - validation:
    - `tests/test_trait_rubrics.py` (`Ran 3 tests ... OK`)
    - `tests/test_shared_behavioral_eval.py` (`Ran 11 tests ... OK`)
- [x] Added and executed a bounded screening-readiness packet based on real branch artifacts:
  - script: `scripts/week2_trait_lane_screening_readiness.py`
  - validation:
    - `tests/test_week2_trait_lane_screening_readiness.py` (`Ran 2 tests ... OK`)
    - `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_*py'` (`Ran 16 tests ... OK`)
  - artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_readiness_20260311T221405Z.json`
- [x] Readiness outcome:
  - `known`: all six live lanes are `screen_ready=true`
  - `known`: `n_live_lanes=6`, `n_screen_ready_lanes=6`
  - `known`: the recommended first actual screening tranche is `slice_a`
    - `assistant_likeness`
    - `honesty`
    - `politeness`
- [x] Branch implication:
  - the lane-expansion branch is no longer blocked on tranche selection, rubric registration, or prompt-prep parity
  - the next highest-value work is the thin actual screening runner for `slice_a`, not another readiness/planning packet and not a third live slice

## Continuation Update (17:43--0500)

- [x] Repaired the first actual `slice_a` screening runner launch path after the cross-app Modal hydration failure.
  - new safe seam: `scripts/week2_trait_lane_behavioral_smoke_run.py` now executes the reused Week 2 kernels inside one runner app via `get_raw_f()` rather than cross-app `.remote()` calls.
  - validation after patch:
    - `python3 -m py_compile scripts/week2_trait_lane_behavioral_smoke_run.py tests/test_week2_trait_lane_behavioral_smoke_run.py`
    - `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_behavioral_smoke_run.py'` (`Ran 4 tests ... OK`)
    - `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_*py'` (`Ran 20 tests ... OK`)
    - `python3 -m unittest discover -s tests -p 'test_shared_behavioral_eval.py'` (`Ran 11 tests ... OK`)
- [x] Relaunched the bounded live `slice_a` screen for `assistant_likeness`, `honesty`, and `politeness`.
  - app: `ap-d6uzMgoxkhGnqgLO6Dc1D9`
  - script: `scripts/week2_trait_lane_behavioral_smoke_run.py`
  - output target: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_20260311T174028Z.json`
- [x] Observed launch state:
  - `known`: the app is active (`ephemeral`, `Tasks=1`)
  - `known`: the launch passed the previous hydration failure point
  - `observed`: extraction sub-run is complete in W&B: `uzvshgjj`
  - `observed`: robustness sub-run is now active in W&B: `7yboubj8`
- [x] Branch implication:
  - the thin actual screening runner is now executing real branch evidence collection for `slice_a`
  - if this app reaches normal terminalization, the next bottleneck becomes interpretation/promotion logic, not launch plumbing

## Continuation Update (18:01--0500)

- [x] Observed further progress on the active bounded `slice_a` screening run (`ap-d6uzMgoxkhGnqgLO6Dc1D9`).
  - `known`: extraction sub-run finished in W&B (`uzvshgjj`)
  - `known`: robustness sub-run finished in W&B (`7yboubj8`)
  - `observed`: new shared Week 2 volume artifact exists:
    - `persona-circuits/week2/extraction_position_ablation_20260311T225037Z.json`
- [x] Interpretation of current run state:
  - `known`: the app is still active (`ephemeral`, `Tasks=1`)
  - `inferred`: the runner has progressed past extraction, bootstrap robustness, and position-ablation into the final branch-specific behavioral-smoke stage
  - `known`: no local terminal screening artifact exists yet under `results/stage1_extraction/trait_lanes_v2/`
- [x] Branch implication:
  - the orchestration fix is holding through all reused Week 2 kernels
  - the remaining risk is judge/behavioral-smoke completion, not the previously failing launch seam


## Continuation Update (18:22--0500)

- [x] The bounded live `slice_a` screening run is now terminalized successfully.
  - app: `ap-d6uzMgoxkhGnqgLO6Dc1D9`
  - final local artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_20260311T174109Z.json`
  - remote screening artifact: `persona-circuits/trait-lanes-v2/screening_execution_20260311T230253Z.json`
- [x] Screening outcome (bounded first-pass evidence, not promotion lock yet):
  - `known`: bootstrap robustness overall pass = `true` for all three lanes
  - `known`: provisional best layers selected by cosine-margin extraction are `assistant_likeness=15`, `honesty=14`, `politeness=15`
  - `known`: behavioral smoke produced at least one coherence-passing condition for all three lanes (`n_with_any_coherence_pass=3/3`)
  - `observed`: best bidirectional effects are `9.0` (`assistant_likeness`, alpha `1.0`), `29.5` (`honesty`, alpha `0.5`), and `33.0` (`politeness`, alpha `2.0`)
- [x] Important bounded limitation from this first screen:
  - `known`: prompt-vs-response position agreement remains below the old `0.7` threshold for all three lanes in the accompanying position-ablation evidence
  - `inferred`: Slice A looks screening-promising, but not yet promotion-complete without an explicit decision on how much response-phase persistence the lane-expansion branch should require
- [x] Branch implication:
  - the first actual trait-lane screening execution is complete end-to-end
  - the next branch decision is now interpretive (`promotion-packet synthesis for Slice A` vs `screen Slice B under the same runner`), not launch-plumbing repair


## Continuation Update (19:03--0500)

- [x] Launched the second bounded live screening tranche, `slice_b` (`persona_drift_from_assistant`, `lying`, `optimism`).
  - app: `ap-fbDtxoplebBzqPKxmDiMXA`
  - output target: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_<timestamp>.json` (in-flight; no local terminal artifact yet)
  - extraction W&B run: `pmif8lxh`
- [x] Observed launch state:
  - `known`: the app is active (`ephemeral`, `Tasks=1`)
  - `known`: the runner cleared initialization and model-load on the same hydration-safe path used by Slice A
  - `inferred`: Slice B is now in the extraction stage of the bounded screen
- [x] Branch implication:
  - the next promotion decision will not be made from Slice A alone unless Slice B fails operationally
  - current bottleneck is collecting the comparative Slice B evidence, not new code or prep work


## Continuation Update (19:18--0500)

- [x] The bounded live `slice_b` screening run is now terminalized successfully.
  - app: `ap-fbDtxoplebBzqPKxmDiMXA`
  - final local artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_20260311T190121Z.json`
  - remote screening artifact: `persona-circuits/trait-lanes-v2/screening_execution_20260312T001714Z.json`
- [x] Screening outcome (bounded comparative evidence, still pre-promotion):
  - `known`: bootstrap robustness overall pass = `true` for all three Slice B lanes
  - `known`: provisional best layers selected by cosine-margin extraction are `persona_drift_from_assistant=16`, `lying=14`, `optimism=16`
  - `known`: behavioral smoke produced at least one coherence-passing condition for all three lanes (`n_with_any_coherence_pass=3/3`)
  - `observed`: selected smoke effects are `-32.25` (`persona_drift_from_assistant`, alpha `0.5`), `38.75` (`lying`, alpha `2.0`), and `9.5` (`optimism`, alpha `1.0`)
- [x] Important comparative limitations after two slices:
  - `known`: prompt-vs-response position agreement remains below the old `0.7` threshold for all six screened lanes across Slice A and Slice B
  - `observed`: `persona_drift_from_assistant` selects a negative bidirectional effect under the current ranking semantics, so branch promotion policy now needs an explicit sign/orientation rule rather than assuming all lane scores are aligned the same way
- [x] Branch implication:
  - the branch now has real bounded screening evidence for two live slices (`A` and `B`)
  - the next highest-value step is synthesis/policy (`A vs B` comparative packet or promotion-policy closure), not another immediate screening launch


## Continuation Update (19:29--0500)

- [x] Generated the first real comparative promotion/synthesis packet over both completed screening slices.
  - artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_promotion_packet_20260312T002859Z.json`
  - inputs:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_20260311T174109Z.json`
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_20260311T190121Z.json`
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_readiness_20260311T221405Z.json`
- [x] Promotion/synthesis outcome:
  - `known`: packet status = `screening_ranked_pending_followons`
  - `known`: recommended follow-on lanes = `lying`, `politeness`, `honesty`
  - `known`: response-phase policy = `tracked_limitation_not_hard_gate` (`n_response_phase_pass=0`, but `n_candidate_or_strong=3`)
  - `known`: orientation policy requires empirical polarity normalization; `persona_drift_from_assistant` is isolated as the orientation-review lane
  - `known`: `assistant_likeness` and `optimism` are currently `weak_positive_hold`
- [x] Branch implication:
  - the branch now has a concrete next-step recommendation that does not require another screening launch first
  - the next highest-value work is targeted follow-on screening for the three recommended lanes (`lying`, `politeness`, `honesty`), especially extraction-free overlap and external smoke where supported


## Continuation Update (19:47--0500)

- [x] Completed the first targeted follow-on validation tranche on the three recommended lanes via extraction-free overlap.
  - app: `ap-VzKsZJqbO6gRQebmsW9Mmj`
  - W&B extraction run: `s2cib7y8`
  - final artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_free_followon_20260312T004752Z.json`
- [x] Follow-on outcome (cross-induction discriminator, still screening-depth only):
  - `known`: overall follow-on pass = `false` (`n_pass=1/3`)
  - `known`: `politeness` is the only passing lane and upgrades to `moderate_overlap`
    - selected layer `15`
    - `mean_cosine=0.2114`
    - `positive_fraction=1.0`
    - `projection_delta_mean=0.6133`
  - `known`: `lying` remains positive but fragile / sub-threshold
    - selected layer `14`
    - `mean_cosine=0.0685`
    - `positive_fraction=0.8333`
    - classification `mixed_or_fragile`
  - `known`: `honesty` falls to `null_overlap`
    - selected layer `14`
    - `mean_cosine=0.0279`
    - `positive_fraction=0.5`
- [x] New branch interpretation after the follow-on artifact:
  - `known`: `politeness` is now the strongest promoted lane in `trait_lanes_v2`
  - `known`: `lying` remains viable only as a weaker follow-on candidate pending external-smoke evidence
  - `known`: `honesty` is no longer a strong promotion candidate under the current screening stack
  - `inferred`: the first promotion-packet ranking should now be treated as superseded informally by the extraction-free follow-on evidence, even before a formal packet refresh
- [x] Next branch move:
  - the highest-value next step is branch-local external-smoke generation/execution for the supported truthfulness lanes (`lying`, `honesty`)
  - no case currently exists for widening to Slice C before that narrower follow-on path is tested


## Continuation Update (19:53--0500)

- [x] Generated the branch-local truthfulness external-smoke prompt sets.
  - summary artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_external_smoke_generation_summary_20260312T005436Z.json`
  - prompt files:
    - `prompts/trait_lanes_v2/external_smoke/honesty_external_smoke.jsonl`
    - `prompts/trait_lanes_v2/external_smoke/lying_external_smoke.jsonl`
- [x] Generation outcome:
  - `known`: both supported truthfulness lanes now have `8` benchmark-style prompts each
  - `known`: category allocation is balanced in both files (`2` each for `direct_fact`, `evidence_pressure`, `social_conflict`, `strategic_concealment`)
  - `observed`: manual spot-checks look plausible and non-duplicative relative to the branch’s earlier extraction/held-out truthfulness prompts
- [x] Branch implication:
  - branch-local truthfulness follow-on inputs are no longer the blocker
  - the next branch bottleneck is execution: a thin external-smoke evaluator for `lying` and `honesty`, or an explicit decision to defer that evaluator and refresh the promotion packet without it


## Continuation Update (20:08--0500)

- [x] Built and launched the thin branch-local truthfulness external-smoke evaluator.
  - script: `scripts/week2_trait_lane_external_smoke_eval.py`
  - tests: `tests/test_week2_trait_lane_external_smoke_eval.py`
  - active app: `ap-vtuIbhZMP0jaYRXjZwdTRF`
- [x] Important launch-path repair:
  - `known`: the first launch attempt (`ap-ZSNEzR9y7q1Zm7yUqcBaaR`) failed before model execution because the reused extraction kernel required both the `wandb` package and the `wandb-key` secret
  - `known`: the evaluator image/secrets were patched accordingly, revalidated locally, and relaunched on the same frozen config
- [x] Current observed state:
  - `known`: the relaunch is past the prior failure seam
  - `observed`: W&B auth loaded successfully and the reused extraction sub-run is active (`a8yx30ua`)
  - `unknown`: no branch-local external-smoke artifact has landed yet; evaluation remains in flight
- [x] Branch implication:
  - the truthfulness external-smoke execution path is now real, not just planned
  - next branch decision still depends on the terminal artifact, not on more prep-only work


## Continuation Update (20:17--0500)

- [x] Closed the truthfulness external-smoke evaluator run.
  - app: `ap-vtuIbhZMP0jaYRXjZwdTRF`
  - final artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_external_smoke_eval_20260312T011734Z.json`
  - extraction sub-run W&B: `a8yx30ua`
- [x] External-smoke outcome:
  - `known`: overall pass = `false` (`n_pass=0/2`)
  - `known`: `honesty` shows one-sided improvement only
    - `plus_vs_baseline=17.5`
    - `baseline_vs_minus=0.125`
    - `plus_minus_delta_ge_threshold=false`
  - `known`: `lying` fails the amplification side on this prompt set
    - `plus_vs_baseline=-3.125`
    - `baseline_vs_minus=18.375`
    - `plus_vs_baseline_positive=false`
    - `plus_minus_delta_ge_threshold=false`
  - `known`: coherence and judge-stability gates pass for both lanes
- [x] Branch interpretation after external smoke:
  - `known`: the truthfulness subfamily did not strengthen under external smoke
  - `inferred`: `politeness` remains the clearest promoted lane in `trait_lanes_v2`
  - `inferred`: `lying` now sits in a weak/mixed bucket (screening positive, extraction-free fragile, external-smoke fail)
  - `inferred`: `honesty` should be treated as non-promoted under the current branch evidence stack
- [x] Next branch move:
  - refresh the promotion packet / branch synthesis around the new truthfulness external-smoke evidence
  - do not widen to Slice C before that ranking/policy refresh is written


## Continuation Update (22:06--0500)

- [x] Refreshed the trait-lane promotion packet with all executed follow-on evidence.
  - superseding packet: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_promotion_packet_20260312T030612Z.json`
  - integrated sources:
    - Slice A screening execution
    - Slice B screening execution
    - extraction-free follow-on
    - truthfulness external-smoke evaluation
- [x] Refreshed branch ranking:
  - `known`: `politeness` is now `promotion_candidate_supported`
  - `known`: `lying` is now `conditional_followon_candidate`
  - `known`: `honesty` is now `deprioritized_after_followons`
  - `known`: `recommended_followon_lanes = [politeness, lying]`
  - `known`: `deprioritized_lanes = [honesty]`
- [x] Branch implication after the refresh:
  - `known`: the branch has a stable winner (`politeness`)
  - `known`: the truthfulness subfamily no longer supports equal-budget follow-on treatment
  - `inferred`: there is no justification for Slice C widening before a separate decision on deeper Week 2 validation for `politeness` and possibly conditional `lying`
- [x] Next branch bottleneck:
  - decide whether to open deeper Week 2 validation for `politeness` only, or `politeness + lying`
  - no more screening-depth breadth work is needed before that decision

## Continuation Update (22:18--0500)
- [x] Added the branch-local deeper-validation launch/readiness packet for promoted trait lanes.
  - script: `scripts/week2_trait_lane_deeper_validation_packet.py`
  - test: `tests/test_week2_trait_lane_deeper_validation_packet.py`
  - artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_packet_20260312T031754Z.json`
- [x] Added append-safe scaling controls to the trait-lane prompt generators.
  - updated: `scripts/shared/trait_lane_generation.py`
  - updated: `scripts/week2_trait_lane_generate_extraction_prompts.py`
  - updated: `scripts/week2_trait_lane_generate_heldout_prompts.py`
  - validation: `python3 -m py_compile ...` passed; `python3 -m unittest discover -s tests -p 'test_trait_lane_generation.py'` passed (`Ran 11 tests ... OK`); `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_*py'` passed (`Ran 35 tests ... OK`).
- [x] Deeper-validation packet outcome:
  - `known`: default selected lane = `politeness`
  - `known`: `launch_recommended_now=false`
  - `known`: branch-local deeper-validation sidecar profile frozen at `48` extraction pairs and `10/10/10` held-out (`30` total)
  - `known`: current `politeness` counts are still `24` extraction / `12` held-out, so the branch is blocked on prompt depth rather than lane ranking
  - `known`: blockers recorded explicitly as `24<48` extraction and `12<30` held-out
  - `known`: full core-upgrade reference remains blocked by a larger gap (`24<100`, `12<50`)
- [x] Append-safe expansion plans emitted for the lead lane.
  - extraction dry-run: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_plan_20260312T031754Z.json`
  - held-out dry-run: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_plan_20260312T031754Z.json`
  - `known`: suggested suffix = `deeperv1`
  - `known`: planned prompt outputs are:
    - `prompts/trait_lanes_v2/politeness_pairs_deeperv1.jsonl`
    - `prompts/trait_lanes_v2/heldout/politeness_heldout_pairs_deeperv1.jsonl`
- [x] Branch implication:
  - the next bottleneck is no longer selection; it is append-safe prompt expansion for `politeness`
  - `lying` remains conditional and should not share equal budget until `politeness` clears the deeper-validation depth gate or a new decision says otherwise

## Continuation Update (22:46--0500)
- [x] Implemented the branch-local deeper-validation execution wrapper for promoted trait lanes.
  - new script: `scripts/week2_trait_lane_deeper_validation_run.py`
  - new test: `tests/test_week2_trait_lane_deeper_validation_run.py`
  - core compatibility patch: `scripts/week2_behavioral_validation_upgrade.py` now supports explicitly disabled cross-trait bleed for sidecar callers
  - validation: `py_compile` passed; `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_deeper_validation_run.py'` passed (`Ran 3 tests ... OK`); `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_*py'` passed (`Ran 39 tests ... OK`)
- [x] Launch contract verified locally for the active branch lane.
  - `known`: local execution-packet resolution confirmed `selected_lane_ids=[politeness]`, `launch_recommended_now=true`, and `condition_rows=18`
  - `known`: active prompt files are:
    - `prompts/trait_lanes_v2/politeness_pairs_deeperv1.jsonl`
    - `prompts/trait_lanes_v2/heldout/politeness_heldout_pairs_deeperv1.jsonl`
- [ ] Bounded remote deeper-validation run is now in flight.
  - app: `ap-LtavuhNzLLXoE0NpA8gtcC`
  - run token: `politeness-deeperv1-20260311T2244Z`
  - W&B extraction sub-run: `tch5s7pg`
  - profile: branch-local deeper Week 2 sidecar (`48` extraction / `30` held-out, split `10/10/10`, relative-only coherence, cross-trait bleed disabled)
  - `known`: launch cleared Modal object creation and W&B auth
  - `unknown`: final extraction summary, selected combo, and quality-gate outcome have not landed yet

## Continuation Update (23:03--0500)
- [x] First bounded `politeness` deeper-validation attempt was closed as an operational failure, not a scientific result.
  - failed app: `ap-LtavuhNzLLXoE0NpA8gtcC`
  - extraction W&B: `tch5s7pg`
  - partial validation W&B: `8cssi3ti`
  - failure mode: eager `vol.reload()` during extraction→validation handoff hit an open Xet log file on the mounted volume
- [x] Patched the resume path and revalidated locally.
  - `known`: `scripts/week2_behavioral_validation_upgrade.py` now supports `checkpoint_reload_before_resume`
  - `known`: `scripts/week2_trait_lane_deeper_validation_run.py` now sets `checkpoint_reload_before_resume=false` for this sidecar wrapper
  - `known`: `py_compile` passed and `python3 -m unittest discover -s tests -p 'test_week2_trait_lane_*py'` passed (`Ran 39 tests ... OK`)
- [ ] Rerun is in flight and has cleared the prior handoff failure.
  - active app: `ap-7uPCLPCfrgGNZ5V70iIeoz`
  - run token: `politeness-deeperv1-20260311T2255Z`
  - W&B extraction sub-run: `t9rb06bq`
  - W&B validation sub-run: `avmoozq4`
  - `known`: extraction completed and the upgraded validation kernel emitted `run_initialized` for trait `politeness`
  - `unknown`: selected combo, gate outcomes, and final artifact have not landed yet

## Continuation Update (23:12--0500)
- [x] The bounded `politeness` rerun cleared the extraction→validation handoff bug.
  - extraction W&B: `t9rb06bq`
  - validation W&B: `avmoozq4`
  - `known`: validation emitted `run_initialized`, `model_loaded`, `split_ready`, and `baseline_start`
- [ ] Rerun did not reach a final artifact and is currently treated as partial / unresolved.
  - app `ap-7uPCLPCfrgGNZ5V70iIeoz` no longer appears in the live app list
  - no final `week2_trait_lane_deeper_validation_execution_*.json` artifact has landed locally
  - remote checkpoint exists at `/persona-circuits/week2/checkpoints/politeness-deeperv1-20260311T2255Z-politeness-upgrade.json`
  - downloaded checkpoint shows `last_stage=split_ready` only
  - `inferred`: the run terminated shortly after entering `baseline_start`, but the exact failure mode is not yet recovered from current evidence
- [ ] Immediate next branch action:
  - recover the most likely failure path from the partial checkpoint / available logs
  - then decide whether the next attempt should keep the single-app wrapper or separate extraction and upgraded validation into distinct launches

## Continuation Update (08:05--0500)
- [x] Logged the new deep trait-lane branch review verbatim and wrote a reconciliation plan before any new branch launch.
  - reviewer packet index: `history/20260312-glp-reviewer-reference-guide.md`
  - verbatim review: `history/reviews/20260312-reviewer-trait-lane-branch-verbatim.md`
  - reconciliation memo: `history/20260312-trait-lane-review-reconciliation-plan-v1.md`
- [x] Branch interpretation has been tightened in response to the review.
  - `known`: `politeness` should currently be treated as the tractability-first lead lane, not as a scientifically preferred new persona lane yet.
  - `known`: `lying` is now under construct-invalid / negative-finding review rather than being treated as a healthy conditional follow-on.
  - `known`: `honesty` remains unresolved and is now better treated as a secondary RLHF-asymmetry lane than as a cleanly closed failure.
  - `known`: response-phase persistence remains unresolved for every screened lane and is now treated as a real pre-launch policy problem, not a soft-pedal-only limitation.
- [ ] Launch freeze before the next trait-lane deeper-validation attempt:
  - compute `politeness` vs `sycophancy` overlap/distinctness
  - re-enable branch-local cross-trait bleed for at least `sycophancy` and `assistant_likeness`
  - explicitly freeze the response-phase persistence policy before collecting more evidence
  - split extraction and upgraded validation into separate launches instead of reusing the single-app wrapper
- [ ] Secondary branch remediation items opened by the review:
  - add a null-lane control plan for the screening pipeline
  - add prompt-sensitivity analysis before interpreting `politeness` as stable
  - strengthen negative/integration test coverage on the promotion/deeper-validation stack

## Continuation Update (08:25--0500)
- [x] Closed the first distinctness check requested by the branch review.
  - local mirror artifacts:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_persona_vectors_sliceA_20260311T224305Z.pt`
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_vector_extraction_summary_sliceA_20260311T224305Z.json`
  - overlap diagnostic:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_overlap_diagnostic_20260312T131958Z.json`
- [x] Distinctness readout changed materially.
  - `known`: `politeness` vs core `sycophancy` overlap is low under the requested cosine check:
    - selected-pair overlap (`sycophancy L12` vs `politeness L15`) = `0.065`
    - same-layer max abs overlap across `11..16` = `0.181`
    - cross-layer max abs overlap across `11..16 x 11..16` = `0.181`
  - `known`: the same diagnostic also shows that the stronger current confound is `assistant_likeness`, not `sycophancy`:
    - `politeness` vs `assistant_likeness` same-layer cosine ranges `0.432 -> 0.628`
    - max abs same-layer overlap = `0.628` at layer `16`
  - `inferred`: the reviewer's `sycophancy`-equivalence concern is weakened, but the assistant-style / tone-transfer confound is now the main distinctness risk.
- [ ] Updated next branch priority after the overlap diagnostic:
  - re-enable branch-local bleed against `sycophancy` and `assistant_likeness`
  - keep the launch freeze in place until that bleed path exists and the persistence policy is explicitly frozen

## Continuation Update (08:27--0500)
- [x] Closed the branch-local bleed/reference remediation item with fresh packet artifacts.
  - refreshed deeper-validation packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_packet_20260312T132600Z.json`
  - refreshed dry-run execution packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_dryrun_packet_20260312T132621Z.json`
  - `known`: the branch-local deeper-validation profile now explicitly carries:
    - `cross_trait_bleed_enabled=true`
    - `cross_trait_bleed_reference_traits=["sycophancy","assistant_likeness"]`
    - `cross_trait_bleed_max_fraction=0.3`
  - `known`: the dry-run execution packet preserves those reference rubrics in the actual launch contract for `politeness`.
- [ ] Remaining launch-freeze items before the next `politeness` deeper-validation attempt:
  - explicitly freeze the response-phase persistence policy
  - split extraction and upgraded validation into separate launches instead of the single-app wrapper
  - design follow-ons for null-lane and prompt-sensitivity checks

## Continuation Update (08:40--0500)
- [x] Closed the remaining launch-freeze governance items for the next `politeness` deeper-validation attempt.
  - frozen persistence policy:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_response_phase_policy_packet_20260312T133907Z.json`
  - refreshed deeper packet with policy snapshot + split-launch mode:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_packet_20260312T133907Z.json`
  - split dry-run packets:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_split_extract_dryrun_packet_20260312T133918Z.json`
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_split_validate_dryrun_packet_20260312T133918Z.json`
  - `known`: split extraction is launch-ready.
  - `known`: split validation is structurally ready but correctly blocked until an extraction vectors artifact exists (`missing_vectors_pt`).
- [ ] Next active branch action:
  - run the split extraction-only `politeness` deeper-validation phase
  - if extraction succeeds, feed its persisted local vectors artifact into the split validation launch
- [ ] Secondary branch remediation items still open but non-blocking for the immediate split extraction step:
  - add a null-lane control plan for the screening pipeline
  - add prompt-sensitivity analysis before treating `politeness` as stable beyond the current branch scope

## Continuation Update (08:52--0500)
- [x] Completed the split extraction-only `politeness` phase.
  - extraction packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_split_extract_packet_20260312T134121Z.json`
  - extraction report:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_extraction_20260312T134121Z.json`
  - local vectors artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_vectors_20260312T134121Z.pt`
  - W&B extraction run: `5nohpxts`
  - `known`: extraction completed cleanly; no handoff/runtime anomaly occurred.
- [~] Split validation-only rerun is currently active against the persisted extraction artifact.
  - first validation attempt failed on a core-only rubric map (`KeyError: 'politeness'`) after `baseline_start`; this was patched in `week2_behavioral_validation_upgrade.py`
  - rerun app: `ap-jxpU3gNy7PWucKaw0lskSV`
  - rerun W&B: `4ngyn0m4`
  - `observed`: rerun has cleared `run_initialized`, `model_loaded`, `split_ready`, and `baseline_start`
  - `inferred`: the split redesign plus shared-rubric patch has moved the branch past the prior wrapper/rubric failure zone, but no final validation artifact exists yet
- [ ] Next branch action after the validation rerun terminalizes:
  - if success: write POST-RUN closeout and interpret `politeness` under explicit bleed + persistence limitations
  - if failure: capture the new failure mode and decide whether the branch is blocked on judge/runtime or on science


## Continuation Update (13:52--0500)
- [x] Completed the split validation-only `politeness` rerun against the persisted extraction artifact.
  - app: `ap-jxpU3gNy7PWucKaw0lskSV`
  - W&B validation rerun: `4ngyn0m4`
  - final artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_validation_20260312T134851Z.json`
- [x] The rerun now gives a real branch-local upgraded Week 2 readout for `politeness`.
  - `known`: selected configuration = `layer 13`, `alpha 2.0`
  - `known`: selected-test bidirectional effect = `46.3333`
  - `known`: judge calibration is strong (`kappa=0.8387`, pairwise sign agreement `1.0`, parse-fail rate `0.0`)
  - `known`: coherence passes under the frozen relative-only policy (`coherence_drop=-6.3333`)
  - `known`: capability proxy passes (`degradation=-0.0333`)
  - `known`: specificity passes (`neutral_shift=1.2`)
- [x] The same artifact also closes the main distinctness risk in a negative direction.
  - `known`: overall branch-local quality gates fail (`overall_pass=false`)
  - `known`: cross-trait bleed fails (`off_target_to_target_ratio=1.0194`)
  - `known`: the dominant off-target effect is `assistant_likeness=47.2333`, slightly larger than the target-lane effect `46.3333`
  - `known`: control-test gate also fails (`control_test_score=50.0`)
- [ ] Next branch decision is now interpretive rather than operational:
  - decide whether `politeness` should be treated as a strong-but-non-distinct assistant-style lane, a remediable lane requiring tighter controls, or a negative result for independent persona-circuit promotion


## Continuation Update (14:28--0500)
- [x] Emitted a branch adjudication packet over the completed screening, follow-on, overlap, and deeper-validation evidence stack.
  - artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_adjudication_packet_20260312T192833Z.json`
- [x] The adjudication packet resolves the branch-level promotion question under current evidence.
  - `known`: branch status = `no_independent_promotion_under_current_evidence`
  - `known`: `politeness` remains behaviorally strong but is classified as `strong_non_distinct_assistant_style_lane`
  - `known`: `lying` is now classified as `negative_finding_construct_invalid_current_protocol`
  - `known`: `honesty` is now classified as `secondary_unresolved_rlhf_asymmetry_lane`
- [x] Current branch recommendation is now explicit rather than inferred from multiple artifacts.
  - `known`: no new trait lane is recommended for independent promotion into the main persona-circuit claim path
  - `known`: if the branch continues, the next work should target assistant-style distinctness, not another blind `politeness` rerun
- [ ] Next branch decision is strategic:
  - either freeze the trait-lane branch as a useful negative/triage result under current evidence
  - or open a new redesign tranche focused on `assistant_likeness` distinctness, null-lane control, and prompt-sensitivity before any further lane-promotion attempt


## Continuation Update (14:49--0500)
- [x] Opened the trait-lane redesign tranche with concrete branch artifacts rather than leaving null-control and prompt-sensitivity as prose TODOs.
  - null-control packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_null_control_packet_20260312T194931Z.json`
  - prompt-sensitivity packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_prompt_sensitivity_packet_20260312T194931Z.json`
  - combined redesign packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_redesign_packet_20260312T194947Z.json`
- [x] The redesign tranche now has an explicit ordered sequence.
  - `known`: next remote priority = `run_null_control_screen`
  - `known`: second remote priority = `run_prompt_sensitivity_sidecar`
  - `known`: assistant-likeness-specific distinctness work is deferred until after those two controls are observed
- [x] The branch remains frozen against premature claim expansion.
  - `known`: redesign packet forbids another blind `politeness` rerun
  - `known`: redesign packet forbids independent lane promotion and Slice C widening under the current evidence stack
- [ ] Next branch action if execution continues:
  - implement or launch the null-control screening lane defined in `week2_trait_lane_null_control_packet_20260312T194931Z.json`

## Continuation Update (15:16--0500)
- [x] Materialized the null-control redesign execution path instead of leaving it as a planning-only packet.
  - new generator: `scripts/week2_trait_lane_generate_null_control_prompts.py`
  - new runner: `scripts/week2_trait_lane_null_control_run.py`
  - new tests:
    - `tests/test_week2_trait_lane_generate_null_control_prompts.py`
    - `tests/test_week2_trait_lane_null_control_run.py`
  - local validation: full `test_week2_trait_lane_*py` suite passes (`Ran 57 tests ... OK`)
- [x] Generated matched null-control prompt files for the lead source lane `politeness`.
  - prompt summary artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_null_control_prompt_summary_20260312T200607Z.json`
  - prompt files:
    - `prompts/trait_lanes_v2/null_controls/politeness_label_permutation_null_v1_pairs_20260312T200607Z.jsonl`
    - `prompts/trait_lanes_v2/null_controls/politeness_label_permutation_null_v1_heldout_pairs_20260312T200607Z.jsonl`
  - `known`: extraction rows are exactly `50%` flipped by category; held-out rows are near-balanced (`14/30` flipped overall).
- [~] Null-control screening execution is currently active.
  - app: `ap-1tXFTxszQBLo98Z3Bx1Ewa`
  - state: `ephemeral (detached)`
  - execution packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_null_control_execution_packet_20260312T201239Z.json`
  - W&B extraction run: `8mxdd2bh`
  - `observed`: run has cleared the prior raw-`python` hydration failure class and is executing remotely through `modal run`
- [ ] Next branch action after terminalization:
  - write POST-RUN closeout for the null-control execution
  - decide whether the pipeline remains below the false-positive frontier before moving to prompt-sensitivity

## Continuation Update (15:32--0500)
- [x] Completed the first redesign execution step: matched null-control screen for `politeness`.
  - final artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_null_control_execution_20260312T202047Z.json`
  - app: `ap-HAH6nNXETOH7hY8feukAD0`
  - `known`: null-control result = `screening_status=hold`
  - `known`: `overall_false_positive_alert=false`
  - `known`: stability remains poor by construction and by measurement (`bootstrap_p05=-0.6763`, `train_vs_heldout=0.2524`, `response_phase_persistence=0.2808`)
  - `known`: the best smoke condition is modest in absolute terms (`14.25`) and negative in oriented terms (`-14.25`), so the control does not cross the promotion frontier
- [x] The redesign branch has now advanced exactly as precommitted.
  - null-control step: complete / passed
  - next step: `prompt_sensitivity` sidecar for `politeness`
- [ ] Next branch action:
  - implement and run the bounded prompt-sensitivity sidecar defined in `week2_trait_lane_prompt_sensitivity_packet_20260312T194931Z.json`

## Continuation Update (15:48--0500)
- [x] Materialized the second redesign execution step for `politeness`: prompt-sensitivity.
  - new generator: `scripts/week2_trait_lane_generate_prompt_sensitivity_prompts.py`
  - new runner: `scripts/week2_trait_lane_prompt_sensitivity_run.py`
  - new tests:
    - `tests/test_week2_trait_lane_generate_prompt_sensitivity_prompts.py`
    - `tests/test_week2_trait_lane_prompt_sensitivity_run.py`
  - local validation: full `test_week2_trait_lane_*py` suite passes (`Ran 63 tests ... OK`)
- [x] Generated the bounded perturbed prompt subset from the frozen packet.
  - prompt summary artifact:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_prompt_sensitivity_prompt_summary_20260312T204520Z.json`
  - output prompt files:
    - `prompts/trait_lanes_v2/prompt_sensitivity/politeness_prompt_sensitivity_extraction_20260312T204520Z.jsonl`
    - `prompts/trait_lanes_v2/prompt_sensitivity/politeness_prompt_sensitivity_heldout_20260312T204520Z.jsonl`
  - `known`: perturbation audit stayed bounded (`mean_similarity~0.382 extraction`, `~0.370 heldout`; `max_similarity<=0.576`)
- [~] Prompt-sensitivity execution is currently active.
  - app: `ap-OzOcd7ie5WdQWNKECaM7eY`
  - state: `ephemeral (detached)`
  - execution packet:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_prompt_sensitivity_execution_packet_20260312T204543Z.json`
  - W&B extraction run: `k2d1xi7p`
  - `observed`: the app has cleared creation and entered the perturbed-extraction subrun
- [ ] Next branch action after terminalization:
  - write POST-RUN closeout for the prompt-sensitivity sidecar
  - decide whether wording fragility or assistant-distinctness remains the primary redesign blocker
