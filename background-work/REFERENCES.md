# ABOUTME: Curated paper library for the persona-circuits experiment.
# ABOUTME: All cited papers with URLs, priority tiers, when-to-consult guidance, and tools.

# Persona Circuits — Reference Library

Single source of truth for all papers, tools, and resources referenced in `persona-circuits-proposal.md` and related background work.

**How to use:**
1. When blocked on a methodology — find the relevant paper, fetch its URL, read it
2. When writing the paper — use "Key Relevance" column for related-work framing
3. Before searching the web for a cited paper — check here first
4. If a URL is marked `? unknown` — search arXiv with the title, then update this file and log in DECISIONS.md: `[date] Verified URL for [paper]: [arXiv ID]`

**URL status legend:**
- `✓ confirmed` — URL verified from external guidance or proposal text
- `~ likely` — best estimate; verify before citing
- `? unknown` — no URL available; search arXiv with title

---

## Tier 1 — Essential (read fully before starting any experiment work)

These papers define the theoretical framework, extraction methodology, critical methodological constraint on ablation, and the character-simulator framing that underpins PSM. Do not start Week 1 without internalizing them.

| # | Paper | URL | Status | What to extract |
|---|-------|-----|--------|-----------------|
| 1 | Marks, S., Lindsey, J., & Olah, C. (2026). **The Persona Selection Model: Why AI Assistants Might Behave Like People.** Anthropic Research. | https://alignment.anthropic.com/2026/psm/ | ✓ confirmed | The theory you are testing. Read §2–§3 for the selection mechanism claim; §5 for mechanistic predictions your circuits must match. |
| 2 | Chen, A., et al. (2025). **Persona Vectors: Monitoring and Controlling Character Traits in Large Language Models.** Anthropic Research. | https://arxiv.org/abs/2507.21509 | ✓ confirmed | The extraction pipeline you are replicating. Read: contrastive prompt generation, mean-difference extraction, behavioral validation protocol, SAE decomposition appendix. |
| 3 | Lindsey, J., et al. (2025). **Circuit Tracing: Revealing Computational Graphs in Language Models.** Anthropic Research. (Also known as: "On the Biology of a Large Language Model" / "Biology paper") | https://transformer-circuits.pub/2025/attribution-graphs/index.html | ~ likely — verify on transformer-circuits.pub | The attribution algorithm you will use. Read the algorithm description, worked examples, and what "circuit" means operationally. Proposal §5.2 is derived from this paper. |
| 4 | Li, M. & Janson, L. (2024). **On the Validity of Ablation Studies for Neural Network Interpretability.** NeurIPS 2024. | ? unknown — search arXiv / NeurIPS 2024 proceedings | **CRITICAL methodological constraint:** ablation-as-mean-replacement overestimates feature importance by ~9×. This is why the proposal requires resample ablation as the primary method. Read before implementing any ablation. |
| 5 | Shanahan, M., McDonell, K., & Reynolds, L. (2023). **Role Play with Large Language Models.** Nature. | https://www.nature.com/articles/s41586-023-06647-8 | ✓ confirmed — local copy: `papers/shanahan2023_role_play_llm.md` | **Theoretical framing:** LLMs as non-deterministic simulators of an infinity of characters; the assistant is one character. Foundational for PSM. Read §2 (simulacra/simulation) and §3 (base character). |
| 6 | Andreas, J. (2022). **Language Models as Agent Models.** arXiv:2212.01681. MIT CSAIL. | https://arxiv.org/abs/2212.01681 | ✓ confirmed — local copy: `papers/andreas2022_lm_agent_models.md` | Why LMs trained on text can learn agent-internal representations (goals, beliefs, plans) even without direct access to agent state. Theoretical grounding for why persona circuits might exist at all. |

---

## Tier 2 — Important (read relevant sections when entering each phase)

### Circuit Analysis Methodology (Week 4–5)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 13 | Conmy, A., et al. (2023). **Towards Automated Circuit Discovery for Mechanistic Interpretability (ACDC).** | https://arxiv.org/abs/2304.14997 | ✓ confirmed | Week 4–5 circuit discovery; ACDC is the algorithmic precursor to the attribution approach |
| 14 | Wang, K., et al. (2022). **Interpretability in the Wild: A Circuit for Indirect Object Identification in GPT-2 Small.** | https://arxiv.org/abs/2211.00593 | ✓ confirmed | Faithfulness standard: ≥80% performance preservation. The IOI circuit is the benchmark for what a "real circuit" looks like. |
| 15 | Campbell, J., et al. (2024). **Localizing Lying in Llama: Understanding Instructed Dishonesty on True-False Questions via Internal Model States.** | ? unknown — search arXiv | Week 4–5 if circuit is unexpectedly large or small; reference: found 46 heads (<1% of model) for lying |

### SAE Infrastructure (Week 1–3)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 17 | He, Z., et al. (2024). **LlamaScope: Extracting Millions of Features from Llama-3.1-8B.** Fudan NLP / OpenMOSS. | https://arxiv.org/abs/2410.20526 | ~ likely | Week 1 SAE loading; Week 3 decomposition. GitHub: `fnlp/Llama-Scope` |
| 16 | Lieberum, T., et al. (2024). **Gemma Scope: Open Sparse Autoencoders Everywhere All At Once.** Google DeepMind. | https://arxiv.org/abs/2408.05147 | ✓ confirmed | Week 6 Gemma validation |
| 18 | Bricken, T., et al. (2023). **Towards Monosemanticity: Decomposing Language Models With Dictionary Learning.** Anthropic Research. | https://transformer-circuits.pub/2023/monosemantic-features/index.html | ✓ confirmed | Background for why SAE features are the right unit of analysis; cite in intro |

### Steering and Extraction Methodology (Week 2)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 9 | Zou, A., et al. (2023). **Representation Engineering: A Top-Down Approach to AI Transparency.** ICLR 2024. | https://arxiv.org/abs/2310.01405 | ✓ confirmed | Historical foundation for contrastive extraction; cite in related work |
| 11 | Rimsky, N., et al. (2024). **Steering Llama 2 via Contrastive Activation Addition.** ACL 2024. | https://arxiv.org/abs/2312.06681 | ✓ confirmed | Most direct precursor to Persona Vectors; dose-response findings |
| 10 | Turner, A., et al. (2024). **Activation Addition: Steering Language Models Without Optimization.** AAAI. | https://arxiv.org/abs/2308.10248 | ✓ confirmed | Background on steering; read if vector quality is poor |

### Behavioral Evaluation and Safety Context (Week 2)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 6 | Wang, Y., et al. (2025). **Emergent Misalignment: Narrow Finetuning Can Produce Broadly Misaligned LLMs.** OpenAI. | https://arxiv.org/abs/2502.17424 | ~ likely | Week 2 evil/toxicity trait design; key precedent for SAE decomposition of persona features |
| 4 | Greenblatt, R., et al. (2024). **Alignment Faking in Large Language Models.** Anthropic Research. | https://arxiv.org/abs/2412.14093 | ~ likely | Context for why the traits matter; cite in motivation |
| 7 | MacDiarmid, M., et al. (2025). **Poser: A Benchmark for Detecting Alignment-Faking Language Models.** | ? unknown — search arXiv | Week 2 behavioral validation design; noise injection baseline reference |

---

## Tier 3 — Background / Consult as Needed

### Adversarial Robustness (Week 7–8 and discussion)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 8 | Bailey, L., et al. (2026). **Obfuscated Activations Bypass LLM Latent-Space Defenses.** ICLR 2026. | ? unknown — search arXiv / ICLR 2026 proceedings | Week 7–8 ablation robustness; §14 future direction on adversarial evaluation; "obfuscation tax" concept |

### Identifiability and Representation Theory (as needed)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 20 | Venkatesh, S., et al. (2026). **On the Non-Identifiability of Steering Vectors in Language Models.** | ? unknown — search arXiv | If extraction yields non-unique vectors; §11 cites the sparsity-recovery result as a mitigation |
| 21 | Park, K., et al. (2024). **The Linear Representation Hypothesis and the Geometry of Large Language Models.** | https://arxiv.org/abs/2311.03658 | ~ likely | Theoretical justification for mean-difference vectors; cite in methodology |
| 22 | Bhandari, A., et al. (2026). **Geometric Constraints on Multi-Trait Steering in Language Models.** | https://arxiv.org/abs/2602.15847 | ✓ confirmed (in proposal) | Week 5 cross-persona analysis; if shared features observed across traits, this explains the geometric mechanism |
| 23 | Yang, H., et al. (2024). **Separating Inference-Time and Training-Time Representations.** | https://arxiv.org/abs/2410.10863 | ✓ confirmed (in proposal) | Week 3 SAE decomposition; timescale distinction (SAEs = training-time traits, RepE = prompt-time) |

### Persona Space Structure (discussion / Week 5)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 24 | Lu, X., et al. (2026). **The Assistant Axis: Characterizing the Principal Component of AI Assistant Persona Space.** | https://arxiv.org/abs/2601.10387 | ✓ confirmed | Week 5 cross-persona analysis; also relevant if adding an `assistant_likeness` screening lane because it directly targets persona-space structure rather than a single narrow trait |

### SAE Limitations (Week 3 if SAE decomposition is weak)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 19 | Kantamneni, R., et al. (2025). **What Do Sparse Autoencoders Miss? A Study of Safety-Relevant Information Loss.** ICML 2025. | ? unknown — search arXiv / ICML 2025 | Week 3 if SAE decomposition yields weak causal features; proposal uses this to pre-register the possibility of SAE failure |

### Theoretical Foundations (intro / discussion writing)

| # | Paper | URL | Status | When to consult |
|---|-------|-----|--------|-----------------|
| 5 | Elhage, N., et al. (2022). **Toy Models of Superposition.** Anthropic Research. | https://transformer-circuits.pub/2022/toy_model/index.html | ✓ confirmed | Why SAE features are the right unit; cite in intro |
| 30 | Hewitt, J. (2026). **How the Residual Stream is (Not) Linear.** | https://www.cs.columbia.edu/~johnhew/residual-stream-isnt-linear.html | ✓ confirmed — local copy: `papers/hewitt2026_residual_stream_isnt_linear.md` | When discussing additive steering assumptions, extraction-position sensitivity, or why empirical validation (not architectural linearity claims) is required |
| 31 | Chen, Z., et al. (2026). **Sycophancy Hides Linearly in the Attention Heads.** | https://arxiv.org/abs/2601.16644 | ✓ confirmed | Week 2 and Week 4–5 if keeping sycophancy as an anchor lane; useful for head-level localization and for arguing that sycophancy remains a strong mechanistic target |
| 32 | Zou, Y., et al. (2026). **LieCraft: A Multi-Agent Framework for Evaluating Deceptive Capabilities in Language Models.** | https://arxiv.org/abs/2603.06874 | ✓ confirmed | Week 2 if adding honesty / lying / deception screening lanes; useful as an evaluation reference for deception-family held-out and external smoke tests |
| 33 | Prieto, L., et al. (2026). **From Data Statistics to Feature Geometry: How Correlations Shape Superposition.** | https://arxiv.org/abs/2603.09972 | ✓ confirmed | Future Stage 2 / Stage 5 interpretation only: consult if clustered/shared feature geometry becomes central to the argument, or if adding a geometry-only sidecar diagnostic. Do not treat this as a reason to widen scope or change the pre-registered causal thresholds. Repo: `LucasPrietoAl/correlations-feature-geometry` |

---

## Tier 4 — Background Surveys and Context (Week 9–10 / paper writing)

Only needed when writing the introduction, related work, or broader context sections.

| # | Paper | URL | Status | Notes |
|---|-------|-----|--------|-------|
| 25 | Tseng, Y.-M., et al. (2024). **Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization.** EMNLP 2024 Findings. | https://aclanthology.org/2024.findings-emnlp.969/ | ✓ confirmed | Comprehensive taxonomy; role-playing vs personalization distinction |
| 26 | Salminen, J., et al. (2021). **A Survey of 15 Years of Data-Driven Persona Development.** IJHCI. | DOI: 10.1080/10447318.2021.1908670 | ✓ confirmed | Historical context for HCI persona research |
| 27 | (Survey) **A Survey of Personality, Persona, and Profile in Conversational Agents.** | https://arxiv.org/abs/2401.00609 | ✓ confirmed | Defines the personality vs persona vs profile distinction |
| 28 | (SCOPE) **The Need for a Socially-Grounded Persona Framework for User Simulation.** | https://arxiv.org/abs/2601.07110 | ✓ confirmed | SCOPE framework; sociopsychological persona construction |
| 29 | Vaswani, A., et al. (2017). **Attention Is All You Need.** NeurIPS 2017. | https://arxiv.org/abs/1706.03762 | ✓ confirmed | Only cite if the paper requires a transformer foundation citation |

---

## Tools and Libraries

### Interpretability

| Tool | Description | URL |
|------|-------------|-----|
| TransformerLens | Mechanistic interpretability library — `HookedTransformer` | https://github.com/neelnanda-io/TransformerLens |
| SAELens | SAE loading and analysis — `SAE.from_pretrained()` | https://github.com/jbloomAus/SAELens |
| circuit-tracer | Attribution graphs (CLT-based) — NOT on PyPI, install from source | https://github.com/safety-research/circuit-tracer |
| NNsight | Neural network inspection and intervention | https://github.com/ndif-team/nnsight |
| Neuronpedia | SAE feature visualization and interpretation (browser) | https://neuronpedia.org |

**Note:** `pyvene` was removed from the dependency list in proposal v2.4 — do not use it.

### Compute and Logging

| Tool | Description | URL |
|------|-------------|-----|
| Modal | Serverless GPU compute (A100-80GB) | https://modal.com |
| Weights & Biases | Experiment tracking — project: `persona-circuits`, entity: `sohailm` | https://wandb.ai/sohailm/persona-circuits |

---

## SAE Checkpoint Quick Reference

| SAE Source | Model | SAELens release key | Notes |
|------------|-------|---------------------|-------|
| Llama Scope | Llama 3.1 8B (Base) | `llama_scope_lxr_32x` | `sae_id`: `l{N}r_32x` — primary SAEs |
| andyrdt | Llama 3.1 8B-Instruct | `llama-3.1-8b-instruct-andyrdt` | `sae_id`: `resid_post_layer_{N}_trainer_1` — available layers: 3,7,11,15,19,23,27 only |
| GemmaScope | Gemma 2 2B | `gemma-scope-2b-pt-res-canonical` | `sae_id`: `layer_{N}/width_16k/canonical` |
| EleutherAI | Llama 3.1 8B | `EleutherAI/sae-llama-3.1-8b-32x` | Cross-check only |

**See proposal Appendix B for full loading code and Appendix G.3 for the `HookedSAETransformer` pattern.**

---

## Curated Resource Collections

| Resource | Description | URL |
|----------|-------------|-----|
| Transformer Circuits Thread | Anthropic's interpretability research — primary source for circuit tracing papers | https://transformer-circuits.pub |
| PersonaPaper (Sahandfer) | Curated list of persona-based dialogue papers | https://github.com/Sahandfer/PersonaPaper |
| PersonaLLM-Survey (MiuLab) | Official repo for "Two Tales of Persona" survey | https://github.com/MiuLab/PersonaLLM-Survey |
| Persona Research (APG team) | Zotero collection with 327+ items | https://www.zotero.org/groups/2331485/persona_research_apg_team |
| Alignment Forum | Primary venue for Anthropic safety research discussion | https://alignmentforum.org |
| LessWrong | Broader AI safety community — useful for preprint discussion | https://lesswrong.com |

---

## Key Authors to Track

Monitor for new preprints (scoop risk and collaboration opportunities):

| Author | Affiliation | Relevant Work |
|--------|-------------|---------------|
| Samuel Marks | Anthropic | PSM, persona vectors |
| Jack Lindsey | Anthropic | Circuit tracing, persona vectors |
| Chris Olah | Anthropic | PSM, interpretability leadership |
| Adam Chen | Anthropic | Persona vectors |
| Ryan Greenblatt | Redwood Research / Anthropic | Alignment faking |
| Monte MacDiarmid | Anthropic | Poser benchmark |
| Neel Nanda | Google DeepMind | TransformerLens, mechanistic interpretability |
| Arthur Conmy | Google DeepMind | ACDC, circuit discovery |
| Joseph Bloom | Independent | SAELens |

---

## BibTeX Templates

```bibtex
@article{marks2026psm,
  title={The Persona Selection Model: Why AI Assistants Might Behave Like People},
  author={Marks, Samuel and Lindsey, Jack and Olah, Chris},
  journal={Anthropic Research},
  year={2026},
  url={https://alignment.anthropic.com/2026/psm/}
}

@article{chen2025persona,
  title={Persona Vectors: Monitoring and Controlling Character Traits in Large Language Models},
  author={Chen, Adam and others},
  journal={Anthropic Research},
  year={2025},
  eprint={2507.21509},
  archivePrefix={arXiv}
}

@article{lindsey2025circuits,
  title={Circuit Tracing: Revealing Computational Graphs in Language Models},
  author={Lindsey, Jack and others},
  journal={Anthropic Research},
  year={2025},
  url={https://transformer-circuits.pub/2025/attribution-graphs/index.html}
}

@inproceedings{li2024ablation,
  title={On the Validity of Ablation Studies for Neural Network Interpretability},
  author={Li, Michael and Janson, Lucas},
  booktitle={NeurIPS},
  year={2024}
}

@article{lieberum2024gemma,
  title={Gemma Scope: Open Sparse Autoencoders Everywhere All At Once},
  author={Lieberum, Tom and others},
  journal={arXiv preprint arXiv:2408.05147},
  year={2024}
}

@inproceedings{conmy2023acdc,
  title={Towards Automated Circuit Discovery for Mechanistic Interpretability},
  author={Conmy, Arthur and others},
  booktitle={NeurIPS},
  year={2023},
  eprint={2304.14997},
  archivePrefix={arXiv}
}

@article{wang2022ioi,
  title={Interpretability in the Wild: A Circuit for Indirect Object Identification in GPT-2 Small},
  author={Wang, Kevin and others},
  journal={arXiv preprint arXiv:2211.00593},
  year={2022}
}

@article{bricken2023monosemanticity,
  title={Towards Monosemanticity: Decomposing Language Models With Dictionary Learning},
  author={Bricken, Trenton and others},
  journal={Anthropic Research},
  year={2023},
  url={https://transformer-circuits.pub/2023/monosemantic-features/index.html}
}

@inproceedings{tseng2024twotales,
  title={Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization},
  author={Tseng, Yu-Min and Huang, Yu-Chao and Hsiao, Teng-Yun and Chen, Wei-Lin
          and Huang, Chao-Wei and Meng, Yu and Chen, Yun-Nung},
  booktitle={Findings of EMNLP},
  year={2024},
  url={https://aclanthology.org/2024.findings-emnlp.969/}
}
```

---

## Quick Reference: Key Thresholds

| Metric | Threshold | Source |
|--------|-----------|--------|
| Necessity | ≥80% reduction | Proposal (conservative) |
| Sufficiency | ≥60% preservation | Wang et al. IOI circuit |
| Minimality | <10% of features | Circuit literature standard |
| Stability (Jaccard) | ≥0.30 | Proposal |
| Significance | p < 0.01 | Conservative |
| Effect size | A₁₂ > 0.71, Cohen's d > 0.8 | Vargha-Delaney / Cohen |
| Gini (modular) | ≥0.50 | Proposal |

| Model | Optimal Persona Layers | Source |
|-------|------------------------|--------|
| Llama 3.1 8B | 11–16 (~35–50% depth) | Chen et al. |
| Gemma 2 2B | Layers available in GemmaScope canonical release | GemmaScope paper |

---

*This is a living document. When you verify a `? unknown` URL or discover a new relevant paper during execution, update this file and log the change in DECISIONS.md.*
