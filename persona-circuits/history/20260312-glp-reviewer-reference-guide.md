# GLP Reviewer Reference Guide

## Scope
This guide covers the full GLP sidecar branch that was built to test whether Generative Latent Prior style activation repair can help the current persona-circuits program.

The branch includes:
- direct reproduction attempts with the released GLP checkpoint
- matched layer-12 GLP training on Llama-3.1-8B-Instruct activations
- unconditional `response_all` and `response_last` variants
- a conditional `prompt_last -> response_last` pilot
- Week 2 behavioral sidecar evaluation
- Week 3 H3-style sufficiency sidecar evaluation
- prompt corpus generation, activation export, and training launch infrastructure

The branch does **not** change the active main-lane runners. Those files are included below only as baseline context and integration references.

## Reviewer Goals
The reviewer should explicitly assess:
- whether the implementation matches the GLP paper and upstream code where intended
- whether the controls are strong enough to support the conclusions
- whether the diagnosis moved correctly from model/layer mismatch to generic-prior / wrong-supervision-target failure
- whether the next-token loss diagnostic is a fair proxy for Delta LM Loss style geometric validity
- whether the training data design is adequate for the intended repair task
- whether the conditional branch is implemented correctly and whether its failure is better explained by data/objective mismatch than by inference bugs
- whether any important evaluation condition, ablation, or confound is still missing

## Suggested Review Order
1. Read the paper and upstream code.
2. Read the local runtime and metrics layer.
3. Read the Week 2 sidecar evaluation path.
4. Read the Week 3 sufficiency sidecar path.
5. Read the prompt generation, export, and training pipeline.
6. Inspect the key result artifacts in chronological order.
7. Review the tests.
8. Review the explicit remaining gaps at the end of this document.

## 1. Paper And Upstream GLP Reference
These are the external references the local implementation was built against.

- [paper.pdf](/tmp/generative_latent_prior/paper.pdf)
- [paper.txt](/tmp/generative_latent_prior/paper.txt)
- [README.md](/tmp/generative_latent_prior/README.md)
- [glp_train.py](/tmp/generative_latent_prior/glp_train.py)
- [denoiser.py](/tmp/generative_latent_prior/glp/denoiser.py)
- [script_steer.py](/tmp/generative_latent_prior/glp/script_steer.py)
- [script_probe.py](/tmp/generative_latent_prior/glp/script_probe.py)
- [integrations/persona_vectors/README.md](/tmp/generative_latent_prior/integrations/persona_vectors/README.md)
- [activation_steer.py](/tmp/generative_latent_prior/integrations/persona_vectors/activation_steer.py)

Reviewer focus:
- whether the local `u`, timestep, and denoising logic are faithful where claimed
- whether the local use of GLP as a post-edit projector is consistent with the paper’s steering setup
- whether the conditional extension is principled or a local experimental deviation
- whether the local next-token diagnostic is a reasonable analogue to the paper’s validity/reconstruction framing

## 2. Baseline Persona-Circuits Context
These files were not the main implementation target of the GLP branch, but they are the baseline that the sidecars were designed around.

- [experiment.yaml](/Users/sohailmohammad/braindstorms/persona-circuits/configs/experiment.yaml)
- [week2_extract_persona_vectors.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_extract_persona_vectors.py)
- [week2_behavioral_validation_upgrade.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_behavioral_validation_upgrade.py)
- [week3_sae_decomposition.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_sae_decomposition.py)
- [week3_stage3_activation_delta_attribution.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_stage3_activation_delta_attribution.py)
- [week3_stage3_candidate_selection.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_stage3_candidate_selection.py)
- [week3_stage4_target_set_freeze.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_stage4_target_set_freeze.py)
- [week3_stage4_sufficiency_preflight.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_stage4_sufficiency_preflight.py)
- [week3_stage4_behavioral_ablation.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_stage4_behavioral_ablation.py)

Key upstream result inputs used by the GLP sidecars:
- [week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json)
- [week2_behavioral_validation_upgrade_evil_20260303T081318Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260303T081318Z.json)

Optional upstream robustness context that informed the GLP tranche:
- [week2_extraction_seed_replication_20260302T180612Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/stage1_extraction/week2_extraction_seed_replication_20260302T180612Z.json)
- [week2_response_mean_sensitivity_20260301T025554Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/stage1_extraction/week2_response_mean_sensitivity_20260301T025554Z.json)

Reviewer focus:
- whether the GLP branch was anchored to the right baseline failure modes
- whether the selected traits and extraction methods were the right ones to stress-test
- whether the GLP sidecars preserved the main-lane evaluation semantics instead of drifting to a weaker benchmark

## 3. Core GLP Runtime And Metrics
These are the most important implementation files in the branch.

- [glp_runtime.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_runtime.py)
- [glp_metrics.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_metrics.py)

What they do:
- load GLP checkpoints
- resolve GLP metadata and training alignment
- apply unconditional and conditional post-processing to edited activations
- clamp condition latents for conditional inference
- compute geometry summaries
- compute next-token loss diagnostics used as a local validity proxy

Reviewer focus:
- correctness of the unconditional sampling path
- correctness of the conditional inference path, especially condition concatenation, clamping, and slicing back to target half
- whether `next_token_loss_summary` is computed at the right token position and interpreted correctly
- whether geometry metrics such as `repair_to_edit_ratio` and `repair_alignment_cosine` support the conclusions being drawn

## 4. Week 2 Behavioral Sidecar
This is the main behavioral evaluation entrypoint for the GLP branch.

- [week2_glp_sidecar_validation.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_validation.py)
- [week2_glp_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_analysis.py)

What it does:
- reuses the Week 2 behavioral validation framing in a sidecar-safe way
- evaluates `selected_raw`, `selected_glp`, `baseline_glp_control`, and `random_glp`
- supports released, matched unconditional, matched `response_last`, and conditional checkpoints
- computes trait effect, coherence, capability, bleed, geometry, and next-token diagnostics

Reviewer focus:
- whether the control set is sufficient
- whether `baseline_glp_control` and `random_glp` are the right nuisance baselines
- whether prompt-side condition capture for the conditional model is implemented correctly
- whether the conclusions about selectivity are supported by the sidecar outputs

## 5. Week 3 H3 / Sufficiency Sidecar
This is the highest-value mechanistic extension of the branch.

- [week3_glp_sufficiency_sidecar.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_sufficiency_sidecar.py)
- [week3_glp_sufficiency_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_sufficiency_sidecar_analysis.py)

What it does:
- compares full-vector raw vs GLP
- compares circuit-only raw vs GLP
- compares random same-size circuit sets
- supports dose-response evaluation
- adds next-token validity diagnostics to H3-style sufficiency testing

Reviewer focus:
- whether the circuit-only reconstruction path is valid
- whether same-size random controls are sufficient and fairly matched
- whether the current negative H3 read is a property of GLP or a property of poor circuit sufficiency to begin with
- whether more H3-specific corruption training is needed before judging GLP fairly

## 6. Exploratory GLP Meta-Neuron Lane
This lane was built but not a major source of the current conclusions.

- [week3_glp_meta_neuron_screen.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_meta_neuron_screen.py)
- [week3_glp_meta_neuron_screen_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_meta_neuron_screen_analysis.py)

Reviewer focus:
- whether the screen is methodologically meaningful as an exploratory feature-discovery tool
- whether it is too disconnected from the main causal claims to justify further investment

Note:
- no substantive result artifact from this lane was used in the main conclusions to date

## 7. Prompt Generation, Dataset Export, And Training Pipeline
These files matter because the branch ultimately moved from “released checkpoint evaluation” to “matched local training.”

- [generate_glp_training_prompt_corpus.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/generate_glp_training_prompt_corpus.py)
- [glp_export_memmap_dataset.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/glp_export_memmap_dataset.py)
- [train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/train_glp_matched_modal.py)

What they do:
- generate a neutral instruct corpus for GLP training
- export matched activation datasets from Llama-3.1-8B-Instruct layer 12
- support `response_all`, `response_last`, and conditional paired exports
- launch Modal training jobs against exported datasets
- patch conditional training behavior by slicing denoiser loss to the target half

Reviewer focus:
- whether the neutral prompt corpus is sufficiently diverse for manifold learning
- whether the conditional paired dataset is aligned to the actual repair task or merely to a natural prompt-response mapping task
- whether the export logic handles prompt vs response boundaries correctly
- whether the conditional training patch is sound or too ad hoc
- whether the training hyperparameters are sensible given dataset sizes

## 8. Configs And Written Plan
These are the branch-level knobs and the explicit training memo.

- [glp_sidecar.yaml](/Users/sohailmohammad/braindstorms/persona-circuits/configs/glp_sidecar.yaml)
- [train_glp_llama31_8b_instruct_layer12.yaml](/Users/sohailmohammad/braindstorms/persona-circuits/configs/train_glp_llama31_8b_instruct_layer12.yaml)
- [20260310-matched-layer12-repair-model-training-plan.md](/Users/sohailmohammad/braindstorms/persona-circuits/history/20260310-matched-layer12-repair-model-training-plan.md)

Reviewer focus:
- whether the config/default split between released, matched, `response_last`, and conditional lanes is coherent
- whether the written plan anticipated the actual failure modes correctly
- whether the next recommended step should still be synthetic edited-target repair training

## 9. Prompt Corpora Used For Matched Training
These are the generated neutral-instruct corpora that fed the matched GLP exports.

- [neutral_instruct_corpus_20260311T145008Z_tranche1_20260311a.jsonl](/Users/sohailmohammad/braindstorms/persona-circuits/prompts/glp_training/neutral_instruct_corpus_20260311T145008Z_tranche1_20260311a.jsonl)
- [neutral_instruct_corpus_20260311T171020Z_tranche2_20260311b.jsonl](/Users/sohailmohammad/braindstorms/persona-circuits/prompts/glp_training/neutral_instruct_corpus_20260311T171020Z_tranche2_20260311b.jsonl)
- [neutral_instruct_corpus_20260311T175246Z_tranche3_nofactual_20260311a.jsonl](/Users/sohailmohammad/braindstorms/persona-circuits/prompts/glp_training/neutral_instruct_corpus_20260311T175246Z_tranche3_nofactual_20260311a.jsonl)

Summary artifacts for prompt generation:
- [glp_training_prompt_corpus_20260311T145008Z_tranche1_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_training_prompt_corpus_20260311T145008Z_tranche1_20260311a.json)
- [glp_training_prompt_corpus_20260311T171020Z_tranche2_20260311b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_training_prompt_corpus_20260311T171020Z_tranche2_20260311b.json)
- [glp_training_prompt_corpus_20260311T175246Z_tranche3_nofactual_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_training_prompt_corpus_20260311T175246Z_tranche3_nofactual_20260311a.json)

Reviewer focus:
- prompt diversity
- duplication control
- whether the corpus is too neutral / too natural for the intended repair task
- category saturation, especially around `factual_qa`

## 10. Dataset And Checkpoint Locations On The Model Volume
These are the main training outputs and should be reviewed alongside the export/training artifacts.

Datasets:
- `/models/persona-circuits/glp_datasets/glp-llama31-instruct-l12-response-all-tranches12-20260311a`
- `/models/persona-circuits/glp_datasets/glp-llama31-instruct-l12-response-last-tranches123-20260311a`
- `/models/persona-circuits/glp_datasets/glp-llama31-instruct-l12-cond-prompt-last-to-response-last-pilot256-20260311a`

Checkpoints:
- `/models/persona-circuits/glp_runs/matched-glp-llama31-instruct-l12-response-all-tranches12-20260311a-full_tranches12_20260311a/final.safetensors`
- `/models/persona-circuits/glp_runs/matched-glp-llama31-instruct-l12-response-last-tranches123-20260311a-response_last_tranches123_20260311a/final.safetensors`
- `/models/persona-circuits/glp_runs/matched-glp-llama31-instruct-l12-cond-prompt-last-to-response-last-pilot256-20260311a-cond_pilot256_20260311a/final.safetensors`

Reviewer focus:
- whether these datasets match the intended evaluation regimes
- whether the checkpoint/data naming and provenance are sufficiently clear for future reproducibility

## 11. Tests
These are the GLP-branch test files the reviewer should assess.

- [test_glp_metrics.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_glp_metrics.py)
- [test_glp_runtime.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_glp_runtime.py)
- [test_week2_glp_sidecar.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_week2_glp_sidecar.py)
- [test_week3_glp_sufficiency_sidecar.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_week3_glp_sufficiency_sidecar.py)
- [test_week3_glp_sufficiency_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_week3_glp_sufficiency_sidecar_analysis.py)
- [test_week3_glp_meta_neuron_screen.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_week3_glp_meta_neuron_screen.py)
- [test_week3_glp_meta_neuron_screen_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_week3_glp_meta_neuron_screen_analysis.py)
- [test_glp_export_memmap_dataset.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_glp_export_memmap_dataset.py)
- [test_generate_glp_training_prompt_corpus.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_generate_glp_training_prompt_corpus.py)
- [test_train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/tests/test_train_glp_matched_modal.py)

Reviewer focus:
- what invariants are covered vs not covered
- whether the most failure-prone code paths have direct tests
- whether any scientific logic is only indirectly tested through plumbing tests

## 12. Result Artifacts To Review
These are grouped by purpose and chronology.

### A. Infrastructure / parity / smoke checks
- [week2_glp_sidecar_validation_20260310T231230Z_parity_smoke_20260310d.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260310T231230Z_parity_smoke_20260310d.json)
- [week2_glp_sidecar_validation_20260310T233039Z_glp_smoke_20260310b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260310T233039Z_glp_smoke_20260310b.json)
- [glp_export_memmap_dataset_20260311T142314Z_smoke_gemma_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T142314Z_smoke_gemma_20260311a.json)
- [glp_export_memmap_dataset_20260311T143100Z_smoke_llama_20260311b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T143100Z_smoke_llama_20260311b.json)
- [glp_export_memmap_dataset_20260311T143244Z_sanity_llama_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T143244Z_sanity_llama_20260311a.json)
- [train_glp_matched_modal_20260311T165041Z_smoke_20260311b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T165041Z_smoke_20260311b.json)
- [train_glp_matched_modal_20260311T165353Z_pilot_smoke_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T165353Z_pilot_smoke_20260311a.json)
- [train_glp_matched_modal_20260311T165659Z_pilot_nosave_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T165659Z_pilot_nosave_20260311a.json)

### B. Released GLP behavioral evidence
- [week2_glp_sidecar_validation_20260311T000624Z_week2_minimatrix_20260310a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T000624Z_week2_minimatrix_20260310a.json)
- [week2_glp_sidecar_validation_20260311T002851Z_evil_frontier_alpha2_20260310b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T002851Z_evil_frontier_alpha2_20260310b.json)
- [week2_glp_sidecar_validation_20260311T002823Z_evil_frontier_alpha3_20260310b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T002823Z_evil_frontier_alpha3_20260310b.json)
- [week2_glp_sidecar_validation_20260311T002756Z_evil_frontier_alpha4_20260310b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T002756Z_evil_frontier_alpha4_20260310b.json)
- [week2_glp_sidecar_validation_20260311T012700Z_evil_frontier_alpha3_nlldiag_20260310a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T012700Z_evil_frontier_alpha3_nlldiag_20260310a.json)

These are the key artifacts behind the conclusion that the released checkpoint was a generic rewrite / wrong-manifold fit for this lane.

### C. Week 3 early sufficiency / diagnostic evidence
- [week3_glp_sufficiency_sidecar_20260310T234528Z_suff_smoke_20260310b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week3_glp_sufficiency_sidecar_20260310T234528Z_suff_smoke_20260310b.json)
- [week3_glp_sufficiency_sidecar_20260310T235244Z_suff_smoke_20260310c.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week3_glp_sufficiency_sidecar_20260310T235244Z_suff_smoke_20260310c.json)
- [week3_glp_sufficiency_sidecar_20260311T023240Z_suff_nlldiag_smoke_20260310a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week3_glp_sufficiency_sidecar_20260311T023240Z_suff_nlldiag_smoke_20260310a.json)

These are the early artifacts behind the conclusion that GLP did not obviously rescue H3-style sufficiency.

### D. Matched unconditional training artifacts
- [glp_export_memmap_dataset_20260311T160236Z_export_tranche1_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T160236Z_export_tranche1_20260311a.json)
- [train_glp_matched_modal_20260311T170044Z_tranche1_full_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T170044Z_tranche1_full_20260311a.json)
- [train_glp_matched_modal_20260311T185837Z_full_tranche1_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T185837Z_full_tranche1_20260311a.json)
- [glp_export_memmap_dataset_20260311T200756Z_tranches12_20260311c.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T200756Z_tranches12_20260311c.json)
- [train_glp_matched_modal_20260311T215042Z_full_tranches12_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T215042Z_full_tranches12_20260311a.json)
- [glp_export_memmap_dataset_20260312T010547Z_response_last_tranches123_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260312T010547Z_response_last_tranches123_20260311a.json)
- [train_glp_matched_modal_20260312T010726Z_response_last_tranches123_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260312T010726Z_response_last_tranches123_20260311a.json)

These show the move from released GLP to matched model/layer training and then to matched `response_last` training.

### E. Matched unconditional behavioral evidence
- [week2_glp_sidecar_validation_20260311T171636Z_matched_glp_evil_alpha3_20260311c.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T171636Z_matched_glp_evil_alpha3_20260311c.json)
- [week2_glp_sidecar_validation_20260311T220017Z_matchedglp_minimatrix_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T220017Z_matchedglp_minimatrix_20260311a.json)
- [week2_glp_sidecar_validation_20260312T030433Z_response_last_minimatrix_20260312a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T030433Z_response_last_minimatrix_20260312a.json)
- [week2_glp_sidecar_validation_20260312T030953Z_response_last_evil_alpha3_20260312a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T030953Z_response_last_evil_alpha3_20260312a.json)
- [week3_glp_sufficiency_sidecar_20260311T220906Z_matchedglp_suff_syc_mean_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week3_glp_sufficiency_sidecar_20260311T220906Z_matchedglp_suff_syc_mean_20260311a.json)

These support the conclusion that matching model/layer fixed catastrophic mismatch but not the core selectivity problem.

### F. Conditional export / train artifacts
- [glp_export_memmap_dataset_20260311T221717Z_cond_response_last_smoke_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T221717Z_cond_response_last_smoke_20260311a.json)
- [glp_export_memmap_dataset_20260311T221908Z_cond_response_last_smoke_20260311b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T221908Z_cond_response_last_smoke_20260311b.json)
- [glp_export_memmap_dataset_20260311T223707Z_cond_response_last_pilot256_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/glp_export_memmap_dataset_20260311T223707Z_cond_response_last_pilot256_20260311a.json)
- [train_glp_matched_modal_20260311T222253Z_cond_smoke_20260311b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T222253Z_cond_smoke_20260311b.json)
- [train_glp_matched_modal_20260311T223944Z_cond_pilot256_20260311a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T223944Z_cond_pilot256_20260311a.json)

These are the infrastructure artifacts behind the conditional branch.

### G. Conditional behavioral evidence
- [week2_glp_sidecar_validation_20260312T032530Z_conditional_evil_alpha3_smoke_20260312b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T032530Z_conditional_evil_alpha3_smoke_20260312b.json)
- [week2_glp_sidecar_validation_20260312T033338Z_conditional_minimatrix_20260312a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T033338Z_conditional_minimatrix_20260312a.json)

These support the current conclusion that the conditional pilot is implemented correctly but is still learning the wrong task.

## 13. Interpretation The Reviewer Should Pressure-Test
The current working interpretation is:
- released GLP failed largely because of manifold mismatch and generic rewrite behavior
- matched unconditional training fixed some gross mismatch but not the main selectivity problem
- matching `response_last` alone did not solve the problem
- the conditional pilot also failed to become selective enough
- therefore the next real step should be synthetic edited-target repair supervision, not more evaluation on the current natural-pairing objectives

This interpretation should be challenged on both engineering and scientific grounds.

## 14. Explicit Gaps And Weak Points The Reviewer Should Look For
- whether the next-token loss metric is too local or too brittle to support geometry claims
- whether `baseline_glp_control` is over- or under-penalizing the GLP variants
- whether the conditional model should have been evaluated on a larger dataset before being judged
- whether the conditional training patch in the launcher is too ad hoc relative to a proper upstream model change
- whether the branch still lacks a true iso-fluency frontier evaluation at useful scale
- whether the Week 3 negative read is limited by weak target sets rather than weak GLP repair
- whether the neutral prompt corpus is too far from the actual intervention distribution
- whether the real missing ingredient is corruption-aware training rather than more matched natural activations
- whether the conditional input should include the clean response state or edited delta, not just `prompt_last`

## 15. Bottom-Line Reviewer Packet
If the reviewer has limited time, start with these files and artifacts first.

Code:
- [glp_runtime.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_runtime.py)
- [glp_metrics.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_metrics.py)
- [week2_glp_sidecar_validation.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_validation.py)
- [glp_export_memmap_dataset.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/glp_export_memmap_dataset.py)
- [train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/train_glp_matched_modal.py)

Artifacts:
- [released checkpoint minimatrix](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T000624Z_week2_minimatrix_20260310a.json)
- [released checkpoint NLL diagnostic](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T012700Z_evil_frontier_alpha3_nlldiag_20260310a.json)
- [matched `response_all` minimatrix](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260311T220017Z_matchedglp_minimatrix_20260311a.json)
- [matched `response_last` minimatrix](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T030433Z_response_last_minimatrix_20260312a.json)
- [conditional minimatrix](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T033338Z_conditional_minimatrix_20260312a.json)
- [matched `response_all` training summary](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T215042Z_full_tranches12_20260311a.json)
- [matched `response_last` training summary](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260312T010726Z_response_last_tranches123_20260311a.json)
- [conditional pilot training summary](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260311T223944Z_cond_pilot256_20260311a.json)

Context:
- [paper.pdf](/tmp/generative_latent_prior/paper.pdf)
- [activation_steer.py](/tmp/generative_latent_prior/integrations/persona_vectors/activation_steer.py)
- [20260310-matched-layer12-repair-model-training-plan.md](/Users/sohailmohammad/braindstorms/persona-circuits/history/20260310-matched-layer12-repair-model-training-plan.md)
