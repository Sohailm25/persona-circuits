"""Week 1 Days 3-5 Modal setup: model/SAE/CLT download and validation."""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal

APP_NAME = "persona-circuits-week1-day3-5"
MODEL_VOLUME_NAME = "persona-circuits-models"

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(["git"])
    .pip_install(
        [
            "torch>=2.1.0",
            "transformers>=4.56.0,<=4.57.3",
            "sae-lens>=6.12.0",
            "transformer-lens>=1.11.0",
            "wandb",
            "huggingface-hub",
            "numpy",
            "scipy",
        ]
    )
    .run_commands(
        [
            "git clone https://github.com/safety-research/circuit-tracer.git /tmp/circuit-tracer",
            "pip install /tmp/circuit-tracer",
        ]
    )
)


def _seed_everything(seed: int = 42) -> None:
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _set_cache_env() -> None:
    os.environ["HF_HOME"] = "/models/huggingface"
    os.environ["TRANSFORMERS_CACHE"] = "/models/huggingface"
    os.environ["HF_HUB_CACHE"] = "/models/huggingface"
    os.environ["HUGGINGFACE_HUB_CACHE"] = "/models/huggingface"
    Path("/models/huggingface").mkdir(parents=True, exist_ok=True)
    Path("/models/persona-circuits/week1").mkdir(parents=True, exist_ok=True)


def _write_report(report: dict[str, Any], filename: str) -> str:
    path = Path("/models/persona-circuits/week1") / filename
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return str(path)


def _cache_summary(root: str = "/models/huggingface") -> dict[str, Any]:
    hf_root = Path(root)
    if not hf_root.exists():
        return {"exists": False, "total_bytes": 0}
    total_bytes = 0
    file_count = 0
    for p in hf_root.rglob("*"):
        if p.is_file():
            file_count += 1
            total_bytes += p.stat().st_size
    return {"exists": True, "total_bytes": total_bytes, "file_count": file_count}


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("wandb-key"),
    ],
    volumes={"/models": vol},
)
def validate_llama_scope_and_andyrdt() -> dict[str, Any]:
    import gc

    _set_cache_env()

    import torch
    import torch.nn.functional as F
    import wandb
    from sae_lens import SAE, HookedSAETransformer

    _seed_everything(42)

    wandb_run = wandb.init(
        project="persona-circuits",
        entity="sohailm",
        job_type="infrastructure",
        name=f"week1-day3-5-llama-setup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        config={
            "phase": "week1_day3_5",
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "llamascope_layers": list(range(12, 25)),
            "andyrdt_layers": [19, 23],
        },
    )

    model = HookedSAETransformer.from_pretrained(
        "meta-llama/Llama-3.1-8B-Instruct",
        device="cuda",
        dtype=torch.bfloat16,
    )
    tokens = model.to_tokens("Sanity check: the model should produce coherent text.", prepend_bos=True)
    logits, cache = model.run_with_cache(tokens)

    forward_summary = {
        "tokens_shape": list(tokens.shape),
        "logits_shape": list(logits.shape),
        "resid_12_shape": list(cache["blocks.12.hook_resid_post"].shape),
        "resid_24_shape": list(cache["blocks.24.hook_resid_post"].shape),
    }

    llama_scope_layers = {}
    for layer in range(12, 25):
        sae_id = f"l{layer}r_32x"
        sae, _, _ = SAE.from_pretrained(
            release="llama_scope_lxr_32x",
            sae_id=sae_id,
            device="cpu",
        )
        llama_scope_layers[sae_id] = {
            "d_in": int(sae.cfg.d_in),
            "d_sae": int(sae.cfg.d_sae),
        }
        del sae
        gc.collect()

    llama_sae_id = "l16r_32x"
    llama_sae, _, _ = SAE.from_pretrained(
        release="llama_scope_lxr_32x",
        sae_id=llama_sae_id,
        device="cuda",
    )
    acts = cache["blocks.16.hook_resid_post"][0].to(torch.float32)
    with torch.no_grad():
        feats = llama_sae.encode(acts)
        recon = llama_sae.decode(feats)
        recon_cosine = float(F.cosine_similarity(acts.flatten(), recon.flatten(), dim=0).item())
    del llama_sae
    gc.collect()
    torch.cuda.empty_cache()

    andyrdt_summary = {}
    for layer in [19, 23]:
        sae_id = f"resid_post_layer_{layer}_trainer_1"
        sae, _, _ = SAE.from_pretrained(
            release="llama-3.1-8b-instruct-andyrdt",
            sae_id=sae_id,
            device="cpu",
        )
        andyrdt_summary[sae_id] = {
            "d_in": int(sae.cfg.d_in),
            "d_sae": int(sae.cfg.d_sae),
        }
        del sae
        gc.collect()

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task": "llama_scope_and_andyrdt_validation",
        "model_name": "meta-llama/Llama-3.1-8B-Instruct",
        "forward_pass": forward_summary,
        "llama_scope_release": "llama_scope_lxr_32x",
        "llama_scope_loaded": llama_scope_layers,
        "llama_scope_reconstruction_cosine_layer16": recon_cosine,
        "andyrdt_release": "llama-3.1-8b-instruct-andyrdt",
        "andyrdt_loaded": andyrdt_summary,
        "cache_summary": {
            "models_volume_hf": _cache_summary("/models/huggingface"),
            "default_root_cache": _cache_summary("/root/.cache/huggingface"),
        },
    }

    wandb.log(
        {
            "infrastructure/llama_scope_layers_loaded": len(llama_scope_layers),
            "infrastructure/andyrdt_layers_loaded": len(andyrdt_summary),
            "infrastructure/llama_layer16_recon_cosine": recon_cosine,
        }
    )

    output_path = _write_report(report, "llama_scope_and_andyrdt_validation.json")
    artifact = wandb.Artifact("week1-llama-andyrdt-validation", type="infrastructure")
    artifact.add_file(output_path)
    wandb_run.log_artifact(artifact)
    wandb_run.finish()
    report["output_path"] = output_path
    return report


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("wandb-key"),
    ],
    volumes={"/models": vol},
)
def validate_gemma_scope_and_clt() -> dict[str, Any]:
    import gc

    _set_cache_env()

    import torch
    import torch.nn.functional as F
    import wandb
    from circuit_tracer import ReplacementModel, attribute
    from sae_lens import SAE, HookedSAETransformer

    _seed_everything(42)

    wandb_run = wandb.init(
        project="persona-circuits",
        entity="sohailm",
        job_type="infrastructure",
        name=f"week1-day3-5-gemma-setup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        config={
            "phase": "week1_day3_5",
            "model": "google/gemma-2-2b-it",
            "gemmascope_release": "gemma-scope-2b-pt-res-canonical",
            "clt_checkpoint": "mntss/clt-gemma-2-2b-426k",
        },
    )

    model = HookedSAETransformer.from_pretrained(
        "google/gemma-2-2b-it",
        device="cuda",
        dtype=torch.bfloat16,
    )
    tokens = model.to_tokens("Sanity check prompt for Gemma.", prepend_bos=True)
    logits, cache = model.run_with_cache(tokens)
    forward_summary = {
        "tokens_shape": list(tokens.shape),
        "logits_shape": list(logits.shape),
        "resid_0_shape": list(cache["blocks.0.hook_resid_post"].shape),
        "resid_25_shape": list(cache["blocks.25.hook_resid_post"].shape),
    }

    gemmascope_loaded = {}
    for layer in range(0, 26):
        sae_id = f"layer_{layer}/width_16k/canonical"
        sae, _, _ = SAE.from_pretrained(
            release="gemma-scope-2b-pt-res-canonical",
            sae_id=sae_id,
            device="cpu",
        )
        gemmascope_loaded[sae_id] = {
            "d_in": int(sae.cfg.d_in),
            "d_sae": int(sae.cfg.d_sae),
        }
        del sae
        gc.collect()

    example_sae, _, _ = SAE.from_pretrained(
        release="gemma-scope-2b-pt-res-canonical",
        sae_id="layer_12/width_16k/canonical",
        device="cuda",
    )
    acts = cache["blocks.12.hook_resid_post"][0].to(torch.float32)
    with torch.no_grad():
        feats = example_sae.encode(acts)
        recon = example_sae.decode(feats)
        recon_cosine = float(F.cosine_similarity(acts.flatten(), recon.flatten(), dim=0).item())
    del example_sae
    gc.collect()
    torch.cuda.empty_cache()

    clt_model = ReplacementModel.from_pretrained(
        "google/gemma-2-2b",
        "mntss/clt-gemma-2-2b-426k",
        dtype=torch.bfloat16,
        backend="transformerlens",
    )
    clt_graph = attribute(
        prompt="Briefly explain what photosynthesis is.",
        model=clt_model,
        max_n_logits=5,
        desired_logit_prob=0.95,
        batch_size=256,
        max_feature_nodes=2048,
        offload="cpu",
        verbose=False,
    )

    clt_adj = clt_graph.adjacency_matrix
    clt_nonzero_edges = int((clt_adj != 0).sum().item())
    clt_feature_nodes = int(len(clt_graph.selected_features))
    clt_source_nodes = int(clt_adj.shape[1])
    clt_target_nodes = int(clt_adj.shape[0])
    if clt_nonzero_edges == 0:
        raise RuntimeError("CLT attribution produced an empty graph; validation failed.")

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task": "gemma_scope_and_clt_validation",
        "model_name": "google/gemma-2-2b-it",
        "forward_pass": forward_summary,
        "gemmascope_release": "gemma-scope-2b-pt-res-canonical",
        "gemmascope_loaded_count": len(gemmascope_loaded),
        "gemmascope_reconstruction_cosine_layer12": recon_cosine,
        "clt_checkpoint": "mntss/clt-gemma-2-2b-426k",
        "clt_test_graph": {
            "feature_nodes": clt_feature_nodes,
            "source_nodes": clt_source_nodes,
            "target_nodes": clt_target_nodes,
            "nonzero_edges": clt_nonzero_edges,
        },
        "cache_summary": {
            "models_volume_hf": _cache_summary("/models/huggingface"),
            "default_root_cache": _cache_summary("/root/.cache/huggingface"),
        },
    }

    wandb.log(
        {
            "infrastructure/gemmascope_layers_loaded": len(gemmascope_loaded),
            "infrastructure/gemma_layer12_recon_cosine": recon_cosine,
            "infrastructure/clt_test_feature_nodes": clt_feature_nodes,
            "infrastructure/clt_test_nonzero_edges": clt_nonzero_edges,
        }
    )

    output_path = _write_report(report, "gemma_scope_and_clt_validation.json")
    artifact = wandb.Artifact("week1-gemma-clt-validation", type="infrastructure")
    artifact.add_file(output_path)
    wandb_run.log_artifact(artifact)
    wandb_run.finish()
    report["output_path"] = output_path
    return report


@app.local_entrypoint()
def main(task: str = "all") -> None:
    results: dict[str, Any] = {}
    if task in {"all", "llama"}:
        results["llama_scope_and_andyrdt"] = validate_llama_scope_and_andyrdt.remote()
    if task in {"all", "gemma"}:
        results["gemma_scope_and_clt"] = validate_gemma_scope_and_clt.remote()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    local_out_dir = Path(__file__).resolve().parents[1] / "results" / "infrastructure"
    local_out_dir.mkdir(parents=True, exist_ok=True)
    local_out = local_out_dir / f"week1_day3_5_modal_validation_{timestamp}.json"
    local_out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"task": task, "local_output": str(local_out), "results": results}, indent=2))
