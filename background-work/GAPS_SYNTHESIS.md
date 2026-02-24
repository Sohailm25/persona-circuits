# Consolidated Gaps Synthesis: Steering Experiments for Mechanistic PSM Grounding

**Date:** 2026-02-24
**Sources evaluated:** Claude (anthropic.md), ChatGPT (chatgpt.md), Gemini (gemini.md), PSM weakness analysis (psm-analysis.md)
**Parent document:** RESEARCH_POSITIONING.md

---

## 0. Source Reliability Assessment

Before synthesizing, each source must be evaluated for reliability. The three AI model outputs disagree on several key points, and some claims are verifiably wrong.

### Claude (anthropic.md) — MOST RELIABLE

**Strengths:** Most structured and actionable. Honest about the CLT bottleneck. Well-sourced claims. Practical fallback methodology. References Li & Janson (2024) ablation spoofing warning, which the other sources miss. PSM awareness confirmed — directly references paper content, date, and future directions.

**Concerns:** Claims GemmaScope has instruction-tuned SAEs at `gemma-scope-9b-it-res` — plausible but needs verification before committing. Claims circuit-tracer supports Qwen-3 (0.6B–14B) — needs verification. The 7–8 week timeline is aggressive for one researcher. The Gemma 3 12B + GemmaScope 2 "upgrade path" with transcoders/CLTs is cited but unverified.

**Overall:** Conservative, honest about limitations, well-organized. Trust level: HIGH.

### ChatGPT (chatgpt.md) — MOST EPISTEMICALLY HONEST

**Strengths:** The most transparent about what it could and couldn't verify. Every claim has a linked citation. Explicitly states it could NOT retrieve the full PSM blog post — only the summary page — and designs around that limitation. Practical about compute: recommends candidate-restricted graphs, not full dense graphs. Provides specific CLT training costs (210 H100-hours for Gemma-2-2B, 3844 H100-hours for Gemma-2-9B) from Anthropic's methods page.

**Concerns:** PSM claims are necessarily limited to what's on the summary page. Doesn't discuss the router hypothesis, Assistant Axis, or exhaustiveness spectrum from PSM in depth (because it couldn't access those sections). MVC scope of 10 prompts/trait is thin for statistical power. Missing the Li & Janson ablation spoofing warning.

**Overall:** Grounded, cautious, well-cited. Where it says something is true, it probably is. Trust level: HIGH (but limited depth on PSM).

### Gemini (gemini.md) — LEAST RELIABLE, USE WITH CAUTION

**Strengths:** Extremely detailed mathematical formulation. Bidirectional causal validation design is genuinely novel and strong. Vargha-Delaney A₁₂ effect size metric is a good choice for non-normal distributions. 200 held-out prompts provides better statistical power. The PSM Claims Validation Matrix is well-structured.

**CRITICAL CONCERNS — claims that are LIKELY WRONG:**

1. **"The circuit-tracer library...natively supports the generation of attribution graphs for the Llama architecture out-of-the-box."** This is misleading to the point of being dangerous. The circuit-tracer library requires pre-trained cross-layer transcoders (CLTs). **No pre-trained CLTs exist for Llama 3.1 8B.** The library supports Gemma-2-2B, Llama-3.2-1B, and Qwen-3 (0.6B–14B, per Claude's claim) with pre-trained transcoders. You cannot just "boot" circuit-tracer on Llama 8B and generate attribution graphs.

2. **"Initialize the Cross-Layer Transcoder (CLT) replacement model"** — written as a routine step in the protocol, as if CLTs for Llama 8B are available. They are not. This is the single biggest infrastructure gap identified by Claude and ChatGPT, and Gemini treats it as a non-issue.

3. **"Generating 60 attribution graphs will consume less than one hour of active time on a single A100 GPU."** — Only true if CLTs exist and the full pipeline works. Since CLTs don't exist for 8B, this estimate is fiction.

4. **α = 2.5 steering coefficient** — presented as an "empirically optimized" value when it is actually a hyperparameter that must be determined experimentally for each model/trait combination.

5. **Pruning threshold of 0.90** — cited as the standard, but Anthropic's documented default is 0.95 (which Gemini contradicts elsewhere in the same document).

6. **Over-confident language throughout:** "decisively," "undisputed," "absolute," "perfectly," "profoundly," "permanently," "catastrophic." This rhetoric masks real uncertainty.

**Overall:** Contains valuable methodological ideas (bidirectional validation, A₁₂ metric, resample ablation emphasis) embedded in a document that conflates assumptions with facts and ignores the central infrastructure bottleneck. Trust level: MEDIUM for methodology, LOW for infrastructure claims.

### PSM Analysis (psm-analysis.md) — RELIABLE AS CRITICAL COMMENTARY

Well-structured critical reading of the PSM paper. The 16 weakness categories are accurate based on our independent reading of the paper. Key insight for experimental design: PSM is "more of a useful heuristic than a validated theory" — this shapes how we frame our contribution. We're not merely validating PSM; we're testing specific, falsifiable derivatives of it.

---

## 1. Model + SAE Selection: RESOLVED

### The disagreement

| Source | Primary Recommendation | Rationale |
|--------|----------------------|-----------|
| Claude | Gemma 2 9B + GemmaScope 1 | Most comprehensive SAE infrastructure (400+ SAEs, 16K–1M features) |
| ChatGPT | Llama 3.1 8B + Llama Scope 128K | Full layer coverage, generalization to instruct verified, clear metrics |
| Gemini | Llama 3.1 8B + andyrdt BatchTopK SAEs | Direct instruction-tuned SAEs, validated for refusal/steering |

### Resolution: Llama 3.1 8B-Instruct (primary) + Gemma-2-2B (proof-of-concept)

**Llama 3.1 8B-Instruct wins as primary** for these reasons:
- **Published baseline exists:** Chen et al. persona vectors paper used Llama-3.1-8B-Instruct (per Claude) or at minimum a comparable architecture, giving us direct comparability
- **SAE depth:** Llama Scope provides 256 SAEs across all 32 layers × multiple sublayer hookpoints (residual stream, MLP, attention) at 32K and 128K widths
- **Instruct generalization verified:** Llama Scope SAEs are trained on base but explicitly evaluated on instruct model with "no significant degradation" per ChatGPT's verified citation
- **Cross-validation available:** andyrdt provides instruct-trained SAEs at layers 19/23 (BatchTopK, 131K features) for robustness checking
- **Community validation:** More downstream persona/steering work exists for Llama than Gemma

**Gemma-2-2B as proof-of-concept** because:
- Pre-trained CLTs exist for Gemma-2-2B in the circuit-tracer library
- This enables the full Anthropic-style attribution graph pipeline as validation
- Demonstrates the full methodology works before applying the hybrid fallback on 8B
- Claude's suggestion of a "dual-scale approach" is methodologically strong

**SAE configuration:**
- Primary: Llama Scope 128K residual stream SAEs at layers 12–24 (middle-to-late depth)
- Cross-check: andyrdt instruct-trained SAEs at layers 19 and 23
- Proof-of-concept: GemmaScope SAEs for Gemma-2-2B (for CLT pipeline validation)

**What about Gemma 2 9B?** Claude makes a strong case for GemmaScope's depth (400+ SAEs, up to 1M features). This remains the upgrade path if: (a) results on Llama 8B warrant scaling to a second architecture, or (b) GemmaScope 2 transcoders become available for Gemma 3, enabling full CLT pipeline at 9B+ scale. But for the MVC, one primary model is sufficient.

**What about Qwen?** Chen et al. also used Qwen for persona vectors, but comprehensive public SAEs for Qwen are less established. The andyrdt Qwen SAEs exist but are less validated. Not recommended for MVC; reserve for replication study.

---

## 2. Attribution Methodology: RESOLVED

### The disagreement

This is where the sources diverge most dangerously.

| Source | Approach | CLT Bottleneck Acknowledged? |
|--------|----------|------------------------------|
| Claude | 4-step hybrid (direct → gradient → targeted patching → head analysis) | YES — explicitly identifies as "critical bottleneck" |
| ChatGPT | Candidate-restricted (cosine → patch candidates → build graph on reduced set) | YES — cites exact CLT training costs |
| Gemini | Full CLT-based attribution as if CLTs exist | **NO — treats CLTs as available for Llama 8B** |

### Resolution: Hybrid approach with Gemma-2-2B validation

**Gemini's methodology is not executable as written.** Its protocol assumes CLTs exist for Llama 8B. They do not. The entire attribution graph generation section of Gemini's document must be treated as aspirational, not actionable.

**The feasible methodology combines Claude's and ChatGPT's approaches:**

**Step 1 — Direct feature attribution (minutes, single GPU)**
Project each persona vector onto SAE decoder directions at each layer. Compute cosine similarity between steering vector and every SAE feature's decoder direction. This identifies geometrically aligned features — "what the steering vector IS in feature space."

**Step 2 — Differential activation analysis (minutes)**
Run model with and without steering on evaluation prompts. Compute Δ-attribution per ChatGPT: for each SAE feature i at token t, δ_{i,t} ≈ −(g_t · d_i)((a_t − ā) · d_i). Select top features by both cosine alignment (Step 1) AND activation change (Step 2).

**Step 3 — Gradient-based attribution patching (hours)**
For top-N candidate features from Steps 1–2, compute gradient of output logits w.r.t. SAE features with and without steering. This is first-order Taylor approximation of activation patching — a fast exploratory step.

**Step 4 — Targeted activation patching / resample ablation (hours)**
For top-50 features from Step 3, perform actual activation patching: swap individual feature activations between steered/unsteered runs. Measure necessity and sufficiency for behavioral change. Use resample ablation (swap with activation from neutral prompt) as gold standard.

**Step 5 — Attention head survey (hours)**
Ablate attention heads one at a time. Measure effect on steering-induced behavior change. Identifies heads that mediate persona routing at coarser granularity.

**Step 6 — Full CLT pipeline on Gemma-2-2B (validation)**
Use circuit-tracer with existing CLTs to generate full attribution graphs for 5–10 prompts per trait on Gemma-2-2B. Compare steered vs. unsteered graphs. This validates the hybrid approach: if the hybrid method on 8B identifies the same functional circuit structure as the full CLT method on 2B (modular vs. diffuse, similar feature categories), the hybrid results are credible.

**Compute estimate:**
- Steps 1–5 on Llama 8B: 2–5 GPU-hours on single A100 80GB (~1 day)
- Step 6 on Gemma-2-2B: 1–3 GPU-hours on single A100 80GB
- Total: ~1 week including prompt engineering, debugging, and analysis

---

## 3. Circuit Operationalization: RESOLVED

### The disagreement

| Criterion | Claude | ChatGPT | Gemini |
|-----------|--------|---------|--------|
| Faithfulness threshold | >80% | ≥70% | 80% |
| Sparsity threshold | <10% components | top 5% → ≥50% effect | ≤5% features |
| Random baseline | p < 0.01, 100+ baselines | Size-matched + layer-matched controls | Not specified quantitatively |
| Stability across prompts | Not explicitly defined | Jaccard ≥0.30 | Not specified |
| Additional metrics | — | Gini coefficient, entropy | — |

### Resolution: Claude's 5-criterion framework + ChatGPT's stability and concentration metrics

**Definition of "coherent persona circuit"** — all five must hold simultaneously:

1. **Faithful:** Running only the circuit recovers >80% of the full model's trait metric (normalized faithfulness >0.8)
2. **Minimal:** Removing any single component reduces faithfulness significantly (p < 0.05 via permutation test)
3. **Sparse:** Circuit contains <10% of model components in the analyzed layer range
4. **Specific:** Ablating the circuit does not degrade unrelated tasks (factual recall, math, coding) by >10%
5. **Superior to random:** Circuit's ablation effect exceeds 100 random same-size subsets at p < 0.01

**Supplementary metrics to report (from ChatGPT):**
- **Stability:** Top-K feature overlap (Jaccard index) ≥0.30 across prompt families
- **Concentration:** Gini coefficient over node contributions (high = modular); entropy of normalized contributions (low = modular); top-p mass (fraction of effect captured by top p% nodes)

**Modular vs. diffuse classification:**
- **Modular:** Top-10 components account for >50% of total causal effect; all 5 criteria met; Gini > 0.5
- **Diffuse:** No circuit of <10% components achieves >60% faithfulness; effect scales linearly with component count; Gini < 0.3
- **Mixed:** Between the above — report the spectrum, not a binary

**Why ChatGPT's ≥70% completeness threshold is too low:** At 70%, almost a third of the effect is unexplained. For claiming "persona vector X operates through circuit Y," we need stronger evidence. If we can only achieve 70%, we should honestly report that the mechanism is partially diffuse rather than lower the bar.

**Why Gemini's ≤5% sparsity threshold is unnecessarily strict:** Published circuits range from 0.2% (ACDC) to 18% (IOI heads). Requiring ≤5% may cause us to reject genuinely modular circuits. The <10% threshold is well within the observed range.

---

## 4. Causal Ablation Design: RESOLVED

### The disagreement

| Dimension | Claude | ChatGPT | Gemini |
|-----------|--------|---------|--------|
| Primary ablation method | Mean ablation | Resample patching preferred | Resample ablation |
| Validation method | Activation patching | Bootstrap CIs | Bidirectional protocol |
| Effect size metric | Cohen's d | Δscore, % mediation | Vargha-Delaney A₁₂ > 0.80 |
| Prompt count | 100+ (200 preferred) | 10 (MVC), expand to 50–200 | 200 |
| Correction | Bonferroni | Paired bootstrap | Not specified |

### Resolution: Multi-method with bidirectional validation

**Primary ablation protocol — 4 tests in sequence:**

1. **Necessity (forward):** Ablate circuit, apply steering. If circuit mediates steering, behavioral shift diminishes by >50% vs. full-model steering.
2. **Sufficiency:** Ablate everything EXCEPT circuit, apply steering. If circuit is sufficient, >60% of effect maintained.
3. **Specificity:** Ablate circuit WITHOUT steering. Test on unrelated tasks. <10% degradation = persona-specific circuit.
4. **Selectivity (random baseline):** Ablate 100+ random same-size sets with steering. Real circuit's effect must be in top 1% of distribution.

**Bidirectional validation (adapted from Gemini — this is genuinely valuable):**

- **Forward test (Steer → Ablate):** Inject persona vector, generate steered attribution, ablate identified circuit nodes. Behavior should revert to baseline.
- **Reverse test (Ablate persona direction → Measure circuit):** Present trait-eliciting prompts without explicit steering. Apply directional ablation to remove persona vector component from residual stream. If circuit activation collapses, the persona vector IS the upstream cause.

This bidirectional design is Gemini's best contribution and should be adopted.

**Ablation methods (ordered by preference):**
1. **Activation patching / resample ablation** (gold standard) — swap activations from neutral/contrasting prompt. Stays on-manifold.
2. **Mean ablation** (fast iteration) — replace with dataset mean. Use for development and rapid iteration.
3. **Zero ablation** — avoid as primary. Li & Janson (2024) showed standard ablation overestimates importance by ~9× due to "spoofing." Only use as a third comparison point.

**Always report results from at least TWO ablation methods.** If mean and resample ablation give qualitatively different results, the circuit claim is weakened.

**Statistical plan:**
- **Minimum prompts:** 100 per trait (this is the floor for adequate power)
- **Preferred:** 200 per trait if compute permits
- **Effect sizes:** Report BOTH Cohen's d (widely understood, comparable to literature) AND Vargha-Delaney A₁₂ (non-parametric, robust to non-normality). Require A₁₂ > 0.71 (large effect) for primary claims.
- **Confidence intervals:** Bootstrapped 95% CIs with ≥1,000 resamples
- **Multiple comparisons:** Bonferroni correction when testing multiple circuits/traits
- **Additional controls:**
  - Dose-response curve: ablate 25%, 50%, 75%, 100% of circuit, verify roughly monotonic degradation
  - General perplexity baseline: confirm model still functions after ablation
  - Ablation method sensitivity: mean vs. resample agreement

**Why A₁₂ > 0.80 (Gemini's threshold) is too strict for MVC:** 0.80 is extremely large — it means the steered condition dominates in 80% of pairwise comparisons. For an MVC, A₁₂ > 0.71 (standard "large" effect) is defensible. Reserve 0.80 for strong claims.

---

## 5. PSM Claims to Test: PRIORITIZED

### PSM ingestion verification

| Source | Had access to full PSM paper? | Evidence |
|--------|-------------------------------|----------|
| Claude | YES | References exhaustiveness spectrum, router hypothesis, Assistant Axis, 5 future work items |
| ChatGPT | PARTIAL | Explicitly states could not access full blog post; only summary page |
| Gemini | YES | References router hypothesis, exhaustiveness, emergent misalignment connection in detail |

ChatGPT's honesty is notable — it explicitly designs around its limitation rather than filling in gaps with assumptions.

### Consolidated PSM claims matrix (5 for MVC, 3 additional for full version)

**MVC CLAIMS (prioritized by tractability × impact):**

| # | Claim | Test | Confirmation | Disconfirmation | Priority |
|---|-------|------|-------------|-----------------|----------|
| 1 | **Persona vectors correspond to sparse, causal SAE features** | Decompose persona vector into SAE features; ablate top features; measure behavioral mediation | Small set (<50 features) mediates >60% of steering effect | Effect requires thousands of features with no concentration | **HIGHEST** — easiest to execute, foundational for all subsequent claims |
| 2 | **Trait inference mediates generalization** — narrow misaligned fine-tuning activates general persona features, not task-specific features | Ablate persona trait features in emergently misaligned model; check if cross-domain misalignment disappears while narrow task behavior persists | Ablating "malicious persona" features eliminates cross-domain but not narrow-task behavior | Shifted features are task-specific; ablation doesn't affect generalization | **HIGH** — directly tests PSM's core thesis, connects to Wang et al. emergent misalignment |
| 3 | **System prompts activate identifiable persona routing** | Attribution graphs across 10+ persona system prompts; identify shared routing circuitry | Consistent routing circuit: early-layer heads read persona cues, gate downstream feature clusters | Each persona uses entirely different circuits with no shared mechanism | **HIGH** — tests the router hypothesis |
| 4 | **Post-training operates within pre-existing persona space** | Compare persona feature space in base vs. post-trained model (Llama 3.1 8B base vs. instruct) | Post-training shifts project mostly onto pre-existing persona feature directions; high SAE feature overlap | Post-training creates fundamentally new features not reducible to pre-existing directions | **HIGH** — directly testable with base + instruct checkpoints |
| 5 | **Exhaustiveness: behavior flows through persona circuits** | Ablate ALL persona-relevant features; measure remaining behavior | Ablation produces incoherent/random output → operating system view | Coherent, goal-directed output persists → shoggoth view | **MEDIUM-HIGH** — philosophically important, harder to execute cleanly |

**EXTENDED CLAIMS (for full version):**

| # | Claim | Priority |
|---|-------|----------|
| 6 | Persona drift during conversation is circuit-localizable (Lu et al. emotional conversation finding) | MEDIUM-HIGH |
| 7 | Toxic persona features share routing circuits with benign personas (Wang et al. overlap) | MEDIUM-HIGH |
| 8 | Persona space geometry mirrors human personality structure (Big Five correlations) | MEDIUM |

### Critical note from psm-analysis.md

PSM is an unfalsifiable theory risk. Every counterexample can be attributed to "simulation failure." Our experiments should be designed to produce genuinely falsifying evidence where possible:

- **If circuits are diffuse (not modular):** This weakens PSM's "character" framing — behavior isn't flowing through a coherent persona mechanism
- **If base and instruct share NO features:** This weakens "post-training selects within persona space"
- **If exhaustiveness ablation reveals coherent non-persona behavior:** This supports the "shoggoth" view, directly contradicting PSM's strongest reading
- **If no router exists:** This weakens PSM's implicit selection mechanism

Pre-register these as legitimate disconfirmation criteria. A paper that honestly reports "PSM claim X was not supported by our mechanistic analysis" is more valuable than one that cherry-picks confirmatory results.

---

## 6. Adversarial Robustness: SCOPE DEFINED

### What all three sources agree on

- Bailey et al. (ICLR 2026) decisively breaks representation-level defenses (probes, SAEs, OOD detectors)
- Circuit-level defenses are UNTESTED against adversarial attack
- The "obfuscation tax" suggests complex functional monitoring inherits some robustness
- We CANNOT claim monitoring robustness without dedicated adversarial testing

### What this means for the MVC

**IN SCOPE for MVC:** Descriptive findings about persona circuit structure. Claiming circuits provide a "candidate monitoring signal." Observing whether circuits are preserved under standard (non-adversarial) distribution shifts.

**OUT OF SCOPE for MVC:** Any claim about adversarial robustness. Any claim about monitoring viability against a motivated adversary.

**PHASE 3 (if pursuing full version):**
- Apply Bailey-style suffix attacks, measure whether circuit structure is preserved
- Fine-tune with circuit-targeted obfuscation loss, measure obfuscation tax
- Compare single-layer probes vs. full attribution analysis under identical attacks
- Gemini's hypothesis about circuit monitoring being "a substantially higher floor of defensive robustness than superficial representation probing" is testable but requires the dedicated adversarial protocol

---

## 7. Competition Assessment: UPDATED

### All three sources agree

- Anthropic is the primary threat (overlapping teams, proprietary access, explicit roadmap via PSM)
- The window is approximately 3–6 months before Anthropic's empirical PSM follow-up
- OpenAI, Google DeepMind, MATS, Apollo are lower risk but non-negligible
- Focusing on open-weight models differentiates from Anthropic's proprietary Claude work

### Key strategic point from ChatGPT (well-grounded)

ChatGPT correctly notes that "persona vectors + SAE decomposition" is ALREADY established (Chen et al. explicitly does this). Our novelty is not "combining persona vectors with SAEs" — it's the **causal circuit tracing and validation**. The differentiation must be:
1. Causal mediation analysis (not just feature enumeration)
2. PSM-specific hypothesis testing (not just descriptive)
3. Bidirectional validation (not just forward ablation)
4. Pre-registered disconfirmation criteria (not just confirmation-seeking)

### Venkatesh et al. (Feb 2026) — important citation from Claude

Steering vectors are "fundamentally non-identifiable" due to large equivalence classes of behaviorally indistinguishable interventions. However, identifiability is recoverable under sparsity constraints — precisely the SAE decomposition we propose. Must cite this paper to preemptively address the identifiability objection.

---

## 8. Consolidated Experimental Protocol

### Phase 0: Infrastructure (Week 0–1)

- Set up compute environment (single A100 80GB minimum)
- Install and validate: TransformerLens, SAE-Lens, pyvene, circuit-tracer
- Load Llama 3.1 8B-Instruct + Llama Scope 128K SAEs
- Load Gemma-2-2B + GemmaScope SAEs + pre-trained CLTs
- Validate basic forward pass, SAE reconstruction quality, steering hook functionality
- Post research plan on LessWrong/Alignment Forum to establish priority

### Phase 1: Persona Vector Extraction (Weeks 1–2)

**Traits:** sycophancy, evil/toxicity, hallucination (the three from Chen et al.)

**Extraction procedure (following Chen et al.):**
1. Input trait name + description to Claude 3.7 Sonnet via generic prompt template
2. Generate 5 contrastive system prompt pairs + 40 questions (20 extraction, 20 evaluation)
3. Generate 10 rollouts per question × prompt pair
4. Filter responses by trait expression score (GPT-4.1-mini judge): retain >50 for positive, <50 for negative
5. Extract residual stream activations at layers 12–24, averaged across response tokens
6. Compute persona vector = mean(positive) − mean(negative) per layer
7. Select optimal layer via steering effectiveness sweep: α ∈ {0.5, 1.0, 1.5, 2.0, 2.5, 3.0}

**Deliverable:** Validated persona vectors with optimal layer and coefficient per trait.

### Phase 2: Behavioral Validation (Weeks 2–3)

- Steering coefficient sweep (positive and negative α)
- GPT-4.1-mini judge scoring on trait-specific rubric (validate with ~50 human labels)
- External benchmarks: TruthfulQA (hallucination), Anthropic sycophancy evals, Betley et al. misalignment probes (evil)
- MMLU accuracy tracking for capability preservation
- **Success criterion:** Monotonic trait increase with α, MMLU degradation <5% at working coefficient

**Deliverable:** Behavioral validation report; working steering coefficients per trait.

### Phase 3: SAE Decomposition (Weeks 3–4)

1. Project persona vectors onto SAE decoder directions → top-200 features per trait by cosine similarity
2. Compute Δ-attribution across steered/unsteered runs → top-100 by causal attribution
3. Auto-interpret top features using max-activating examples + LLM description
4. Causal validation: steer individual top features, measure trait induction/suppression
5. Cross-check: repeat on andyrdt instruct-trained SAEs at layers 19/23

**Deliverable:** Top-100–200 features per trait with interpretations and causal validation.

### Phase 4: Circuit Tracing — Hybrid Approach (Weeks 4–6)

**On Llama 3.1 8B (main results):**
Execute the 6-step hybrid methodology from Section 2.

**On Gemma-2-2B (validation):**
Execute full CLT pipeline via circuit-tracer for 5–10 prompts per trait. Compare steered vs. unsteered attribution graphs. Extract delta circuits.

**Prompt selection:** 20 prompts per trait minimum:
- 8 strong trait elicitation
- 6 ambiguous (tests routing)
- 6 neutral competence (controls)

**Deliverable:** Candidate persona circuits per trait; attribution maps; hybrid vs. full-pipeline comparison.

### Phase 5: Causal Ablation Validation (Weeks 6–8)

Execute the 4-test ablation protocol (necessity, sufficiency, specificity, selectivity) plus bidirectional validation on ≥100 prompts per trait.

**Primary method:** Activation patching (resample ablation)
**Secondary method:** Mean ablation (for comparison)
**Report:** Normalized faithfulness, Cohen's d, A₁₂, percentile rank vs. 100 random baselines, bootstrapped 95% CIs, dose-response curves.

**Cross-trait analysis:** Feature overlap between circuits for different traits.
**Cross-seed stability:** Full pipeline on ≥3 random seeds.

**Deliverable:** Ablation results with full statistical validation; cross-trait comparison; modular vs. diffuse classification.

### Phase 6: Analysis and Writing (Weeks 8–10)

- Assess each PSM claim against evidence
- Write up results with honest disconfirmation where applicable
- Prepare code and data for public release
- Submit preprint

**Total estimated compute:** 20–50 GPU-hours on A100 80GB
**Total estimated wall-clock time:** 8–10 weeks with one researcher

---

## 9. Unresolved Questions and Known Unknowns

### Must verify before starting

1. **Does `gemma-scope-9b-it-res` actually exist on HuggingFace?** Claude claims it does. If not, Gemma-2-2B is still available for the proof-of-concept, but the Gemma 9B upgrade path needs revision.
2. **Does circuit-tracer support Qwen-3 at 14B?** Claude claims so. If true, this is relevant for replication.
3. **Do andyrdt SAEs cover layers 19 AND 20 for Llama 8B-Instruct?** Gemini claims both; ChatGPT confirms 19 and 23.
4. **What specific layer did Chen et al. find optimal for persona vector steering?** Sources cite ~35–50% of model depth. For Llama 8B (32 layers), that's layers 11–16. For our middle-to-late analysis window (12–24), we may need to adjust.

### Methodological uncertainties

5. **Will hybrid attribution on 8B produce qualitatively similar results to full CLT on 2B?** This is the central methodological bet. If 2B results are completely different from 8B, the hybrid approach is not validated. We won't know until we run both.
6. **Is resample ablation actually feasible at scale for 100+ prompts × 50+ features?** The compute cost of generating "neutral" activations for every feature × prompt combination may be significant.
7. **How sensitive are results to SAE width?** 32K vs. 128K SAEs may identify different "top features." Cross-checking at both widths is important.

### Theoretical uncertainties

8. **PSM's "persona" is undefined (psm-analysis.md weakness #1).** We can't fully test a theory when the core concept is ambiguous. Our operational definition: a persona is a coherent set of SAE features that, when activated together, produce trait-consistent behavior. This is pragmatic but may not match what PSM's authors intend.
9. **The exhaustiveness test may be underdetermined.** Ablating "all persona features" requires knowing what ALL persona features are. If we miss some, we'll find residual behavior and incorrectly conclude "shoggoth" when the answer is "incomplete feature set."
10. **Scale effects.** All work is on 8B models. PSM may behave differently at 70B+ where post-training is more intensive and capabilities are qualitatively different.

---

## 10. Summary Decision Matrix (Updated)

| Dimension | Assessment | Source Agreement |
|-----------|------------|-----------------|
| **Model selection** | Llama 3.1 8B-Instruct (primary) + Gemma-2-2B (CLT proof-of-concept) | 2/3 agree on Llama; hybrid approach is synthesis |
| **SAE selection** | Llama Scope 128K (primary), andyrdt instruct-trained (cross-check) | All three endorse, different emphasis |
| **Attribution method** | Hybrid approach (no CLTs for 8B); full CLT on 2B for validation | Claude + ChatGPT agree; Gemini wrong about CLT availability |
| **Ablation method** | Resample (primary), mean (secondary), multi-method always | Gemini + ChatGPT agree on resample gold standard; Claude recommends mean primary |
| **Effect size** | Report both Cohen's d AND Vargha-Delaney A₁₂ | Synthesis of Claude (Cohen's d) + Gemini (A₁₂) |
| **Prompt count** | 100 minimum, 200 preferred | Claude (100–200), ChatGPT (10 MVC → 200), Gemini (200) |
| **Circuit threshold** | >80% faithfulness, <10% sparsity, p<0.01 vs random | Claude framework + ChatGPT stability metric |
| **PSM claims** | 5 for MVC, 3 additional for full version | Synthesized across all three |
| **Adversarial scope** | OUT of MVC; Phase 3 only | All three agree |
| **Timeline** | 8–10 weeks (one researcher) | More conservative than Claude's 7–8 |
| **Scoop risk** | HIGH from Anthropic, 3–6 month window | All three agree |

### Key takeaway

The three sources provide complementary strengths: Claude for structure and honest infrastructure assessment, ChatGPT for epistemic discipline and grounded citations, Gemini for methodological innovation (bidirectional validation, A₁₂ metric) — but Gemini must be read with extreme caution on infrastructure claims. The synthesis resolves every major disagreement and produces an executable protocol.

The most important thing this analysis reveals is that **the CLT bottleneck is THE critical constraint.** Any plan that ignores it (as Gemini does) will fail on day one. The hybrid approach + Gemma-2-2B validation is the pragmatic path forward.
