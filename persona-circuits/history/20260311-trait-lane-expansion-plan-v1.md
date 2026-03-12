# Trait-Lane Expansion Plan v1 — Reconciled With Current Core Progress

## Status
- Status: planning artifact
- Date: 2026-03-11
- Scope: add a new Stage-1/Week-2 breadth-first trait-lane screening branch without breaking or superseding the current core experiment
- This plan does **not** authorize immediate new launches. It defines the branch, sequencing, reuse strategy, and safeguards.

## 1. Executive Summary
The project should add a **lane-expansion screening branch** that explores five paper-backed candidate families while preserving the current core line (`sycophancy`, `machiavellian_disposition`, `hallucination` as negative control, active Stage4 H3 work).

The branch should be deliberately scoped:
- broad at Stage 1 / Week 2 screening depth,
- narrow at later stages,
- non-invasive to the current core code path until winners are promoted.

The right operational model is:
1. preserve the current core line,
2. freeze the active H3 run from interference,
3. reuse existing Week 2 infrastructure wherever possible,
4. screen new candidate families cheaply,
5. promote only winning lanes into the expensive validation path.

## 2. Current-State Reconciliation

### 2.1 What is currently active
- `known`: one core Modal run is active:
  - app: `ap-mCOxAI9Xp7WCZoxpslD6Yi`
  - description: `persona-circuits-week3-stage4-behavioral-sufficiency`
  - state from latest local check: `ephemeral (detached)`, `Tasks=1`
- `known`: this run is a bounded claim-grade H3 tranche on `sycophancy` and remains the critical path for the current mechanistic claim.

### 2.2 What must remain untouched while this run is active
1. No relaunch or superseding Stage4 H3 run for the same lane.
2. No mutation of core claim-lane decisions (`sycophancy`, `machiavellian_disposition`, `hallucination` negative-control status) without an explicit new decision packet.
3. No edits that silently change default behavior of the current H3 path.
4. No overwriting of current artifacts, manifests, or results-index entries.

### 2.3 What can proceed safely now
1. Planning artifacts
2. Literature refresh docs
3. Registry/schema design
4. Non-invasive code planning for future lane screening
5. Reuse audit and test-plan drafting

## 3. Strategic Objective of the New Branch
The new branch is not “start a second experiment.”

It is:
- a **breadth-first Stage-1/Week-2 screen** for better mechanistic targets,
- run under a separate planning/governance lane,
- with explicit promotion gates before any Stage2+ commitment.

This branch exists to answer:
- Are we bottlenecked by trait choice?
- Which trait families are better aligned with the project’s mechanistic question?
- Which lanes are tractable enough to justify deeper decomposition and causal validation?

## 4. Candidate Family Set
All five candidate families should be explored.

### Family A — Honesty / Lying / Deception
Initial micro-lanes:
- `honesty`
- `lying`
- `deception` (screening lane)
- optional later extension: `strategic_deception`

Why include:
- strongest literature cluster after sycophancy
- better construct separation than hallucination

Main risk:
- overlaps with strategy/intention rather than pure persona

### Family B — Assistant-Likeness / Persona Drift
Initial micro-lanes:
- `assistant_likeness`
- `persona_drift_from_assistant`

Why include:
- closest fresh literature match to the project’s PSM framing

Main risk:
- broad construct; external benchmarks less standardized

### Family C — Light Style/Persona Family
Initial micro-lanes:
- `politeness`
- `optimism`
- `apathy`
- `humor`

Why include:
- explicitly present in the persona-vector literature
- likely lower safety confounding

Main risk:
- may be mechanistically cleaner but less important scientifically

### Family D — Big Five Slice
Initial micro-lane:
- `agreeableness`

Why include:
- paper-backed personality framing
- may explain or contextualize sycophancy

Main risk:
- entanglement/interference and open-ended unreliability

### Family E — Refusal / Harmlessness
Initial micro-lanes:
- `refusal_expression`
- `harmfulness_judgment`
- optional derived comparison: `harmlessness`

Why include:
- unusually strong mechanistic literature
- strong comparison class against persona-like lanes

Main risk:
- not obviously a persona construct; can drift toward safety-policy monitoring

## 5. Core Principle: Family Breadth, Lane Promotion, Not Full-Matrix Explosion
The project should not run all new lanes through the full current pipeline.

Recommended expansion pattern:
1. Screen all five families at shallow Stage-1/Week-2 depth.
2. Promote only the top `2-3` individual lanes to deeper Week 2 validation.
3. Promote only the top `1-2` beyond that into Stage2+ mechanistic work.

This is mandatory for time, compute, and scientific discipline.

## 6. Reuse Inventory: What Already Exists and Must Be Reused

### 6.1 Prompt generation and auditing
Existing reusable components:
- `scripts/generate_prompt_datasets.py`
- `scripts/generate_week2_heldout_prompts.py`
- `scripts/prompt_quality_rules.py`
- `scripts/audit_prompt_datasets.py`
- `tests/test_prompt_quality_rules.py`
- `tests/test_week2_heldout_scaling.py`

Reuse intent:
- Keep the current scripts behaviorally frozen for legacy/core lanes.
- Reuse their category/spec/audit patterns when building new lane-screening prompt generators.

### 6.2 Extraction and diagnostics
Existing reusable components:
- `scripts/week2_extract_persona_vectors.py`
- `scripts/week2_vector_diagnostics.py`
- `scripts/week2_extraction_position_ablation.py`
- `scripts/week2_extraction_robustness_bootstrap.py`
- `scripts/week2_extraction_seed_replication.py`
- tests for the above

Reuse intent:
- These are already most of the Stage-1 screening stack.
- Minimal changes should be preferred over a rewrite.

### 6.3 Behavioral validation and judge stack
Existing reusable components:
- `scripts/shared/behavioral_eval.py`
- `scripts/week2_behavioral_validation.py`
- `scripts/week2_behavioral_validation_upgrade.py`
- `scripts/week2_glp_sidecar_validation.py`
- `scripts/week2_glp_sidecar_analysis.py`
- `scripts/week2_coherence_policy_diagnostic.py`
- `scripts/week2_cross_trait_bleed_sensitivity.py`
- `scripts/week2_manual_concordance_policy_closure.py`
- `scripts/week2_capability_suite_spec.py`

Reuse intent:
- The upgraded Week 2 runner is too trait-hardcoded to be the first vehicle for all new lanes.
- The judge helper stack and policy diagnostics should be reused.
- The existing GLP sidecar path is a proof-of-pattern that isolated sidecar runners can be added without mutating the active core lane machinery.
- First-pass screening should use a thinner new sidecar-style wrapper rather than immediately generalizing the whole upgraded runner.

### 6.4 Extraction-free validation
Existing reusable components:
- `scripts/week2_prepare_extraction_free_eval.py`
- `scripts/week2_extraction_free_activation_eval.py`
- `scripts/week2_extraction_free_reanalysis.py`
- modal variant and tests

Reuse intent:
- Use only for persona-like lanes.
- Do not force extraction-free evaluation on refusal/harmfulness lanes where the comparison may be conceptually mismatched.

### 6.5 External transfer / gap checks
Existing reusable components:
- `scripts/week2_prelaunch_gap_checks.py`
- `scripts/week2_machiavellian_external_transfer.py`
- related tests and policy artifacts

Reuse intent:
- Reuse the architecture of external smoke testing.
- Replace lane-specific benchmark logic with registry-based hooks where needed.

## 7. New Artifacts To Add
The lane-expansion branch should add new files rather than destabilize current defaults.

### 7.1 New config / registry layer
1. `configs/trait_lanes_v2.yaml`
2. `scripts/shared/trait_lane_registry.py`

Registry fields should include:
- `family_id`
- `lane_id`
- `display_name`
- `high_vs_low_construct`
- `persona_class` (`persona_like`, `strategy_like`, `safety_like`, `style_like`, `epistemic_like`)
- `prompt_generator_template`
- `heldout_template`
- `judge_rubric_id`
- `requires_ground_truth`
- `supports_extraction_free`
- `supports_external_transfer`
- `external_transfer_benchmark_type`
- `known_confounds`
- `promotion_gate_profile`

### 7.2 New planning / construct docs
1. `history/20260311-trait-lane-literature-refresh-v1.md`
2. `history/20260311-trait-lane-expansion-plan-v1.md`
3. `history/construct_cards/` (new folder)
   - one construct card per candidate lane family / micro-lane

### 7.3 New screening-specific scripts
Recommended new wrappers, not immediate rewrites of the hardened core runner:
1. `scripts/week2_trait_lane_prompt_screen.py`
2. `scripts/week2_trait_lane_heldout_screen.py`
3. `scripts/week2_trait_lane_behavioral_smoke.py`
4. `scripts/week2_trait_lane_promotion_packet.py`

Recommended new result namespace:
- `results/stage1_extraction/trait_lanes_v2/`
- `prompts/trait_lanes_v2/`

Optional shared helper extraction only after parity tests:
- `scripts/shared/trait_prompt_generation.py`
- `scripts/shared/trait_rubrics.py`

## 8. Phased Execution Plan

### Phase P0 — Governance Freeze and Isolation
Before any implementation beyond docs:
1. Record a decision that lane expansion is a **parallel planning branch**, not a superseding core pivot.
2. Freeze a rule: no lane-expansion remote launches while the active H3 app is still running.
3. Keep current `experiment.yaml` trait defaults unchanged until promotion rules exist.
4. Keep all current Stage2–Stage5 artifacts and claim-trait mappings untouched.

Deliverables:
- DECISION entry
- CURRENT_STATE update
- RESULTS_INDEX entries for the new planning artifacts

### Phase P1 — Construct Design and Lane Registry
1. Create `trait_lanes_v2.yaml` with all five families and their initial micro-lanes.
2. Write construct cards for each lane to prevent conflation:
   - `honesty` vs `lying` vs `deception`
   - `assistant_likeness` vs generic roleplay
   - `agreeableness` vs `sycophancy`
   - `refusal_expression` vs `harmfulness_judgment`
   - `hallucination` vs `uncertainty/calibration`
3. For each lane, define whether it is:
   - eligible for extraction-free overlap testing,
   - eligible for external benchmark smoke,
   - eligible for cross-trait bleed sensitivity.

Deliverables:
- registry file
- construct cards
- decision packet locking lane definitions

### Phase P2 — Build the Minimal Screening Harness
Principle: do **not** generalize the entire Week 2 upgraded runner first.

Instead:
1. Generalize `week2_extract_persona_vectors.py` only as much as needed to accept registry-defined selected lanes with nonbreaking defaults.
2. Reuse `week2_extraction_robustness_bootstrap.py` and `week2_extraction_position_ablation.py` with registry-driven lane lists.
3. Build a new thin behavioral-smoke runner for lane screening using:
   - shared chat formatting
   - shared judge parse/retry logic
   - simple small alpha grid (`0.5, 1.0, 2.0`)
   - relative coherence only
   - no full Week2 lockbox/cross-bleed bundle yet
4. Add generic rubric registration rather than hardcoding every new lane into the core upgraded runner immediately.

Deliverables:
- non-invasive screening wrapper(s)
- tests proving legacy behavior is unchanged for current three traits

### Phase P3 — Generate Breadth-First Screening Data
Per micro-lane, generate:
- extraction pairs: `24`
- held-out evaluation prompts: `12`
- extraction-free prompts: `12` for eligible persona-like lanes
- external smoke prompts: `8` where benchmarkable

Rules:
- no overwrite of existing prompt files
- use a new namespace such as `prompts/trait_lanes_v2/`
- keep hashes/manifests from the start
- audit prompt leakage against both current train and held-out prompt sets

Deliverables:
- prompt files
- audit report
- overlap/manifest report

### Phase P4 — Run Stage-1 / Week-2 Screening
For each micro-lane:
1. vector extraction at layers `11-16`
2. bootstrap subset stability
3. train-vs-heldout cosine
4. prompt-last vs response-mean diagnostic
5. tiny behavioral alpha sweep (`0.5, 1.0, 2.0`)
6. relative coherence smoke
7. extraction-free overlap if eligible
8. external transfer smoke if eligible

Do not run Stage2+ here.

Deliverables:
- one screening artifact per lane
- one aggregate ranking artifact

### Phase P5 — Promotion Packet
For each lane, score:
- literature support
- construct clarity
- prompt quality / audit health
- bootstrap stability
- train-vs-heldout cosine
- behavioral steerability
- response-phase persistence
- coherence preservation
- benchmark smoke compatibility
- confound risk

Promotion policy:
- promote top `2-3` lanes to deeper Week 2 validation
- hold the rest as documented negatives or tractability references

### Phase P6 — Only Then: Deeper Validation for Promoted Lanes
For promoted lanes only:
1. decide whether they deserve full upgraded Week 2 validation
2. decide whether they can supersede or supplement existing core lanes
3. only after that consider Stage2 decomposition

## 9. Family-Specific Evaluation Notes

### Honesty / Lying / Deception
- Should not be collapsed into hallucination.
- Prefer separate rubrics for truthful accuracy, instructed lying, and strategic deception.
- Benchmarking should rely on truth/deception references, not TruthfulQA alone.

### Assistant-Likeness
- Needs custom construct cards and likely custom held-out prompts.
- Likely best treated as a broad persona-space lane, not a standard “high/low trait score” lane with one naive rubric.

### Light Style/Persona Family
- Best candidate for low-confound screening.
- Good place to test whether the pipeline itself can produce cleaner mechanistic signals.

### Agreeableness
- Use as a broader parent-lane test around sycophancy.
- Compare directly against sycophancy rather than treating it as independent by default.

### Refusal / Harmlessness
- Must split `harmfulness_judgment` from `refusal_expression`.
- Do not reuse the old evil/harmful-content framing here.

## 10. No-Regression Safeguards
1. No new lane should modify current claim-lane artifacts.
2. No existing script should change default trait lists silently.
3. New lane artifacts must live under new names / directories.
4. New configs must not replace `experiment.yaml` as the live source for the current H3 run.
5. Current Stage2–Stage5 claim files must remain interpretable without awareness of the new branch.
6. Any refactor that touches legacy scripts must come with parity tests for current three-trait behavior.

## 11. Secondary Pass — Duplication / Reuse Audit
This section exists to ensure we do not recreate infrastructure that already exists.

### Findings from duplication audit
- Prompt generation already exists and should be adapted, not reimagined.
- Held-out generation already exists and should be adapted, not rebuilt.
- Extraction, bootstrap robustness, position ablation, and extraction-free evaluation already exist.
- Judge formatting, parsing, rate limiting, and retries already exist.
- Policy diagnostics for coherence, capability-scope, cross-trait bleed, and manual concordance already exist.

### Consequence
The first coding tranche for lane expansion should mostly add:
- registry/config
- construct cards
- thin wrappers
- generic rubric registration

It should **not** start with a new end-to-end evaluation framework.

## 12. Tertiary Pass — Failure Mode / Interference Audit
This section exists to ensure the new branch does not damage current progress.

### Risk 1 — Active-run interference
- Failure mode: new launches or silent default changes confuse interpretation while H3 is live.
- Mitigation: no lane-expansion remote launches until `ap-mCOxAI9Xp7WCZoxpslD6Yi` terminalizes and is ingested.

### Risk 2 — Core-governance drift
- Failure mode: new lanes implicitly supersede Week 2 scope before formal promotion.
- Mitigation: treat lane expansion as a separate planning and screening branch until promotion packet is accepted.

### Risk 3 — Trait conflation
- Failure mode: honesty, lying, hallucination, refusal, and harmfulness get treated as synonyms.
- Mitigation: construct cards and registry typing are mandatory before prompt generation.

### Risk 4 — Screening runner scope creep
- Failure mode: attempting to fully generalize the upgraded Week 2 runner before screening any lane.
- Mitigation: start with thin wrappers and generic rubric registration.

### Risk 5 — Artifact confusion
- Failure mode: new files overwrite or collide with existing Week 2 paths.
- Mitigation: use a new `trait_lanes_v2` namespace in prompts/results/configs.

### Risk 6 — Scientific overreaction
- Failure mode: broad screening produces something interesting and the project abandons the current H3 critical path prematurely.
- Mitigation: the active H3 tranche remains the current core critical path until it is terminal and interpreted.

## 13. Concrete First Implementation Tranche (after plan approval)
This is the first coding tranche the project should execute after approval of this plan and after confirming the active H3 run is not being disturbed.

1. Add literature refresh and planning artifacts to docs/indexes.
2. Add `configs/trait_lanes_v2.yaml`.
3. Add `history/construct_cards/` with seed construct cards for all five families.
4. Add a small shared registry loader.
5. Add a non-invasive prompt-generation wrapper for new lanes.
6. Add parity tests proving current three-trait prompt generation/extraction defaults still behave identically.
7. Do **not** launch new remote jobs yet.

## 14. Ready / Not-Ready Verdict
### Ready now
- planning branch
- docs refresh
- registry design
- construct-card drafting
- non-invasive implementation of screening wrappers

### Not ready now
- new remote screening launches
- promotion of any new lane into the core claim set
- modifications that alter the live H3 path or the current `experiment.yaml` trait defaults

## 15. Plan Confidence
`inferred`: this plan is strong because it:
- preserves the current core line,
- reuses existing Week 2 infrastructure,
- avoids immediate full-run explosion,
- explicitly guards against duplication, state drift, and live-run interference.

Remaining unknowns are scientific, not planning-structural:
- which new lanes will actually screen well,
- whether any new lane is mechanistically cleaner than the current best lanes,
- whether trait choice is a primary bottleneck or only a contributing one.
