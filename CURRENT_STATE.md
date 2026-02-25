# Current State

**Last updated:** 2026-02-25T09:11:21-0600  
**Updated by:** codex-gpt5 (session010)  
**Status:** in_progress  
**Current phase:** Phase 1 — Persona Extraction (Week 2)

## Active Phase

Phase 1 is active. Week 1 infrastructure milestone is closed with a pass, and Week 2 extraction has started with first vector artifacts produced.

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
  - Run: `https://wandb.ai/sohailm/persona-circuits/runs/mud40b2t`
  - Artifacts: `results/stage1_extraction/week2_vector_extraction_summary_20260225T010808Z.json`, `results/stage1_extraction/week2_persona_vectors_20260225T010808Z.pt`
- [ ] Identify optimal layers per trait (behavioral criterion)
  - Preliminary (activation-margin proxy): layer 16 for sycophancy/evil/hallucination
  - Final criterion pending Week 2 behavioral validation (§6.2.3)

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
  - Planning artifacts: `results/stage1_extraction/week2_upgrade_parallel_plan_20260225T141045Z.json`, `scratch/week2_upgrade_launch_commands.sh`
- [ ] Validate all 3 persona vectors (steering works)
  - Status: frozen baseline run (`run=8b3fp37q`) failed reliability gates; upgraded smoke reruns confirmed patched execution paths; primary-tier evidence tranche is now running (`sycophancy: ty3k95jg / ap-kqV4eWSGwrVt8nKE4ZA3NF`, `evil: t8lajipl / ap-SAFulvrYqaddpusCHafEzB`, `hallucination: 81rimxnc / ap-Ae34zytuXoYv11ksGBM5XH`)
  - Observed selected combos (provisional only): sycophancy `(15, 3.0)`, evil `(16, 3.0)`, hallucination `(16, 2.5)`
  - Blocking issues: kappa <0.6 for all traits; hallucination parse-fallback risk; evil steering asymmetry
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
- Post-patch smoke check for upgraded runner (after `top_k=None` generation fix) completed successfully:
  - Modal app: `ap-12Do4tY1DwxrIafMY9lWtr`
  - W&B run: `i1pg2y8c`
  - Artifact: `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260225T131007Z.json` (execution smoke only; tiny-sample gates not used for scientific closeout)
- Post-reviewer patch smoke check (strict parser + lockbox + bleed gate + control norm matching) completed successfully:
  - Modal app: `ap-ICdOlw6drTUL50qWgc6edW`
  - W&B run: `j48ylybc`
  - Artifact: `results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260225T135828Z.json` (execution smoke only; tiny-sample gates not used for scientific closeout)
- Primary-tranche run status snapshot (as of 2026-02-25T09:11:21-0600):
  - sycophancy: `ap-kqV4eWSGwrVt8nKE4ZA3NF` (`state=ephemeral (detached)`, `tasks=1`, `stopped_at=None`)
  - evil: `ap-SAFulvrYqaddpusCHafEzB` (`state=ephemeral (detached)`, `tasks=1`, `stopped_at=None`)
  - hallucination: `ap-Ae34zytuXoYv11ksGBM5XH` (`state=ephemeral (detached)`, `tasks=1`, `stopped_at=None`)
  - Local artifact directory has no new primary result JSON yet (only earlier smoke artifacts).

## Completed Phases

- Phase 0 — Infrastructure (Week 1) completed on 2026-02-24.

## Blocking Issues

None.

## Current Risks / Notes

- `observed`: Sample SAE reconstruction cosines in Week 1 infra checks were low (Llama layer16: 0.1278; Gemma layer12: 0.4526).
- `inferred`: This is not a Week 2 blocker for vector extraction, but remains a Week 3 interpretation gate.
- Required follow-up remains tracked in `THOUGHT_LOG.md` pending actions: rerun reconstruction sanity with stage-appropriate hooks before trusting decomposition claims.
- `known`: Full upgraded parallel plan is broad and expensive if launched all-at-once (15 jobs; latest estimate ~53k primary judge calls after stricter controls); should be launched in tranches.
- `known`: Latest prelaunch gap-check artifact fails external transfer + extraction A/B robustness gates; treat as open risk until rerun on primary-selected combos.

## Next Action

1. Do **not** relaunch Week 2 primary jobs while these app IDs remain active: `ap-kqV4eWSGwrVt8nKE4ZA3NF`, `ap-SAFulvrYqaddpusCHafEzB`, `ap-Ae34zytuXoYv11ksGBM5XH`.
2. Monitor those three runs to terminal completion and write post-run checkpoints with artifact paths and gate outcomes.
3. Execute manual 5-example judge concordance spot-check on upgraded primary outputs.
4. Re-run prelaunch gap checks (external transfer + extraction A/B) on the newly selected primary combos before Week 2 closeout claim.
5. Run rollout-stability sensitivity check on selected combos (`confirm_rollouts_per_prompt: 3 -> 5`) before Week 2 closeout claim.
6. Require replication consistency (primary + at least 2 replication seeds passing) before Week 2 closeout.
7. After closeout criteria pass, proceed to Week 3 SAE decomposition.

## Handoff Resume Protocol (if session restarts now)

1. Verify in-flight app status (no relaunch unless app is stopped/failed):
   - `modal app list --json`
   - confirm status for `ap-kqV4eWSGwrVt8nKE4ZA3NF`, `ap-SAFulvrYqaddpusCHafEzB`, `ap-Ae34zytuXoYv11ksGBM5XH`
2. Check for newly written primary artifacts:
   - `ls -lt results/stage1_extraction/week2_behavioral_validation_upgrade_* | head`
3. If any app reaches terminal state, immediately write `POST-RUN` entry in `SCRATCHPAD.md` with:
   - app ID, W&B run URL, outcome, key metrics/gates, artifact path.
4. Only after all three primary runs finish:
   - compile gate summary across traits
   - run manual judge concordance spot-check
   - run updated prelaunch gap checks on primary-selected combos
5. Launch replication/stress only if primary evidence review is complete and documented.

---

## Phase Tracker

| Phase | Status | Start Date | End Date | Key Result |
|-------|--------|------------|----------|------------|
| 0. Infrastructure | completed | 2026-02-24 | 2026-02-24 | Modal/W&B/model/SAE/CLT setup validated; prompt datasets regenerated and strict-audit passed |
| 1. Persona Extraction | in_progress | 2026-02-24 | | Contrastive vectors extracted; first frozen behavioral run completed but failed reliability gates (needs calibrated rerun) |
| 2. SAE Decomposition | not_started | | | |
| 3. Circuit Tracing | not_started | | | |
| 4. Causal Validation | not_started | | | |
| 5. Cross-Persona Analysis | not_started | | | |
| 6. Gemma-2-2B Validation | not_started | | | |
| 7. Writing | not_started | | | |

## Hypothesis Status

| Hypothesis | Status | Current Evidence | Confidence |
|------------|--------|-----------------|------------|
| H1 (Coherence) | untested | Stage1 vectors extracted; no decomposition/concentration evidence yet | low |
| H2 (Necessity) | untested | No causal ablations yet | low |
| H3 (Sufficiency) | untested | No sufficiency tests yet | low |
| H4 (Cross-Persona) | untested | No overlap/routing analysis yet | low |
| H5 (Router) | untested | No router search yet | low |
