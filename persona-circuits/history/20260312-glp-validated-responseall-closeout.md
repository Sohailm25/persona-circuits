# GLP Validated `response_all` Closeout

## Purpose
This memo updates the GLP branch interpretation after the validated multi-epoch retrain and the matched Week 2 reruns completed.

It replaces the earlier undertrained read with the stronger result we now have:

- the matched unconditional `response_all` GLP was retrained with validation and materially better loss
- the corresponding `20`-prompt Week 2 rerun still did not show selective repair

## Key Artifacts

### Training
- validated smoke:
  - [train_glp_matched_modal_20260312T132823Z_responseall_valsmoke_20260312b.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260312T132823Z_responseall_valsmoke_20260312b.json)
- validated `3`-epoch retrain:
  - [train_glp_matched_modal_20260312T133750Z_responseall_val3e_20260312a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/train_glp_matched_modal_20260312T133750Z_responseall_val3e_20260312a.json)

### Week 2 evaluation
- old matched `1`-epoch `20`-prompt rerun:
  - [week2_glp_sidecar_validation_20260312T144330Z_matched_responseall_rowdiag20_20260312a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T144330Z_matched_responseall_rowdiag20_20260312a.json)
  - [week2_glp_sidecar_analysis_20260312T145600Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_analysis_20260312T145600Z.json)
- validated `3`-epoch `5`-prompt quick read:
  - [week2_glp_sidecar_validation_20260312T141947Z_matched_responseall_val3e_rowdiag5_20260312a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T141947Z_matched_responseall_val3e_rowdiag5_20260312a.json)
  - [week2_glp_sidecar_analysis_20260312T142704Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_analysis_20260312T142704Z.json)
- validated `3`-epoch `20`-prompt rerun:
  - [week2_glp_sidecar_validation_20260312T151500Z_matched_responseall_val3e_rowdiag20_20260312a.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_validation_20260312T151500Z_matched_responseall_val3e_rowdiag20_20260312a.json)
  - [week2_glp_sidecar_analysis_20260312T155851Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_analysis_20260312T155851Z.json)

## What Changed

### 1. Training adequacy improved materially
The reviewer was correct that the earlier `1`-epoch read was confounded by undertraining.

Validated `response_all` retrain:
- epoch `1`: train `1.8394`, val `1.6729`
- epoch `2`: train `1.6326`, val `1.5969`
- epoch `3`: train `1.5789`, val `1.5795`

This is a real improvement over the earlier validation smoke:
- smoke val loss: `2.2371`

So the branch can no longer claim that the matched unconditional lane was judged fairly under the original `1`-epoch training regime.

### 2. Better loss did not translate into Week 2 selectivity
The validated `3`-epoch checkpoint was then rerun on the matched Week 2 steering sidecar with `20` prompts per active trait and `3` random-direction draws.

That rerun did not show the change we needed.

## Main Behavioral Result

### `sycophancy`
Validated `3`-epoch run:
- `selected_raw`: effect `-71.9`, coherence `50.975`
- `selected_glp`: effect `-72.25`, coherence `44.975`
- `baseline_glp_control`: effect `-77.3`, coherence `49.775`
- `random_glp`: effect `-74.75`, coherence `47.93`

Read:
- trait effect is roughly preserved
- coherence gets worse by about `6`
- baseline and random GLP remain too competitive with the selected direction

### `evil`
Validated `3`-epoch run:
- `selected_raw`: effect `-59.6`, coherence `34.75`
- `selected_glp`: effect `-54.65`, coherence `33.075`
- `baseline_glp_control`: effect `-61.5`, coherence `33.375`
- `random_glp`: effect `-59.5`, coherence `32.51`

Read:
- trait effect weakens
- coherence is slightly worse
- baseline and random GLP are again essentially as strong as the selected GLP condition

## Comparison Against The Older `1`-Epoch Checkpoint
The crucial point is that the validated retrain improved optimization, but not the behavioral conclusion.

### `sycophancy`
Old `1`-epoch matched rerun:
- `selected_glp`: effect `-71.3`, coherence `44.55`

Validated `3`-epoch matched rerun:
- `selected_glp`: effect `-72.25`, coherence `44.975`

This is effectively a wash on the behavioral outcome.

### `evil`
Old `1`-epoch matched rerun:
- `selected_glp`: effect `-51.6`, coherence `33.6`

Validated `3`-epoch matched rerun:
- `selected_glp`: effect `-54.65`, coherence `33.075`

Again, this is not a meaningful selectivity gain.

## Metric Validity Update
The new `20`-prompt validated analysis now computes per-prompt metric-validity summaries.

Those correlations remain weak.

Examples from [week2_glp_sidecar_analysis_20260312T155851Z.json](/Users/sohailmohammad/braindstorms/persona-circuits/results/glp_sidecar/week2_glp_sidecar_analysis_20260312T155851Z.json):

### `sycophancy`
- `nll_vs_coherence_delta`: Pearson `0.078`, Spearman `0.164`
- `nll_vs_effect_delta`: Pearson `0.340`, Spearman `0.211`
- `repair_ratio_vs_coherence_delta`: Pearson `-0.113`, Spearman `-0.136`

### `evil`
- `nll_vs_coherence_delta`: Pearson `-0.176`, Spearman `-0.101`
- `nll_vs_effect_delta`: Pearson `0.021`, Spearman `-0.098`
- `repair_ratio_vs_effect_delta`: Pearson `0.398`, Spearman `0.317`

Interpretation:
- these metrics are still useful as diagnostics
- they are still not validated enough to treat as strong scientific proxies for behavior

## Updated Scientific Claim
The strongest defensible claim after the validated rerun is:

> Even after materially improving the matched unconditional `response_all` GLP training loss with validation-aware multi-epoch training, we still do not observe evidence of selective Week 2 repair in the current persona-steering lane.

That is stronger than the earlier undertrained interpretation, because it survives the validated retrain.

## What This Result Does And Does Not Establish

### What it establishes
1. The released-checkpoint negative remains valid.
2. The matched unconditional `response_all` lane was undertrained originally.
3. After correcting that with a validated `3`-epoch retrain, Week 2 selectivity still does not appear.
4. The central current problem remains selectivity, not merely optimizer failure.

### What it does not establish
1. It does not prove GLP is unusable for persona repair in general.
2. It does not isolate the clean-train / edited-eval distribution-shift hypothesis.
3. It does not show that `response_last` or conditional repair are inherently worse objectives.
4. It does not justify skipping the remaining confound-separating experiments.

## Best Current Interpretation
The current unconditional matched `response_all` GLP now has a stronger negative result than it did before.

Not because:
- it was trained badly

But because:
- it was retrained better
- and the Week 2 selectivity problem persisted anyway

This is the right update:

- training adequacy was a real confound
- we addressed it for the matched unconditional `response_all` lane
- and the main behavioral issue still remained

So the branch should now treat the unconditional clean-trained `response_all` lane as a stronger negative than before.

## Recommended Next Steps
The next work should stay aligned with the post-review remediation plan in [20260312-glp-post-review-remediation-plan.md](/Users/sohailmohammad/braindstorms/persona-circuits/history/20260312-glp-post-review-remediation-plan.md).

Priority order:

1. Fix the row-record persistence/schema mismatch so the new metric-validity machinery is fully inspectable from raw artifacts, not just derived analysis.
2. Scale `response_last` before comparing it against `response_all`.
3. Scale the conditional lane to a nontrivial data regime before reading it as evidence.
4. Run the direct mixed clean+edited training ablation to isolate the distribution-shift hypothesis.
5. Only then decide whether synthetic edited-target repair is justified.

## Current Branch-Level Bottom Line
This is the updated closeout:

- released GLP: negative for direct adoption
- matched unconditional `response_all`, undertrained: inconclusive
- matched unconditional `response_all`, validated `3`-epoch rerun: stronger negative for selective Week 2 repair
- conditional pilot: still underpowered
- core unresolved issue: clean-train / edited-eval mismatch remains unisolated
