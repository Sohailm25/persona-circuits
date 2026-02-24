# Closing gaps for PSM mechanistic grounding

**The first empirical mechanistic test of Anthropic's Persona Selection Model is feasible within 3–4 months using Gemma 2 9B + GemmaScope SAEs and a hybrid attribution approach, but a critical infrastructure gap—no pre-trained cross-layer transcoders for 7–9B models—requires adopting a fallback methodology combining direct feature attribution, attribution patching, and targeted activation patching rather than full Anthropic-style attribution graphs.** This report consolidates all findings needed to close research gaps and begin execution immediately. The competitive window is approximately 6 months before Anthropic likely publishes their own mechanistic PSM validation, making speed essential.

---

## 1. Model and SAE selection: Gemma 2 9B wins on infrastructure depth

### The recommendation

**Primary: Gemma 2 9B + GemmaScope 1.** This combination offers the most comprehensive SAE infrastructure available for any open-weight model. GemmaScope provides **400+ SAEs** covering all 42 layers and all sublayers (residual stream, MLP output, attention output) with dictionary sizes from **16K to 1M features**. Critically, instruction-tuned SAEs are available (`gemma-scope-9b-it-res`), SAELens integration is native, and Neuronpedia provides interactive feature dashboards. Reconstruction quality is documented with full Pareto curves across sparsity-fidelity tradeoffs, and Google DeepMind invested ~15% of Gemma 2 9B's pre-training compute in SAE training.

**Secondary: Llama 3.1 8B + Llama Scope (OpenMOSS/Fudan NLP).** This option has the advantage that Chen et al.'s persona vectors paper used Llama-3.1-8B-Instruct directly, providing a published baseline. Llama Scope covers all 32 layers with 256 SAEs at **32K and 128K** dictionary sizes across residual stream, MLP, and attention sites. The SAEs were trained on base Llama but validated to generalize to instruct variants. EleutherAI also provides SAEs at 131K features (`sae-llama-3.1-8b-32x`).

**Upgrade path: Gemma 3 12B + GemmaScope 2.** If compute permits, GemmaScope 2 provides state-of-the-art Matryoshka-trained SAEs plus **transcoders** (including cross-layer transcoders), which Google DeepMind explicitly recommends for circuit analysis and attribution graphs. This would enable the full Anthropic-style attribution pipeline.

| Model | SAE Source | Layers | Dictionary Sizes | Sites | Instruct SAE? | Reconstruction | Availability |
|-------|-----------|--------|-----------------|-------|---------------|---------------|-------------|
| **Gemma 2 9B** | GemmaScope 1 (GDM) | All 42 + sublayers | 16K–1M | Res, MLP, Attn | ✅ | Excellent (Pareto curves published) | HF: `google/gemma-scope-9b-*` |
| Llama 3.1 8B | Llama Scope (OpenMOSS) | All 32 + sublayers (256 SAEs) | 32K, 128K | Res, MLP, Attn | ❌ (base, transfers to IT) | Good (published metrics) | HF: `fnlp/Llama-Scope` |
| Llama 3.1 8B | EleutherAI | All layers + MLP | ~131K (32×) | Res, MLP | ❌ (base) | Limited docs | HF: `EleutherAI/sae-llama-3.1-8b-32x` |
| Llama 3.1 8B-IT | Goodfire | Layer 19 only | Unknown | Res | ✅ | L0=91 | HF: `Goodfire/Llama-3.1-8B-Instruct-SAE-l19` |
| Qwen 2.5 7B-IT | FAST (paper only) | Unknown | Unknown | Unknown | ✅ | MSE=0.6468 | ⚠️ Weights not confirmed public |
| Gemma 3 4B–27B | GemmaScope 2 (GDM) | All layers | 16K, 262K (up to 1M) | Res, MLP, Attn + Transcoders | ✅ | State-of-the-art | HF: `google/gemma-scope-2-*` |

**No comprehensive Qwen SAE suite exists publicly.** Chen et al. used Qwen for persona vectors but did not release SAEs; their paper mentions SAE decomposition as "a promising first step" without implementing it end-to-end. Our project would be novel work in this direction.

### Layer selection guidance

For Gemma 2 9B (42 layers): target layers **18–35** for middle-to-late analysis (~43–83% depth). For Llama 3.1 8B (32 layers): target layers **12–24** (~38–75% depth). Chen et al. found persona vector steering effectiveness peaks at approximately **35–50% of model depth** (layers 10–15 for Qwen 2.5 7B at 28 layers). The recommended configuration is **65K or 131K width SAEs** with medium L0 sparsity, using instruction-tuned SAEs where available.

---

## 2. Attribution graph methodology and the transcoder bottleneck

### How Anthropic's method works

Anthropic's circuit tracing, published in March 2025 by Ameisen, Lindsey et al., uses **Cross-Layer Transcoders (CLTs)** as a replacement for MLP layers, creating a "replacement model" where feature-feature interactions become linear. The mathematical core: each CLT feature has encoder weights at one layer but decoder vectors for all downstream layers. Edge weights between features are computed as **A_{s→t} = a_s × w_{s→t}**, where a_s is the source activation and w_{s→t} is the "virtual weight" derived from backward Jacobians with stop-gradients on all nonlinearities. Attention patterns are **frozen** from the actual forward pass (capturing OV circuits but not QK circuits), and normalization denominators are likewise frozen. This makes all pre-activations linear in upstream features, enabling exact linear attribution.

Attribution graphs are computed for a **specific target token position** (usually next-token prediction). Features at each (layer, token_position) pair are separate nodes. The unpruned graph has millions of edges even for short prompts; default pruning reduces nodes by ~10× while losing only ~20% of explained behavior. Output nodes cover tokens capturing **95% probability mass** (up to 10 tokens).

### The critical bottleneck: no 7–9B transcoders exist

The **circuit-tracer** library (github.com/decoderesearch/circuit-tracer), the primary open-source implementation, supports Gemma-2-2B, Llama-3.2-1B, and Qwen-3 (0.6B–14B) with pre-trained transcoders. However, **no pre-trained CLTs exist for any 7–9B model**. Training CLTs for a 7B+ model requires an estimated **100–500 GPU-hours on 4–8 A100s** with 100M–1B tokens of training data. This represents a major upfront cost.

EleutherAI's `attribute` library offers an independent CLT-based attribution implementation, and their `clt-training` fork provides memory-efficient sharding for training CLTs. Goodfire has replicated circuit tracing on GPT-2 for validation.

### The recommended hybrid approach

Given the CLT bottleneck, we recommend a **four-step hybrid methodology** that provides ~80% of the insight at ~10% of the cost:

**Step 1 — Direct feature attribution (minutes).** Project each persona vector onto SAE decoder directions at each layer: compute cosine similarity between the steering vector and every SAE feature's decoder direction. This identifies which features are most geometrically aligned with the persona vector—revealing "what the steering vector IS" in feature space with negligible compute.

**Step 2 — Gradient-based attribution patching (hours).** For each prompt, compute the gradient of output logits with respect to SAE features with and without steering. This is a first-order Taylor approximation of activation patching—a single forward + backward pass per prompt pair. Neel Nanda recommends this as a fast exploratory tool before validation with actual patching. This identifies which features gain or lose causal importance under steering.

**Step 3 — Targeted activation patching (hours).** For the top features identified above, perform actual activation patching: run the model on steered input, cache feature activations, then patch individual features between steered and unsteered runs. This confirms which features are causally necessary and sufficient for the behavioral change. TransformerLens, pyvene, and SAE-Lens all support this.

**Step 4 — Attention head analysis (minutes).** Ablate attention heads one at a time and measure the effect on steering-induced behavior change. This identifies which heads mediate persona routing at a coarser granularity.

### Compute estimates

| Approach | Compute | Time | Hardware |
|----------|---------|------|----------|
| Full CLT-based attribution (60 graphs) | 5–15 hrs A100 | 1–2 days | 1× A100 80GB |
| CLT training for 7–9B model | 100–500 GPU-hrs | 1–2 weeks | 4–8× A100 |
| **Hybrid approach (recommended)** | **2–5 hrs A100** | **1 day** | **1× A100 80GB** |
| Direct feature attribution alone | <1 hr | Hours | 1× A100 |

For the MVC scope of 60 conditions (10 prompts × 3 traits × with/without steering), the hybrid approach is feasible on a **single A100 80GB in approximately one day**.

An alternative strategy: **downscale to Gemma-2-2B** (where CLTs already exist) for the full attribution graph pipeline as proof-of-concept, then apply the hybrid approach to the 7–9B model for the main results. This dual-scale approach would be methodologically strong.

---

## 3. What counts as a coherent circuit: definitions and thresholds

### The standard framework

The field converges on three evaluation criteria originated by Wang et al. (2023) in the IOI circuit paper: **faithfulness** (the circuit's behavior matches the full model on the task), **completeness** (ablating everything outside the circuit preserves behavior), and **minimality** (removing any component degrades performance). There is no single formal standard definition, but the consensus is: *a circuit is a sparse subgraph of the model's computational graph sufficient to recover the model's behavior on a specific task, as measured by a task-relevant metric.*

**Normalized faithfulness** (Marks et al., 2025; MIB benchmark) is the proportion of divergence between the empty circuit and the full model that the circuit recovers: 0 = empty circuit performance, 1 = full model recovery. **A critical warning from Marks et al. (2024)**: "Existing circuit faithfulness scores reflect both the methodological choices of researchers as well as the actual components of the circuit." Small changes in ablation methodology produce significantly different faithfulness scores, requiring multi-method validation.

### Circuit sizes in published work

Published task-specific circuits are consistently sparse: the IOI circuit comprises **26 heads out of 144** (~18% of heads, but ~1.5% of head×position pairs). ACDC identified **68 edges out of 32,000** (~0.2%). Lying circuits in Llama-3.1-8B use approximately **20 heads out of 1,024** (~2%). A single "safety head" ablation (0.006% of parameters) allows 16× more harmful query responses. The general pattern: **task-specific circuits are 1–10% of model components**.

### Our operationalization

For this project, we adopt the following definitions:

**Coherent circuit:** A sparse subgraph C satisfying five criteria simultaneously: (1) **Faithful**: running only C recovers >80% of the full model's task metric (normalized faithfulness >0.8); (2) **Minimal**: removing any single component reduces faithfulness significantly (p < 0.05); (3) **Sparse**: C contains <10% of model components; (4) **Specific**: ablating C does not degrade unrelated tasks by >10%; (5) **Superior to random**: C's ablation effect exceeds random same-size subsets at p < 0.01.

**Modular mechanism:** The top-10 components account for >50% of total causal effect, and the circuit meets all five criteria above.

**Diffuse mechanism:** No circuit of <10% of components achieves >60% faithfulness, or the effect scales approximately linearly with component count (no sharp circuit boundary).

**Criteria for claiming "persona vector X operates through circuit Y":** (1) *Necessity*: ablating Y reduces steering effect of X by >50%; (2) *Specificity*: ablating random same-size sets reduces effect by <20%; (3) *Selectivity*: ablation disproportionately affects persona metrics versus general capabilities; (4) *Sufficiency* (strong claim): running only Y preserves >60% of steering effect.

### Critical caveats from the literature

Li and Janson (2024, NeurIPS) showed that standard ablation methods massively overestimate component importance due to "spoofing"—the ablated value actively misleads downstream computation. Optimal ablation accounts for only **11.1% of zero-ablation Δ** for the median component. This means most measured effects from standard ablation are artifacts. We must validate using multiple ablation methods and always compare against random baselines.

---

## 4. Causal ablation experimental design

### Recommended ablation method

Use **mean ablation** as primary (replacing activations with dataset mean, balancing informativeness and stability) with **activation patching** (swapping between steered/unsteered runs) as the gold standard for validation. Report results from both methods. Per Zhang and Nanda (2024, ICLR), use **logit difference** rather than raw probability as the metric.

### Experimental protocol for persona circuit validation

The protocol has four tests run in sequence:

**Test 1 — Necessity:** Ablate the putative persona circuit, then apply the steering vector. If the circuit mediates the steering effect, behavioral shift should diminish by >50% compared to full-model steering. This establishes that the circuit is required for the steering vector to produce its effect.

**Test 2 — Sufficiency:** Ablate everything except the circuit, then apply steering. If the circuit is sufficient, persona behavior should be preserved (>60% of effect maintained). This is a stronger claim than necessity.

**Test 3 — Specificity:** Ablate the circuit without steering and test on unrelated tasks (factual recall, math, coding). If the circuit is persona-specific, these tasks should show <10% degradation. This distinguishes "circuit is causal for persona behavior" from "ablation just breaks the model."

**Test 4 — Selectivity (random baseline):** Ablate 100+ random component sets of the same size as the circuit, with steering applied. Compute the distribution of effects. The real circuit's ablation effect should fall in the **top 1%** of this distribution (p < 0.01, one-tailed permutation test).

**Additional controls:** (a) Dose-response curve—ablate 25%, 50%, 75%, 100% of circuit components and verify roughly monotonic degradation; (b) Ablation method sensitivity—run with at least two methods (mean + resample or mean + activation patching) and verify qualitative consistency; (c) General degradation baseline—measure perplexity on general text after ablation to ensure the intervention isn't globally destructive.

### Statistical plan

Use a minimum of **100 prompts per trait** (200 preferred). Compute **paired permutation tests** for the necessity comparison (full model + steering vs. ablated model + steering). Report **Cohen's d** effect sizes plus raw metric differences with bootstrapped 95% confidence intervals (≥1,000 resamples). Apply **Bonferroni correction** when testing multiple circuits or configurations. For the random baseline comparison, generate ≥100 random circuits and test whether the real circuit falls in the top 5% (report exact percentile and p-value).

---

## 5. Eight testable PSM claims, ranked by tractability and impact

The PSM paper ("The Persona Selection Model: Why AI Assistants might Behave like Humans") was published February 23, 2026, by Sam Marks, Jack Lindsey, and Christopher Olah at Anthropic. Its core thesis: **LLMs are best understood as actors capable of simulating a vast repertoire of characters, and the AI assistant is one such character.** Post-training "refines and fleshes out" the Assistant persona "roughly within the space of existing personas" rather than fundamentally changing its nature.

The companion paper by Lu et al. (January 2026) empirically demonstrates an "Assistant Axis" (PC1 of persona space across 275 character archetypes) that captures the degree to which the model operates in Assistant mode, validated on Gemma 2 27B, Qwen 3 32B, and Llama 3.3 70B.

| # | Claim | Experiment | Confirmation | Disconfirmation | Priority |
|---|-------|-----------|-------------|-----------------|----------|
| 1 | **Trait inference mediates generalization** — fine-tuning on narrow misaligned behavior activates general personality trait features, not task-specific features | Ablate persona trait features in emergently misaligned models; check if cross-domain misalignment disappears while narrow task behavior persists | Ablating "malicious persona" features eliminates cross-domain misalignment | Shifted features are task-specific; ablation doesn't affect generalization | **HIGHEST** |
| 2 | **System prompts route through identifiable persona circuits** | Attribution graphs across 20+ persona system prompts; map shared routing circuitry | Consistent routing circuit: early attention heads read persona cues and gate downstream feature clusters | Each persona uses entirely different circuits with no shared mechanism | **HIGH** |
| 3 | **Post-training operates within pre-existing persona space** | Compare persona feature space (crosscoder/model-diffing) in base vs. post-trained model | Post-training shifts project mostly onto pre-existing persona feature directions | Post-training creates fundamentally new features not reducible to pre-existing directions | **HIGH** |
| 4 | **Persona drift is circuit-localizable** | Trace attribution graphs through conversations that induce persona drift; identify drift-mediating features | Specific features/circuits mediate drift; ablation prevents it | Drift caused by diffuse, non-localizable mechanisms | **HIGH** |
| 5 | **The Assistant Axis has a computable circuit** | Trace how the Axis direction is set by early attention heads reading context | Coherent circuit sets Axis value based on contextual cues; ablation causes persona instability | Axis emerges from distributed computation with no identifiable circuit | **MEDIUM-HIGH** |
| 6 | **Exhaustiveness: behavior flows through persona circuits** | Ablate all persona-relevant features; measure remaining behavior | Ablation produces random/incoherent output (supports exhaustive PSM) | Coherent, goal-directed output persists (supports "masked shoggoth") | **MEDIUM-HIGH** |
| 7 | **Toxic persona features share routing circuits with benign personas** | Compare attribution graphs for emergent misalignment vs. normal persona switching | Same routing bottleneck; toxic features are reachable from same mechanism | Entirely separate circuits for toxic vs. benign personas | **MEDIUM-HIGH** |
| 8 | **Persona space mirrors human personality structure** | PCA of many persona vectors; compare geometry to Big Five or similar frameworks | Correlated traits in humans are correlated in activation space | Persona features organized along non-human dimensions | **MEDIUM** |

### The router hypothesis

The PSM paper does not use the word "router" explicitly, but strongly implies a routing mechanism: the model must select which persona to activate based on context. The August 2025 Transformer Circuits update provides a concrete proof-of-concept: attribution graphs on Claude 3.5 Haiku showed that a "preschool student" system prompt activates persona-specific features flowing through "'examples of X speaking'-style features." They explicitly asked whether other personas flow through similar features—**this is precisely our research question**.

A plausible router architecture: **early-layer attention heads** attend to persona-relevant context (system prompt, chat formatting); **mid-layer features** represent inferred persona identity; **gating mechanisms** where persona features modulate downstream computation (suppressing knowledge, adjusting tone, selecting response strategies); the **Assistant Axis** as the primary routing dimension.

### The exhaustiveness question

This is PSM's central open question, framed as a spectrum between the "masked shoggoth" view (an alien outer agent puppets personas) and the "operating system" view (everything flows through persona mechanisms). Our experiment design: identify all persona-relevant features/circuits, then for diverse behaviors (factual recall, reasoning, code, refusal, emotion), measure what fraction of output logit is attributable to persona features vs. non-persona features. If persona circuits account for ~100% of behavioral variance → operating system view. If a small fraction → masked shoggoth view. A critical observable: when persona features are ablated, does the model produce incoherent output (exhaustive PSM), coherent but personality-less output (operating system), or coherent goal-directed output driven by different objectives (masked shoggoth)?

---

## 6. Adversarial robustness landscape favors circuit-level monitoring but remains unproven

### Bailey et al. decisively breaks representation-level defenses

"Obfuscated Activations Bypass LLM Latent-Space Defenses" (Bailey et al., December 2024, accepted ICLR 2026) demonstrates that **all representation-level monitoring can be bypassed** by adversarial training. Their joint optimization combines a behavior loss (ensuring harmful output) with an obfuscation loss (fooling the monitor): the result reduces probe recall from 100% to 0% while maintaining 90% jailbreaking rate. They bypassed linear probes, nonlinear probes, SAE-based detection, and out-of-distribution detectors on Llama-3-8B-Instruct. The attacks show remarkable transferability across monitor types.

However, two findings are relevant for our project. First, there is an **"obfuscation tax"**: on complex functional tasks (SQL code generation), obfuscation significantly degrades model performance. Second, the authors failed to find activations "almost orthogonal to natural ones" while preserving model behavior, suggesting fundamental geometric constraints on obfuscation.

### Circuit-level defenses occupy untested territory

**Bailey et al. did NOT test circuit-level defenses**—only representation-level monitors (probes at individual layers, SAE features, OOD detectors). This gap is directly relevant to our project.

Arguments favoring circuit robustness: circuits capture functional computation, meaning the model must actually compute harmful outputs through some pathway; obfuscating the structure of computation across multiple layers simultaneously is a harder optimization than fooling a single-layer probe; the obfuscation tax evidence suggests complex functional monitoring inherits robustness. Arguments against: neural networks have redundant pathways that could circumvent monitored circuits; Li et al. (EACL 2026) showed tiny adversarial perturbations can manipulate SAE concept interpretations without changing model behavior; Neel Nanda (May 2025) argued that superposition and inherent SAE reconstruction error prevent confident conclusions from any interpretability-based monitoring.

**No empirical comparison of probe vs. circuit robustness exists as of February 2026.** This is a critical research gap our Phase 3 could address.

### What we can claim in the MVC

We can responsibly claim: (1) descriptive findings about persona circuit structure; (2) that these circuits provide a *candidate* monitoring signal; (3) that based on Bailey et al., circuit-level monitoring is *plausibly* more robust due to the functional computation constraint. We **cannot** claim monitoring robustness without adversarial testing. Phase 3 should include: applying Bailey-style suffix attacks and measuring whether circuit structure is preserved; fine-tuning with circuit-targeted obfuscation loss and measuring the obfuscation tax; comparing single-layer probes vs. full attribution graphs under identical attacks.

---

## 7. Competition assessment: a 3–4 month window exists

### Anthropic is the primary threat

Anthropic has already demonstrated preliminary persona circuit tracing in their August 2025 Transformer Circuits update, tracing a "preschool student" persona through attribution graphs on Claude 3.5 Haiku. They explicitly asked the question our project aims to answer. **Jack Lindsey co-authored the circuit tracing methods paper, the persona vectors paper, the Assistant Axis paper, AND the PSM paper**—he is the natural person to lead mechanistic PSM validation with proprietary access to Claude internals and massive compute. The publication cadence (Biology March 2025 → Persona Vectors July 2025 → Assistant Axis January 2026 → PSM February 2026) suggests a comprehensive mechanistic paper could appear in **Q3–Q4 2026**.

### Other competitors

OpenAI's Wang et al. team has SAE persona features on GPT-4o and could extend to circuit-level analysis (medium risk). Google DeepMind's Nanda team published convergent misalignment directions work but has pivoted toward "pragmatic interpretability" (low-medium risk). MATS fellows cohorts starting May and July 2026 could produce related projects (medium risk). Apollo Research, Redwood Research, FAR AI, and academic groups show no evidence of pursuing this specific combination (low risk).

A key methodological concern to address: Venkatesh et al. (February 2026) proved that steering vectors are "fundamentally non-identifiable" due to large equivalence classes of behaviorally indistinguishable interventions. However, identifiability is **recoverable under sparsity constraints**—precisely the SAE decomposition we propose. This paper should be cited to strengthen our approach.

### Differentiation strategy

- **Speed**: target completion within 3–4 months
- **Open-weight focus**: provide the first mechanistic PSM grounding on open models (non-duplicative with Anthropic's proprietary Claude work)
- **Full pipeline**: no one has published persona vectors → SAE features → attribution/patching → persona circuits → causal ablation end-to-end
- **Post a research plan on LessWrong/Alignment Forum** to establish priority
- **Use Anthropic's own open-source tools** (circuit-tracer, persona_vectors code)

---

## 8. Complete experimental protocol

### Phase 1: Persona vector extraction (weeks 1–2)

**Model selection:** Gemma 2 9B-IT (primary) or Llama 3.1 8B-Instruct (secondary, for direct comparison to Chen et al.).

**Traits:** sycophancy, evil/toxicity, hallucination (the three from Chen et al.), with optional extension to optimistic, impolite, apathetic, humorous.

**Extraction procedure (following Chen et al.):**
1. Input trait name + natural-language description to Claude 3.7 Sonnet via generic prompt template
2. Generate 5 contrastive system prompt pairs + 40 questions (20 extraction, 20 evaluation) + evaluation rubric
3. Generate 10 rollouts per question × prompt pair (up to 1,000 responses per trait)
4. Filter responses by trait expression score: retain >50 for positive, <50 for negative
5. Extract residual stream activations at every layer, **averaged across response tokens** (Chen et al. found this superior to last-token extraction for steering)
6. Compute persona vector = mean(positive) − mean(negative) per layer
7. Select optimal layer via steering effectiveness sweep: α ∈ {0.5, 1.0, 1.5, 2.0, 2.5}

**Expected optimal layers:** For Gemma 2 9B (42 layers), approximately layers 15–21 (~36–50% depth). For Llama 3.1 8B (32 layers), approximately layers 10–16.

### Phase 2: Behavioral validation (weeks 2–3)

**Steering sweep:** Test α ∈ {0.5, 1.0, 1.5, 2.0, 2.5} and α ∈ {−0.5, −1.0, −1.5, −2.0, −2.5} for each trait at the optimal layer.

**Scoring:** GPT-4.1-mini as judge using the auto-generated trait-specific rubric (0–100 scale). Validate LLM judge agreement with human evaluators on ~50 samples.

**External benchmarks:** TruthfulQA for hallucination, Anthropic model-written-evals sycophancy datasets for sycophancy, Betley et al. prompts (20+ misalignment probes) for evil/toxicity. Track MMLU accuracy for capability preservation at each coefficient.

**Success criteria:** Monotonic increase in trait expression with α, coherence maintained above 75/100, MMLU degradation <5% at working coefficient.

### Phase 3: SAE decomposition (weeks 3–4)

**SAE selection:** For Gemma 2 9B, use GemmaScope IT residual stream SAEs at 65K or 131K width with medium L0. For Llama 3.1 8B, use Llama Scope 128K SAEs or EleutherAI 131K SAEs.

**Feature identification pipeline:**
1. Project persona vectors onto SAE decoder directions → identify top-200 features per trait by cosine similarity
2. Apply OpenAI's Δ-attribution method: compute δ_{i,t} ≈ −(g_t · d_i)((a_t − ā) · d_i) for each latent i at token t; average over tokens and prompt pairs; select top-100 latents by Δ-attribution
3. Auto-interpret features using max-activating examples + LLM description (Claude)
4. Rate feature relevance to persona trait
5. **Causal validation**: steer individual top features and measure trait induction/suppression

**Key hyperparameters:** SAE width 131K, BatchTopK sparsity with k=64, top-100–200 features for analysis, activation extraction at last prompt token (for monitoring) and response token mean (for steering).

### Phase 4: Circuit tracing via hybrid approach (weeks 4–6)

**Prompt selection:** 20–50 prompts per trait where persona vector produces measurable behavioral change, sampled from evaluation set. Include both "easy" (clear trait elicitation) and "hard" (ambiguous) prompts.

**Step 1 — Direct feature attribution:** For each layer, compute cosine similarity between persona vector and all SAE feature decoder directions. Identify features geometrically aligned with the steering direction. Compute this for the optimal layer and ±5 surrounding layers.

**Step 2 — Attribution patching:** For each of 20 prompts per trait, compute gradient-based attribution of output logits with respect to SAE features. Run with and without steering vector. Compare attribution patterns to identify features that gain/lose importance under steering.

**Step 3 — Targeted activation patching:** For top-50 features from Steps 1–2, perform actual activation patching between steered/unsteered runs. Measure necessity (patching individual features) and sufficiency (patching sets of features) for the behavioral change.

**Step 4 — Attention head survey:** Ablate all attention heads one at a time, measure effect on steering-induced behavior change. Identify heads that mediate persona routing.

**Optional Step 5 (if using Gemma-2-2B for full pipeline):** Use circuit-tracer with existing CLTs to generate full attribution graphs for 10 prompts per trait. Compare steered vs. unsteered graphs. This serves as a proof-of-concept validation of the hybrid approach on the larger model.

### Phase 5: Causal ablation and validation (weeks 6–7)

Execute the four-test ablation protocol (necessity, sufficiency, specificity, selectivity) described in Section 4 above. Run on ≥100 prompts per trait. Use mean ablation as primary method with activation patching as secondary. Report normalized faithfulness, Cohen's d, percentile rank versus 100 random baselines, and bootstrapped 95% CIs.

**Cross-trait analysis:** Check feature overlap between persona circuits for different traits. If sycophancy and evil share significant circuit components, this supports PSM's trait-inference model. If they are completely disjoint, this suggests independent, modular mechanisms per trait.

**Cross-seed stability:** Run the full pipeline on ≥3 random seeds and report consistency of identified features and circuits.

---

## 9. Risk assessment and what we can versus cannot claim

### Technical risks and mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| No CLTs for 7–9B models | HIGH | Use hybrid approach (attribution patching + targeted patching); use Gemma-2-2B as proof-of-concept |
| Persona mechanisms are diffuse, not modular | MEDIUM | Pre-register this as a legitimate finding; report the modularity spectrum rather than binary pass/fail |
| Ablation "spoofing" overestimates circuit importance | MEDIUM | Use multiple ablation methods; always compare to random baselines; consider optimal ablation |
| SAE reconstruction errors corrupt circuit identification | MEDIUM | Use multiple SAE widths; validate features with manual inspection; check consistency across SAE sizes |
| Steering vectors are non-identifiable (Venkatesh et al.) | LOW | SAE sparsity constraints recover identifiability; cite this paper to preemptively address |

### Scoop risk

**Overall: MEDIUM-HIGH.** Anthropic is almost certainly working on this internally and has 6–9 months of lead time in tooling and access. The window for being first on open-weight models is approximately **3–4 months** before MATS cohorts and incremental Anthropic releases begin to close the gap. Speed is critical. The differentiation strategy of focusing on open-weight models, publishing the full pipeline, and pre-registering publicly provides meaningful protection.

### Claims we can make in the MVC

- "We identified coherent persona circuits in [model] using SAE feature decomposition and hybrid attribution methods"
- "Persona vector X operates through a sparse circuit comprising <Y% of model features, preserving >Z% of the steering effect under ablation"
- "These circuits provide a candidate monitoring signal that could inform safety interventions"
- "Based on Bailey et al., we hypothesize that circuit-level monitoring may be more robust than probe-based monitoring due to the functional computation constraint"
- "Our findings provide the first empirical mechanistic evidence for/against PSM's claim that [specific claim]"

### Claims that require additional work

- Monitoring robustness (requires Phase 3 adversarial testing)
- Whether circuits are the *only* pathway for persona behavior (requires exhaustive analysis)
- Whether findings generalize to frontier models (requires replication on larger models)
- Whether PSM holds under intensive post-training (requires access to multiple training checkpoints)

---

## 10. Consolidated execution timeline

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1–2 | Persona vector extraction for 3 traits on Gemma 2 9B-IT (or Llama 3.1 8B-IT) | Validated persona vectors with layer sweep |
| 2–3 | Behavioral validation: steering sweep, external benchmarks, LLM judge calibration | Behavioral validation report; working steering coefficients |
| 3–4 | SAE decomposition: project vectors onto SAE features, auto-interpret, causal validate top features | Top-100–200 features per trait with interpretations |
| 4–6 | Hybrid circuit tracing: direct attribution + attribution patching + targeted patching + head survey | Candidate persona circuits per trait; attribution maps |
| 6–7 | Causal ablation: necessity/sufficiency/specificity/selectivity tests on ≥100 prompts per trait | Ablation results with statistical validation |
| 7–8 | Analysis, writing, cross-trait comparison, reproducibility verification | Draft paper; all code and data prepared for release |

**Total estimated compute:** 20–50 GPU-hours on A100 80GB for the full pipeline. **Total estimated wall-clock time:** 7–8 weeks with one researcher, 4–5 weeks with two.

Post the research plan publicly on LessWrong/Alignment Forum in week 1 to establish priority. Target preprint submission by week 8.
