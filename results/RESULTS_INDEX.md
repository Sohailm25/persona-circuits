# Results Index

Master index of all experimental results. Each entry links to the result artifact and maps to the traceability matrix (proposal §5.6).

**Rules:**
- Every result file must be registered here
- Include traceability matrix row reference
- Include pass/fail/inconclusive status against pre-registered thresholds
- Never delete entries — mark superseded results as `[SUPERSEDED by: filename]`

---

## Infrastructure (Week 1)

| Artifact | Task | Status | Path |
|----------|------|--------|------|
| Week1 modal setup validation (llama+andyrdt) | Download + forward-pass validation for Llama-3.1-8B-Instruct, LlamaScope (l12..l24), and andyrdt (19,23) | partial (reconstruction cosine warning) | results/infrastructure/week1_day3_5_modal_validation_20260224T220740Z.json |
| Week1 modal setup validation (gemma initial) | Gemma+GemmaScope+CLT initial check | partial [SUPERSEDED by: week1_day3_5_modal_validation_20260224T224332Z.json] | results/infrastructure/week1_day3_5_modal_validation_20260224T222304Z.json |
| Week1 modal setup validation (gemma final) | Gemma+GemmaScope+CLT validation with persistent cache + nonzero graph edges | pass (infrastructure) | results/infrastructure/week1_day3_5_modal_validation_20260224T224332Z.json |
| Prompt dataset generation summary | Initial 3-trait dataset generation with required category counts | pass (infrastructure) | results/infrastructure/week1_prompt_generation_summary.json |
| Prompt dataset strict audit (final) | Structural + content-spec compliance audit after remediation (all 3 traits) | pass (`overall_pass=true`) | results/infrastructure/week1_prompt_audit_report.json |

## Stage 1: Persona Extraction

| Artifact | Trait | Traceability Row | Status | Path |
|----------|-------|-----------------|--------|------|
| Week2 held-out prompt audit (all traits) | sycophancy + evil + hallucination | Methodology pre-check for §6.2.3 behavioral validation prompt integrity | pass (`overall_pass=true`) | results/stage1_extraction/week2_heldout_prompt_audit_report.json |
| Week2 held-out prompt manifest (hashes/counts) | sycophancy + evil + hallucination | Methodology traceability support for §6.2.3 reruns | pass (input hashing complete) | results/stage1_extraction/week2_heldout_prompt_manifest_20260225T040156Z.json |
| Week2 extraction implementation spot-check | sycophancy | Methodology pre-check for §6.2.2 extraction pipeline (no hypothesis claim) | pass | results/stage1_extraction/week2_local_spot_check_20260225T010310Z.json |
| Week2 vector extraction summary (initial layer sweep) | sycophancy + evil + hallucination | Methodological row: "Persona vectors steer behavior as expected" (§5.6.2, pre-validation extraction step) | partial (vectors extracted; behavioral validation pending) | results/stage1_extraction/week2_vector_extraction_summary_20260225T010808Z.json |
| Week2 persona vectors tensor artifact (initial layer sweep) | sycophancy + evil + hallucination | Methodological row: "Persona vectors steer behavior as expected" (§5.6.2, pre-validation extraction step) | partial (vectors extracted; behavioral validation pending) | results/stage1_extraction/week2_persona_vectors_20260225T010808Z.pt |
| Week2 behavioral validation (frozen held-out rerun) | sycophancy + evil + hallucination | Methodological row: "Persona vectors steer behavior as expected" (§5.6.2, behavioral validation) | partial / gate-fail (run executed, but cross-rater kappa <0.6 for all traits; hallucination parse-fallback flag) | results/stage1_extraction/week2_behavioral_validation_20260225T071504Z.json |
| Week2 prelaunch gap checks (external transfer + extraction A/B robustness) | sycophancy + evil + hallucination | Methodology pre-closeout checks for §6.2.3 reliability | fail (`overall_pass=false`; external transfer and extraction A/B similarity gates failed) | results/stage1_extraction/week2_prelaunch_gap_checks_20260225T131521Z.json |
| Week2 upgraded validation smoke (post rollout/norm + top_k compatibility fix) | sycophancy | Methodology implementation validation for §6.2.3 upgraded runner (not final hypothesis evidence) | pass (execution smoke; report emitted with new norm diagnostics) / gate-fail expected on tiny sample | results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260225T131007Z.json |
| Week2 upgraded validation smoke (post reviewer patchset + control norm match) | sycophancy | Methodology implementation validation for §6.2.3 upgraded runner (not final hypothesis evidence) | pass (execution smoke; strict-parse + lockbox/test + bleed + control-norm fields emitted) / gate-fail expected on tiny sample | results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260225T135828Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v1) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T120651Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T113925Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v2, throttle-aware) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T120651Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T115947Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v3, coherence+directionality controls) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T120651Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T120508Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v4, coherence+directionality+random-p95 controls) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T123225Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T120651Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v5, stricter acceptance gates) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T123703Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T123225Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v6, stricter gates + TruthfulQA known-fact check) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T124550Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T123703Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v7, rollout-averaging + norm diagnostics) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T125134Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T124550Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v8, sweep multi-rollout default + expanded norm diagnostics) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T132327Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T125134Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v9, strict parser + lockbox test gates + stronger null controls + objective hallucination gate) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact [SUPERSEDED by: week2_upgrade_parallel_plan_20260225T141045Z.json] | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T132327Z.json |
| Week2 upgraded parallel sweep plan (pre-launch v10, cross-rater/test hard bound + primary-first launch script) | sycophancy + evil + hallucination | Methodology planning support for §6.2.3 reliability rerun; not hypothesis evidence | planning artifact (current) | results/stage1_extraction/week2_upgrade_parallel_plan_20260225T141045Z.json |
| Week2 literature second pass memo | sycophancy + evil + hallucination | Methodology review support for §6.2.3 reliability hardening; not hypothesis evidence | review artifact (completed) | results/stage1_extraction/week2_literature_second_pass_20260225T120710Z.md |
| Week2 literature third pass memo (critical audit) | sycophancy + evil + hallucination | Methodology review support for §6.2.3 closeout rigor; not hypothesis evidence | review artifact (completed) | results/stage1_extraction/week2_literature_third_pass_20260225T123439Z.md |
| Week2 gap 3/4 literature addendum (sampling stability + norm diagnostics) | sycophancy + evil + hallucination | Methodology review support for §6.2.3 closeout rigor; not hypothesis evidence | review artifact (completed) | results/stage1_extraction/week2_gap34_literature_addendum_20260225T130737Z.md |

## Stage 2: SAE Decomposition

| Artifact | Trait | Traceability Row | Status | Path |
|----------|-------|-----------------|--------|------|
| (none yet) | | | | |

## Stage 3: Circuit Tracing

| Artifact | Trait | Traceability Row | Status | Path |
|----------|-------|-----------------|--------|------|
| (none yet) | | | | |

## Stage 4: Causal Validation

| Artifact | Trait | Traceability Row | Status | Path |
|----------|-------|-----------------|--------|------|
| (none yet) | | | | |

## Stage 5: Cross-Persona Analysis

| Artifact | Traceability Row | Status | Path |
|----------|-----------------|--------|------|
| (none yet) | | | |

## Gemma-2-2B Validation

| Artifact | Traceability Row | Status | Path |
|----------|-----------------|--------|------|
| (none yet) | | | |

## Hypothesis Verdicts

| Hypothesis | Verdict | Key Evidence | Effect Size | Confidence Interval |
|------------|---------|-------------|-------------|-------------------|
| H1 | pending | | | |
| H2 | pending | | | |
| H3 | pending | | | |
| H4 | pending | | | |
| H5 | pending | | | |
