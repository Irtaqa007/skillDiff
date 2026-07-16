"""Risk Engine — scores DiffResult using deterministic YAML-based rules."""
from __future__ import annotations
import yaml
from pathlib import Path
from .models import DiffResult, Change

_DEFAULT_RULES_PATH = Path(__file__).parent.parent / "rules" / "default.yaml"

_SEVERITY_SCORE = {
    "Critical": 40,
    "High": 20,
    "Medium": 10,
    "Low": 2,
    "Info": 0,
}

_RISK_LEVELS = [
    (80, "Critical"),
    (50, "High"),
    (20, "Medium"),
    (1,  "Low"),
    (0,  "None"),
]


def _load_rules(rules_path: Path | None = None) -> dict:
    """Load risk rules from YAML. Falls back to defaults if path not given."""
    path = rules_path or _DEFAULT_RULES_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _apply_rules(change: Change, rules: dict) -> None:
    """Apply YAML rules to upgrade severity of a change in-place."""
    permission_rules = rules.get("permissions", {})
    tool_rules = rules.get("tools", {})

    if change.category == "permissions":
        for pattern, config in permission_rules.items():
            if pattern in change.field or change.field.startswith(pattern):
                severity = config.get("severity", change.severity)
                recommendation = config.get("recommendation", change.recommendation)
                change.severity = severity
                if recommendation:
                    change.recommendation = recommendation

    elif change.category == "tools":
        for pattern, config in tool_rules.items():
            if pattern in change.field:
                severity = config.get("severity", change.severity)
                change.severity = severity


def score(result: DiffResult, rules_path: Path | None = None) -> DiffResult:
    """Apply risk rules to all changes and compute overall risk score."""
    rules = _load_rules(rules_path)

    total = 0
    for change in result.changes:
        _apply_rules(change, rules)
        total += _SEVERITY_SCORE.get(change.severity, 0)

    result.risk_score = min(total, 100)

    for threshold, level in _RISK_LEVELS:
        if total >= threshold:
            result.risk_level = level
            break

    return result
