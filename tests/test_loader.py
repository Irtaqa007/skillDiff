"""Tests for the Loader module."""
import json
import pytest
import yaml
from pathlib import Path
from skilldiff.loader import load_skill_file, LoadError


def test_load_yaml(tmp_path):
    f = tmp_path / "skill.yaml"
    f.write_text("name: test\nmodel:\n  name: gpt-4\n")
    result = load_skill_file(f)
    assert result["name"] == "test"


def test_load_json(tmp_path):
    f = tmp_path / "skill.json"
    f.write_text(json.dumps({"name": "test", "model": {"name": "gpt-4"}}))
    result = load_skill_file(f)
    assert result["name"] == "test"


def test_load_missing_file():
    with pytest.raises(LoadError, match="File not found"):
        load_skill_file("/nonexistent/path/skill.yaml")


def test_load_unsupported_format(tmp_path):
    f = tmp_path / "skill.txt"
    f.write_text("hello")
    with pytest.raises(LoadError, match="Unsupported format"):
        load_skill_file(f)


def test_load_invalid_yaml(tmp_path):
    f = tmp_path / "skill.yaml"
    f.write_text("key: [unclosed bracket")
    with pytest.raises(LoadError, match="Parse error"):
        load_skill_file(f)


def test_load_invalid_json(tmp_path):
    f = tmp_path / "skill.json"
    f.write_text("{invalid json")
    with pytest.raises(LoadError, match="Parse error"):
        load_skill_file(f)


def test_load_real_example():
    path = Path(__file__).parent.parent / "examples" / "old_skill.yaml"
    result = load_skill_file(path)
    assert "metadata" in result
    assert "model" in result
