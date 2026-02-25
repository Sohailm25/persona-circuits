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
