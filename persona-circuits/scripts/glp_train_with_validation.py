"""Local GLP training wrapper with validation tracking.

This keeps the upstream GLP model classes but avoids patching upstream source
files in-place. It adds:
- deterministic train/validation splitting
- epoch-level validation loss reporting
- conditional loss slicing for concatenated [condition ; target] datasets
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import numpy as np
import torch
from omegaconf import ListConfig, OmegaConf
from torch.utils.data import ConcatDataset, DataLoader, Dataset, Subset
from tqdm import tqdm

from glp import flow_matching
from glp.denoiser import GLP as UpstreamGLP
from glp.denoiser import Normalizer
from glp.utils_acts import MemmapReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrainConfig:
    model_name: str = ""
    glp_kwargs: Optional[Any] = None
    shuffle: bool = True
    train_dataset: str = ""
    rep_statistic: str = ""
    use_bf16: bool = True
    num_epochs: int = 1
    epoch_size: Optional[int] = None
    batch_size: int = 4096
    learning_rate: float = 5e-5
    lr_scheduler: Optional[dict] = None
    gradient_accumulation_steps: int = 1
    gradient_clipping_threshold: float = 1.0
    log_every_n_steps: int = 10
    save_every_n_steps: Optional[int] = None
    save_epochs: Optional[list[int]] = None
    save_opt_state: bool = False
    output_path: Optional[Path] = None
    wandb_enabled: bool = False
    wandb_entity: Optional[str] = None
    wandb_project: Optional[str] = None
    wandb_run_name: Optional[str] = None
    validation_fraction: float = 0.0
    validation_seed: int = 42
    validation_max_batches: Optional[int] = None


class ConditionalAwareGLP(UpstreamGLP):
    def __init__(
        self,
        normalizer_config: dict[str, Any],
        denoiser_config: dict[str, Any],
        tracedict_config: dict[str, Any] | None = None,
        conditional_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            normalizer_config=normalizer_config,
            denoiser_config=denoiser_config,
            tracedict_config=tracedict_config,
        )
        self.conditional_config = conditional_config or None

    def forward(
        self,
        *,
        latents: torch.FloatTensor,
        u: torch.FloatTensor | float | None = None,
        layer_idx: torch.LongTensor | int | None = None,
        loss_kwargs: dict | None = None,
        generator: torch.Generator | None = None,
        **kwargs: Any,
    ) -> SimpleNamespace:
        assert latents.ndim == 3, f"Expected (batch, seq, dim), got shape {latents.shape}"
        self.normalizer.check_normalized(latents)
        self.scheduler.set_timesteps(self.scheduler.config.num_train_timesteps)
        if isinstance(u, float):
            u = torch.full((latents.shape[0],), u, device=latents.device)

        loss_kwargs = loss_kwargs or {}
        noise = torch.randn(latents.shape, dtype=latents.dtype, generator=generator).to(latents.device)
        noisy_latents, target, timesteps, _meta = flow_matching.fm_prepare(
            self.scheduler,
            latents,
            noise,
            u=u,
            generator=generator,
        )
        outputs = self.denoiser(
            latents=noisy_latents,
            timesteps=timesteps,
            layer_idx=layer_idx,
            **kwargs,
        )
        conditional_config = self.conditional_config or {}
        target_slice_start = conditional_config.get("target_slice_start")
        target_slice_end = conditional_config.get("target_slice_end")
        if target_slice_start is not None or target_slice_end is not None:
            slice_start = int(target_slice_start or 0)
            slice_end = int(target_slice_end) if target_slice_end is not None else int(outputs.shape[-1])
            outputs_for_loss = outputs[..., slice_start:slice_end]
            target_for_loss = target[..., slice_start:slice_end]
        else:
            outputs_for_loss = outputs
            target_for_loss = target
        loss = torch.nn.functional.mse_loss(outputs_for_loss, target_for_loss, **loss_kwargs)
        return SimpleNamespace(
            latents=outputs,
            timesteps=timesteps,
            loss=loss,
        )


class ActDataset(Dataset):
    def __init__(self, reader: MemmapReader | list[MemmapReader]):
        reader = [reader] if not isinstance(reader, (list, ListConfig)) else reader
        self.reader = reader

    def __len__(self) -> int:
        return len(self.reader[0])

    def __getitem__(self, idx: int) -> dict[str, Any]:
        batch: dict[str, Any] = {}
        layer_match = re.search(r"layer_(\d+)", str(self.reader[0].data_dir))
        if layer_match:
            batch["layer_idx"] = int(layer_match.group(1))
        latents = [torch.tensor(reader[idx])[None, :] for reader in self.reader]
        latents = torch.cat(latents, dim=-1)
        latents = latents.view(torch.bfloat16) if latents.dtype == torch.int16 else latents
        latents = latents.float()
        batch["activations"] = latents
        return batch


class ActivationCollator:
    def __init__(self, normalizer: Normalizer):
        self.normalizer = normalizer

    @torch.no_grad()
    def __call__(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        batch: dict[str, Any] = {}
        if rows and "layer_idx" in rows[0]:
            layer_idx = torch.tensor([row["layer_idx"] for row in rows], dtype=torch.long)
            batch["layer_idx"] = layer_idx
        else:
            layer_idx = None
        latents = torch.stack([row["activations"] for row in rows], dim=0)
        batch["latents"] = self.normalizer.normalize(latents, layer_idx=layer_idx)
        return batch


def load_activation_dataset(dataset_paths: str | list[str]) -> Dataset:
    dataset_paths = [dataset_paths] if isinstance(dataset_paths, str) else dataset_paths
    datasets = []
    for path_str in dataset_paths:
        path = Path(path_str)
        dtype_path = path / "dtype.txt"
        dtype = np.dtype(dtype_path.read_text().strip().replace("np.", ""))
        reader = MemmapReader(path, dtype)
        datasets.append(ActDataset(reader=reader))
    return ConcatDataset(datasets)


def get_activation_dataloader(
    dataset: Dataset,
    *,
    batch_size: int,
    normalizer: Normalizer,
    shuffle: bool,
    drop_last: bool,
) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=drop_last,
        collate_fn=ActivationCollator(normalizer),
        num_workers=0,
        pin_memory=False,
    )


def linear_scheduler(step: int, max_steps: int, initial_factor: float, final_factor: float) -> float:
    if max_steps <= 0:
        return float(final_factor)
    alpha = step / max_steps
    return alpha * final_factor + (1 - alpha) * initial_factor


def linear_scheduler_with_warmup(
    step: int,
    *,
    warmup_steps: float,
    max_steps: int,
    initial_factor: float,
    final_factor: float,
) -> float:
    warmup_steps_int = max(0, int(round(float(warmup_steps))))
    if warmup_steps_int > 0 and step < warmup_steps_int:
        return linear_scheduler(step, warmup_steps_int, initial_factor, 1.0)
    if step >= max_steps:
        return final_factor
    return linear_scheduler(step - warmup_steps_int, max_steps - warmup_steps_int, 1.0, final_factor)


def cosine_scheduler(step: int, max_steps: int, initial_factor: float, final_factor: float) -> float:
    alpha = step / max_steps
    cosine_out = 0.5 * (1 + math.cos(math.pi * alpha))
    return final_factor + (initial_factor - final_factor) * cosine_out


def cosine_scheduler_with_warmup(
    step: int,
    *,
    warmup_steps: float,
    max_steps: int,
    initial_factor: float,
    final_factor: float,
) -> float:
    warmup_steps_int = max(0, int(round(float(warmup_steps))))
    if warmup_steps_int > 0 and step < warmup_steps_int:
        return linear_scheduler(step, warmup_steps_int, initial_factor, 1.0)
    if step >= max_steps:
        return final_factor
    return cosine_scheduler(step - warmup_steps_int, max_steps - warmup_steps_int, 1.0, final_factor)


def _build_glp_model(glp_kwargs: Any) -> UpstreamGLP:
    kwargs = OmegaConf.to_container(glp_kwargs, resolve=True) if not isinstance(glp_kwargs, dict) else dict(glp_kwargs)
    kwargs = dict(kwargs or {})
    conditional_config = kwargs.pop("conditional_config", None)
    if conditional_config:
        return ConditionalAwareGLP(conditional_config=conditional_config, **kwargs)
    return UpstreamGLP(**kwargs)


def _split_dataset(dataset: Dataset, *, validation_fraction: float, seed: int) -> tuple[Dataset, Dataset | None]:
    total = len(dataset)
    if total <= 1 or validation_fraction <= 0.0:
        return dataset, None
    n_val = int(round(total * validation_fraction))
    n_val = max(1, min(total - 1, n_val))
    rng = np.random.default_rng(int(seed))
    permutation = rng.permutation(total)
    val_indices = permutation[:n_val].tolist()
    train_indices = permutation[n_val:].tolist()
    return Subset(dataset, train_indices), Subset(dataset, val_indices)


@torch.no_grad()
def _evaluate_loss(
    *,
    model: UpstreamGLP,
    dataloader: DataLoader | None,
    device: str,
    use_bf16: bool,
    max_batches: int | None,
) -> dict[str, Any]:
    if dataloader is None:
        return {"num_batches": 0, "num_examples": 0, "mean_loss": None}
    model.eval()
    losses: list[float] = []
    num_examples = 0
    for batch_idx, batch in enumerate(dataloader):
        if max_batches is not None and batch_idx >= max_batches:
            break
        batch = {k: v.to(device) if v is not None else None for k, v in batch.items()}
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=use_bf16):
            outputs = model(**batch)
        losses.append(float(outputs.loss.detach().float().item()))
        latents = batch.get("latents")
        if latents is not None:
            num_examples += int(latents.shape[0])
    return {
        "num_batches": int(len(losses)),
        "num_examples": int(num_examples),
        "mean_loss": float(np.mean(np.asarray(losses, dtype=np.float64))) if losses else None,
    }


def save_checkpoint(
    model: UpstreamGLP,
    output_path: Path,
    checkpoint_name: str,
    optimizer: torch.optim.Optimizer | None = None,
    scheduler: Any | None = None,
    *,
    save_opt_state: bool = False,
) -> None:
    model.save_pretrained(path=output_path, name=checkpoint_name)
    logger.info(f"Model saved to {output_path}/{checkpoint_name}")
    if save_opt_state:
        if optimizer is not None:
            torch.save(optimizer.state_dict(), output_path / "optimizer_state.pt")
        if scheduler is not None:
            torch.save(scheduler.state_dict(), output_path / "scheduler_state.pt")


def main(device: str = "cuda:0") -> None:
    config_base = OmegaConf.structured(TrainConfig())
    OmegaConf.set_struct(config_base, False)
    config_cli = OmegaConf.from_cli()
    config_path = config_cli.pop("config", None)
    config_file = OmegaConf.load(config_path) if config_path else OmegaConf.create()
    config = OmegaConf.merge(config_base, config_file, config_cli)

    output_path = Path(config.output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving checkpoints to {output_path}")
    OmegaConf.save(config, output_path / "config.yaml")

    rep_statistic = config.glp_kwargs.get("normalizer_config", {}).get("rep_statistic")
    if rep_statistic and os.path.exists(rep_statistic):
        logger.info(f"Waiting for rep_statistic {rep_statistic}...")
        while not os.path.exists(rep_statistic):
            time.sleep(5)

    torch.cuda.set_device(device)
    torch.cuda.empty_cache()
    logger.info(f"Config: {config}")

    wandb_run = None
    if config.wandb_enabled:
        import wandb

        wandb_run = wandb.init(
            entity=config.wandb_entity,
            project=config.wandb_project,
            name=config.wandb_run_name,
            config=OmegaConf.to_container(config),
        )

    model = _build_glp_model(config.glp_kwargs)
    model.to(device)
    logger.info(f"Model param count: {sum(p.numel() for p in model.parameters())}")

    full_dataset = load_activation_dataset(config.train_dataset)
    train_dataset, val_dataset = _split_dataset(
        full_dataset,
        validation_fraction=float(config.validation_fraction or 0.0),
        seed=int(config.validation_seed),
    )
    logger.info(
        "Dataset split: train=%s val=%s total=%s",
        len(train_dataset),
        0 if val_dataset is None else len(val_dataset),
        len(full_dataset),
    )

    per_device_batch = int(config.batch_size) // int(config.gradient_accumulation_steps)
    train_dataloader = get_activation_dataloader(
        dataset=train_dataset,
        batch_size=per_device_batch,
        normalizer=model.normalizer,
        shuffle=bool(config.shuffle),
        drop_last=True,
    )
    val_dataloader = (
        get_activation_dataloader(
            dataset=val_dataset,
            batch_size=per_device_batch,
            normalizer=model.normalizer,
            shuffle=False,
            drop_last=False,
        )
        if val_dataset is not None
        else None
    )

    epoch_size = (int(config.epoch_size) // int(config.batch_size)) if config.epoch_size else len(train_dataloader)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config.learning_rate))
    if config.lr_scheduler is None:
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=lambda step: 1.0)
    else:
        total_num_steps = int(config.num_epochs) * (epoch_size // int(config.gradient_accumulation_steps))
        scheduler = torch.optim.lr_scheduler.LambdaLR(
            optimizer,
            lr_lambda=lambda step: globals()[str(config.lr_scheduler["scheduler_cls"])](
                step,
                warmup_steps=float(config.lr_scheduler["warmup_ratio"]) * total_num_steps,
                max_steps=total_num_steps,
                initial_factor=float(config.lr_scheduler["initial_factor"]),
                final_factor=float(config.lr_scheduler["final_factor"]),
            ),
        )

    train_steps = 0
    num_gradient_steps = 0
    epoch_history: list[dict[str, Any]] = []

    for epoch in range(int(config.num_epochs)):
        model.train()
        gradient_steps_in_epoch = epoch_size // int(config.gradient_accumulation_steps)
        pbar = tqdm(
            total=gradient_steps_in_epoch,
            desc=f"Training Epoch: {epoch + 1}",
            dynamic_ncols=True,
        )
        step_losses: list[float] = []

        for step, batch in enumerate(train_dataloader):
            batch = {k: v.to(device) if v is not None else None for k, v in batch.items()}
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=bool(config.use_bf16)):
                outputs = model(**batch)
                loss = outputs.loss

            raw_loss = float(loss.detach().float().item())
            step_losses.append(raw_loss)
            loss = loss / int(config.gradient_accumulation_steps)
            loss.backward()
            train_steps += 1

            if train_steps % int(config.gradient_accumulation_steps) == 0:
                num_gradient_steps += 1

                if float(config.gradient_clipping_threshold) > 0.0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), float(config.gradient_clipping_threshold))

                optimizer.step()
                optimizer.zero_grad()
                scheduler.step()

                pbar.update(1)
                pbar.set_description(
                    f"Epoch: {epoch + 1}/{config.num_epochs}, "
                    f"batch {step + 1}/{epoch_size} "
                    f"(loss: {raw_loss:.4f})"
                )

                if num_gradient_steps % int(config.log_every_n_steps) == 0 and wandb_run is not None:
                    wandb_run.log(
                        {
                            "train/epoch": epoch,
                            "train/step": num_gradient_steps,
                            "train/loss": raw_loss,
                            "train/learning_rate": scheduler.get_last_lr()[0],
                        },
                        step=num_gradient_steps,
                    )

                if config.save_every_n_steps and num_gradient_steps % int(config.save_every_n_steps) == 0:
                    save_checkpoint(
                        model,
                        output_path,
                        f"step_{num_gradient_steps}",
                        optimizer,
                        scheduler,
                        save_opt_state=bool(config.save_opt_state),
                    )

            if step >= gradient_steps_in_epoch * int(config.gradient_accumulation_steps):
                break

        pbar.close()
        val_summary = _evaluate_loss(
            model=model,
            dataloader=val_dataloader,
            device=device,
            use_bf16=bool(config.use_bf16),
            max_batches=(
                int(config.validation_max_batches)
                if config.validation_max_batches not in (None, "", 0)
                else None
            ),
        )
        epoch_summary = {
            "epoch": int(epoch + 1),
            "train_loss_mean": float(np.mean(np.asarray(step_losses, dtype=np.float64))) if step_losses else None,
            "train_loss_last": float(step_losses[-1]) if step_losses else None,
            "train_gradient_steps": int(gradient_steps_in_epoch),
            "learning_rate_last": float(scheduler.get_last_lr()[0]),
            "validation": val_summary,
        }
        epoch_history.append(epoch_summary)
        logger.info("Epoch summary: %s", epoch_summary)
        if wandb_run is not None:
            wandb_run.log(
                {
                    "train/epoch_mean_loss": epoch_summary["train_loss_mean"],
                    "train/epoch_last_loss": epoch_summary["train_loss_last"],
                    "train/epoch_index": int(epoch + 1),
                    "validation/loss": val_summary["mean_loss"],
                    "validation/num_batches": val_summary["num_batches"],
                },
                step=num_gradient_steps,
            )

        if config.save_epochs and (epoch + 1) in set(config.save_epochs):
            save_checkpoint(model, output_path / "checkpoints", f"epoch_{epoch + 1}")

        save_checkpoint(model, output_path, "final", optimizer, scheduler, save_opt_state=bool(config.save_opt_state))

    metrics_path = output_path / "training_metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "train_dataset_size": int(len(train_dataset)),
                "validation_dataset_size": int(0 if val_dataset is None else len(val_dataset)),
                "epoch_history": epoch_history,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Training metrics written to %s", metrics_path)

    if wandb_run is not None:
        wandb.finish()


if __name__ == "__main__":
    main()
