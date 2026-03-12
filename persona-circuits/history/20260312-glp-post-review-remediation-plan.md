# GLP Post-Review Remediation Plan

## Purpose
This memo revises the GLP branch interpretation and defines the next experiment tranche after reviewer feedback.

The key correction is simple:

- the GLP infrastructure is strong
- the released-checkpoint negative is still useful
- but the broader conclusion that "GLP does not work for persona steering repair" is not yet supported

The next phase must separate:
- scale limits
- objective mismatch
- clean-train / edited-eval distribution shift
- metric validity

## Revised Scientific Claim
The strongest defensible claim today is:

> At current data scale, training regime, and objective design, we do not see evidence that GLP provides selective repair for persona steering in the current Week 2 / Week 3 lanes.

This replaces weaker formulations such as:
- "GLP does not work for this task"
- "unconditional GLP is exhausted"
- "conditional GLP failed"

## What Remains Robust
These conclusions still stand.

1. Direct reuse of the released GLP checkpoint is not supported for this lane.
2. Matching model and layer removes gross mismatch pathologies.
3. Selectivity is the real target, not just stability.
4. The current conditional natural-pairing objective is not yet showing selective repair.

## What Is Not Yet Supported
These conclusions should be treated as unproven.

1. That `response_last` is worse than `response_all` as an objective.
   The current comparison is confounded by sample count and training scale.
2. That conditional repair is fundamentally unhelpful.
   The conditional pilot is too small and too lightly trained.
3. That the current next-token NLL proxy is a claim-grade geometry metric.
4. That synthetic edited-target supervision is already justified over all simpler scaling tests.

## Main Confounds To Separate
The next tranche should explicitly separate these four confounds.

### 1. Data Scale
Current training sizes are too uneven:
- `response_all`: about `92k` samples
- `response_last`: about `4.4k` samples
- conditional pilot: `256` samples

A negative comparison between these regimes is not interpretable without scale-matching.

### 2. Training Adequacy
Current runs are mostly:
- `1` epoch
- no held-out validation loss tracking
- no convergence sweep

This means "neutral result" may mean undertraining rather than objective mismatch.

### 3. Distribution Shift
Current training is on clean natural activations, while evaluation is on edited activations.
This is likely important, but it has not been isolated experimentally.

### 4. Metric Validity
We used next-token loss correctly as an early-warning diagnostic, but not yet as a validated scientific proxy.
It must earn that role.

## Revised Experiment Order
The next tranche should be executed in this order.

## Tranche A: Validate Existing Metrics And Controls
Goal: determine whether our diagnostics are actually informative before scaling more runs.

### A1. Validate NLL proxy against behavior
Files:
- [glp_metrics.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_metrics.py)
- [week2_glp_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_analysis.py)
- [week3_glp_sufficiency_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_sufficiency_sidecar_analysis.py)

Add:
- per-prompt correlation between `delta_target_nll_vs_clean` and `coherence_delta`
- per-prompt correlation between `delta_target_nll_vs_clean` and `trait_effect_delta`
- per-prompt correlation between `repair_to_edit_ratio` and both coherence/effect deltas

Decision gate:
- if these correlations are weak or unstable, downgrade NLL and geometry metrics to debug-only status

### A2. Strengthen random controls
Files:
- [week2_glp_sidecar_validation.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_validation.py)
- [week3_glp_sufficiency_sidecar.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_sufficiency_sidecar.py)

Add:
- multiple random directions per run, not one
- aggregate mean and spread across random draws

Reason:
- one random draw is too brittle to support selectivity claims

### A3. Make conditional control framing explicit
Files:
- [week2_glp_sidecar_validation.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_validation.py)
- [week2_glp_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_analysis.py)

Add reporting for:
- clean-clean conditional GLP regime
- clean-edited conditional GLP regime
- any asymmetry this induces in baseline comparisons

Reason:
- the reviewer is right that conditional baseline framing is different from selected conditional inference

## Tranche B: Exhaust Cheaper Scaling Paths Before New Objectives
Goal: separate undertraining from objective mismatch.

### B1. Multi-epoch sweep for matched `response_all`
Files:
- [train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/train_glp_matched_modal.py)
- [train_glp_llama31_8b_instruct_layer12.yaml](/Users/sohailmohammad/braindstorms/persona-circuits/configs/train_glp_llama31_8b_instruct_layer12.yaml)
- [glp_sidecar.yaml](/Users/sohailmohammad/braindstorms/persona-circuits/configs/glp_sidecar.yaml)

Run:
- `response_all` matched checkpoint at `3`, `5`, and `10` epochs
- with a held-out validation split and validation-loss logging

Success criterion:
- if validation improves and selectivity improves over the current `1`-epoch checkpoint, undertraining was a real confound

Stop criterion:
- if validation saturates while selectivity stays flat, scaling unconditional clean training is likely not enough

### B2. Scale-match `response_last`
Files:
- [generate_glp_training_prompt_corpus.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/generate_glp_training_prompt_corpus.py)
- [glp_export_memmap_dataset.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/glp_export_memmap_dataset.py)
- [train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/train_glp_matched_modal.py)

Run:
- export substantially more `response_last` samples
- target at least low tens of thousands before comparing to `response_all`
- then train multi-epoch with validation

Reason:
- current `response_last` conclusion is confounded by extreme data shortage

### B3. Scale the conditional pilot before judging it
Files:
- [glp_export_memmap_dataset.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/glp_export_memmap_dataset.py)
- [train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/train_glp_matched_modal.py)
- [week2_glp_sidecar_validation.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_validation.py)

Run:
- conditional paired export at `2k` to `5k+` samples minimum
- `5+` epochs with validation
- evaluation on `20+` prompts per active trait

Reason:
- `256` samples and `1` epoch is pipeline validation, not scientific evidence

## Tranche C: Directly Test The Distribution-Shift Hypothesis
Goal: determine whether the core problem is clean-training vs edited-evaluation mismatch.

### C1. Mixed clean + edited training set
Files:
- new exporter extension in [glp_export_memmap_dataset.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/glp_export_memmap_dataset.py)
- likely a new helper script under `scripts/` for synthetic edit injection

Design:
- start with a clean dataset
- add a controlled fraction of edited activations using current Week 2 steering vectors
- keep the target as the clean activation or edited activation depending on the training objective under test

Minimum ablation:
- `0%` edited
- `10%` edited
- `25%` edited

Reason:
- this is the cleanest direct test of the reviewer’s main criticism

### C2. Persona-adjacent training data
Files:
- [generate_glp_training_prompt_corpus.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/generate_glp_training_prompt_corpus.py)
- likely a new prompt-source script under `prompts/glp_training/`

Design:
- build a small persona-adjacent but non-eval-overlapping corpus
- compare against the current neutral corpus

Reason:
- train/test drift may exist even before edited activation drift

## Tranche D: Only Then Decide On Synthetic Edited-Target Repair
Goal: build the more expensive repair-specific pipeline only if simpler tests do not already resolve the issue.

This tranche is justified only if:
- multi-epoch scale-ups remain neutral
- mixed edited training shows signal that distribution shift matters
- conditional scaling remains non-selective under natural pairing

Then build:
- a corruption-aware paired dataset
- clean condition + edited target input
- clean target supervision or pass-through supervision depending on exact repair hypothesis

## Minimum Power Requirements Before Reading A Result As Informative
These should be treated as hard floors.

### Week 2 steering evaluation
- at least `20` prompts per active trait for decision-grade reads
- at least `3` random-direction draws per condition
- same evaluation settings across compared checkpoints

### Week 3 sufficiency evaluation
- no `n=1` prompt decisions
- at least one small but real prompt batch per trait and per dose
- same-size random circuits sampled multiple times

### Conditional evaluation
- do not treat a conditional checkpoint as informative below low-thousands training samples unless the result is catastrophically bad

## Code Patch List
These are worth doing regardless of the experimental direction.

### P1. Harden conditional config errors
File:
- [glp_runtime.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_runtime.py)

Patch:
- replace raw key indexing for `target_slice_start` / `target_slice_end` with explicit validation and clear errors

### P2. Document triple-clamp logic
File:
- [glp_runtime.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_runtime.py)

Patch:
- add a short comment explaining why condition clamping occurs before denoising, after zeroing condition noise, and after scheduler step

### P3. KL defensive smoothing
File:
- [glp_metrics.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/shared/glp_metrics.py)

Patch:
- apply epsilon smoothing or equivalent defensive handling before computing KL
- add a regression test for extreme-logit cases

### P4. Export skip accounting
File:
- [glp_export_memmap_dataset.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/glp_export_memmap_dataset.py)

Patch:
- surface skipped-no-response counts more prominently
- warn when the skip fraction crosses a threshold

### P5. Remove in-place upstream patching
File:
- [train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/train_glp_matched_modal.py)

Patch:
- stop modifying upstream source in-place inside the training container
- instead vendor a small local wrapper or patch file with explicit provenance

### P6. Add validation tracking to training launcher
File:
- [train_glp_matched_modal.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/train_glp_matched_modal.py)

Patch:
- split training/validation indices
- log validation loss by epoch
- persist validation summary to artifact

### P7. Add multi-random support
Files:
- [week2_glp_sidecar_validation.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_validation.py)
- [week3_glp_sufficiency_sidecar.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_sufficiency_sidecar.py)

Patch:
- evaluate multiple random control draws per run
- aggregate means and uncertainty

## Analysis Patch List
These should be added before the next review cycle.

### AP1. Correlation report for metric validity
Files:
- [week2_glp_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week2_glp_sidecar_analysis.py)
- [week3_glp_sufficiency_sidecar_analysis.py](/Users/sohailmohammad/braindstorms/persona-circuits/scripts/week3_glp_sufficiency_sidecar_analysis.py)

Add:
- rank correlations and scatter summaries tying geometry/NLL to behavioral outcomes

### AP2. Training adequacy report
Add a simple per-run table:
- sample count
- epochs
- train loss trajectory
- validation loss trajectory
- downstream Week 2 selectivity metrics

Reason:
- reviewer’s main critique is that training adequacy and objective mismatch were not separated

## New Decision Gates
Use these instead of the previous more aggressive interpretations.

### Gate 1: Released checkpoint
If controls are strong and NLL/KL distortions are large, direct reuse is rejected.
This gate is already passed.

### Gate 2: Matched unconditional scaling
If multi-epoch matched `response_all` and scale-matched `response_last` still show no selective gain over controls, then unconditional clean-training GLP is likely near its ceiling.

### Gate 3: Conditional natural pairing
If a scaled conditional model still tracks clean response reconstructions more than selected edits, then natural prompt-response conditioning is probably the wrong task.

### Gate 4: Mixed edited training
If adding edited activations to training improves selectivity, the distribution-shift hypothesis is supported.
If not, objective design or architecture limits are more likely.

## Recommended Immediate Build Sequence
This is the concrete order for implementation.

1. Patch the code-quality items P1 through P6.
2. Add AP1 correlation reporting.
3. Launch multi-epoch `response_all` retraining with validation.
4. Expand `response_last` export to a scale where it can be compared fairly.
5. Expand the conditional paired export to low-thousands scale and retrain.
6. Re-run Week 2 on a properly powered prompt set.
7. Only then build mixed clean + edited training.
8. Only after that decide whether synthetic edited-target repair is necessary.

## Stop Conditions
Stop pursuing unconditional GLP if all of the following are true after scaling:
- matched `response_all` saturates on validation loss
- scale-matched `response_last` does not improve selectivity
- controls remain close to selected GLP
- geometry and NLL diagnostics do not predict behavioral wins

Stop pursuing natural-pairing conditional GLP if all of the following are true after scaling:
- validation improves but selectivity does not
- conditional baseline remains too strong
- selected conditional repair continues to collapse toward clean behavior

## Bottom Line
The branch should now shift from:
- broad architectural verdicts

to:
- confound-separating experiments with minimum acceptable power

The reviewer’s correction is valid.
The next job is not to abandon the branch, and not to immediately build the most complicated new objective.
The next job is to run the cheapest clean tests that can actually distinguish:
- undertraining
- data scarcity
- objective mismatch
- edited-distribution mismatch
