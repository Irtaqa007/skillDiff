"""Tests for the Risk Engine."""
from skilldiff.normalizer import normalize
from skilldiff.semantic_engine import compare
from skilldiff.risk_engine import score
from skilldiff.models import Change, DiffResult


def _diff(old_data, new_data):
    old = normalize(old_data)
    new = normalize(new_data)
    result = compare(old, new)
    return score(result)


def test_no_changes_zero_risk():
    s = normalize({"tools": ["web_search"]})
    result = compare(s, s)
    scored = score(result)
    assert scored.risk_score == 0
    assert scored.risk_level == "None"


def test_shell_permission_is_critical():
    result = _diff({}, {"permissions": ["shell.execute"]})
    shell_changes = [c for c in result.changes if "shell" in c.field]
    assert any(c.severity == "Critical" for c in shell_changes)


def test_filesystem_write_is_critical():
    result = _diff(
        {"permissions": ["filesystem.read"]},
        {"permissions": ["filesystem.read", "filesystem.write"]},
    )
    write_changes = [c for c in result.changes if "write" in c.field]
    assert any(c.severity == "Critical" for c in write_changes)


def test_risk_score_accumulates():
    result = _diff(
        {},
        {
            "permissions": ["filesystem.write", "shell.execute"],
            "tools": ["send_email"],
        },
    )
    assert result.risk_score > 0


def test_risk_level_critical_on_high_score():
    result = _diff(
        {},
        {"permissions": ["shell.execute", "filesystem.write", "database", "camera", "microphone"]},
    )
    assert result.risk_level in ("Critical", "High")


def test_critical_changes_property():
    result = _diff({}, {"permissions": ["shell.execute"]})
    assert len(result.critical_changes) >= 1
