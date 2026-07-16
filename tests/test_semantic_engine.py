"""Tests for the Semantic Change Engine."""
from skilldiff.normalizer import normalize
from skilldiff.semantic_engine import compare
from skilldiff.models import DiffResult


def _skill(data):
    return normalize(data)


def test_no_changes_identical_skills():
    s = _skill({"model": {"name": "gpt-4"}, "tools": ["web_search"]})
    result = compare(s, s)
    assert not result.has_changes


def test_detect_prompt_expansion():
    old = _skill({"system_prompt": "Summarize reports."})
    new = _skill({"system_prompt": "Summarize reports and send emails to stakeholders."})
    result = compare(old, new)
    prompt_changes = [c for c in result.changes if c.category == "prompt"]
    assert len(prompt_changes) >= 1
    assert any("expanded" in c.description for c in prompt_changes)


def test_detect_tool_added():
    old = _skill({"tools": ["web_search"]})
    new = _skill({"tools": ["web_search", "send_email"]})
    result = compare(old, new)
    tool_changes = [c for c in result.changes if c.category == "tools" and c.new_value == "send_email"]
    assert len(tool_changes) == 1
    assert "added" in tool_changes[0].description


def test_detect_tool_removed():
    old = _skill({"tools": ["web_search", "read_file"]})
    new = _skill({"tools": ["web_search"]})
    result = compare(old, new)
    removed = [c for c in result.changes if c.category == "tools" and c.old_value == "read_file"]
    assert len(removed) == 1


def test_detect_permission_added():
    old = _skill({"permissions": ["filesystem.read"]})
    new = _skill({"permissions": ["filesystem.read", "filesystem.write"]})
    result = compare(old, new)
    perm_changes = [c for c in result.changes if c.category == "permissions" and "write" in c.field]
    assert len(perm_changes) == 1


def test_detect_model_change():
    old = _skill({"model": {"name": "gpt-4o-mini", "temperature": 0.3}})
    new = _skill({"model": {"name": "gpt-4o", "temperature": 0.7}})
    result = compare(old, new)
    model_changes = [c for c in result.changes if c.category == "model"]
    fields = {c.field for c in model_changes}
    assert "name" in fields
    assert "temperature" in fields


def test_detect_network_domain_added():
    old = _skill({"network": {"allowed_domains": ["api.internal.com"]}})
    new = _skill({"network": {"allowed_domains": ["api.internal.com", "external.io"]}})
    result = compare(old, new)
    net_changes = [c for c in result.changes if c.category == "network"]
    assert any("external.io" in c.field for c in net_changes)


def test_diff_result_has_changes_property():
    old = _skill({})
    new = _skill({"tools": ["shell"]})
    result = compare(old, new)
    assert result.has_changes
    assert isinstance(result, DiffResult)
