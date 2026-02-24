# ABOUTME: Practical guidance for mechanistic interpretability research.
# ABOUTME: Hard-won field lessons, gotchas, sanity checks, and failure mode taxonomy.

# Mechanistic Interpretability — Practical Field Guidance

Hard-won lessons from the interpretability research community. The tacit knowledge that doesn't make it into methods sections but determines whether your results are meaningful.

**When to use this document:**
- Before starting each new phase — skim the relevant section for gotchas
- When something unexpected happens — check §8.2 (Failure Mode Taxonomy) first
- Before reporting any result — run the §12 Sanity Checks
- Before writing up — use the §11 Logging Checklist to verify completeness
- When a result seems too clean or too messy — read §10 (Red Flags)

---

## 1. General Mindset and Philosophy

### 1.1 Mech Interp Is an Empirical Science

The field operates more like biology than mathematics. You're reverse-engineering an alien system without documentation.

**Implications:**
- Your first hypothesis about what a circuit does is almost always wrong
- Negative results are common and valuable
- Exploratory work is legitimate, but know when you're exploring vs. confirming
- The model doesn't owe you interpretable structure — it may not exist

### 1.2 The Cherry-Picking Trap

This is the single most pervasive failure mode in interpretability research.

> "There's an epistemic challenge in this field: it's tempting (and easy) to cherry-pick interpretability findings that look good, while ignoring those that don't fit a neat story."

**Protection strategies:**
- Pre-register your analysis plan before looking at results (the proposal IS your pre-registration)
- Report the denominator: "We found interpretable circuits for 2 of 7 traits tested"
- Always report failure cases alongside successes
- Use held-out validation prompts you've never looked at until final evaluation
- Have someone else pick the examples for your figures

### 1.3 Confirmation Bias in Circuit Discovery

When you're looking for a circuit that does X, you'll find patterns that look like X even in random networks.

> "A 2020 paper found that saliency maps barely changed when different layers were set to random values — suggesting the maps don't capture what the model learned."

**Protection strategies:**
- Always run sanity checks against randomized baselines
- Test whether your "discovered" pattern exists in an untrained model
- Check if the pattern persists when you change the input distribution
- Use multiple independent analysis methods and check convergence

---

## 2. Steering Vector and Persona Vector Gotchas

### 2.1 Steering Coefficient Sensitivity

> "Remember to try a bunch of coefficients for the vector when adding it. This is a crucial hyper-parameter and steered model behaviour varies a lot depending on its value."

**What to do:**
- Always sweep α ∈ {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0}
- Plot the dose-response curve — it should be monotonic in the working range
- Watch for phase transitions (sudden jumps in behavior)
- If effect is only present at very high α, the vector may be weak or wrong
- Log the coefficient with every result

### 2.2 Layer Selection Is Non-Obvious

Different layers have qualitatively different effects:
- Too early: effect is weak or diffuse
- Optimal: strong, targeted effect
- Too late: may break coherence or have diminishing returns

**What to do:**
- Always sweep layers, not just the one reported in prior work
- Prior work used different models — optimal layer may differ for Llama 3.1 8B
- Plot effect magnitude × output coherence as a function of layer
- The "best" layer for steering may differ from the best layer for circuit analysis

### 2.3 Extraction Method Sensitivity

The same "concept" extracted via different methods gives different vectors.

> "Steering vectors are fundamentally non-identifiable due to large equivalence classes of behaviorally indistinguishable interventions." (Venkatesh et al. 2026)

**What to do:**
- Extract using multiple methods (mean difference, PCA, probing)
- Check cosine similarity between vectors from different methods
- If similarity is low (<0.7), your "concept" may not be well-defined
- Report which method you used and why

### 2.4 Prompt Set Contamination

Your extraction prompts and test prompts MUST be disjoint.

**What to do:**
- Split prompts: 70% extraction, 15% validation, 15% held-out test
- Never look at held-out test results until final evaluation
- If you iterate on extraction prompts after seeing results, you're overfitting
- Log which prompts were used for which purpose

### 2.5 The "Last Token" Assumption

Most work extracts at the last prompt token, but this isn't always optimal.

**What to do:**
- Try extraction at: last token, mean over all tokens, mean over last N tokens
- For some concepts, specific token positions matter (e.g., the subject's name)
- Document your choice and test sensitivity

---

## 3. SAE Decomposition Gotchas

### 3.1 Reconstruction Error Matters

> "Large errors in SAE reconstruction raise the question whether SDL methods can reconstruct the hidden representation sufficiently well such that the latents learned are adequately faithful."

**What to do:**
- Always report reconstruction loss (MSE, explained variance)
- Check that SAE reconstruction doesn't break the model's behavior
- Run: original activations → SAE encode → SAE decode → continue forward pass
- If final output differs significantly, SAE is losing important information
- Kantamneni et al. showed SAEs can miss safety-relevant features — this is a known limitation

### 3.2 Feature Splitting and Absorption

> "Because SAEs optimize for sparsity, a parent feature is often absorbed into a more specific child feature latent to save on the L1 penalty, resulting in seemingly monosemantic features that actually have significant false negative rates."

**What to do:**
- Don't assume a feature labeled "X" catches all instances of X
- Check false negative rate: how often does concept X occur without feature activating?
- Look for multiple features that might jointly capture a concept
- "Feature 42 = sycophancy" is probably "Feature 42 = one subtype of sycophancy"

### 3.3 Polysemanticity Persists

Even in SAE features, polysemanticity is common.

> "The same neuron responded most strongly to different kinds of sentences on a different dataset. Researchers claim to have discovered the singular role of a neuron or circuit, but eventually people find various exceptions."

**What to do:**
- Test feature activation on diverse inputs, not just your target domain
- Look for "dark" activations — when does the feature fire unexpectedly?
- A feature that fires on "French cities" may also fire on "European capitals"
- Report the top-10 max-activating examples AND a random sample of activations

### 3.4 Auto-Interpretation Hallucination

LLM-generated feature interpretations are often wrong or too narrow.

**What to do:**
- Treat auto-interpretations as hypotheses, not facts
- Validate interpretations with held-out stimuli
- Try adversarial examples that should / shouldn't activate the feature
- Human spot-check at least the top-20 features you rely on for claims

### 3.5 Different SAEs Give Different Features

**What to do:**
- Run your analysis with at least two SAE sources (Llama Scope + andyrdt)
- Check whether the same "concept" decomposes into similar features
- If decomposition differs dramatically, your findings may be SAE-specific artifacts
- This is especially important for novel claims — cross-SAE agreement = stronger evidence

---

## 4. Ablation Study Gotchas

### 4.1 Ablation Method Choice Matters Enormously

> "Standard ablation (mean/zero ablation) overestimates component importance by approximately 9×. This is due to 'spoofing': the ablated value actively misleads downstream computation." (Li & Janson 2024)

**This is critical. Most published ablation results are inflated by this amount.**

**What to do:**
- **Primary:** Resample ablation (activation patching from a different input)
- **Secondary:** Mean ablation (for comparison and fast iteration)
- **Tertiary:** Zero ablation (for completeness)
- Report all three methods for every causal claim
- If methods disagree by >2×, investigate why

### 4.2 Ablation Can Break the Model

Ablating too many components at once produces incoherent outputs, making sufficiency testing meaningless.

**What to do:**
- Always check output coherence after ablation (perplexity, human inspection)
- If output is garbage, you can't conclude anything about the circuit
- Use graded ablation: ablate 10%, 20%, 30%... and track both effect and coherence
- Consider "scaffold" approaches (keep minimal language backbone)

### 4.3 Random Baseline Is Essential

An ablation that reduces effect by 50% sounds impressive until you learn random same-size ablations reduce it by 40%.

**What to do:**
- Always run 100+ random ablations of the same size as your circuit
- Your circuit must be in the top 1% to claim significance at p<0.01
- Report the full distribution, not just your circuit's result

### 4.4 Order Effects in Sequential Ablation

If you ablate features one-by-one to build a circuit, the order matters.

**What to do:**
- Try multiple orderings (by importance, random, reverse)
- Check if the final circuit is stable across orderings
- Greedy selection ≠ optimal selection
- Consider joint ablation of feature sets, not just sequential

---

## 5. Circuit Analysis Gotchas

### 5.1 Circuits Are Prompt-Specific

> "When they altered the task slightly, the importance of those neurons dropped, implying the discovered circuit was not the whole story."

**What to do:**
- Always validate circuits on held-out prompts
- Report cross-prompt stability (Jaccard overlap)
- If Jaccard < 0.3, your "circuit" may be prompt-specific noise
- Test on prompts from different distributions (formal vs. casual, different phrasings)

### 5.2 The Interpretability Illusion

> "Researchers described looking for sentences that maximally activated a single target neuron and initially found a compelling pattern. But when presented with a different dataset, the pattern vanished."

**What to do:**
- Test your circuit on data from a different distribution
- If circuit only works on your specific prompt format, it's fragile
- Ask: would this circuit explanation satisfy a skeptic?

### 5.3 Circuits Require Compute Budgets

**What to do:**
- Scope your circuit search to specific layers/components
- Use fast gradient-based methods for exploration, slow patching for validation
- Set a compute budget before starting — don't go down infinite rabbit holes
- Document your search procedure so others can replicate

### 5.4 Attention ≠ Importance

High attention weights don't mean a head is important for the computation.

**What to do:**
- Don't interpret attention patterns as causal importance
- Validate attention-based hypotheses with ablation
- A head can have interpretable attention patterns but minimal causal effect
- Conversely, a head with diffuse attention can be critical

---

## 6. Probing Gotchas

### 6.1 Probes Detect Correlation, Not Causation

> "A probe's success doesn't guarantee the model uses that feature — it might just be latent. Overly complex probes can even 'teach themselves' features the model didn't explicitly encode."

**What to do:**
- Use linear probes only (consistent with the linear representation hypothesis)
- High probe accuracy ≠ the model uses this information
- Follow up with causal interventions (activation patching)
- If you can't causally validate, be explicit: "The model encodes X (probing evidence), but we don't know if it uses X"

### 6.2 Probe Training Data Leakage

**What to do:**
- Strict train/test splits for probes
- Probe trained on extraction prompts, tested on held-out prompts
- Report probe accuracy on truly out-of-distribution data

---

## 7. Statistical and Reporting Gotchas

### 7.1 Report Effect Sizes, Not Just P-Values

p < 0.001 with a tiny effect size is not meaningful.

**What to do:**
- Always report Cohen's d or Vargha-Delaney A₁₂
- A₁₂ > 0.71 = large effect (our threshold)
- Small effects may be statistically significant but practically meaningless
- Confidence intervals via bootstrap (n=1000)

### 7.2 Multiple Comparisons

If you test 100 features, 5 will be "significant" at p<0.05 by chance.

**What to do:**
- Bonferroni correction for feature-level tests
- FDR correction if Bonferroni is too conservative
- Report how many tests you ran, not just the ones that worked
- Pre-register your analysis plan to limit fishing (the proposal IS your pre-registration)

### 7.3 Log Everything

You will forget what you tried. Future you will hate past you.

**What to do:**
- Log every hyperparameter, random seed, and config
- Log negative results and failed experiments
- Log the exact prompts used (or hash of prompt file)
- Log intermediate artifacts (vectors, feature lists, attribution maps)
- Use W&B — not just local files

### 7.4 Versioning Artifacts

Your persona vector from Tuesday is different from your persona vector from Thursday.

**What to do:**
- SHA256 hash every artifact at time of creation; store hash in RESULTS_INDEX.md
- Version your prompts, vectors, and circuits (v1_, v2_ prefixes)
- When you report results, reference specific artifact versions
- Keep a changelog of methodology changes in DECISIONS.md

---

## 8. Deeper Insights: What to Look For

### 8.1 Phase Transitions

Sudden jumps in behavior during sweeps often indicate mechanistically interesting boundaries.

**What to log:**
- Non-monotonic relationships (effect increases then decreases)
- Sharp transitions (flat → steep → flat in α sweep)
- Points where qualitative behavior changes (helpful → harmful)

These are often the most scientifically interesting findings — log them in THOUGHT_LOG.md.

### 8.2 Failure Mode Taxonomy

When things don't work, categorize why before changing anything:

| Failure Type | Symptom | What It Means |
|---|---|---|
| Weak effect | Steering produces <10% behavior change at all α | Vector doesn't capture the concept well |
| Fragile effect | Works on some prompts, not others | Concept is prompt-specific or vector is noisy |
| Coherence collapse | High α produces gibberish | Steering is too strong; need smaller α |
| Inverse effect | Steering produces opposite of expected | Vector may be inverted; check extraction sign |
| Diffuse circuit | No small feature set captures >50% of effect | Computation may be genuinely distributed (valid finding) |
| Unstable circuit | Different prompts give different circuits | Circuit is not a robust property of the model |

Log which failure mode you hit. This is valuable data — record in SCRATCHPAD and THOUGHT_LOG.

### 8.3 Cross-Model Consistency

If your finding only holds in one model, it may be an artifact.

**What to log:**
- Same analysis on Llama vs. Gemma (Week 6 is specifically for this)
- Same analysis on base vs. instruct
- Same analysis on different model sizes (if compute permits)

Findings that replicate across models are more likely to be real. Findings that don't are still interesting — investigate why.

### 8.4 Unexpected Activations

When a feature fires unexpectedly, investigate rather than dismiss.

Example: Your "sycophancy" feature also fires on apologies. This isn't noise — it may reveal that the model represents sycophancy and apologies in the same subspace. **This is a finding.** Log it in THOUGHT_LOG.md.

### 8.5 Look for What's Missing

> "Any interpretation that fails to explain or anticipate edge cases is not only less useful for understanding how the model functions, but also less useful for safety."

**What to log:**
- Cases where your circuit predicts behavior X but model does Y
- Edge cases that don't fit your explanation
- The "long tail" of behaviors your circuit doesn't cover

---

## 9. Practical Workflow Advice

### 9.1 Start Small

Before the full experiment, run a 2-day pilot on 1 trait, 10 prompts.
- Validate your infrastructure works end-to-end
- Catch bugs before they corrupt 100 hours of compute
- This is what Week 1 is for — don't skip it

### 9.2 Fast Iteration → Slow Validation

Use cheap methods for exploration, expensive methods for validation.

| Phase | Method | Speed | Use For |
|---|---|---|---|
| Exploration | Gradient-based attribution | Fast | Identifying candidate features |
| Exploration | Mean ablation | Medium | Quick importance estimates |
| Validation | Resample ablation | Slow | Final causal claims |
| Validation | Cross-method comparison | Slow | Robustness checks |

Don't run expensive validation until you're confident in your direction.

### 9.3 Write As You Go

**What to do:**
- Draft your results section before you have results
- Write: "If we find X, we will conclude Y. If we find Z, we will conclude W."
- This forces clarity on what you're actually testing
- Update the draft as results come in (this is what CURRENT_STATE.md hypothesis fields are for)

### 9.4 Know When to Stop

Interpretability research can be infinite. Set boundaries.
- Define "done" criteria before starting each phase (the proposal's §10.2 does this)
- Set compute budgets and time limits
- "Good enough" is publishable; "perfect" is never finished
- If you've been stuck for a week, step back and reconsider the approach — trigger BLOCKED Protocol

---

## 10. Red Flags to Watch For

### 10.1 Red Flags in Your Own Work

| Red Flag | What It Suggests |
|---|---|
| Results only work with very specific prompts | Overfitting to prompt format |
| You can't explain why your method works | You may not understand what you're measuring |
| Effect sizes are much larger than prior work | Check for bugs or inflated estimates |
| Results change significantly with random seeds | Noise is dominating signal |
| You've been iterating on the same analysis for weeks | You're fishing; step back |
| Your "circuit" is >20% of the model | It's not a circuit; it's the whole model |

### 10.2 Red Flags in Others' Work (for related-work section)

| Red Flag | What It Suggests |
|---|---|
| Only reports successes, no failures | Cherry-picking |
| No random baseline comparison | May be measuring noise |
| Only one ablation method | May be overestimating importance |
| Claims based on small number of examples | May not generalize |
| No cross-prompt stability analysis | May be prompt-specific |
| "Interpretable" features with no validation | May be pareidolia |

---

## 11. Logging Checklist

For every experiment run, verify you have logged:

### 11.1 Configuration
- [ ] Model name and exact checkpoint
- [ ] SAE source and checkpoint
- [ ] Layer(s) analyzed
- [ ] Random seed
- [ ] All hyperparameters
- [ ] Git commit hash

### 11.2 Inputs
- [ ] Exact prompts used (or SHA256 hash of prompt file)
- [ ] Prompt set split (extraction/validation/test)
- [ ] System prompts if used
- [ ] Token counts

### 11.3 Intermediate Artifacts
- [ ] Persona vectors (with hash)
- [ ] Feature lists (with importance scores)
- [ ] Attribution maps
- [ ] Candidate circuits

### 11.4 Results
- [ ] Primary metrics with confidence intervals
- [ ] Effect sizes (Cohen's d, A₁₂)
- [ ] P-values with correction method noted
- [ ] All three ablation methods compared
- [ ] Random baseline distribution

### 11.5 Diagnostics
- [ ] Reconstruction loss (SAE)
- [ ] Output coherence (perplexity)
- [ ] Cross-prompt stability (Jaccard)
- [ ] Cross-method agreement
- [ ] Failure modes encountered

### 11.6 Meta
- [ ] Experiment duration
- [ ] Compute used (GPU-hours)
- [ ] Any methodology changes from plan (must also be in DECISIONS.md)
- [ ] Notes on unexpected findings (must also be in THOUGHT_LOG.md)

---

## 12. Sanity Checks (Run Before Trusting Any Result)

### 12.1 Randomization Checks
- [ ] Does the effect disappear with a random vector of same norm?
- [ ] Does the "circuit" exist in an untrained model?
- [ ] Is your circuit better than random same-size ablation?

### 12.2 Generalization Checks
- [ ] Does the effect hold on held-out prompts?
- [ ] Does the effect hold on prompts from a different distribution?
- [ ] Does the circuit transfer to a different model?

### 12.3 Robustness Checks
- [ ] Do different SAEs give similar decomposition?
- [ ] Do different ablation methods agree within 2×?
- [ ] Is the circuit stable across random seeds?

### 12.4 Coherence Checks
- [ ] Does the model still produce coherent output after ablation?
- [ ] Does the feature interpretation make sense to a human?
- [ ] Can you predict what the circuit will do on a new prompt?

---

## Quick Reference: Top 10 Gotchas

1. **Steering coefficients matter a lot** — always sweep α; never report a single value
2. **Ablation methods inflate importance by ~9×** — use resample ablation as primary (Li & Janson 2024)
3. **Cherry-picking is pervasive** — pre-register and report failures alongside successes
4. **SAE features aren't monosemantic** — check for polysemy, feature splitting, false negatives
5. **Circuits are prompt-specific** — validate on held-out prompts; Jaccard < 0.3 = noise
6. **Probing ≠ causation** — always follow up with causal interventions
7. **Random baselines are essential** — always compare to 100+ random same-size ablations
8. **Different SAEs give different features** — cross-check Llama Scope vs. andyrdt
9. **Auto-interpretations hallucinate** — validate feature labels with held-out stimuli
10. **Log everything** — you will forget what you tried; W&B is the authoritative record
