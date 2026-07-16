"""
risk_engine.py — Deterministic risk scoring from detected changes.

Loads severity weights from rules/risk_policy.yaml.
No AI. No LLM. Pure rule-based scoring.
"""

from __future__ import annotations
from pathlib import Path
import yaml
from skilldiff.models import Change, DiffResult

# Default rules path — can be overridden
DEFAULT_RULES_PATH = Path(__file__).parent.parent / "rules" / "risk_policy.yaml"


def _load_policy(rules_path: Path | None = None) -> dict:
    path = rules_path or DEFAULT_RULES_PATH
    if not path.exists():
        return _default_policy()
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or _default_policy()


def _default_policy() -> dict:
    return {
        "severity_weights": {
            "critical": 40,
            "high": 20,
            "medium": 10,
            "low": 5,
            "info": 0,
        },
        "thresholds": {
            "none": 0,
            "low": 10,
            "medium": 25,
            "high": 50,
            "critical": 80,
        },
    }


def score(result: DiffResult, rules_path: Path | None = None) -> DiffResult:
    """
    Calculate and attach a risk score and risk level to a DiffResult.

    Modifies result in place and returns it.

    Args:
        result: DiffResult with changes populated by semantic_engine.
        rules_path: Optional override for the risk policy YAML path.

    Returns:
        The same DiffResult with risk_score and risk_level populated.
    """
    policy = _load_policy(rules_path)
    weights: dict[str, int] = policy.get("severity_weights", _default_policy()["severity_weights"])
    thresholds: dict[str, int] = policy.get("thresholds", _default_policy()["thresholds"])

    total = sum(weights.get(change.severity, 0) for change in result.changes)
    result.risk_score = total

    # Determine risk level from thresholds (highest threshold not exceeded)
    level = "none"
    for lvl in ("low", "medium", "high", "critical"):
        if total >= thresholds.get(lvl, 9999):
            level = lvl
    result.risk_level = level

    return result
