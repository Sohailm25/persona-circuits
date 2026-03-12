# Week3 Stage4 H3 Bounded Claim-Grade Tranche A Closeout

## Scope
- App: `ap-mCOxAI9Xp7WCZoxpslD6Yi`
- Run token: `week3-stage4-h3-claimgrade-syc-resample-trancheA-20260311T0844-0500`
- Trait/method: `sycophancy` / `resample`
- Doses planned: `0.25, 0.50, 1.00`
- Ablation scope: `full_sae_complement`
- Claim mode: `claim_grade`

## Terminal outcome
- `known`: app is stopped.
- `observed`: `dose=0.50` completed and checkpointed.
- `observed`: `dose=1.00` reached `65/100` random baseline sets before runner termination.
- `observed`: terminal error was `Judge returned unparseable output after 6 attempts (model=claude-sonnet-4-6, trait=sycophancy).`

## Recoverability
- `known`: token-stable checkpoint exists on the Modal volume and was copied locally.
- `known`: the checkpoint only contains completed doses `0.25` and `0.50`.
- `known`: this runner does not checkpoint mid-dose random-baseline progress.
- `inferred`: a rerun with the same run token would restart `dose=1.00` from scratch, not from `65/100`.

## Scientific read from completed doses
- `observed`: `dose=0.25` has `observed_mean_preservation=0.286`, `sufficiency_threshold_pass=false`, coherence-drop mean `73.2`, capability proxy `0.0`.
- `observed`: `dose=0.50` has `observed_mean_preservation=0.357`, `sufficiency_threshold_pass=false`, coherence-drop mean `73.2`, capability proxy `0.0`.
- `observed`: raw circuit-only output audits for both completed doses are repetitive degenerate text (`"is is is ..."`, `"::: is is is ..."`), not coherent preserved behavior.
- `inferred`: full-complement circuit-only ablation in this bounded sycophancy lane is already a negative feasibility signal at low and mid doses.

## Closeout decision
- `inferred`: this bounded tranche is sufficient for a scoped H3 determination.
- `inferred`: do not rerun this exact bounded tranche by default.
- `inferred`: record it as a negative feasibility read for claim-grade full-complement H3 on the sycophancy/resample lane, then advance to the next planned branch (`trait_lanes_v2`).

## Primary closeout artifact
- `results/stage4_ablation/week3_stage4_behavioral_sufficiency_claimgrade_trancheA_closeout_20260311T1919Z.json`
