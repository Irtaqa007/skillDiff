"""Internal skill model — normalized representation of any skill version."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillModel:
    """Normalized internal representation of an AI skill definition."""

    metadata: dict[str, Any] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)
    prompt: dict[str, Any] = field(default_factory=dict)
    tools: list[dict[str, Any]] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    resources: list[dict[str, Any]] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)
    network: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)

    @property
    def tool_names(self) -> set[str]:
        return {t.get("name", "") for t in self.tools}

    @property
    def permission_set(self) -> set[str]:
        return set(self.permissions)


@dataclass
class Change:
    """A single detected behavioral change between two skill versions."""

    category: str          # prompt | tools | permissions | model | network | resources
    field: str             # specific field that changed
    old_value: Any
    new_value: Any
    description: str
    severity: str = "Low"  # Critical | High | Medium | Low | Info
    recommendation: str = ""


@dataclass
class DiffResult:
    """Complete result of comparing two skill versions."""

    old_skill: SkillModel
    new_skill: SkillModel
    changes: list[Change] = field(default_factory=list)
    risk_score: int = 0
    risk_level: str = "Low"

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def critical_changes(self) -> list[Change]:
        return [c for c in self.changes if c.severity == "Critical"]

    @property
    def high_changes(self) -> list[Change]:
        return [c for c in self.changes if c.severity == "High"]
