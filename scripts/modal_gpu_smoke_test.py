"""Day 1 Modal GPU smoke test for persona-circuits."""

from __future__ import annotations

import json

import modal

app = modal.App("persona-circuits-day1-gpu-smoke")
image = modal.Image.debian_slim(python_version="3.11").pip_install(["torch>=2.1.0"])


@app.function(gpu="A100-80GB", image=image, timeout=600)
def get_gpu_info() -> dict:
    import platform

    import torch

    return {
        "python_version": platform.python_version(),
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "torch_version": torch.__version__,
    }


@app.local_entrypoint()
def main() -> None:
    info = get_gpu_info.remote()
    print(json.dumps(info, indent=2))
