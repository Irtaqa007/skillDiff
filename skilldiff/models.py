"""
models.py — Internal normalized skill representation.

All skill inputs are parsed into SkillModel before comparison.
Never compare raw YAML or JSON directly.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillMetadata:
    name: str = ""
    version: str = ""
    description: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class SkillModel:
    """
    Normalized internal representation of an AI skill definition.
    Every input format (YAML, JSON) is converted to this model
    before any comparison logic runs.
    """

    metadata: SkillMetadata = field(default_factory=SkillMetadata)
    model: dict[str, Any] = field(default_factory=dict)
    prompt: str = ""
    tools: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)
    network: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Change:
    """A single detected behavioral change between two skill versions."""

    field: str
    change_type: str          # added | removed | modified | expanded | restricted
    old_value: Any
    new_value: Any
    description: str
    severity: str             # critical | high | medium | low | info
    recommendation: str = ""


@dataclass
class DiffResult:
    """Full result of comparing two skill versions."""

    old_path: str
    new_path: str
    changes: list[Change] = field(default_factory=list)
    risk_score: int = 0
    risk_level: str = "none"  # none | low | medium | high | critical

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def critical_count(self) -> int:
        return sum(1 for c in self.changes if c.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for c in self.changes if c.severity == "high")
