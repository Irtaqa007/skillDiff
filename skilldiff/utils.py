"""Utility helpers."""
from __future__ import annotations
from pathlib import Path
from .loader import load_skill_file
from .normalizer import normalize
from .semantic_engine import compare
from .risk_engine import score
from .models import DiffResult


def diff_files(old_path: str, new_path: str, rules_path: str | None = None) -> DiffResult:
    """Full pipeline: load → normalize → compare → score."""
    old_raw = load_skill_file(old_path)
    new_raw = load_skill_file(new_path)
    old_skill = normalize(old_raw)
    new_skill = normalize(new_raw)
    result = compare(old_skill, new_skill)
    rp = Path(rules_path) if rules_path else None
    return score(result, rules_path=rp)
