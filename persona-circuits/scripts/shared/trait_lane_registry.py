"""Registry helpers for non-invasive trait-lane screening branches."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = ROOT / "configs" / "trait_lanes_v2.yaml"


class TraitLaneRegistryError(ValueError):
    """Raised when the lane registry is malformed or an invalid selection is requested."""


def _read_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TraitLaneRegistryError(f"Registry at {path} must be a YAML mapping.")
    return raw


def load_trait_lane_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or DEFAULT_REGISTRY_PATH
    payload = _read_yaml(registry_path)
    schema_version = int(payload.get("schema_version", 0))
    if schema_version != 1:
        raise TraitLaneRegistryError(f"Unsupported trait-lane registry schema_version={schema_version}")
    families = payload.get("families")
    if not isinstance(families, dict) or not families:
        raise TraitLaneRegistryError("Registry must define a non-empty `families` mapping.")

    seen_lane_ids: set[str] = set()
    for family_id, family_payload in families.items():
        if not isinstance(family_payload, dict):
            raise TraitLaneRegistryError(f"Family {family_id} payload must be a mapping.")
        if not family_payload.get("construct_card"):
            raise TraitLaneRegistryError(f"Family {family_id} is missing construct_card.")
        lanes = family_payload.get("lanes")
        if not isinstance(lanes, dict) or not lanes:
            raise TraitLaneRegistryError(f"Family {family_id} must define non-empty lanes.")
        for lane_id, lane_payload in lanes.items():
            if lane_id in seen_lane_ids:
                raise TraitLaneRegistryError(f"Duplicate lane_id detected: {lane_id}")
            seen_lane_ids.add(lane_id)
            if not isinstance(lane_payload, dict):
                raise TraitLaneRegistryError(f"Lane {lane_id} payload must be a mapping.")
            for key in (
                "display_name",
                "high_vs_low_construct",
                "persona_class",
                "judge_rubric_id",
                "promotion_gate_profile",
            ):
                if not lane_payload.get(key):
                    raise TraitLaneRegistryError(f"Lane {lane_id} missing required field: {key}")
    return payload


def list_family_ids(registry: dict[str, Any]) -> list[str]:
    return list((registry.get("families") or {}).keys())


def list_lane_ids(
    registry: dict[str, Any],
    *,
    family_ids: Iterable[str] | None = None,
) -> list[str]:
    selected_families = set(family_ids or list_family_ids(registry))
    lane_ids: list[str] = []
    for family_id, family_payload in (registry.get("families") or {}).items():
        if family_id not in selected_families:
            continue
        for lane_id in family_payload.get("lanes", {}):
            lane_ids.append(lane_id)
    return lane_ids


def get_family_config(registry: dict[str, Any], family_id: str) -> dict[str, Any]:
    families = registry.get("families") or {}
    if family_id not in families:
        raise TraitLaneRegistryError(f"Unknown family_id: {family_id}")
    return families[family_id]


def get_lane_config(registry: dict[str, Any], lane_id: str) -> dict[str, Any]:
    for family_id, family_payload in (registry.get("families") or {}).items():
        lanes = family_payload.get("lanes", {})
        if lane_id in lanes:
            lane_payload = dict(lanes[lane_id])
            lane_payload["family_id"] = family_id
            lane_payload["construct_card"] = str(family_payload.get("construct_card"))
            lane_payload["family_display_name"] = str(family_payload.get("display_name", family_id))
            lane_payload["priority_rank"] = int(family_payload.get("priority_rank", 999))
            return lane_payload
    raise TraitLaneRegistryError(f"Unknown lane_id: {lane_id}")


def parse_id_csv(raw: str) -> list[str]:
    values = [chunk.strip() for chunk in raw.split(",") if chunk.strip()]
    dedup: list[str] = []
    for value in values:
        if value not in dedup:
            dedup.append(value)
    return dedup


def resolve_selected_lane_ids(
    registry: dict[str, Any],
    *,
    lane_ids: Iterable[str] | None = None,
    family_ids: Iterable[str] | None = None,
) -> list[str]:
    selected: list[str] = []
    for family_id in family_ids or []:
        if family_id not in list_family_ids(registry):
            raise TraitLaneRegistryError(f"Unknown family_id: {family_id}")
        for lane_id in list_lane_ids(registry, family_ids=[family_id]):
            if lane_id not in selected:
                selected.append(lane_id)
    for lane_id in lane_ids or []:
        get_lane_config(registry, lane_id)
        if lane_id not in selected:
            selected.append(lane_id)
    if not selected:
        selected = list_lane_ids(registry)
    return selected


def construct_card_path(registry: dict[str, Any], family_id: str) -> Path:
    namespaces = registry.get("namespaces") or {}
    rel = str(namespaces.get("construct_cards_dir", "history/construct_cards"))
    family_cfg = get_family_config(registry, family_id)
    return (ROOT / rel / str(family_cfg["construct_card"]))


def build_lane_screening_plan(
    registry: dict[str, Any],
    *,
    lane_ids: Iterable[str] | None = None,
    family_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    namespaces = registry.get("namespaces") or {}
    prompts_dir = ROOT / str(namespaces.get("prompts_dir", "prompts/trait_lanes_v2"))
    selected_lane_ids = resolve_selected_lane_ids(registry, lane_ids=lane_ids, family_ids=family_ids)
    defaults = registry.get("defaults") or {}
    plan: list[dict[str, Any]] = []
    for lane_id in selected_lane_ids:
        lane_cfg = get_lane_config(registry, lane_id)
        family_id = str(lane_cfg["family_id"])
        plan.append(
            {
                "lane_id": lane_id,
                "family_id": family_id,
                "display_name": lane_cfg["display_name"],
                "family_display_name": lane_cfg["family_display_name"],
                "priority_rank": int(lane_cfg["priority_rank"]),
                "persona_class": lane_cfg["persona_class"],
                "judge_rubric_id": lane_cfg["judge_rubric_id"],
                "supports_extraction_free": bool(lane_cfg.get("supports_extraction_free", False)),
                "supports_external_transfer": bool(lane_cfg.get("supports_external_transfer", False)),
                "supports_cross_trait_bleed": bool(lane_cfg.get("supports_cross_trait_bleed", False)),
                "external_transfer_benchmark_type": lane_cfg.get("external_transfer_benchmark_type", "none"),
                "construct_card_path": str(construct_card_path(registry, family_id)),
                "planned_prompt_files": {
                    "extraction_pairs": str(prompts_dir / f"{lane_id}_pairs.jsonl"),
                    "heldout_pairs": str(prompts_dir / "heldout" / f"{lane_id}_heldout_pairs.jsonl"),
                    "extraction_free": str(prompts_dir / "extraction_free" / f"{lane_id}_eval.jsonl"),
                    "external_smoke": str(prompts_dir / "external_smoke" / f"{lane_id}_external_smoke.jsonl"),
                },
                "screening_counts": {
                    "extraction_pairs": int(defaults.get("extraction_pairs_per_lane", 24)),
                    "heldout_pairs": int(defaults.get("heldout_prompts_per_lane", 12)),
                    "extraction_free": int(defaults.get("extraction_free_prompts_per_lane", 12)),
                    "external_smoke": int(defaults.get("external_smoke_prompts_per_lane", 8)),
                },
                "screening_layers": [int(x) for x in defaults.get("screening_layers", [11, 12, 13, 14, 15, 16])],
                "screening_alpha_grid": [float(x) for x in defaults.get("screening_alpha_grid", [0.5, 1.0, 2.0])],
                "high_vs_low_construct": lane_cfg["high_vs_low_construct"],
                "known_confounds": list(lane_cfg.get("known_confounds", [])),
                "promotion_gate_profile": lane_cfg["promotion_gate_profile"],
            }
        )
    return plan


def build_construct_card_status(registry: dict[str, Any], *, lane_ids: Iterable[str]) -> dict[str, Any]:
    status: dict[str, Any] = {"missing": [], "present": []}
    families_seen: set[str] = set()
    for lane_id in lane_ids:
        lane_cfg = get_lane_config(registry, lane_id)
        family_id = str(lane_cfg["family_id"])
        if family_id in families_seen:
            continue
        families_seen.add(family_id)
        path = construct_card_path(registry, family_id)
        bucket = "present" if path.exists() else "missing"
        status[bucket].append(str(path))
    status["all_present"] = not status["missing"]
    return status


def build_namespace_collision_report(registry: dict[str, Any], *, lane_ids: Iterable[str]) -> dict[str, Any]:
    collisions: list[str] = []
    for lane in build_lane_screening_plan(registry, lane_ids=lane_ids):
        for path_str in lane["planned_prompt_files"].values():
            path = Path(path_str)
            if path.exists():
                collisions.append(str(path))
    return {
        "collision_count": len(collisions),
        "collisions": collisions,
        "has_collisions": bool(collisions),
    }
