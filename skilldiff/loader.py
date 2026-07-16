"""Loader — reads YAML or JSON skill files into raw dicts."""
from __future__ import annotations
import json
import yaml
from pathlib import Path


class LoadError(Exception):
    pass


def load_skill_file(path: str | Path) -> dict:
    """Load a skill definition from a YAML or JSON file.

    Args:
        path: Path to the skill file.

    Returns:
        Raw dict representation of the skill.

    Raises:
        LoadError: If the file cannot be read or parsed.
    """
    p = Path(path)
    if not p.exists():
        raise LoadError(f"File not found: {path}")

    suffix = p.suffix.lower()
    if suffix not in (".yaml", ".yml", ".json"):
        raise LoadError(f"Unsupported format '{suffix}'. Only YAML and JSON are supported.")

    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise LoadError(f"Cannot read file {path}: {e}") from e

    try:
        if suffix == ".json":
            return json.loads(text)
        else:
            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                raise LoadError(f"Expected a YAML mapping at top level, got {type(data).__name__}")
            return data
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise LoadError(f"Parse error in {path}: {e}") from e
