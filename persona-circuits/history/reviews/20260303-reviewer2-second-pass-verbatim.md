# Reviewer 2 — Second Pass (Verbatim)

Source: user-provided reviewer text on 2026-03-03.

Second-Pass Critical Review

I. What Was Addressed Well

Credit where it's due. The remediation tranche handled several items cleanly:

Genuinely resolved:
- Hallucination formally closed (R2-C3/R2-G2). The trait scope resolution artifact correctly
  classifies it as negative_finding_stage1 and removes it from active claim scope. This is the right
  call.
- Evil construct alignment (R1-F5/R2-C4/R2-G3). The machiavellian external transfer is the strongest
  new artifact: overall_pass=true, plus_vs_minus=42.67, all directional gates pass. This validates the
  reframing.
- Stage 2 false-positive path closed (R1-F1). The claim-layer + multi-seed audit now correctly fails.
  You can't accidentally declare Stage 2 ready when it isn't. Good governance.
- Dual-scorecard governance (R1-F4). Surfacing both proposal-compatibility and hardening-reliability
  scorecards prevents goalpost-drift accusations. Smart.
- Rollout stability (R2-G7). 3→5 rollouts show sycophancy is stable (+0.47 delta) and evil has modest
  variance (-5.25 delta). This removes rollout count as a confound.

II. The Coherence Gate Problem Is Structural — My Original Diagnosis Was Partially Wrong

In my first review, I said coherence failure was "almost certainly a symptom of oversteer at
alpha=3.0." The constrained-selection evidence now proves that was only partially correct. Look at
the actual numbers:

┌──────────────────────────┬──────────────────────┬────────────────┬───────────┐
│          Config          │ Sycophancy coherence │ Evil coherence │ Threshold │
├──────────────────────────┼──────────────────────┼────────────────┼───────────┤
│ Alpha 3.0, prompt-last   │ 68.55                │ 64.63          │ 75.0      │
├──────────────────────────┼──────────────────────┼────────────────┼───────────┤
│ Alpha 2.0, prompt-last   │ 69.47                │ 64.63          │ 75.0      │
├──────────────────────────┼──────────────────────┼────────────────┼───────────┤
│ Alpha 2.0, response-mean │ ~similar             │ ~similar       │ 75.0      │
├──────────────────────────┼──────────────────────┼────────────────┼───────────┤
│ Rollout5, alpha 2.0      │ still fails          │ still fails    │ 75.0      │
└──────────────────────────┴──────────────────────┴────────────────┴───────────┘

Sycophancy coherence barely moves between alpha 3.0 and 2.0 (+0.92 points). Evil coherence is
identical at both alphas. Switching extraction method doesn't fix it. Adding rollout depth doesn't
fix it.

CURRENT_STATE.md:285 notes: "coherence failure appears dominated by absolute coherence_min_score=75
threshold (steered coherence improves vs baseline but remains below threshold)."

This is the critical finding. If steered coherence is higher than baseline coherence, and both are
below 75, then the gate is measuring a property of the model + prompt combination, not a property of
the steering quality. The coherence gate is rejecting outputs that the model would produce anyway,
even without any persona vector injection.

This changes the entire interpretation:

1. The 75 threshold was likely calibrated for a different model or prompt distribution
2. Chen's coherence concerns were about degradation relative to baseline, not absolute quality floors
3. Rimsky's multiplier limits are about the delta from unsteered behavior, not about hitting an
absolute score

Recommendation: This needs an immediate diagnostic: run the coherence scoring on unsteered baseline
outputs for both traits. If baseline coherence is also <75, the absolute threshold is miscalibrated
and should be replaced with a **relative gate** (e.g., steered_coherence >= baseline_coherence -
max_drop where max_drop=10). The relative gate already exists in the runner (max_drop=10.0) but
appears to not be the binding constraint — the absolute min_score=75 is. This distinction matters
enormously: a relative gate protects against steering-induced degradation (which is what the
literature actually warns about), while an absolute gate protects against low-quality models (which
isn't the experiment's concern).

If I'm right that baseline is also <75, this single change could unblock the entire project. But it
needs to be documented as an explicit decision with the rationale tied to what Chen/Rimsky actually
measured.

III. Extraction A/B: Correctly Characterized, Incorrectly Gated

The expanded position ablation (week2_extraction_position_ablation_20260227T225251Z.json) is thorough
— 50 pairs, layers 11-16, three extraction positions. The data is clear: no trait at any layer
reaches 0.7 prompt-last vs response-mean cosine.

But the expanded ablation also revealed something important that I missed in my first review:
response-mean vs response-last cosine IS high for sycophancy and evil (~0.75 / ~0.74). Within the
response generation regime, the two measurement points agree reasonably well. The disagreement is
specifically between prompt-end and response-generation.

This is actually expected from a mechanistic perspective:
- Prompt-last captures the model's planned disposition before autoregressive generation begins
- Response-mean captures the model's enacted disposition during generation
- These can genuinely differ because autoregressive dynamics introduce feedback loops not present at
the prompt boundary

The current A/B gate is comparing across computational regimes. That's a meaningful diagnostic (and
the result is informative), but treating it as a hard blocker conflates "extraction method
robustness" with "activation position consistency." These are different properties.

The more relevant robustness check — which you haven't run — would be:
1. Bootstrap resampling of extraction pairs: draw 80 of 100 pairs, extract vector, repeat 20 times.
If pairwise cosines are >0.8, the direction is prompt-robust. If they're low, the direction is
prompt-dependent.
2. Extraction vs held-out prompt agreement: extract from training prompts vs extract from held-out
prompts, check cosine agreement.

These test whether the direction is content-robust (same direction regardless of which specific
prompts you use), which is what matters for the PSM claim.

IV. Seed Replication Is Vacuous — This Needs Honest Acknowledgment

The seed replication artifact shows all pairwise cosines = 1.0 across seeds [42, 123, 456, 789]. This
was marked as resolved (R2-G6), but I need to flag: this test isn't testing what it appears to test.

The extraction pipeline uses ALL 100 extraction pairs per trait (no subsampling). The forward pass is
deterministic. The mean difference of a fixed set of fixed inputs is the same regardless of seed.
What the test actually verified is that torch.mean() is deterministic — which it always is.

The meaningful replication test would be bootstrap resampling (different subsets of extraction pairs)
or different extraction prompts entirely. The extraction-free overlap analysis is much closer to the
right test, and it showed weak-positive for sycophancy (cosine 0.13), moderate for evil (cosine
0.22), and null for hallucination.

I'm not saying this is urgent to re-run, but the checklist should note that seed replication
confirmed numerical determinism, not direction robustness. Don't cite it as evidence of extraction
stability in the paper.

V. Evil Asymmetry Is Inconsistent Across Domains

This is a new concern that emerged from cross-referencing the new artifacts:

Behavioral validation (rollout5, held-out prompts):
- Steering shift (plus): +2.03% (tiny)
- Reversal shift (minus): +40.52% (large)
- Pattern: can SUPPRESS evil, can't AMPLIFY it

Machiavellian external transfer:
- Plus vs baseline: +40.23 (large)
- Baseline vs minus: +2.43 (tiny)
- Pattern: can AMPLIFY evil, can't SUPPRESS it

These are opposite asymmetry patterns on different prompt distributions. On held-out prompts, the
model is already somewhat "machiavellian" at baseline (so you can suppress but not amplify). On
external machiavellian prompts, the model is NOT machiavellian at baseline (so you can amplify but
not suppress).

This is explainable by floor/ceiling effects and is not necessarily disqualifying. But it complicates
the "coherent bidirectional persona axis" claim. The direction works, but its behavioral expression
depends on the prompt distribution's starting point relative to the trait. This is worth documenting
as a limitation — it's honest mechanistic science, not a flaw.

VI. The Time-vs-Evidence Problem Is Now Acute

The project is 10 days into a multi-week plan. All 5 hypotheses remain "untested / low confidence."
No SAE decomposition has run. No attribution. No causal ablation. The entire remediation tranche
(WS-A through WS-F) produced validation evidence but zero hypothesis-testing results.

The remaining blockers are:
1. Coherence gate — likely resolvable with threshold recalibration (see Section II)
2. Extraction A/B — structural property, unlikely to clear 0.7 threshold; needs reframing as known
limitation or different robustness test
3. Stage 2 claim-layer integrity — token reconstruction at layer 12 fails (cos=0.70 < 0.75, EV=0.48 <
0.50); cross-SAE overlap at layer 12 is empty

You need to make a strategic decision about whether to keep iterating on Stage 1 gates or accept
documented limitations and advance to hypothesis testing.

VII. Recommended Next Actions (Priority-Ordered)

P0 — Potentially unblocks everything (hours, not days):

1. Run baseline (unsteered) coherence scoring on the same prompts for sycophancy and evil. If
baseline coherence is <75, the absolute threshold is miscalibrated. Document a decision to switch to
relative-only coherence gating (steered >= baseline - max_drop) with explicit rationale citing
Chen/Rimsky's focus on steering-induced degradation, not model-level quality floors.

P1 — Reframe rather than fix:

2. Reclassify extraction A/B from a hard gate to a documented limitation. The prompt-last vs
response-mean comparison tests cross-regime consistency, not extraction robustness. Add a proper
robustness test (bootstrap resampling of extraction pairs, or extraction from held-out prompts) and
gate on that instead. If bootstrap cosines are >0.8, the direction is prompt-robust even though it's
position-dependent.
3. Address Stage 2 claim-layer with a policy decision: either (a) accept single-SAE decomposition at
layer 12 as a limitation (no cross-check), (b) move primary claim layer to 11 where andyrdt coverage
exists, or (c) add an additional decomposition at layer 11 as a sensitivity check alongside layer 12.

P2 — Honest documentation:

4. Note seed replication tests determinism, not direction robustness.
5. Document evil asymmetry as a floor/ceiling phenomenon across prompt distributions.
6. Make a decision on R1-F6 (bleed threshold), R2-C5 (concordance sample size), and R2-G8 (capability
 suite). These are the three pending checklist items. For each, either do the work or explicitly
scope it as a known limitation.

VIII. Strategic Recommendation

The project's scientific contribution is at risk of being consumed by validation infrastructure. You
have strong behavioral evidence that sycophancy and machiavellian steering work (bidirectional
effects of 34% and 43% respectively). You have honest negative findings (hallucination,
harmful-content framing). You have rigorous methodology.

What you need now is hypothesis-testing data, not more gate refinement. I'd recommend:

1. Resolve the coherence gate (P0 above — probably a threshold fix)
2. Document A/B as a limitation, not a blocker
3. Make a policy decision on Stage 2 claim layer
4. Advance to SAE decomposition for sycophancy and machiavellian disposition with explicit documented
 caveats about reconstruction quality and cross-SAE limitations
5. Get H1 (coherence/concentration) evidence — this is the claim that will make or break the paper

The honest framing I suggested last time still holds: "persona steering operates through a partially
distributed mechanism with method-sensitive but seed-stable directions." The A/B failure and the
asymmetry are features of the story, not bugs — they constrain the PSM in specific, publishable ways.
