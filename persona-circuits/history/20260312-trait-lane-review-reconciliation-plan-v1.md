# Trait-Lane Branch Review Reconciliation Plan v1

Date: 2026-03-12
Inputs:
- `history/reviews/20260312-reviewer-trait-lane-branch-verbatim.md`
- `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_20260311T174109Z.json`
- `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_screening_execution_20260311T190121Z.json`
- `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_free_followon_20260312T004752Z.json`
- `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_external_smoke_eval_20260312T011734Z.json`
- `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_promotion_packet_20260312T030612Z.json`
- `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_packet_20260312T032309Z.json`
- `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_deeper_validation_execution_packet_20260312T033948Z.json`

## Status Summary

- `known`: the review is materially correct that the branch has over-committed to `politeness` as a lead lane without yet establishing distinctness from `sycophancy` or resolving response-phase persistence.
- `known`: the review is materially correct that `lying` is weaker than its current `conditional_followon_candidate` label suggests.
- `known`: the review is materially correct that disabling cross-trait bleed in the deeper-validation sidecar created a real interpretive blind spot.
- `known`: the review is materially correct that the next deeper-validation attempt should be split into separate extraction and validation launches.
- `inferred`: the right response is not to abandon the branch, but to pause new deeper-validation launches until overlap, persistence, and bleed policy are explicitly repaired.

## Finding-by-Finding Reconciliation

### R1. Narrowing from 6 lanes to 1 is operationally, not scientifically, justified

- Review verdict: agree in part.
- `known`: the current ranking packet selects `politeness` because it has the strongest combined screening + extraction-free evidence under the executed branch stack.
- `known`: the current packet does not prove `politeness` is the most scientifically informative lane for the broader PSM question.
- `known`: `honesty` was not dropped on extraction-free evidence alone; it also had mixed external-smoke evidence.
- `inferred`: the present narrowing should be described as tractability-first triage, not as proof that `politeness` is the best mechanistic lane.

Action:
1. Reframe branch language in state/decision docs from "stable winner" to "current tractability-first lead lane".
2. Keep `honesty` available as a secondary unresolved lane rather than treating it as scientifically closed.

### R2. Politeness may be tone transfer, not persona

- Review verdict: agree.
- `known`: the light-style construct card already flags collapse-to-tone risk.
- `known`: `politeness` has strong bounded screening (`bidirectional_effect=33.0`) but low reversal (`1.25`) and moderate extraction-free overlap (`mean_cosine=0.2114`), not overwhelming cross-induction evidence.
- `inferred`: before deeper validation, the branch needs an explicit distinctness check against `sycophancy` and nearby assistant-style lanes.

Action:
1. Compute `politeness` vs `sycophancy` cosine similarity before the next deeper-validation launch.
2. Add cross-trait bleed references for at least `sycophancy` and `assistant_likeness`.

### R3. Response-phase persistence is being under-weighted

- Review verdict: agree.
- `known`: `politeness`, `lying`, and `honesty` all fail the legacy `0.7` response-phase persistence threshold.
- `known`: the promotion packet downgraded this from hard gate to tracked limitation because no screened lane passed.
- `inferred`: this is a real policy problem and should not remain an unregistered relaxation.

Action:
1. Freeze new deeper-validation launches until the persistence policy is explicitly re-decided.
2. Accept only one of two next steps:
   - investigate the metric itself, or
   - preregister a relaxed interpretation rule before new evidence is collected.

### R4. Lying lane is construct-invalid, not merely weak

- Review verdict: mostly agree.
- `known`: in external smoke, `lying` plus-steering reduces lying below the low baseline (`plus_vs_baseline=-3.125`), while minus-steering suppresses lying more strongly than plus amplifies it.
- `known`: extraction-free classification is only `mixed_or_fragile`.
- `inferred`: the current `conditional_followon_candidate` label overstates viability.

Action:
1. Reclassify `lying` in branch tracking as a negative or construct-invalid finding under the current protocol.
2. Remove it from immediate follow-on budget unless a later construct redesign explicitly revives it.

### R5. Honesty deprioritization may be premature

- Review verdict: partial agreement.
- `known`: `honesty` screening signal is strong and robust (`bidirectional_effect=29.5`, bootstrap and held-out cosines high).
- `known`: `honesty` extraction-free overlap is null and external smoke is one-sided/mixed.
- `inferred`: the RLHF-asymmetry explanation is plausible enough that the lane should be treated as unresolved rather than fully dead.

Action:
1. Keep `honesty` as a secondary lane held for RLHF-asymmetry-aware follow-up, not as a lead lane.
2. Do not allocate equal budget with `politeness` before the distinctness/persistence tranche closes.

### R6. Judge-as-ground-truth circularity

- Review verdict: partial agreement.
- `known`: the branch still relies on the same judge stack used elsewhere in Week 2.
- `known`: manual concordance remains underpowered.
- `known`: this is a general experiment limitation, not a trait-lane-only bug.

Action:
1. Carry this as a documented limitation in the branch memo.
2. Do not claim psychometric-grade behavioral ground truth from the branch screens.

### R7. N=4 behavioral smoke is small

- Review verdict: agree.
- `known`: the bounded screens are intentionally screening-only.
- `known`: the deeper-validation sidecar was created precisely because `n=4` smoke is not enough.
- `inferred`: this is a framing issue more than a hidden bug.

Action:
1. Keep screening outputs explicitly labeled as screening-only in branch documentation.
2. Do not treat the n=4 smoke as promotion-proof by itself.

### R8. Cross-trait bleed was disabled exactly where it matters most

- Review verdict: agree.
- `known`: the deeper-validation sidecar explicitly disabled bleed to avoid forcing branch lanes through the legacy hardcoded trait matrix.
- `known`: this made operational reuse easier but removed the most important distinctness diagnostic.
- `inferred`: this tradeoff is no longer acceptable for the next launch.

Action:
1. Re-enable branch-local bleed for `sycophancy` and `assistant_likeness` before the next deeper-validation attempt.
2. If this requires a sidecar-specific bleed implementation, do that instead of mutating the core legacy matrix.

### R9. Layer selection is under-constrained

- Review verdict: partial disagreement.
- `known`: screening selected a provisional layer via cosine-margin diagnostics.
- `known`: the deeper-validation sidecar already sweeps layers `11-16` behaviorally, so the final validation step does not lock to the screening layer.
- `inferred`: this is a real caution on how we narrate the provisional layer, but not a decisive methodological flaw in the deeper-validation design.

Action:
1. Keep all layer selections explicitly provisional until deeper validation completes.
2. Avoid describing screening-selected layers as mechanistically preferred layers.

### R10. Test infrastructure gaps

- Review verdict: mostly agree.
- `known`: the branch has good unit coverage on packet/building blocks, but limited negative and integration coverage.
- `known`: deeper-validation execution failure paths are not well covered.

Action:
1. Add negative-path tests for malformed packet inputs and missing artifact fields.
2. Add at least one thin integration test from screening artifact -> promotion packet -> deeper-validation packet.
3. Add formula-specific assertions for ranking and effect calculations.

## Missing-Entirely Items

### M1. No comparison to sycophancy baseline

- Review verdict: agree.
- `known`: no trait-lane artifact currently computes `politeness` vs `sycophancy` cosine or bleed.

Action:
1. Add a small overlap/distinctness analysis before the next deeper-validation launch.

### M2. No null-lane control

- Review verdict: agree.
- `known`: there is no branch-specific null-lane false-positive estimate today.

Action:
1. Add a null-lane screening plan before branch interpretation freeze.

### M3. No prompt-sensitivity analysis

- Review verdict: agree.
- `known`: bootstrap robustness addresses pair subsampling, not prompt wording sensitivity.

Action:
1. Add a prompt-sensitivity sidecar plan before treating `politeness` ranking as stable.

### M4. PSM connection is thinning

- Review verdict: agree.
- `known`: if `politeness` is just a rotated sycophancy/assistant-style tone axis, its value to H4/H5 is limited.

Action:
1. Treat distinctness from `sycophancy` as the next decisive scientific gate for the branch.

## Immediate Operational Plan

### Freeze

- `known`: do not relaunch `politeness` deeper validation until the following are closed:
  1. `politeness` vs `sycophancy` overlap analysis
  2. branch-local bleed re-enabled for `sycophancy` and `assistant_likeness`
  3. response-phase persistence policy explicitly frozen
  4. next attempt split into separate extraction and validation launches

### Reclassifications

1. `politeness`
   - new interpretation: tractability-first lead lane, not yet scientifically preferred lane
2. `lying`
   - new interpretation: provisional negative finding / construct-invalid under current protocol
3. `honesty`
   - new interpretation: secondary unresolved lane with RLHF-asymmetry caveat

### Next build tranche

1. Distinctness analysis: `politeness` vs `sycophancy`
2. Branch-local bleed sidecar for `sycophancy` + `assistant_likeness`
3. Persistence-policy preregistration or metric investigation
4. Execution redesign: split extraction and validation launches
5. Test hardening: negative + integration + formula coverage

## Recommendation

- `inferred`: the next launch should not be another blind `politeness` deeper-validation rerun.
- `inferred`: the correct next move is a short remediation tranche that closes the review's strongest interpretive objections before additional GPU spend.
