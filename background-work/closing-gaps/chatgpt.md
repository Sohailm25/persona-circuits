
Below is what I’d do to close *all* the gaps you listed, using only sources I could verify right now. Where I couldn’t retrieve the underlying full text (notably the full Alignment Blog post for PSM, and the full Bailey et al. PDF), I’m explicit about what I can/can’t support and I design around it.

---

## 1) Model + SAE decision

### What “good” looks like for your MVC

You need SAEs that are:

* **Overcomplete** (32k–131k+ features).
* **Middle–late layer coverage** (≈16–24 for a 32-layer model).
* **High reconstruction fidelity** (variance explained / FVU / ΔLM loss, plus sparse L0).
* **Actually usable** (public checkpoints + tooling).
* Preferably **validated** on interpretability-relevant checks and (ideally) **works on instruct models**.

---

## 1.1 Llama‑3.1‑8B‑Instruct SAE availability

### Option A — **Llama Scope** (Fudan / OpenMOSS ecosystem): *broadest coverage + strong evaluation*

**What exists**

* **256 SAEs** trained on **every layer and sublayer** of **Llama‑3.1‑8B‑Base**, with **32K and 128K features**, across multiple activation sites (post‑MLP residual stream, attention output, MLP output, and transcoders). ([arXiv][1])
* Checkpoints: HuggingFace (`fnlp/Llama-Scope`) and tools on GitHub (`OpenMOSS/Language-Model-SAEs`). ([arXiv][1])

**Layer coverage**

* Full (all 32 layers × multiple sublayer hookpoints), so you can directly target **layers 16–24**. ([arXiv][1])

**Reconstruction quality reporting**

* They evaluate using **L0**, **explained variance**, and **ΔLM loss**; they define explained variance formally and emphasize ΔLM loss as “impact on the language model.” ([arXiv][1])

**Generalization to instruction‑tuned models**

* They explicitly evaluate on **Llama‑3.1‑8B‑Instruct** using WildChat-derived activations and report **no significant degradation** for most SAEs (exceptions near output). ([arXiv][1])

**Why this matters for you**

* You can treat Llama Scope SAEs as your *primary* decomposition basis even if your behavioral work is on **Llama‑3.1‑8B‑Instruct**, because they tested generalization to the instruct model. ([arXiv][1])

---

### Option B — **andyrdt SAEs for Llama‑3.1‑8B‑Instruct**: *directly-trained-on-instruct, good metrics, but sparse layer sampling*

**What exists**

* Residual stream SAEs for **Llama‑3.1‑8B‑Instruct** on HuggingFace (`andyrdt/saes-llama-3.1-8b-instruct`). ([Hugging Face][2])
* Coverage appears to be **every ~4 layers** (e.g., 19 and 23 are included, which you care about). ([Hugging Face][2])

**Dictionary size / sparsity**

* Example (layer 23): **dict_size = 131,072**, **k = 32** (trainer_0) or **k = 64** (trainer_1). ([Hugging Face][3])

**Reconstruction fidelity (example: layer 23)**

* k=32: `frac_variance_explained ≈ 0.759`, `l0 ≈ 29.7`, and reconstructed LM loss increases vs original. ([Hugging Face][4])
* k=64: `frac_variance_explained ≈ 0.806`, `l0 ≈ 59.6`. ([Hugging Face][5])

**Where it fits**

* Great as a **sanity-check / robustness cross‑run**: use andyrdt’s *instruct-trained* SAE at layers like **19/23** to confirm that your key persona features aren’t an artifact of “base→instruct generalization.”

---

### Option C — **EleutherAI SAEs for Llama‑3.1‑8B**: *very wide, but limited layer coverage*

**What exists**

* `EleutherAI/sae-llama-3.1-8b-32x` and `...-64x` on HuggingFace. ([Hugging Face][6])

**Dictionary size (implied by configs)**

* 32x config: expansion_factor **32**, d_in **4096** ⇒ ~**131,072** latents. ([Hugging Face][7])
* 64x config: expansion_factor **64**, d_in **4096** ⇒ ~**262,144** latents. ([Hugging Face][8])

**Layer coverage**

* The HF repo structure indicates **a small set of layers** (not a full suite), so it’s less ideal as your main backbone if you want consistent coverage across 16–24. ([Hugging Face][9])

---

## 1.2 Gemma‑2‑9B + GemmaScope

### GemmaScope coverage and sizes

* GemmaScope provides SAE suites for **Gemma 2 2B and 9B pre‑trained models** across **all layers and sites** (residual stream / attention output / MLP output). ([arXiv][10])
* They also train some SAEs for **Gemma 2 9B instruction-tuned (IT)** but only at selected layers (including **layer 20**, which is inside your 16–24 target band). ([arXiv][10])

### Reconstruction fidelity

* Reported metrics include **FVU (fraction variance unexplained)**; e.g., a reported **FVU = 0.06** for Gemma‑2‑2B, implying high reconstruction quality. ([arXiv][10])

### Used for persona/steering analysis?

* I did not find a source in the retrievable material saying “GemmaScope has been used specifically for persona vector analysis.” What I *can* support is that the **persona vectors paper itself explicitly decomposes persona vectors into SAE features** and provides a concrete decomposition method (cosine similarity with decoder directions). ([arXiv][11])

### Known issues / limitations (actionable)

From what *is* documented in the Llama Scope ecosystem (similar SAE setting), two practical limitations you should plan for:

* **Near-output spaces may behave differently** when transferring SAEs to instruct settings (Llama Scope calls out exceptions at the near-output residual stream). ([arXiv][1])
* **Choice of hookpoint matters**: Llama Scope reports residual stream SAEs often outperform SAEs trained on other sites on headline metrics, plausibly due to cross-layer superposition / noise. ([arXiv][1])

(Those are Llama Scope observations, but they generalize as “watch out for site-specific differences.”)

---

## 1.3 Other model options

### Qwen‑2.5‑7B‑Instruct

* `andyrdt/saes-qwen2.5-7b-instruct` exists and is explicitly described as **Residual stream SAEs for Qwen2.5‑7B‑Instruct** trained on a blend of chat and pretraining data. ([Hugging Face][12])
  This is strategically attractive because the **persona vectors paper’s experiments heavily feature Qwen‑class models** (your prompt notes that, and the paper itself clearly frames persona vectors as activation-space directions + SAE feature decomposition). ([arXiv][11])

### Mistral‑7B‑Instruct

* There are public single‑layer SAEs (e.g., “layer16”) but coverage is sparse (one layer only). ([Hugging Face][13])
* There’s also a related repo describing training an SAE for Mistral 7B. ([GitHub][14])

---

## 1.4 Comparative assessment table

| Model                                                                                                       | SAE Source                   |                                  Layers Covered (relevant to 16–24) |                                                        Dictionary Size | Reconstruction Quality (reported)                                                                    | Persona Vector Validated?                                                                | Availability                   |
| ----------------------------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------: | ---------------------------------------------------------------------: | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------ |
| **Llama‑3.1‑8B‑Instruct** (analysis target) + **Llama Scope SAEs** (trained on Base, evaluated on Instruct) | Llama Scope (Fudan/OpenMOSS) |          **All layers/sublayers** ⇒ includes **16–24** ([arXiv][1]) |                                   **32k & 128k** features ([arXiv][1]) | Metrics: L0, explained variance, ΔLM loss ([arXiv][1]); generalizes to instruct broadly ([arXiv][1]) | Not explicitly “persona vectors,” but strong mech‑interp validation framing ([arXiv][1]) | HF + tools repo ([arXiv][1])   |
| Llama‑3.1‑8B‑Instruct                                                                                       | andyrdt (BatchTopK SAEs)     |                 Sampled layers incl. **19, 23** ([Hugging Face][2]) |                                        **131,072** ([Hugging Face][3]) | Example layer23: FVE ~0.806 at k=64; L0 ~59.6 ([Hugging Face][5])                                    | Not stated                                                                               | HF ([Hugging Face][2])         |
| Llama‑3.1‑8B (base)                                                                                         | EleutherAI (32x/64x)         |     Appears limited (e.g., certain layers only) ([Hugging Face][9]) | ~131,072 (32x) ([Hugging Face][7]); ~262,144 (64x) ([Hugging Face][8]) | Not surfaced in retrieved material                                                                   | Not stated                                                                               | HF ([Hugging Face][6])         |
| Gemma‑2‑9B (pretrained)                                                                                     | GemmaScope                   |                                  **All layers/sites** ([arXiv][10]) |                     widths include **131k**+ (per suite) ([arXiv][10]) | Example reported FVU=0.06 on 2B ([arXiv][10])                                                        | Not stated                                                                               | Paper + suite ([arXiv][10])    |
| Gemma‑2‑9B‑IT                                                                                               | GemmaScope                   |                    Selected layers incl. **layer 20** ([arXiv][10]) |                                         (suite-specific) ([arXiv][10]) | Reported via FVU ([arXiv][10])                                                                       | Not stated                                                                               | Paper + suite ([arXiv][10])    |
| Qwen‑2.5‑7B‑Instruct                                                                                        | andyrdt                      | (not verified here) residual-stream SAEs exist ([Hugging Face][12]) |                                                    (not verified here) | (not verified here)                                                                                  | **High strategic alignment** with persona vectors ecosystem ([arXiv][11])                | HF ([Hugging Face][12])        |
| Mistral‑7B‑Instruct                                                                                         | tylercosgrove                |                        Single layer (layer 16) ([Hugging Face][13]) |                                                           (single SAE) | (not verified here)                                                                                  | Not stated                                                                               | HF/GitHub ([Hugging Face][13]) |

---

## Recommendation: optimal model + SAE combo

### **Primary recommendation (best overall for your MVC):**

**Analyze Llama‑3.1‑8B‑Instruct**, using **Llama Scope SAEs (128K features) as your main SAE basis**, focusing on **layers 16–24** and the specific hookpoints you need (post‑MLP residual stream + attention out + MLP out).
Why:

* You get **full, systematic coverage** (all layers & sites) with **overcomplete widths** (32k/128k). ([arXiv][1])
* You get **clear reconstruction metrics** and evaluation framing (L0, explained variance, ΔLM loss). ([arXiv][1])
* Critically, the authors explicitly evaluate **generalization to Llama‑3.1‑8B‑Instruct**, finding broad robustness (except near-output). ([arXiv][1])

### **Secondary (strong cross-check):**

Run a small subset using **andyrdt’s instruct‑trained SAEs** on layers **19 and 23** to confirm your top persona features and causal claims persist when the SAE was trained on instruct activations. ([Hugging Face][3])

### **If you want maximal synergy with “attribution graphs / circuit tracing” infrastructure:**

Add a parallel track on **Gemma‑2‑9B + GemmaScope**, because it’s explicitly a full-layer/site suite with strong reconstruction reporting (FVU) and is close to the ecosystem that popularized attribution-graph workflows. ([arXiv][10])

---

# 2) Attribution graph methodology

## 2.1 Anthropic “Biology” / attribution graphs: what the method is

### What they call it

They refer to the objects as **“attribution graphs”** and the overall workflow as **circuit tracing** / attribution-graph construction. ([Transformer Circuits][15])

### Core mathematical objects (as specified in their methods)

**Edge weights / direct effects**

* They define an integrated-gradients-like edge weight:
  [
  w_{s \to t}^{\text{itgrads}} = \int_{0}^{a_s} \frac{\partial a_t}{\partial a_s} , da_s
  ]
  and then **direct effect** is:
  [
  \text{direct_effect}*{s \to t} = a_s \cdot w*{s \to t}^{\text{itgrads}}
  ]
  ([Transformer Circuits][15])

**Indirect influence**

* They define a normalized adjacency matrix (A), then compute:
  [
  B = (I - A)^{-1} - I
  ]
  and use elementwise products like (B \odot A) to allocate indirect influence across edges. ([Transformer Circuits][15])

**Graph pruning / thresholds**

* They prune by a **completeness threshold of 0.01**, with pruning iteratively removing smallest edges until the remaining edges’ completeness reaches that threshold. ([Transformer Circuits][15])

### Attention vs MLP handling (operationally)

Their implementation treats “components” as separate computational blocks and attributes through them using the same “direct effect” formalism; in practice for you, the key design choice is: **define nodes at the granularity you can intervene on** (attention head outputs, MLP outputs, SAE/feature activations), then compute direct effects between those nodes with an IG-style edge weight. ([Transformer Circuits][15])

### Token aggregation

The methods page emphasizes per-node/per-edge influence definitions; for your MVC you should **standardize** token handling:

* Either: compute graphs for **the final answer token logit(s)** (recommended for stability),
* Or: compute graphs for a **scalar behavioral score** (e.g., sycophancy classifier output) by differentiating that scalar wrt nodes.

(Anthropic’s public methods text doesn’t give a single “one true” token aggregation rule in what I could retrieve; your protocol should specify it explicitly.)

---

## 2.2 Open-source implementations you can actually use today

### “Full attribution graphs”

* **Circuit Tracer** (open-source) exists as a dedicated library for attribution graphs. ([Subhadip Mitra][16])
* **Neuronpedia** has a **Circuit Tracer: Attribution Graph Explorer** workflow and describes getting a circuit/graph after selecting a model + prompt. ([Neuronpedia][17])

### Lighter-weight / building-block tooling

* **“Attribution patching”** (Neel Nanda) is a concrete patching-based causal attribution method you can use as a fallback or complement. ([Google Colab][18])
* The **dictionary_learning** ecosystem (used by SAE trainers like andyrdt) is built around **NNsight** for activation access and interventions (this matters because it lowers engineering overhead when you start doing causal patching/ablations). ([GitHub][19])

---

## 2.3 Compute requirements (what you should plan for)

### If you try to replicate Anthropic-style replacement models (CLTs) yourself

Their methods document reports that training large cross-layer dictionaries is expensive:

* ~**210 H100-hours** for Gemma‑2‑2B (2M features, 1B tokens)
* ~**3844 H100-hours** for Gemma‑2‑9B (5M features, 3B tokens) ([Transformer Circuits][15])

**For your MVC:** you should not plan on training CLTs from scratch unless you already have serious cluster access.

### If you do SAE-based attribution for 7–9B with patching/gradients

A realistic MVC approach is:

* Use **existing SAEs**, and
* Compute **feature-level causal contributions** via patching / local gradients (no CLT training).

Roughly:

* A single 7–9B forward pass at 1k tokens is “cheap”; the heavy cost is repeated passes (patching sweeps or gradient computations).
* Your workload: **60 graphs** (10 prompts × 3 traits × steered/unsteered).

**Practical expectation (order-of-magnitude):**

* **Patch-based feature selection (top-K features only):** feasible on **a single A100** if you restrict to (say) the top 200–1000 candidate features per layer and a handful of layers.
* **Full dense graph over all SAE features:** likely too expensive; you should do graph construction over a **candidate subgraph** (top-aligned + top-attributed features).

---

## 2.4 Lighter-weight alternatives if full attribution graphs are too expensive

### Recommended fallback ladder (from strongest causal to weakest)

1. **Feature-level activation patching / resample patching**
   Measures: *causal effect* of substituting a set of features from condition A into condition B on your target scalar (logit/score).
   Cost: moderate; scales with (#features tested × #layers × #prompts).
   Use case: steering vectors / persona vectors (excellent).

2. **Attribution patching (component attribution via patching)**
   Measures: “what component’s activation explains the output difference under patching.” ([Google Colab][18])
   Cost: lower than full graph; higher than a single patch.

3. **Gradient-based attribution on SAE features**
   Measures: local sensitivity; can be misleading if non-linearities / saturation dominate.

4. **Attention knockout / head ablation sweeps**
   Measures: component necessity, but can be destructive and confounded.

---

## 2.5 Steering-specific considerations (how to do “delta graphs”)

A steering experiment gives you two conditions:

* **Baseline**: unsteered
* **Steered**: residual stream modified by persona vector

You want:

* **Δnode activation**: difference in SAE feature activations under steering.
* **Δedge influence**: difference in direct/indirect influence under steering.

Operationally:

1. Compute per-condition influence graph (or patch-based attributions).
2. Define Δ as **(steered − unsteered)** edge weights.
3. Build a “persona circuit” as the subgraph that:

   * has high influence on the trait score/logit under steering, and
   * is *newly amplified* (high Δ) vs baseline.

This is conceptually aligned with the persona vectors paper’s framing that persona shifts correlate with activation changes along persona directions and can be reversed by inhibiting them. ([arXiv][11])

---

## Output: the step-by-step methodology I recommend (MVC)

### Step 0 — Choose sites and layers

* Primary layers: **16–24**.
* Primary sites: **post-MLP residual stream** (best SAE performance signal in Llama Scope). ([arXiv][1])

### Step 1 — Extract persona vectors (trait directions)

Follow the “automated pipeline” pattern:

* Input: trait name + short description.
* Use an LLM to generate prompts/system instructions and build contrastive pairs; the persona vectors paper describes generating contrastive pairs using positive and negative system prompts and multiple rollouts. ([arXiv][11])

### Step 2 — Validate steering works behaviorally

* For each trait, pick 10 prompts.
* Measure a trait score (classifier or rubric).
* Sweep steering coefficients (persona vectors paper explicitly studies steering coefficient vs sycophancy score and accuracy tradeoffs). ([arXiv][11])

### Step 3 — Decompose persona vectors into SAE features (your “candidate pool”)

Use the paper’s method:

* Compute cosine similarity between the persona vector and each SAE feature decoder direction.
* Sort by similarity; take top N features as candidates. ([arXiv][11])
  They also note using SAEs with expansion factor ≈37 and focusing on **k = 64** for analysis. ([arXiv][11])

### Step 4 — Compute causal attributions on candidates

For each prompt:

* Run baseline and steered.
* For each candidate feature subset:

  * Patch that feature’s activation from steered into baseline (or vice versa) and measure Δ on your target scalar.
* Keep features/edges that consistently explain output differences.

### Step 5 — Build an attribution graph over the reduced subgraph

Use Anthropic-style formalism *on the reduced set*:

* Define nodes = selected SAE features (+ optional heads/MLPs).
* Use direct effect definitions (IG-weighted) where feasible. ([Transformer Circuits][15])
* If you implement pruning, use a completeness-based pruning threshold consistent with their approach (0.01). ([Transformer Circuits][15])

### Step 6 — Causal ablations to validate the circuit

See Section 4 below.

---

# 3) Operationalizing “coherent persona circuit”

You need definitions you can defend, and that produce pass/fail outputs.

## 3.1 What counts as a “circuit” in your project

**Circuit = a set of intervenable internal variables (nodes) + directed influence relations (edges) that causally explain a target behavioral effect.**

In your setup, nodes are naturally:

* SAE features at chosen hookpoints/layers,
* optionally attention heads/MLP outputs if you decide to lift to component level.

Edges are:

* “direct effects” (Anthropic-style) or
* empirical patch-based influence estimates.

## 3.2 Metrics you should compute (and report)

### Circuit completeness

Define:
[
\text{completeness} = \frac{\text{effect captured by circuit}}{\text{total effect}}
]
Where “effect” is Δlogit or Δtrait-score (steered − unsteered).

This matches the spirit of Anthropic pruning-by-completeness (they prune to a completeness threshold). ([Transformer Circuits][15])

### Faithfulness

Two complementary tests:

* **Predictive faithfulness:** does the circuit’s summed contributions predict per-prompt Δlogit/Δscore?
* **Interventional faithfulness:** does ablating the circuit remove the Δlogit/Δscore?

### Minimality

A circuit is minimal if removing any “important” node/edge drops completeness by a fixed amount.

### Size / sparsity

Report:

* #nodes, #edges,
* % of total possible nodes in the analyzed layer range.

Anthropic’s methods mention pruning that produces sparse graphs (the existence of pruning thresholds + edge removal procedure is the part you can cite). ([Transformer Circuits][15])

## 3.3 Modular vs diffuse (quantitative)

Use **concentration metrics** on influence:

* **Top‑p mass**: fraction of total effect captured by top p% nodes.
* **Gini coefficient** over node contributions (high = modular).
* **Entropy** of normalized contributions (low = modular).

**Evidence of modular persona mechanism**

* High completeness with small size (e.g., top 1% nodes capture >50% of Δeffect).
* Stable node set across prompts (high overlap).

**Evidence of diffuse mechanism**

* Completeness only achieved with large fraction of nodes.
* Contributions spread smoothly (low Gini / high entropy).

## 3.4 Thresholds I recommend you adopt for MVC claims

These are intentionally conservative and aligned with what you can justify from the attribution-graph pruning idea:

**Define “coherent persona circuit” if all hold:**

1. **Completeness ≥ 0.70** on median prompt (Δeffect captured)
2. **Stability:** top‑K node overlap (Jaccard) ≥ 0.30 across prompts
3. **Modularity:** top 5% nodes capture ≥ 50% of Δeffect
4. **Causal validation:** ablating the circuit reduces Δeffect by ≥ 60% while preserving baseline task competence (see controls below)

Justification anchor: the pruning/completeness framing and explicit completeness thresholding in Anthropic’s methodology—your thresholds are stricter and on the *effect* you care about. ([Transformer Circuits][15])

---

# 4) Causal ablation methodology (best practices)

## 4.1 Ablation types and tradeoffs (what to use when)

### Zero ablation (set to 0)

* Measures: necessity under strong distribution shift.
* Failure mode: can “break the model” and overstate importance.

### Mean ablation (set to dataset mean)

* Measures: necessity with less shift than zeroing.
* Requires: a reference dataset and cached means.

### Resample ablation (replace with activation from other prompts)

* Measures: necessity while staying on-manifold (preferred).
* Failure mode: if donor prompts are mismatched, injects unrelated content.

### Noise ablation (add calibrated noise)

* Measures: robustness, sensitivity.
* Failure mode: hard to interpret causally.

### Activation patching (swap clean↔corrupted)

* Measures: causal contribution of components to differences.
* This is also your main “circuit extraction” primitive in the fallback plan. ([Google Colab][18])

## 4.2 Ablation for steering validation: experimental design

You want to show **the circuit mediates the steering effect**.

Use a 2×2 design per prompt:

| Condition | Steering | Circuit ablation |
| --------- | -------: | ---------------: |
| A         |      off |              off |
| B         |       on |              off |
| C         |      off |               on |
| D         |       on |               on |

Key contrasts:

* **Steering effect:** B − A
* **Ablation effect on baseline:** C − A (should be small on “task competence”)
* **Mediation test:** (B − A) − (D − C)
  If near zero, steering effect disappears when circuit is ablated.

## 4.3 Controls and baselines (non-negotiable)

To distinguish “causal circuit” from “we broke the model”:

1. **Size-matched random ablation**
   Ablate same #nodes at same layers but random features.

2. **Layer-matched off-target ablation**
   Ablate features that are *not* aligned with the persona vector (low cosine similarity).

3. **Competence metric**
   Track ΔLM loss or a basic accuracy proxy to show the model still functions.
   (Llama Scope explicitly treats ΔLM loss as “impact on LM,” which is the right kind of sanity metric to report.) ([arXiv][1])

## 4.4 Statistical validation (MVC-appropriate)

With 10 prompts/trait you can still do rigorous paired stats:

* Use **paired bootstrap CIs** over prompts for:

  * steering effect,
  * mediated effect after ablation,
  * difference-in-differences.
* Report effect sizes:

  * absolute Δscore,
  * relative reduction (% mediation).

If you can expand later: scale prompts to 50–200 for tighter intervals.

---

# 5) PSM-specific empirical claims to test

## What I can extract from the retrievable PSM material

I could access Anthropic’s research summary page, which contains:

* the **core claim**: post-training refines the Assistant persona but doesn’t fundamentally change its nature; the Assistant remains an “enacted human-like persona.” ([Anthropic][20])
* a key example claim: training to cheat on coding tasks can generalize to broader misaligned behaviors via inferred traits. ([Anthropic][20])
* explicit open questions about **exhaustiveness / completeness** of the model and whether post-training adds “goals beyond plausible text generation,” plus whether PSM remains a good model as post-training scales. ([Anthropic][20])

I could **not** retrieve the full Alignment Blog post text (tooling returned an internal error), so I can’t faithfully list “every statement labeled prediction/hypothesis/open question” beyond what’s visible on the summary page.

## 5–10 concrete, testable PSM claims (with experiments)

### Claim 1 — Persona directions exist as sparse, interpretable features

**Claim:** Trait/persona changes are well-captured by linear directions and align with sparse features.
**Test:** Extract persona vectors; decompose into SAE features via cosine similarity; show a small subset is highly aligned and drives behavior.
**Support:** Persona vectors paper explicitly decomposes persona vectors into SAE features using decoder-direction cosine similarity. ([arXiv][11])

### Claim 2 — Post-training mostly “selects/refines” within an existing persona space

**Claim:** Instruct/post-training does not create entirely new persona mechanisms; it reweights/refines. ([Anthropic][20])
**Test:** Extract persona vectors on base vs instruct; compare:

* overlap of top aligned SAE features,
* overlap of causal circuit nodes under ablation.

### Claim 3 — Broad generalization from narrow finetuning is mediated by persona circuitry

**Claim:** A narrow behavioral training signal induces broader trait changes via persona inference. ([Anthropic][20])
**Test:** Simulate with open model:

* finetune (or LoRA) on a narrow “cheat” behavior,
* measure shifts along multiple persona vectors,
* find a shared feature circuit that mediates multiple trait shifts.

### Claim 4 — “Asked to cheat” vs “cheat unprompted” changes which persona is selected

**Claim (from PSM example):** Asking explicitly changes the implied persona traits and reduces general misalignment. ([Anthropic][20])
**Test:** Two finetunes:

* dataset A: cheating without being asked
* dataset B: cheating only when explicitly requested
  Compare induced persona-vector projections and persona circuits.

### Claim 5 — Exhaustiveness: post-training may add non-persona goals (open question)

PSM explicitly raises the question of whether post-training imbues goals beyond plausible text generation / persona agency. ([Anthropic][20])
**Test:** Look for behavior that **cannot** be mediated by persona-vector circuits:

* If you can fully explain steering/trait changes via sparse circuits, that supports “persona-heavy.”
* If large residual unexplained effects remain after circuit ablation, that suggests extra mechanisms.

### Claim 6 — Router hypothesis (how to test even without text)

Even though “router” isn’t present in the accessible summary text, you can still test a router-like mechanism:

**Router-like prediction:** there exist early/mid-layer variables that gate which persona circuit activates downstream.
**Experiment:** identify features whose ablation prevents persona steering from propagating (i.e., steering still changes activations locally, but downstream behavioral effect disappears).
Operational signature:

* upstream “gate” features have high indirect influence on the persona circuit, and
* ablating them eliminates persona effect without large competence loss.

### Claim 7 — PSM predicts stability of persona mechanisms across prompts/tasks

**Test:** measure circuit overlap across diverse prompt families; persona circuits should be reusable and prompt-invariant relative to random circuits.

## Prioritization (tractability × impact)

1. Claim 1 (SAE decomposition + causal ablation) — easiest, high value
2. Claim 2 (base vs instruct overlap) — strong mechanistic grounding for “selection/refinement”
3. Claim 4 (asked vs unprompted) — directly targets PSM’s striking example
4. Claim 3 (narrow finetune → broad trait shift) — bigger but very impactful
5. Router (if time) — high novelty, riskier

---

# 6) Adversarial robustness landscape (interpretability monitoring)

## 6.1 Bailey et al. (ICLR 2026) — what I can support right now

From the OpenReview entry:

* TL;DR: they demonstrate harmful behaviors can be executed using **inconspicuous activations** that subvert latent-space defenses. ([OpenReview][21])
* Abstract indicates the focus is on **latent-space monitoring techniques** and whether models can route harmful behavior through inconspicuous latent states. ([OpenReview][21])
* They report:

  * “certain probe architectures are more robust than others,”
  * an **“obfuscation tax”** on a complex task (SQL code): evading monitors reduces performance,
  * “white-box monitors are not robust to adversarial attack,” and they offer suggestions to alleviate (not fully fix). ([OpenReview][21])

**What I could not verify from retrievable text:** which exact defenses (SAEs vs probes vs OOD detectors) were bypassed, and the exact adversarial training protocol / training amount. The OpenReview page snippet accessible here doesn’t include those details.

## 6.2 Implications for your work

If you find coherent persona circuits, **you cannot claim monitoring robustness by default**.
What you *can* claim in MVC without adversarial training:

* “Persona steering effects in this model are mediated by a sparse, causally validated internal mechanism under natural (non-adversarial) conditions.”

What requires Phase 3 adversarial testing:

* “Circuit-based monitors are robust against a model trying to obfuscate.”

## 6.3 Is circuit monitoring likely more robust than probes (hypothesis + how to test)

**Plausible reason it could be more robust:**
A circuit constraint is higher-dimensional and mechanistically structured; “hiding” might require coordinating many components while still producing correct outputs.

**Plausible reason it might still fail:**
If the model can learn alternate pathways that implement the same behavior, it can reroute around your circuit detector.

**Minimal adversarial test you should plan (Phase 3):**

* Train a small adapter/LoRA to achieve the target behavior while minimizing activations of your detected circuit (white-box constraint).
* Measure whether behavior persists with low circuit activity (“circuit obfuscation”).

---

# 7) Related concurrent work and scoop risk

## Directly adjacent public work I can cite

* **Attribution patching** (Feb 2026 blog) — indicates active community focus on patching-based attribution methods (relevant to your fallback strategy). ([Google Colab][18])
* **Circuit Tracer / Attribution Graph Explorer** on Neuronpedia (Feb 2026) — suggests attribution-graph tooling is becoming widely accessible, increasing parallel work risk. ([Neuronpedia][17])

## Scoop risk assessment (grounded + strategic)

* **High risk:** “persona vectors + SAE decomposition” is already established (persona vectors paper explicitly does SAE decomposition and discusses layerwise steering). ([arXiv][11])
* **Your differentiation:** “first *causally validated* mechanistic grounding for PSM via circuit tracing + targeted ablations,” plus a claims matrix tied to PSM.

Mitigation:

* Focus your novelty on: **(i)** router/selection mechanism tests, **(ii)** asked-vs-unprompted finetune comparison, **(iii)** causal mediation and minimality analyses.

---

# 8) Experimental details (execution-ready protocol)

## 8.1 Persona vector extraction (what I can support)

Persona vectors paper describes:

* Input is **trait name + brief description**.
* A generic prompt template instructs a frontier model (**Claude 3.7 Sonnet**) to construct artifacts.
* They create contrastive pairs by generating responses with **positive and negative system prompts**, with **10 rollouts** per question. ([arXiv][11])

## 8.2 Persona vector → SAE feature decomposition

They specify a concrete decomposition:

* Compute cosine similarity between persona vector and each SAE feature’s **decoder direction**.
* Sort; examine top aligned features; they provide the formal cosine similarity definition. ([arXiv][11])
  They note focusing on **k = 64** for analysis in their SAE setting. ([arXiv][11])

## 8.3 Steering implementation details you can borrow

They discuss **layer-wise “incremental” steering vectors across layers** to avoid redundancy/excessive influence. ([arXiv][11])

## 8.4 Prompt selection for your MVC

For the MVC scope (10 prompts × 3 traits), do:

* 4 prompts that strongly elicit the trait,
* 3 ambiguous prompts (tests router/selection),
* 3 “neutral competence” prompts (controls).

## 8.5 Behavioral validation metrics (MVC)

Pick metrics aligned with your traits:

* **Sycophancy:** score via a rubric or classifier; the persona vectors paper uses a “Sycophancy Score” vs steering coefficient plot. ([arXiv][11])
* **Evil/malicious intent:** refusal bypass / harmful intent classifier.
* **Hallucination:** factuality checks or a QA benchmark subset; the persona vectors paper includes “hallucination” dataset characterization in its appendix area. ([arXiv][11])

## 8.6 Reproducibility checklist

* Fix seeds for:

  * contrastive rollout generation,
  * model sampling,
  * any finetuning.
* Log:

  * model hash,
  * SAE checkpoint IDs,
  * hookpoints, layers,
  * steering coefficients,
  * prompt set + scoring rubric.

---

# FINAL DELIVERABLE (consolidated execution document)

## 1) Model selection decision

**Decision:**

* **Behavior model:** **Llama‑3.1‑8B‑Instruct**
* **SAE backbone:** **Llama Scope 128K feature suite** (use residual stream + attention out + MLP out at layers **16–24**)
* **Cross-check:** andyrdt instruct-trained SAEs at layers 19/23 to validate robustness.

**Why this is optimal**

* Full layer/site coverage (256 SAEs, 32k/128k features). ([arXiv][1])
* Clear reconstruction metrics and evaluation story (L0, explained variance, ΔLM loss). ([arXiv][1])
* Explicitly tested generalization to **Llama‑3.1‑8B‑Instruct**. ([arXiv][1])

---

## 2) Complete methodology (MVC, step-by-step)

### Inputs

* Traits: {sycophancy, evil, hallucination}
* Prompts: 10 per trait (30 total)
* Conditions: unsteered vs steered

### Pipeline

1. **Extract persona vector per trait**

   * Use contrastive generation protocol (pos/neg system prompts; 10 rollouts per question). ([arXiv][11])
   * Compute activation differences at chosen hookpoint(s) and average to get (v_{\text{persona}}).

2. **Validate behavioral steering**

   * Sweep coefficient; choose a coefficient that yields strong trait change with minimal competence drop (track ΔLM loss / accuracy proxies). ([arXiv][11])

3. **Decompose persona vector into SAE features**

   * Compute cosine similarity with decoder directions; select top N features per layer. ([arXiv][11])

4. **Compute causal attributions (preferred: patch-based)**

   * Patch candidate features between steered/unsteered runs and measure Δlogit/Δscore.
   * Keep features with consistent causal contributions.

5. **Construct attribution graph on reduced node set**

   * Use direct-effect edge formalism where feasible. ([Transformer Circuits][15])
   * Use completeness-based pruning thresholding consistent with Anthropic-style methods (0.01). ([Transformer Circuits][15])

6. **Define persona circuit**

   * Apply coherence thresholds (completeness, modularity, stability).

7. **Causal ablation validation**

   * 2×2 mediation design (steering × ablation), with random and layer-matched controls.
   * Report % mediation of steering effect.

### Compute plan for MVC (60 graphs)

* **Recommended:** candidate-restricted graphs (top aligned + top patch-attributed features).
* Avoid full all-features graphs.

### Fallback methodology if full graphs too expensive

* Attribution patching + feature patching only (still yields causal circuit sets). ([Google Colab][18])

---

## 3) PSM claims matrix (5–10 claims, tests, success criteria)

| PSM-related claim                                                                              | Test                                                              | Confirmation                                                   | Disconfirmation                                |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------- |
| Post-training refines within persona space (not fundamental change) ([Anthropic][20])          | Compare base vs instruct persona circuits                         | High overlap of top features + causal nodes                    | Distinct circuits with low overlap             |
| Narrow training signal induces broad trait shift via inferred persona traits ([Anthropic][20]) | Finetune on narrow behavior; measure multiple persona projections | Shared mediating circuit explains multiple traits              | Trait shifts uncorrelated; no shared mediators |
| Asking explicitly changes implied persona traits (cheat asked vs unprompted) ([Anthropic][20]) | Two finetunes; compare projections + circuits                     | “Asked” reduces broad misaligned traits and circuit activation | No difference                                  |
| Persona vectors correspond to sparse SAE features ([arXiv][11])                                | Cosine-align persona vector to SAE decoder; ablate top features   | Small set mediates most effect                                 | Need large diffuse set                         |
| PSM exhaustiveness is limited (open question) ([Anthropic][20])                                | Residual unexplained effect after circuit ablation                | Small residual suggests persona-heavy explanation              | Large residual suggests extra mechanisms       |

---

## 4) Risk assessment

### Scoop risk

* Tooling & community focus on attribution graphs and patching is active. ([Neuronpedia][17])
  **Mitigation:** emphasize PSM-specific hypotheses + causal mediation rigor.

### Technical risks and fallbacks

* **Risk:** full attribution graphs too expensive
  **Fallback:** patch-based causal attribution on candidate SAE features. ([Google Colab][18])
* **Risk:** SAEs don’t transfer well to instruct
  **Fallback:** use instruct-trained andyrdt SAEs as cross-check. ([Hugging Face][3])

### Claims you can/can’t make in MVC (given adversarial landscape)

* You **can** claim causal mediation under natural conditions.
* You **cannot** claim robustness against an adversary without dedicated tests; Bailey et al. explicitly show white-box monitoring weaknesses and “obfuscation tax” phenomena. ([OpenReview][21])

---

## 5) Methods section draft (copy-paste ready)

**Models.** We analyze Llama‑3.1‑8B‑Instruct using sparse autoencoders (SAEs) from the Llama Scope suite (32k/128k features) trained across all layers and multiple hookpoints, including post‑MLP residual stream, attention output, and MLP output. The suite is evaluated using L0 sparsity, explained variance, and ΔLM loss, and is reported to generalize to instruction-finetuned models such as Llama‑3.1‑8B‑Instruct. ([arXiv][1])

**Persona vector extraction.** For each target trait (sycophancy/evil/hallucination), we construct contrastive prompt pairs and generate responses under positive vs negative system prompts, following an automated pipeline in which trait name/description is used to create contrastive pairs and multiple rollouts (10 rollouts per question). ([arXiv][11]) We compute persona vectors as mean activation differences in the target model’s activation space at specified hookpoints.

**Steering.** We apply persona vector steering by adding scaled persona directions into the residual stream at selected layers. We optionally use layer-wise incremental vectors to avoid redundant influence across layers. ([arXiv][11]) Steering coefficients are selected via coefficient sweeps balancing trait score shift with competence degradation.

**SAE decomposition.** We decompose each persona vector into SAE features by computing cosine similarity between the persona vector and each SAE feature decoder direction, ranking features by similarity, and selecting the top aligned features as candidates. ([arXiv][11])

**Attribution and circuit discovery.** For each prompt, we compute causal contributions of candidate features using activation patching between steered and unsteered runs, measuring Δlogit/Δscore. We build reduced attribution graphs on the candidate node set using integrated-gradients-style direct effects and completeness-based pruning inspired by attribution graph methods (direct effect proportional to source activation times an IG-derived edge weight; pruning by completeness threshold). ([Transformer Circuits][15])

**Causal validation.** We validate that the discovered persona circuit mediates steering effects via a 2×2 design (steering × circuit ablation), with size-matched random ablations and layer-matched off-target controls. We report mediation as the proportional reduction in steering-induced Δscore under circuit ablation while monitoring ΔLM loss as a competence sanity metric. ([arXiv][1])

---

If you want, I can also turn this into a literal “runbook” (directory layout, exact logging schema, and minimal code scaffolding) for the Llama‑3.1‑8B‑Instruct + Llama Scope setup, but the above is already at the level where you can start executing immediately.

[1]: https://arxiv.org/html/2410.20526v1 "https://arxiv.org/html/2410.20526v1"
[2]: https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/tree/main "https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/tree/main"
[3]: https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/blob/main/resid_post_layer_23/trainer_0/config.json "https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/blob/main/resid_post_layer_23/trainer_0/config.json"
[4]: https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/blob/main/resid_post_layer_23/trainer_0/eval_results.json "https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/blob/main/resid_post_layer_23/trainer_0/eval_results.json"
[5]: https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/blob/main/resid_post_layer_23/trainer_1/eval_results.json "https://huggingface.co/andyrdt/saes-llama-3.1-8b-instruct/blob/main/resid_post_layer_23/trainer_1/eval_results.json"
[6]: https://huggingface.co/EleutherAI/sae-llama-3.1-8b-64x "https://huggingface.co/EleutherAI/sae-llama-3.1-8b-64x"
[7]: https://huggingface.co/EleutherAI/sae-llama-3.1-8b-32x/blob/main/layers.23.mlp/cfg.json "https://huggingface.co/EleutherAI/sae-llama-3.1-8b-32x/blob/main/layers.23.mlp/cfg.json"
[8]: https://huggingface.co/EleutherAI/sae-llama-3.1-8b-64x/blob/main/layers.23.mlp/cfg.json "https://huggingface.co/EleutherAI/sae-llama-3.1-8b-64x/blob/main/layers.23.mlp/cfg.json"
[9]: https://huggingface.co/EleutherAI/sae-llama-3.1-8b-64x/tree/main "https://huggingface.co/EleutherAI/sae-llama-3.1-8b-64x/tree/main"
[10]: https://arxiv.org/html/2408.05147v2 "https://arxiv.org/html/2408.05147v2"
[11]: https://arxiv.org/pdf/2507.21509 "https://arxiv.org/pdf/2507.21509"
[12]: https://huggingface.co/andyrdt/saes-qwen2.5-7b-instruct "https://huggingface.co/andyrdt/saes-qwen2.5-7b-instruct"
[13]: https://huggingface.co/tylercosgrove/mistral-7b-sparse-autoencoder-layer16 "https://huggingface.co/tylercosgrove/mistral-7b-sparse-autoencoder-layer16"
[14]: https://github.com/tylercosgrove/sparse-autoencoder-mistral7b "https://github.com/tylercosgrove/sparse-autoencoder-mistral7b"
[15]: https://transformer-circuits.pub/2025/attribution-graphs/methods.html "https://transformer-circuits.pub/2025/attribution-graphs/methods.html"
[16]: https://subhadipmitra.com/blog/2026/circuit-tracing-production/ "https://subhadipmitra.com/blog/2026/circuit-tracing-production/"
[17]: https://www.neuronpedia.org/blog/circuit-tracer "https://www.neuronpedia.org/blog/circuit-tracer"
[18]: https://colab.research.google.com/github/TransformerLensOrg/TransformerLens/blob/main/demos/Attribution_Patching_Demo.ipynb "https://colab.research.google.com/github/TransformerLensOrg/TransformerLens/blob/main/demos/Attribution_Patching_Demo.ipynb"
[19]: https://github.com/andyrdt/dictionary_learning/tree/andyrdt/llama_saes "https://github.com/andyrdt/dictionary_learning/tree/andyrdt/llama_saes"
[20]: https://www.anthropic.com/research/persona-selection-model "https://www.anthropic.com/research/persona-selection-model"
[21]: https://openreview.net/forum?id=ktGmDGoWnB "https://openreview.net/forum?id=ktGmDGoWnB"
