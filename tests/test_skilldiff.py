"""
Tests for SkillDiff core components.
"""

from __future__ import annotations
import json
import textwrap
from pathlib import Path

import pytest
import yaml

from skilldiff.loader import LoadError, load_skill_file
from skilldiff.normalizer import normalize
from skilldiff.models import SkillModel
from skilldiff.semantic_engine import compare
from skilldiff.risk_engine import score


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def old_skill_dict():
    return {
        "metadata": {"name": "test-skill", "version": "1.0"},
        "model": {"name": "gpt-4o-mini", "provider": "openai", "temperature": 0.2},
        "prompt": "Summarize the document.",
        "tools": ["read_document"],
        "permissions": ["filesystem.read"],
        "resources": ["docs_folder"],
        "network": {"allowed_domains": ["internal.company.com"]},
    }


@pytest.fixture
def new_skill_dict():
    return {
        "metadata": {"name": "test-skill", "version": "2.0"},
        "model": {"name": "gpt-4o", "provider": "openai", "temperature": 0.9},
        "prompt": "Summarize the document and send an email with the results.",
        "tools": ["read_document", "send_email"],
        "permissions": ["filesystem.read", "filesystem.write", "shell.execute"],
        "resources": ["docs_folder", "email_templates"],
        "network": {"allowed_domains": ["internal.company.com", "smtp.mail.com"]},
    }


# ── Loader tests ───────────────────────────────────────────────────────────────

class TestLoader:
    def test_load_yaml(self, tmp_path: Path, old_skill_dict):
        p = tmp_path / "skill.yaml"
        p.write_text(yaml.dump(old_skill_dict), encoding="utf-8")
        data = load_skill_file(p)
        assert data["metadata"]["name"] == "test-skill"

    def test_load_json(self, tmp_path: Path, old_skill_dict):
        p = tmp_path / "skill.json"
        p.write_text(json.dumps(old_skill_dict), encoding="utf-8")
        data = load_skill_file(p)
        assert data["metadata"]["name"] == "test-skill"

    def test_missing_file_raises(self):
        with pytest.raises(LoadError, match="not found"):
            load_skill_file("/nonexistent/path/skill.yaml")

    def test_unsupported_extension_raises(self, tmp_path: Path):
        p = tmp_path / "skill.txt"
        p.write_text("name: test", encoding="utf-8")
        with pytest.raises(LoadError, match="Unsupported"):
            load_skill_file(p)

    def test_invalid_yaml_raises(self, tmp_path: Path):
        p = tmp_path / "bad.yaml"
        p.write_text("key: [unclosed", encoding="utf-8")
        with pytest.raises(LoadError, match="Parse error"):
            load_skill_file(p)

    def test_non_mapping_root_raises(self, tmp_path: Path):
        p = tmp_path / "list.yaml"
        p.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(LoadError, match="mapping"):
            load_skill_file(p)


# ── Normalizer tests ───────────────────────────────────────────────────────────

class TestNormalizer:
    def test_produces_skill_model(self, old_skill_dict):
        model = normalize(old_skill_dict)
        assert isinstance(model, SkillModel)

    def test_metadata_extracted(self, old_skill_dict):
        model = normalize(old_skill_dict)
        assert model.metadata.name == "test-skill"
        assert model.metadata.version == "1.0"

    def test_prompt_extracted(self, old_skill_dict):
        model = normalize(old_skill_dict)
        assert "Summarize" in model.prompt

    def test_tools_list(self, old_skill_dict):
        model = normalize(old_skill_dict)
        assert "read_document" in model.tools

    def test_permissions_list(self, old_skill_dict):
        model = normalize(old_skill_dict)
        assert "filesystem.read" in model.permissions

    def test_empty_dict_safe(self):
        model = normalize({})
        assert isinstance(model, SkillModel)
        assert model.prompt == ""
        assert model.tools == []

    def test_single_tool_coerced_to_list(self):
        model = normalize({"tools": "read_document"})
        assert model.tools == ["read_document"]


# ── Semantic engine tests ──────────────────────────────────────────────────────

class TestSemanticEngine:
    def test_no_changes_identical(self, old_skill_dict):
        old = normalize(old_skill_dict)
        result = compare(old, old, "old.yaml", "new.yaml")
        assert not result.has_changes

    def test_detects_tool_added(self, old_skill_dict, new_skill_dict):
        old = normalize(old_skill_dict)
        new = normalize(new_skill_dict)
        result = compare(old, new, "old.yaml", "new.yaml")
        fields = [c.field for c in result.changes]
        assert "tools" in fields

    def test_detects_permission_added(self, old_skill_dict, new_skill_dict):
        old = normalize(old_skill_dict)
        new = normalize(new_skill_dict)
        result = compare(old, new, "old.yaml", "new.yaml")
        perm_changes = [c for c in result.changes if c.field == "permissions"]
        added_perms = [c.new_value for c in perm_changes if c.change_type == "added"]
        assert "shell.execute" in added_perms

    def test_detects_model_change(self, old_skill_dict, new_skill_dict):
        old = normalize(old_skill_dict)
        new = normalize(new_skill_dict)
        result = compare(old, new, "old.yaml", "new.yaml")
        model_changes = [c for c in result.changes if "model." in c.field]
        assert len(model_changes) > 0

    def test_shell_execute_is_critical(self, old_skill_dict, new_skill_dict):
        old = normalize(old_skill_dict)
        new = normalize(new_skill_dict)
        result = compare(old, new, "old.yaml", "new.yaml")
        shell_changes = [
            c for c in result.changes
            if c.field == "permissions" and c.new_value == "shell.execute"
        ]
        assert shell_changes[0].severity == "critical"

    def test_prompt_expansion_detected(self):
        old = normalize({"prompt": "Summarize the report."})
        new = normalize({"prompt": "Summarize the report and send an email."})
        result = compare(old, new, "old.yaml", "new.yaml")
        prompt_changes = [c for c in result.changes if c.field == "prompt"]
        assert len(prompt_changes) == 1
        assert prompt_changes[0].severity in ("high", "medium")


# ── Risk engine tests ──────────────────────────────────────────────────────────

class TestRiskEngine:
    def test_zero_score_no_changes(self, old_skill_dict):
        old = normalize(old_skill_dict)
        result = compare(old, old, "old.yaml", "new.yaml")
        result = score(result)
        assert result.risk_score == 0
        assert result.risk_level == "none"

    def test_critical_permission_raises_score(self, old_skill_dict, new_skill_dict):
        old = normalize(old_skill_dict)
        new = normalize(new_skill_dict)
        result = compare(old, new, "old.yaml", "new.yaml")
        result = score(result)
        assert result.risk_score > 0
        assert result.risk_level in ("medium", "high", "critical")

    def test_risk_level_is_valid(self, old_skill_dict, new_skill_dict):
        old = normalize(old_skill_dict)
        new = normalize(new_skill_dict)
        result = score(compare(old, new, "old.yaml", "new.yaml"))
        assert result.risk_level in ("none", "low", "medium", "high", "critical")
