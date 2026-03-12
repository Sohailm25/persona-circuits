# Matched Layer-12 Repair-Model Training Plan

## Objective
Train a single-layer activation repair model aligned to the current claim lane:

- source model: `meta-llama/Llama-3.1-8B-Instruct`
- hook: `resid_post`
- layer: `12`
- primary intervention surface: `response_last`

The current released GLP checkpoint is diagnostic-only and misaligned. The sidecar artifacts show:

- `model_match = false`
- `layer_match = false`
- strong baseline-control distortion
- large negative local-validity deltas under GLP postprocessing

That makes further scaling of the released checkpoint a poor use of time.

## Core Hypothesis
Our raw persona and circuit edits likely contain some real semantic signal, but the released repair prior is trained on the wrong activation manifold. A matched repair model may preserve prompt-specific information instead of snapping states toward a generic high-density region.

## Training Target
Train a **single-layer** repair model first.

Why single-layer:

- it matches the current claim layer directly
- it removes the layer-conditioning confound
- it is the closest analogue to the paper's main single-layer checkpoints
- it is operationally simpler to evaluate and debug than a multi-layer model

Use the config template:

- [train_glp_llama31_8b_instruct_layer12.yaml](/Users/sohailmohammad/braindstorms/persona-circuits/configs/train_glp_llama31_8b_instruct_layer12.yaml)

## Data Requirements
The upstream trainer expects a memmap dataset directory with:

- `dtype.txt`
- `data_indices.npy`
- one or more shard files `data_0000.npy`, `data_0001.npy`, ...
- `rep_statistics.pt`

Each indexed sample must be a single activation vector of shape `(4096,)`.

Important upstream gotcha:

- do **not** name the dataset folder with the pattern `layer_<N>`
- the trainer uses that pattern to infer multi-layer mode
- for a single-layer run, prefer names like `glp_llama31_8b_instruct_l12_chat_1m`

## Data Distribution
Do not train on base-model web text activations. That recreates the failure mode.

The export set should instead mix:

1. generic instruct-style chat prompts
2. assistant response prefixes from neutral/non-persona tasks
3. a small held-out slice of persona-adjacent prompts used only for post-training evaluation, not export

The repair model should learn the manifold of **instruction-following residual states**, not generic completion states.

## Export Plan
Build a dedicated export step for natural layer-12 `resid_post` activations.

Recommended export shape:

1. tokenize instruct-style prompts with the same chat formatting used in the main pipeline
2. run the model without intervention
3. capture `blocks.12.hook_resid_post`
4. save one vector per token position, or only the response-last token if we choose to specialize
5. compute `rep_statistics.pt` from the exported vectors

Decision:

- first export should be **all natural response tokens**
- not intervention outputs
- not persona-steered outputs

Reason:

- the repair model should estimate the unedited activation manifold first
- intervention-conditioned or steered activations can be added later if needed

## Evaluation Ladder
Do not treat training loss as sufficient.

Use this order:

1. **Local validity**
   - next-token Delta-LM-Loss-style metric
   - compare raw edit vs repaired edit on held-out natural prompts
   - success means repaired states increase NLL less than raw edits

2. **Week 2 frontier**
   - `evil`, `sycophancy`
   - `response_last`
   - matched-coherence frontier, not just matched alpha
   - success means repaired edits preserve or improve effect at similar coherence without strong baseline-control distortion

3. **Week 3 H3 sufficiency**
   - `full_vector_raw`
   - `full_vector_repaired`
   - `circuit_only_raw`
   - `circuit_only_repaired`
   - same-size random controls
   - success means `circuit_only_repaired` beats raw and remains selective against random repaired controls

## Go / No-Go Gates
Proceed beyond local validity only if all are true:

1. baseline repaired control is materially weaker than selected repaired intervention
2. next-token NLL deltas shrink relative to raw, not grow
3. repaired intervention does not collapse target-token probability
4. repaired random controls remain weaker than repaired selected controls

Stop if:

- repaired baseline control remains large
- repaired random controls remain comparably strong
- local validity still worsens sharply

That would mean the problem is not just checkpoint mismatch, but a deeper mismatch between unconditional denoising and our intervention regime.

## Design Extension If Needed
If the matched single-layer model still over-smooths:

1. move to a **conditional repair model**
   - condition on the clean activation
   - predict a repaired activation from `(clean, edited)` rather than denoising edited alone

2. specialize to **response-last repair**
   - restrict the data/export and evaluation target to the token position we actually edit

3. consider a **small bottleneck repair objective**
   - mimic the paper's information bottleneck idea, but on the aligned instruct manifold

## Immediate Build Order
1. finish the Week 3 next-token diagnostic lane
2. build an exporter for single-layer layer-12 instruct activations
3. export a 1M-vector sanity dataset
4. train the single-layer repair model with the template config
5. run local-validity evaluation before any persona sweep

## Notes On Upstream Trainer
The upstream GLP trainer:

- reads memmap datasets listed in `train_dataset`
- expects `rep_statistics.pt` with `mean` and `var`
- uses `multi_layer_n_layers: null` for single-layer mode
- will mis-handle single-layer runs if the dataset directory name matches `layer_<N>`

The current template already reflects those constraints.
