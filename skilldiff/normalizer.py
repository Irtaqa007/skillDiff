"""
normalizer.py — Converts raw skill dicts into SkillModel instances.

All comparison logic operates on SkillModel, never on raw dicts.
"""

from __future__ import annotations
from typing import Any
from skilldiff.models import SkillMetadata, SkillModel


def normalize(raw: dict[str, Any]) -> SkillModel:
    """
    Normalize a raw skill dictionary into a SkillModel.

    Unknown fields are preserved in raw for auditability.
    Missing fields default to safe empty values.

    Args:
        raw: Dictionary loaded from a YAML or JSON skill file.

    Returns:
        Normalized SkillModel instance.
    """
    meta_raw = raw.get("metadata", {}) or {}
    metadata = SkillMetadata(
        name=str(meta_raw.get("name", "")),
        version=str(meta_raw.get("version", "")),
        description=str(meta_raw.get("description", "")),
        author=str(meta_raw.get("author", "")),
        tags=_coerce_list(meta_raw.get("tags")),
    )

    model_raw = raw.get("model", {}) or {}
    model: dict[str, Any] = {
        "name": str(model_raw.get("name", "")),
        "provider": str(model_raw.get("provider", "")),
        "context_window": model_raw.get("context_window"),
        "temperature": model_raw.get("temperature"),
    }

    prompt = str(raw.get("prompt", "") or "")

    tools = _coerce_list(raw.get("tools"))
    permissions = _coerce_list(raw.get("permissions"))
    resources = _coerce_list(raw.get("resources"))

    memory_raw = raw.get("memory", {}) or {}
    network_raw = raw.get("network", {}) or {}
    environment_raw = raw.get("environment", {}) or {}

    return SkillModel(
        metadata=metadata,
        model=model,
        prompt=prompt,
        tools=tools,
        permissions=permissions,
        resources=resources,
        memory=dict(memory_raw),
        network=dict(network_raw),
        environment=dict(environment_raw),
        raw=raw,
    )


def _coerce_list(value: Any) -> list[str]:
    """Coerce a value to a list of strings, tolerating None and single values."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
