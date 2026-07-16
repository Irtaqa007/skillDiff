"""
semantic_engine.py — Detects behavioral changes between two SkillModel instances.

Compares normalized models field by field and produces Change objects
describing what the AI can now do differently. No AI or LLM required.
"""

from __future__ import annotations
from skilldiff.models import Change, DiffResult, SkillModel


def compare(old: SkillModel, new: SkillModel, old_path: str, new_path: str) -> DiffResult:
    """
    Compare two normalized skill models and return a DiffResult.

    Args:
        old: Normalized old skill version.
        new: Normalized new skill version.
        old_path: Path string for old file (for reporting).
        new_path: Path string for new file (for reporting).

    Returns:
        DiffResult containing all detected behavioral changes.
    """
    result = DiffResult(old_path=old_path, new_path=new_path)

    result.changes.extend(_compare_prompt(old.prompt, new.prompt))
    result.changes.extend(_compare_list_field("tools", old.tools, new.tools))
    result.changes.extend(_compare_permissions(old.permissions, new.permissions))
    result.changes.extend(_compare_model(old.model, new.model))
    result.changes.extend(_compare_list_field("resources", old.resources, new.resources))
    result.changes.extend(_compare_network(old.network, new.network))

    return result


# ── Prompt ────────────────────────────────────────────────────────────────────

def _compare_prompt(old: str, new: str) -> list[Change]:
    changes: list[Change] = []
    if old == new:
        return changes

    old_words = set(old.lower().split())
    new_words = set(new.lower().split())
    added_words = new_words - old_words

    # Detect capability expansion keywords
    expansion_signals = {
        "send", "write", "delete", "execute", "run", "deploy", "publish",
        "create", "modify", "update", "upload", "download", "access",
        "read", "fetch", "call", "invoke", "post", "submit", "share",
    }
    expansions = expansion_signals & added_words

    if expansions:
        description = (
            f"Prompt now contains action verbs not present in the old version: "
            f"{', '.join(sorted(expansions))}. This may indicate capability expansion."
        )
        severity = "high"
        recommendation = (
            "Review the new prompt carefully. Capability-expanding verbs suggest "
            "the skill may now perform actions beyond its original scope."
        )
    else:
        description = "Prompt text has changed. Review for unintended behavioral shifts."
        severity = "medium"
        recommendation = "Compare old and new prompt side by side to verify intent is preserved."

    changes.append(Change(
        field="prompt",
        change_type="modified",
        old_value=old[:200] + ("…" if len(old) > 200 else ""),
        new_value=new[:200] + ("…" if len(new) > 200 else ""),
        description=description,
        severity=severity,
        recommendation=recommendation,
    ))
    return changes


# ── List fields (tools, resources) ────────────────────────────────────────────

def _compare_list_field(field_name: str, old: list[str], new: list[str]) -> list[Change]:
    changes: list[Change] = []
    old_set, new_set = set(old), set(new)

    for item in sorted(new_set - old_set):
        changes.append(Change(
            field=field_name,
            change_type="added",
            old_value=None,
            new_value=item,
            description=f"New {field_name[:-1] if field_name.endswith('s') else field_name} added: '{item}'.",
            severity="medium",
            recommendation=f"Verify that '{item}' is intentionally granted and scoped correctly.",
        ))

    for item in sorted(old_set - new_set):
        changes.append(Change(
            field=field_name,
            change_type="removed",
            old_value=item,
            new_value=None,
            description=f"'{item}' removed from {field_name}.",
            severity="info",
            recommendation=f"Confirm removal of '{item}' is intentional and does not break downstream dependencies.",
        ))

    return changes


# ── Permissions ───────────────────────────────────────────────────────────────

# Permissions with elevated risk when added
_HIGH_RISK_PERMISSIONS = {
    "shell.execute", "filesystem.write", "camera", "microphone",
    "clipboard.write", "database.write", "internet",
}

_MEDIUM_RISK_PERMISSIONS = {
    "filesystem.read", "database.read", "clipboard.read", "network",
}


def _compare_permissions(old: list[str], new: list[str]) -> list[Change]:
    changes: list[Change] = []
    old_set, new_set = set(old), set(new)

    for perm in sorted(new_set - old_set):
        if perm in _HIGH_RISK_PERMISSIONS:
            severity = "critical"
            recommendation = (
                f"Permission '{perm}' grants significant system access. "
                "Require explicit security review before deploying."
            )
        elif perm in _MEDIUM_RISK_PERMISSIONS:
            severity = "high"
            recommendation = (
                f"Permission '{perm}' grants data access. "
                "Verify it is scoped to the minimum required data."
            )
        else:
            severity = "medium"
            recommendation = f"Review the scope and necessity of permission '{perm}'."

        changes.append(Change(
            field="permissions",
            change_type="added",
            old_value=None,
            new_value=perm,
            description=f"Permission granted: '{perm}'.",
            severity=severity,
            recommendation=recommendation,
        ))

    for perm in sorted(old_set - new_set):
        changes.append(Change(
            field="permissions",
            change_type="removed",
            old_value=perm,
            new_value=None,
            description=f"Permission revoked: '{perm}'.",
            severity="info",
            recommendation="Confirm removal is intentional. Ensure skill still functions correctly.",
        ))

    return changes


# ── Model ─────────────────────────────────────────────────────────────────────

def _compare_model(old: dict, new: dict) -> list[Change]:
    changes: list[Change] = []

    checks = [
        ("name", "Model changed", "high",
         "A different model may have different capabilities, safety properties, and failure modes."),
        ("provider", "Provider changed", "high",
         "Changing provider affects data residency, compliance posture, and API behavior."),
        ("context_window", "Context window changed", "low",
         "Larger context windows may allow ingestion of more data than intended."),
        ("temperature", "Temperature changed", "low",
         "Higher temperature increases output variability and unpredictability."),
    ]

    for key, desc, severity, recommendation in checks:
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val and not (old_val in (None, "") and new_val in (None, "")):
            changes.append(Change(
                field=f"model.{key}",
                change_type="modified",
                old_value=old_val,
                new_value=new_val,
                description=f"{desc}: '{old_val}' → '{new_val}'.",
                severity=severity,
                recommendation=recommendation,
            ))

    return changes


# ── Network ───────────────────────────────────────────────────────────────────

def _compare_network(old: dict, new: dict) -> list[Change]:
    changes: list[Change] = []

    old_domains = set(_coerce_list(old.get("allowed_domains", [])))
    new_domains = set(_coerce_list(new.get("allowed_domains", [])))

    for domain in sorted(new_domains - old_domains):
        changes.append(Change(
            field="network.allowed_domains",
            change_type="added",
            old_value=None,
            new_value=domain,
            description=f"New network domain allowed: '{domain}'.",
            severity="high",
            recommendation=(
                f"Verify '{domain}' is a trusted endpoint. "
                "New outbound domains may enable data exfiltration."
            ),
        ))

    for domain in sorted(old_domains - new_domains):
        changes.append(Change(
            field="network.allowed_domains",
            change_type="removed",
            old_value=domain,
            new_value=None,
            description=f"Network domain removed: '{domain}'.",
            severity="info",
            recommendation="Confirm removal is intentional.",
        ))

    return changes


def _coerce_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
