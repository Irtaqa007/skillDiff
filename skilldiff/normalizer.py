"""Normalizer — converts raw dicts into SkillModel objects."""
from __future__ import annotations
from typing import Any
from .models import SkillModel


def normalize(raw: dict[str, Any]) -> SkillModel:
    """Normalize a raw skill dict into a SkillModel.

    Handles nested or flat structures, missing fields, and type coercion.
    Never fails on missing fields — uses safe defaults.
    """
    skill = raw.get("skill", raw)  # support both top-level and nested

    def _as_list(val: Any) -> list:
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return [val]
        return [val]

    def _as_dict(val: Any) -> dict:
        if isinstance(val, dict):
            return val
        return {}

    # Normalize tools — support both string names and full dicts
    raw_tools = _as_list(skill.get("tools"))
    tools = []
    for t in raw_tools:
        if isinstance(t, str):
            tools.append({"name": t})
        elif isinstance(t, dict):
            tools.append(t)

    # Normalize permissions — flatten nested permission dicts
    raw_perms = skill.get("permissions", [])
    permissions: list[str] = []
    if isinstance(raw_perms, dict):
        for category, items in raw_perms.items():
            if isinstance(items, list):
                permissions.extend(f"{category}.{item}" for item in items)
            elif isinstance(items, bool) and items:
                permissions.append(category)
    elif isinstance(raw_perms, list):
        for p in raw_perms:
            permissions.append(str(p))

    return SkillModel(
        metadata=_as_dict(skill.get("metadata") or skill.get("meta")),
        model=_as_dict(skill.get("model") or skill.get("llm")),
        prompt={
            "system": skill.get("system_prompt") or skill.get("prompt", {}).get("system", ""),
            "user": skill.get("user_prompt") or skill.get("prompt", {}).get("user", ""),
            "instructions": skill.get("instructions") or skill.get("prompt", {}).get("instructions", ""),
        },
        tools=tools,
        permissions=permissions,
        resources=_as_list(skill.get("resources")),
        memory=_as_dict(skill.get("memory")),
        network=_as_dict(skill.get("network")),
        environment=_as_dict(skill.get("environment") or skill.get("env")),
    )
