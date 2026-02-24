# Proposal Review: persona-circuits-proposal.md

**Reviewed against:** GAPS_SYNTHESIS.md, all closing-gaps/ sources, all persona-vectors/ sources, all circuit-tracing/ sources, RESEARCH_POSITIONING.md
**Date:** 2026-02-24

---

## CRITICAL ISSUES (must fix before execution)

### 1. Model selection is backwards from synthesis conclusion

**Proposal (§7.2):** Gemma 2 9B-IT = Primary, Llama 3.1 8B-Instruct = Replication
**GAPS_SYNTHESIS:** Llama 3.1 8B-Instruct = Primary, Gemma-2-2B = CLT proof-of-concept

The synthesis resolved this with substantial justification: 2/3 closing-gaps sources favor Llama, Chen et al. validated persona vectors on Llama 3.1 8B (as well as Qwen), Llama Scope provides full 32-layer coverage with instruct generalization verified, and andyrdt provides instruct-trained cross-check SAEs.

The proposal's choice of Gemma 2 9B-IT as primary is defensible IF GemmaScope IT SAEs actually exist at the needed layers — but the proposal's own Appendix B uses `google/gemma-scope-9b-pt-res` (pretrained, not IT), contradicting the §6.3.1 claim of using "Gemma 2 9B-IT" SAEs. This is a direct internal inconsistency.

**Fix:** Either (a) adopt GAPS_SYNTHESIS recommendation (Llama primary, Gemma-2-2B for CLT validation), or (b) verify GemmaScope IT SAE availability at layers 18–35 and fix Appendix B paths. Option (a) is safer and better justified.

### 2. Appendix B SAE checkpoint paths are wrong

**Line 1634:** `GEMMASCOPE_BASE = "google/gemma-scope-9b-pt-res"` — This is the PRE-TRAINED model SAEs, not instruction-tuned. The proposal claims to use Gemma 2 9B-IT (§6.3.1, §7.2), but the actual paths point to the pre-trained model.

**Line 1649:** `LLAMASCOPE_BASE = "EleutherAI/llama-scope-8b-res"` — This path does not match any verified source. Per ChatGPT closing-gaps (with citations):
- Llama Scope is from Fudan/OpenMOSS: `fnlp/Llama-Scope`
- EleutherAI's SAEs are: `EleutherAI/sae-llama-3.1-8b-32x` and `EleutherAI/sae-llama-3.1-8b-64x`

These are different projects from different organizations. The proposal conflates them.

**Fix:** Correct all HuggingFace paths. Use verified paths from ChatGPT closing-gaps (which provides linked citations for each).

### 3. Ablation method ordering contradicts best practice

**Proposal (§7.4, line 1052):** Mean ablation = Primary, Zero/Resample = Secondary
**GAPS_SYNTHESIS + Gemini + ChatGPT:** Resample ablation = Gold standard

Mean ablation has known problems: it introduces unrelated concept information into the forward pass, muddying causal signal. Li & Janson (2024) showed standard ablation overestimates importance by ~9×. The proposal mentions Li & Janson (line 1054) but then proceeds to use mean ablation as primary anyway.

**Fix:** Resample ablation (activation patching) as primary. Mean ablation as fast-iteration secondary. Report both. This aligns with 2/3 sources and the literature consensus.

### 4. Missing bidirectional causal validation

**Proposal:** Only includes forward direction (steer → ablate → measure).
**GAPS_SYNTHESIS identified Gemini's bidirectional design as its single best contribution:**

- **Forward:** Inject persona vector → identify circuit → ablate circuit → behavior should revert
- **Reverse:** Present trait-eliciting prompts naturally → ablate persona vector direction from residual stream → if circuit activation collapses, persona vector IS the upstream cause

The reverse test provides fundamentally different evidence: it shows the persona vector is the causal TRIGGER, not just correlated with the circuit. Without it, you can only claim the circuit is necessary for the steering effect — you can't claim the persona representation is the upstream cause of natural trait-consistent behavior.

**Fix:** Add reverse causal test to §6.5 and §9.

### 5. No pre-registered disconfirmation criteria

**psm-analysis.md (weakness #5):** "If any behavior contradicting PSM can be attributed to 'simulation failure,' the theory becomes unfalsifiable."

The proposal lists "PSM Validation Criteria" (§9.5) with "Supported If" and "Challenged If" columns, but these are vague. More importantly, the proposal doesn't specify what constitutes a FAILED experiment vs. a "we need more data" experiment. Without pre-registered stopping rules and disconfirmation thresholds, there's a risk of post-hoc rationalization.

**Fix:** For each hypothesis, specify the exact threshold below which the result constitutes a negative finding. Example: "If no circuit of <20% of components achieves >50% completeness across ≥2 traits, we conclude persona mechanisms are diffuse and PSM's mechanistic predictions are not supported at this scale." Write these before running experiments.

---

## SIGNIFICANT ISSUES (should fix for rigor)

### 6. Completeness threshold is too low

**Proposal (§5.2, §7.3, §9.2):** Uses 0.70 completeness threshold throughout.
**GAPS_SYNTHESIS:** Argues 0.70 is too low — at 70%, almost a third of the effect is unexplained. Recommends >0.80 for faithfulness.

The proposal actually uses 0.70 for completeness AND 0.80 for faithfulness (§9.2), which creates confusion: completeness ≥70% but faithfulness ≥80%? These measure different things but the distinction isn't clearly drawn. The definitions in §5.2 are:
- Completeness: "Ablating C_T reduces steering effect by ≥70%"
- Faithfulness: "Running only C_T preserves ≥80% of full model steering behavior"

This means the sufficiency bar (80%) is HIGHER than the necessity bar (70%), which is backwards from usual practice. Necessity should be the stronger claim.

**Fix:** Align thresholds: necessity (completeness) ≥80%, sufficiency (faithfulness) ≥60% (as in GAPS_SYNTHESIS §4.1). This matches the intuition that it's easier to show something is necessary than sufficient.

### 7. Statistical plan lacks effect size metrics

**Proposal (§9.3):** Mentions p < 0.01, 95% CIs, Bonferroni, bootstrap. But does NOT specify effect size metrics.
**GAPS_SYNTHESIS:** Recommends reporting BOTH Cohen's d AND Vargha-Delaney A₁₂.

P-values without effect sizes are insufficient for this type of work. A circuit that reduces the steering effect by 51% (barely passing the >50% necessity threshold) with p < 0.01 is a very different finding than one that reduces it by 90%.

**Fix:** Add Cohen's d and A₁₂ to §9.3. Specify A₁₂ > 0.71 (large effect) as the minimum for primary claims.

### 8. Concentration metrics missing for modularity classification

**Proposal (§5.2):** Defines modular vs. diffuse qualitatively but provides no quantitative concentration metrics.
**GAPS_SYNTHESIS (from ChatGPT):** Recommends Gini coefficient, entropy of normalized contributions, top-p mass.

These metrics are critical for the modular vs. diffuse classification that's central to the paper's contribution. Without them, "modular" and "diffuse" are judgment calls rather than quantitative findings.

**Fix:** Add to §9.2:
- Gini coefficient over node contributions (high = modular, threshold > 0.5)
- Shannon entropy of normalized contributions (low = modular)
- Top-p mass: fraction of total effect captured by top p% nodes

### 9. Venkatesh et al. (2026) not cited — identifiability objection unaddressed

**GAPS_SYNTHESIS + RESEARCH_POSITIONING:** Venkatesh et al. (Feb 2026) proved steering vectors are "fundamentally non-identifiable" due to large equivalence classes of behaviorally indistinguishable interventions. However, identifiability is recoverable under sparsity constraints — precisely the SAE decomposition we propose.

This is a known objection that a reviewer will raise. The proposal should cite this paper proactively and explain why SAE sparsity resolves the identifiability problem.

**Fix:** Add Venkatesh et al. to §3 Literature Review and §11 Risk Assessment. Explain the sparsity recovery argument.

### 10. Chen et al. model usage is imprecise

**Proposal (line 177):** "Layer 20 (Qwen-7B) / Layer 16 (Llama-3-8B) as sharpest extraction points"
**Verified fact:** Chen et al. used BOTH Qwen2.5-7B AND Llama-3.1-8B. The proposal should say "Qwen2.5-7B" not "Qwen-7B" and "Llama-3.1-8B" not "Llama-3-8B".

More importantly, the proposal's layer selection guidance (layers 18-35 for Gemma, layers 12-24 for Llama) should explicitly connect to Chen et al.'s finding: steering effectiveness peaks at ~35-50% of model depth. For Llama 3.1 8B (32 layers), that's layers 11-16, which overlaps with but is lower than the proposal's 12-24 range. The optimal layer for circuit tracing may differ from the optimal steering layer.

**Fix:** Correct model names. Add a note about the distinction between optimal steering layer and optimal circuit analysis range.

### 11. 4 traits may be overambitious for 8-week timeline

**Proposal:** 4 traits (sycophancy, evil, hallucination, refusal)
**GAPS_SYNTHESIS and RESEARCH_POSITIONING MVC:** 3 traits (sycophancy, evil, hallucination)

Adding refusal as a 4th trait increases:
- Extraction compute by 33%
- Circuit tracing compute by 33%
- Ablation validation by 33%
- Cross-persona comparisons from 3 pairs to 6 pairs

The proposal's compute estimate (100-160 A100-hours) already includes cross-model replication. With GAPS_SYNTHESIS estimating 20-50 hours for 3 traits on one model, the proposal's scope is 3-8× larger than the MVC.

**Fix:** Either (a) start with 3 traits and add refusal as extension, or (b) extend timeline to 10-12 weeks, or (c) cut cross-model replication from the 8-week scope.

### 12. Sycophancy measurement (Appendix C) is naive

**Appendix C (line 1665-1691):** Uses keyword matching ("you're right", "actually") to measure sycophancy. This is brittle — a model can be sycophantic without using any of these phrases, and can use these phrases while disagreeing.

**Proposal main text (implied by §7.3):** Uses GPT-4.1-mini as judge with trait-specific rubric.

These are inconsistent. The keyword approach in the appendix will not produce reliable scores.

**Fix:** Remove the keyword implementation from Appendix C. Replace with the LLM-judge approach described in the closing-gaps sources (GPT-4.1-mini scoring on 0-100 rubric). The appendix should show the actual evaluation rubric, not a keyword matcher.

---

## MODERATE ISSUES (improve if time permits)

### 13. Missing Lu et al. (2026) — Assistant Axis

The Assistant Axis paper (Lu et al., Jan 2026) is referenced in PSM and in GAPS_SYNTHESIS/RESEARCH_POSITIONING as foundational, but is absent from the proposal's literature review. The Assistant Axis (PC1 of persona space across 275 character archetypes) is directly relevant to Hypothesis H5 (Router) and to the cross-persona analysis (§6.6).

**Fix:** Add to §3.1 and connect to H5.

### 14. Circuit tracing code (§6.4) lacks attention to computational graph

The gradient-based attribution code (lines 729-741) computes gradients of delta_logits w.r.t. SAE features. This is fine as a first-order approximation, but it doesn't capture feature-to-feature interactions. The code identifies which features are important for the output change, but doesn't map the edges between features.

For a paper claiming to identify "circuits" (not just "important features"), some inter-feature edge analysis is needed. The proposal should either:
(a) Build a reduced attribution graph over top features using direct-effect formalism (per ChatGPT §Step 5), or
(b) Be explicit that the hybrid approach identifies "important feature sets" rather than "circuits" in the strict graph-theoretic sense, and note this as a limitation

**Fix:** Add a step between gradient attribution and ablation that constructs a reduced edge graph over top candidate features. Alternatively, scope the claims appropriately.

### 15. W&B config (Appendix E) lists Gemma as primary

**Line 1731-1737:** The W&B config has `"primary": "google/gemma-2-9b-it"` and `"secondary": "meta-llama/Llama-3.1-8B-Instruct"`. This will need updating if model selection changes per Issue #1.

### 16. Prompt count inconsistencies

| Context | Count |
|---------|-------|
| Persona extraction (§6.2.2) | 100 prompt pairs per trait |
| Behavioral validation (§7.1.2) | 50 held-out per trait |
| Circuit analysis (§7.1.3) | 20 per trait |
| Ablation validation (§6.5) | Not specified explicitly |
| GAPS_SYNTHESIS recommendation | 100 min, 200 preferred for ablation |

The ablation validation section should specify a prompt count. With only 20 circuit analysis prompts, there's a risk that identified circuits overfit to those specific prompts. The stability metric (Jaccard ≥0.30) partially addresses this, but the ablation validation should run on a HELD-OUT set larger than the circuit discovery set.

**Fix:** Specify 100 held-out prompts for ablation validation, separate from the 20 circuit discovery prompts.

### 17. Compute estimate is inconsistent with scope

**Proposal (§8.2):** 100-160 A100-hours total
**GAPS_SYNTHESIS:** 20-50 A100-hours for 3 traits, 1 model

The proposal includes 4 traits × 2 models, which should be roughly 4× the single-model estimate. But 4 × 50 = 200, which exceeds the proposal's own estimate. The cross-model replication alone is listed as 40-60 hours.

**Fix:** Re-estimate. If keeping full scope, estimate 150-250 A100-hours. If sticking with the 100-160 budget, cut scope accordingly.

### 18. Gemma-2-2B role is underspecified

**Proposal (§7.2):** Lists Gemma 2 2B-IT for "Methodology validation" but doesn't explain what this means in practice.
**GAPS_SYNTHESIS:** Specifies Gemma-2-2B with existing CLTs for full-pipeline proof-of-concept — run the full Anthropic-style attribution graph pipeline on 2B to validate that the hybrid approach on 8B produces qualitatively similar results.

This is a critical piece of the methodology's credibility. If the hybrid approach on 8B identifies different circuit structures than the full CLT approach on 2B, the hybrid results are suspect.

**Fix:** Expand §7.2 or add a subsection explaining exactly how Gemma-2-2B validates the hybrid methodology. Specify: run full CLT pipeline on 5-10 prompts per trait on 2B, compare circuit properties (modularity, feature categories, cross-trait overlap) to hybrid results on 8B.

### 19. Missing Li & Janson context despite citation

**Line 1054:** "Report all three to check robustness (per Li & Janson recommendation)"

This undersells the finding. Li & Janson (2024, NeurIPS) showed that standard ablation overestimates component importance by ~9× due to "spoofing" — the ablated value actively misleads downstream computation, producing artificially large effects. This isn't just "check robustness" — it's "your primary results may be wrong by an order of magnitude if you only use one ablation method."

**Fix:** Add a dedicated subsection about this in §6.5 or §11. Make multi-method validation a REQUIREMENT, not a nice-to-have.

### 20. No mention of "obfuscation tax" implications for our work

**Bailey et al.** found that obfuscation severely degrades model performance on complex tasks. This has a direct implication for our circuit claims: if persona circuits handle complex persona simulation, they may be inherently harder to obfuscate than single-layer representations. The proposal mentions Bailey et al. (§3.2.2) but doesn't connect the obfuscation tax to our circuit robustness hypothesis.

**Fix:** Add this connection in §3.2.2 or §14.1.

---

## MINOR ISSUES

### 21. Document status should not be "Ready for Execution"

Given the issues above, the proposal is a strong draft but not execution-ready. Change to "Draft — Under Review."

### 22. Code formatting is broken in several places

Multiple code blocks in the proposal have garbled formatting (e.g., lines 593-596, 668-669, 714-718, 775-784). Variable names are concatenated (`personavector`, `outputsteered`, `deltalogits`). This suggests the document was generated and not carefully proofread.

**Fix:** Clean up all code blocks. Variable names should use underscores consistently.

### 23. Table formatting is broken

Several tables (§2.3, §3.5, §4.3) appear as tab-separated text rather than proper markdown tables. This is a rendering issue.

### 24. "Steering coefficients typically 0.5-2.0" may be too narrow

The proposal (line 183) cites Chen et al. for α typically 0.5-2.0, but the steering sweep in Phase 1 should go to at least 3.0 (per GAPS_SYNTHESIS) to fully characterize the dose-response curve. Claude closing-gaps also recommends {0.5, 1.0, 1.5, 2.0, 2.5}.

**Fix:** Extend sweep to α ∈ {0.5, 1.0, 1.5, 2.0, 2.5, 3.0} and note that working coefficient will be determined empirically.

### 25. Missing citations from RESEARCH_POSITIONING

The following papers are in the required citations list (RESEARCH_POSITIONING §3) but absent from the proposal:
- Venkatesh et al. (2026) — steering vector non-identifiability
- Lu et al. (2026) — Assistant Axis
- Yang et al. (2024) — SAEs vs RepE timescale distinction
- Bhandari et al. (2026) — trait interference / geometric limitations
- Rimsky et al. (2024) — CAA (systematic scaling of steering vectors)
- Kantamneni et al. (ICML 2025) — SAE reconstruction discards safety-relevant info

---

## CROSS-SOURCE INCONSISTENCIES

### A. Proposal vs. GAPS_SYNTHESIS

| Dimension | Proposal | GAPS_SYNTHESIS | Which is correct? |
|-----------|----------|----------------|-------------------|
| Primary model | Gemma 2 9B-IT | Llama 3.1 8B-Instruct | GAPS_SYNTHESIS (better justified) |
| Primary ablation | Mean | Resample | GAPS_SYNTHESIS (literature consensus) |
| Completeness threshold | ≥0.70 | ≥0.80 (faithfulness) | Adopt ≥0.80 for necessity, ≥0.60 for sufficiency |
| Effect size metrics | Not specified | Cohen's d + A₁₂ | GAPS_SYNTHESIS |
| Bidirectional validation | Missing | Included | GAPS_SYNTHESIS |
| Trait count | 4 | 3 (MVC) | 3 for MVC, 4 as extension |
| Timeline | 8 weeks | 8-10 weeks | 10 weeks more realistic for this scope |
| Compute estimate | 100-160 hrs | 20-50 hrs (single model) | Both may be wrong; need careful re-estimation |

### B. Proposal vs. Source Materials

| Claim in Proposal | Actual (per source materials) |
|-------------------|-------------------------------|
| "Layer 20 (Qwen-7B)" (line 177) | Should be "Qwen2.5-7B" — version matters |
| "Layer 16 (Llama-3-8B)" (line 177) | Should be "Llama-3.1-8B" — version matters |
| Llama Scope from EleutherAI (Appendix B) | Llama Scope is from fnlp/OpenMOSS, NOT EleutherAI |
| GemmaScope uses JumpReLU (line 353) | Correct for GemmaScope 1; andyrdt uses BatchTopK |
| "Alignment Faking (Denison et al., December 2024)" (line 249) | The primary alignment faking paper is Greenblatt et al., not Denison. Denison is the Sycophancy to Subterfuge paper |

### C. Internal Inconsistencies in the Proposal

1. §6.3.1 says "Gemma 2 9B-IT" SAEs; Appendix B paths use pretrained model (`-pt-res`)
2. §7.1.3 says 20 prompts for circuit analysis; §6.4.1 code operates on arbitrary prompt count
3. §7.4 says mean ablation is primary; the Li & Janson citation in the same section implies it shouldn't be
4. Appendix C uses keyword matching; main text implies LLM-judge evaluation
5. §1.4 scope says "3-4 traits"; §7.1 specifies exactly 4 traits
6. §8.2 compute estimate includes replication; timeline milestone (§10.2) allows cutting replication

---

## SYNTHESIS: WHAT GAPS_SYNTHESIS SHOULD CONTRIBUTE TO THE PROPOSAL

### Direct augmentations (merge in)

1. **Bidirectional causal validation protocol** (GAPS_SYNTHESIS §4, from Gemini) — the proposal's strongest missing piece
2. **Effect size metrics** (Cohen's d + A₁₂) — required for publication quality
3. **Concentration metrics** (Gini, entropy, top-p mass) — needed for quantitative modularity classification
4. **Disconfirmation criteria** — needed for scientific credibility and to address PSM unfalsifiability concern
5. **Venkatesh et al. citation** — preemptive defense against identifiability objection
6. **Li & Janson elevated prominence** — the 9× overestimation finding changes how ablation results should be interpreted
7. **Correct SAE checkpoint paths** — the current ones are wrong

### Modifications (change existing content)

1. **Swap model priority** — Llama primary, Gemma-2-2B validation (or verify Gemma IT SAE availability first)
2. **Swap ablation priority** — resample primary, mean secondary
3. **Align thresholds** — necessity ≥80%, sufficiency ≥60%
4. **Reduce to 3 traits** for MVC (add refusal as extension)
5. **Fix all checkpoint paths**
6. **Fix all code formatting**
7. **Correct citation for alignment faking** — Greenblatt et al., not Denison et al.

### Enhancements (add new sections)

1. **Source reliability assessment** — note that Gemini's infrastructure claims were wrong; this matters because the proposal seems to have drawn from multiple sources without reconciling conflicts
2. **Explicit CLT proof-of-concept subsection** — explain exactly how Gemma-2-2B validates the hybrid methodology
3. **Steering coefficient dose-response subsection** — extend sweep range, connect to circuit stability analysis
4. **Obfuscation tax connection** — strengthen the circuit robustness hypothesis

---

## OVERALL ASSESSMENT

The proposal is comprehensive, well-structured, and covers the right ground. The literature review is solid. The methodology is sound in concept. The timeline is aggressive but plausible for a dedicated researcher.

**However, it has significant inconsistencies that suggest it was assembled from multiple AI-generated sources without full reconciliation.** The wrong SAE paths, the model name imprecisions, the ablation ordering contradicting the cited literature, the broken code formatting — these all point to a document that needs one more careful editing pass where every claim is verified and every path is checked.

The GAPS_SYNTHESIS fills the proposal's biggest methodological gaps: bidirectional validation, effect size metrics, concentration metrics, and disconfirmation criteria. Merging these in would elevate the proposal from "strong draft" to "execution-ready."

**Recommended next step:** Fix the 5 critical issues, merge the GAPS_SYNTHESIS augmentations, verify all HuggingFace paths against actual repos, and clean up code formatting. Then change status to "Ready for Execution."
