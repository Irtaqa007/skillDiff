"""
loader.py — File loading for YAML and JSON skill definitions.

Supports only YAML and JSON in V1. All other formats raise LoadError.
"""

from __future__ import annotations
import json
import yaml
from pathlib import Path
from typing import Any


class LoadError(Exception):
    """Raised when a skill file cannot be loaded or parsed."""


SUPPORTED_EXTENSIONS = {".yaml", ".yml", ".json"}


def load_skill_file(path: str | Path) -> dict[str, Any]:
    """
    Load a skill definition file from disk.

    Args:
        path: Path to the YAML or JSON skill file.

    Returns:
        Raw dictionary parsed from the file.

    Raises:
        LoadError: If the file does not exist, has an unsupported format,
                   or cannot be parsed.
    """
    p = Path(path)

    if not p.exists():
        raise LoadError(f"File not found: {path}")

    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise LoadError(
            f"Unsupported file format '{p.suffix}'. "
            f"SkillDiff V1 supports: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    try:
        content = p.read_text(encoding="utf-8")
    except OSError as e:
        raise LoadError(f"Cannot read file '{path}': {e}") from e

    try:
        if p.suffix.lower() == ".json":
            data = json.loads(content)
        else:
            data = yaml.safe_load(content)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise LoadError(f"Parse error in '{path}': {e}") from e

    if not isinstance(data, dict):
        raise LoadError(
            f"Expected a mapping at the root of '{path}', "
            f"got {type(data).__name__}."
        )

    return data
