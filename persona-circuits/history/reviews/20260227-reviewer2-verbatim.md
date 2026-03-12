REVIEWER 2:
Deep Critical Review: Persona Circuits — Week 2 Closeout

  I. Executive Position Summary

  Sohail, after reading through the full artifact trail, the project is in a scientifically honest but structurally precarious state. You've built rigorous
  validation infrastructure (literature-grounded gates, multi-source checks, deterministic traceability), but the underlying persona vectors themselves are
  showing signs of fragility that go deeper than any individual gate failure. The NO-GO decision is correct. Below I lay out where you actually stand, what
  the gaps are, and where the real misalignments with the literature lie.

  ---
  II. Where You Actually Are

  Completed:
  - Infrastructure (Week 1): PASS — model loading, SAE forward passes, prompt generation, audit
  - Contrastive extraction pipeline: implemented, vectors extracted, cosine-margin backfill done
  - Behavioral validation upgrade: comprehensive (judge calibration, lockbox splits, norm diagnostics, cross-trait bleed, rollout averaging)
  - Primary reruns: all 3 traits terminalized and deterministically ingested
  - Closeout checks: manual concordance + gap checks executed
  - Stage 2 audit: token-level SAE reconstruction passes (barely)
  - Stage 3/4 scaffold: metric primitives + ablation modality schema in place
  - Local test suite: 66 tests passing

  Not completed:
  - No hypothesis has ANY evidence (all 5 are "untested / low confidence")
  - No SAE decomposition has been run
  - No attribution/circuit discovery
  - No causal ablation
  - Gemma validation: not started
  - Writing: not started

  Effective status: Two weeks of work have produced a validated extraction pipeline and a comprehensive methodology harness, but zero hypothesis-testing
  results. This is defensible from a rigor perspective — you didn't cut corners — but the project has a time-vs-evidence problem.

  ---
  III. Critical Issue #1: The Alpha 3.0 Selection Problem

  All three selected combos use alpha=3.0 — the maximum of your sweep range [0.5, 1.0, 1.5, 2.0, 2.5, 3.0].

  This is the single most concerning structural finding. The sweep maximized raw behavioral signal by picking the most aggressive coefficient. But:

  - Chen et al. (2025) explicitly reports that "increasing trait suppression with larger coefficients" comes with "capability degradation at high
  coefficients" (your own lit review notes this at chen2025_persona_vectors.md:839-840).
  - Rimsky (2024) CAA "explicitly limits multiplier range when larger multipliers degrade open-ended quality"
  (rimsky2024_contrastive_activation_addition.md:198).
  - Turner (2024) defines relative steering magnitude as injection norm / residual norm and warns that effective coefficients approaching the residual scale
  cause oversteer (turner2024_activation_addition.md:987-1003, :1015).

  The coherence gate failing for ALL THREE traits is almost certainly a symptom of oversteer at alpha=3.0. This isn't a rubric calibration issue — it's the
  predictable consequence of injecting at the maximum sweep value. The sweep selected "biggest behavioral delta" rather than "strongest reliable signal,"
  which is a different optimization target.

  Implication for downstream work: If you proceed to Stage 2 decomposition with alpha=3.0 vectors, the SAE features you identify may reflect oversteer
  artifacts (model confusion/degradation) rather than actual persona circuit activation. This would contaminate H1 (coherence), H2 (necessity), and H3
  (sufficiency) claims.

  Recommendation: Re-run the selection at alpha=2.0 or 2.5 and check whether the coherence gate passes. If the behavioral effect at alpha=2.0 is too weak to
  pass steering gates, that itself is informative — it suggests the direction is noisy rather than the persona axis being strong.

  ---
  IV. Critical Issue #2: Extraction Method A/B Failure (Fundamental)

  All three traits show cosine similarity ~0.37-0.41 between prompt-last and response-mean extraction methods, against a 0.7 threshold.

  This is not a calibration problem. A cosine of 0.4 means the two methods disagree on roughly half the variance in the direction. For a "persona vector"
  that's supposed to represent a coherent latent trait, this is deeply concerning.

  What it means: The direction you get depends enormously on WHERE in the forward pass you measure activations. Prompt-end activations (before generation)
  and response-mean activations (during generation) point in substantially different directions. If the persona vector were a robust, circuit-level feature,
  you'd expect reasonable agreement — not 0.4.

  Paper grounding:
  - Zou et al. (2023) uses reading vectors at fixed positions (last token) and acknowledges extraction position sensitivity
  (zou2023_representation_engineering.md:455).
  - Turner (2024) notes that activation vectors from different positions can have very different characteristics — this is expected in some degree, but
  cosine 0.4 is far below what contrastive methods typically produce when the underlying signal is strong.

  The 0.7 threshold is actually generous. In representation engineering work, cosines >0.8 between extraction methods are typical for robust directions
  (e.g., truthfulness, sentiment). 0.4 suggests either:
  1. The extraction prompt pairs are not eliciting the intended contrast cleanly
  2. The trait definition is too diffuse to produce a single coherent direction
  3. The layer selection is capturing local prompt-response dynamics rather than a stable trait representation

  This directly threatens the PSM (Persona Selection Model) foundation. If the persona vector isn't stable across extraction methods, the "sparse
  identifiable circuit" story in H1 becomes much harder to tell.

  ---
  V. Critical Issue #3: Hallucination is Null — Drop It

  The evidence across every test is consistent:

  ┌───────────────────────────────────┬──────────────────────┬────────────────────────────────────┐
  │               Test                │ Hallucination Result │           Interpretation           │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Reversal shift                    │ -0.30%               │ Noise                              │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Bidirectional effect              │ 5.92%                │ Sub-threshold                      │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Judge kappa                       │ 0.608                │ Borderline                         │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Extraction-free cosine            │ -0.006               │ Null (indistinguishable from zero) │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Extraction-free positive fraction │ 0.44                 │ Below chance correction            │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Sign-test p-value                 │ 0.48                 │ Not significant                    │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Set-mean CV                       │ 3.28                 │ Extreme instability                │
  ├───────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
  │ Section 6.2.3                     │ FAIL                 │ Reversal + judge reliability       │
  └───────────────────────────────────┴──────────────────────┴────────────────────────────────────┘

  Your own THOUGHT_LOG correctly infers that "hallucination likely tracks instruction-conditioned calibration/refusal dynamics rather than a stable
  persona-like direction under current protocol."

  This is important negative evidence for the paper. It's not a failure — it's a finding. If hallucination doesn't steer like sycophancy and evil, that
  constrains the PSM: not every behavioral dimension people call a "persona trait" is actually mediated by a coherent latent direction. This is worth
  reporting honestly.

  Recommendation: Formally mark hallucination as a negative finding for Stage 1 and exclude it from primary Stage 2-5 claims. Consider including it as
  supplementary/exploratory evidence. If you want a third trait, you could add a genuinely steering-amenable axis (e.g., formality, verbosity, or
  agreeableness — per Chen's broader trait set).

  ---
  VI. Critical Issue #4: Evil Trait Bidirectionality + Framing Tension

  Evil passes section 6.2.3 (steering + reversal) and shows the strongest extraction-free overlap (cosine 0.223), but fails external transfer directionally
  because baseline_vs_minus < 0 on the harmful_behaviors benchmark.

  This means: applying the negative (reversal) direction doesn't reduce harmful behavior on external prompts. The plus direction works (increases it), but
  minus doesn't reverse it.

  Why this matters:
  - Bidirectionality is a core claim in contrastive activation addition (Rimsky 2024, Turner 2024). If the direction is only "pushable" in one direction, it
  may be an artifact of instruction-following sensitivity rather than a persona feature.
  - The reframing from "harmful content" to "machiavellian disposition" is honest and well-documented, but it creates an interpretation gap: your extraction
  prompts were designed for harm, your extraction-free evidence supports machiavellian, and your external benchmark uses harm. These are different
  constructs.

  Recommendation:
  - Run the external transfer check with a machiavellian/manipulation benchmark rather than harmful_behaviors
  - If it passes bidirectionally on the right benchmark, the reframing is validated
  - If it doesn't, the direction may be unidirectional (which is still publishable but changes the claim)

  ---
  VII. Critical Issue #5: Manual Concordance is Too Small for Its Claims

  5 examples per trait (15 total) gives you effectively zero statistical power. The overall MAE of 4.7 looks good on a 0-100 scale, but:

  - For evil, sign agreement is only 60% (3/5 agreed) — this is a coin flip
  - With n=5, even 100% agreement has a very wide confidence interval
  - Chen et al. uses substantially larger human evaluation sets for judge calibration

  The concordance check is useful as a "sanity check" but should not be cited as evidence of judge reliability. The cross-rater kappa from the behavioral
  validation runner (0.795 for sycophancy, 0.788 for evil) is much stronger evidence.

  Recommendation: If you do remediation work, increase the manual concordance to at least 15-20 per trait. Or, rely on the kappa metric from the runner and
  downweight the manual concordance in your narrative.

  ---
  VIII. Critical Issue #6: SAE Reconstruction Quality for Stage 2

  Token-level reconstruction passes at cosine=0.77 (base) / 0.77 (instruct), explained variance=0.57/0.57. Your threshold is cosine≥0.75, EV≥0.50.

  These numbers pass your gates, but they are low by SAE literature standards:

  - Bricken et al. (2023) and Cunningham et al. (2023) typically report reconstruction cosines >0.90 for SAEs they consider high-quality.
  - An explained variance of 0.57 means 43% of activation variance is unaccounted for. Features identified from this SAE may explain less than half of the
  actual model computation.

  Implication for H1 (Coherence): If you decompose your persona vector through an SAE that only captures 57% of variance, you might find that the vector is
  "diffuse" not because the circuit is diffuse, but because the SAE's basis doesn't cover the relevant computation space. This creates an attribution
  confound — you can't distinguish "the circuit is genuinely spread out" from "the SAE is lossy."

  Cross-SAE validation is also limited: Layers 11 and 15 overlap between LlamaScope and andyrdt, but your selected steering layers are 12 and 13. Neither
  selected layer has cross-check SAE coverage. This means you cannot validate your primary decomposition results against an independent SAE at the layers
  that matter most.

  ---
  IX. Gap Analysis — What's Missing

  ┌────────────────────────────────┬──────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │              Gap               │ Severity │                                               Description                                                │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Lower-alpha validation         │ High     │ No evidence that alpha <3.0 produces steerable, coherent behavior. Required to distinguish "signal       │
  │                                │          │ exists" from "only visible under oversteer"                                                              │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Hallucination formal status    │ Medium   │ Not formally dropped; still occupies checklist items and future planning                                 │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Evil external benchmark        │ Medium   │ External benchmark (harmful_behaviors) doesn't match reframed construct (machiavellian)                  │
  │ alignment                      │          │                                                                                                          │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Cross-SAE at selected layers   │ High     │ No independent SAE validation at layers 12, 13 — the actual selected layers                              │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Extraction method robustness   │ High     │ No diagnosis of WHY prompt-last vs response-mean disagree at 0.4 cosine                                  │
  │ root cause                     │          │                                                                                                          │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Multi-seed extraction          │ Medium   │ Extraction was done with seed=42 only; seeds 123, 456, 789 are planned but not run                       │
  │ replication                    │          │                                                                                                          │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Rollout stability beyond 3     │ Low      │ 3 rollouts per config is a start; Chen uses 10, Wang uses 1000                                           │
  │ samples                        │          │                                                                                                          │
  ├────────────────────────────────┼──────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Capability benchmark suite     │ Low      │ "Capability preservation" is mentioned as <5% drop but the benchmark itself isn't clearly specified      │
  └────────────────────────────────┴──────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  X. Misalignment Between Implementation and Literature

  1. Layer selection criterion differs from Chen.
  Chen selects layers based on held-out behavioral effect at moderate coefficients. Your sweep selected based on maximum behavioral signal at alpha=3.0.
  These can produce different optimal layers.

  2. Extraction protocol differs from Zou's recommendation.
  Zou (2023) explicitly uses "far-out-of-distribution stimuli" to prevent leakage and overfitting to extraction conditions. Your extraction uses
  system-prompt pairs that are close to the evaluation distribution. The extraction-free evaluation was a good addition to check this, but hallucination's
  null result suggests it may be partially capturing prompt-distribution artifacts rather than underlying trait directions.

  3. Random baseline count is planned but not executed.
  Your PREREG specifies "≥100 random same-size baselines." The scaffold includes this requirement, but no actual random baseline comparison has been run yet.
   This is a Stage 4 dependency but worth tracking.

  4. The coherence-vs-capability trade-off is underspecified.
  Chen and Rimsky both identify the coefficient where capability starts degrading as a key methodological parameter. Your pipeline has a coherence gate
  (which is failing) but doesn't have a formal "optimal alpha = argmax(behavioral_effect subject to coherence≥threshold)" selection procedure. Instead, it
  selects the (layer, alpha) with the highest raw effect.

  ---
  XI. Recommended Priority Actions

  P0 (Must-do before any Stage 2 work):

  1. Re-run behavioral validation at alpha=2.0 and alpha=2.5 for sycophancy and evil. If behavioral effects remain above threshold AND coherence passes, you
  have your answer: alpha=3.0 was oversteer. If effects collapse at lower alpha, the underlying direction is weak. Either outcome is scientifically
  informative.
  2. Root-cause the extraction A/B failure. Before treating this as "method sensitivity," check whether the prompt-last vs response-mean disagreement is
  driven by layer choice, specific prompts, or a systematic activation-position effect. Run the A/B check at layers 11-16 to see if any layer shows higher
  agreement.
  3. Formally close hallucination as a negative finding for Stage 1. Remove it from active planning for Stages 2-5. Include it as supplementary evidence in
  the paper.

  P1 (Should-do before paper claims):

  4. Run evil external transfer on a machiavellian-aligned benchmark to validate the reframing. If it fails bidirectionally on the right benchmark too, the
  direction is unidirectional.
  5. Check whether andyrdt SAE at layer 11 or 15 can provide meaningful cross-validation for the nearest selected layer (12). If not, consider adding layer
  11 or 15 to your primary steering candidate set.

  P2 (Nice-to-have):

  6. Increase manual concordance sample to 15-20 per trait.
  7. Run multi-seed extraction (seeds 123, 456, 789) to check extraction stability.
  8. Formalize the alpha selection procedure as "maximum effect subject to coherence constraint" rather than "maximum effect."

  ---
  XII. Overall Assessment

  Strengths of the project:
  - Exceptionally rigorous validation infrastructure (multi-gate, literature-grounded)
  - Honest negative findings are tracked and not swept away
  - Traceability is excellent (every artifact is logged, indexed, timestamped)
  - The NO-GO decision shows scientific maturity

  Core vulnerability:
  The persona vectors themselves may be fragile. The combination of alpha=3.0 selection, extraction A/B failure at 0.4 cosine, universal coherence gate
  failure, and hallucination null signal all point in the same direction: the contrastive extraction is capturing something, but that something may be more
  method-dependent and less circuit-like than the PSM hypothesis requires. This isn't fatal — sycophancy and evil show real behavioral effects and
  extraction-free overlap — but it constrains how strong your eventual claims can be.

  The honest framing for the paper might be: "We find evidence for concentrated persona-relevant features for sycophancy and a machiavellian disposition
  axis, but not for hallucination. The representation is extraction-method-sensitive, suggesting persona steering operates through a partially distributed
  mechanism rather than a single clean direction."

  That's a publishable, interesting finding — potentially more interesting than the clean "sparse circuits everywhere" story, because it constrains the PSM
  in a specific, testable way.
