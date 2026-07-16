"""Tests for the Normalizer module."""
from skilldiff.normalizer import normalize
from skilldiff.models import SkillModel


def test_normalize_basic():
    raw = {
        "model": {"name": "gpt-4", "temperature": 0.5},
        "system_prompt": "You are helpful.",
        "tools": ["web_search", "read_file"],
        "permissions": ["filesystem.read"],
    }
    skill = normalize(raw)
    assert isinstance(skill, SkillModel)
    assert skill.model["name"] == "gpt-4"
    assert skill.prompt["system"] == "You are helpful."
    assert len(skill.tools) == 2
    assert "filesystem.read" in skill.permissions


def test_normalize_empty():
    skill = normalize({})
    assert skill.tools == []
    assert skill.permissions == []
    assert skill.model == {}


def test_normalize_string_tools_become_dicts():
    raw = {"tools": ["web_search", "send_email"]}
    skill = normalize(raw)
    assert skill.tools[0] == {"name": "web_search"}
    assert skill.tools[1] == {"name": "send_email"}


def test_normalize_permission_dict():
    raw = {
        "permissions": {
            "filesystem": ["read", "write"],
            "internet": True,
        }
    }
    skill = normalize(raw)
    assert "filesystem.read" in skill.permissions
    assert "filesystem.write" in skill.permissions
    assert "internet" in skill.permissions


def test_normalize_nested_skill_key():
    raw = {"skill": {"model": {"name": "claude-3"}, "tools": ["bash"]}}
    skill = normalize(raw)
    assert skill.model["name"] == "claude-3"


def test_normalize_tool_names_property():
    raw = {"tools": ["web_search", "send_email"]}
    skill = normalize(raw)
    assert skill.tool_names == {"web_search", "send_email"}
