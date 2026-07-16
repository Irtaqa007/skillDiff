"""Semantic Change Engine — detects behavioral differences between two SkillModels."""
from __future__ import annotations
from .models import SkillModel, Change, DiffResult


def _compare_prompts(old: SkillModel, new: SkillModel, changes: list[Change]) -> None:
    """Detect capability expansion or reduction in prompts."""
    fields = [
        ("system", "System prompt"),
        ("user", "User prompt template"),
        ("instructions", "Instructions"),
    ]
    for key, label in fields:
        old_val = old.prompt.get(key, "") or ""
        new_val = new.prompt.get(key, "") or ""
        if old_val == new_val:
            continue
        # Detect expansion vs reduction
        old_len = len(old_val)
        new_len = len(new_val)
        if new_len > old_len:
            direction = "expanded"
            description = f"{label} expanded — AI may have new capabilities"
        elif new_len < old_len:
            direction = "reduced"
            description = f"{label} reduced — AI may have fewer capabilities"
        else:
            direction = "modified"
            description = f"{label} modified with same length — behavior may have changed"
        changes.append(Change(
            category="prompt",
            field=key,
            old_value=old_val[:120] + "..." if len(old_val) > 120 else old_val,
            new_value=new_val[:120] + "..." if len(new_val) > 120 else new_val,
            description=description,
            severity="Medium",
            recommendation=f"Review {label.lower()} changes carefully before deploying.",
        ))


def _compare_tools(old: SkillModel, new: SkillModel, changes: list[Change]) -> None:
    """Detect added, removed, or modified tools."""
    old_names = old.tool_names
    new_names = new.tool_names

    added = new_names - old_names
    removed = old_names - new_names
    common = old_names & new_names

    for name in sorted(added):
        changes.append(Change(
            category="tools",
            field=name,
            old_value=None,
            new_value=name,
            description=f"Tool '{name}' was added — new capability granted",
            severity="High",
            recommendation=f"Verify that '{name}' is intentionally granted and follows least-privilege.",
        ))

    for name in sorted(removed):
        changes.append(Change(
            category="tools",
            field=name,
            old_value=name,
            new_value=None,
            description=f"Tool '{name}' was removed — capability revoked",
            severity="Low",
            recommendation=f"Confirm removal of '{name}' is intentional.",
        ))

    # Check for modified tool definitions
    old_tool_map = {t.get("name", ""): t for t in old.tools}
    new_tool_map = {t.get("name", ""): t for t in new.tools}
    for name in sorted(common):
        if old_tool_map.get(name) != new_tool_map.get(name):
            changes.append(Change(
                category="tools",
                field=name,
                old_value=old_tool_map.get(name),
                new_value=new_tool_map.get(name),
                description=f"Tool '{name}' definition was modified",
                severity="Medium",
                recommendation=f"Review changes to '{name}' tool definition.",
            ))


def _compare_permissions(old: SkillModel, new: SkillModel, changes: list[Change]) -> None:
    """Detect added or removed permissions."""
    old_perms = old.permission_set
    new_perms = new.permission_set

    for perm in sorted(new_perms - old_perms):
        changes.append(Change(
            category="permissions",
            field=perm,
            old_value=None,
            new_value=perm,
            description=f"Permission '{perm}' was granted",
            severity="High",
            recommendation=f"Verify '{perm}' is required and follows least-privilege.",
        ))

    for perm in sorted(old_perms - new_perms):
        changes.append(Change(
            category="permissions",
            field=perm,
            old_value=perm,
            new_value=None,
            description=f"Permission '{perm}' was revoked",
            severity="Low",
            recommendation=f"Confirm revocation of '{perm}' is intentional.",
        ))


def _compare_model(old: SkillModel, new: SkillModel, changes: list[Change]) -> None:
    """Detect model, provider, context window, or temperature changes."""
    fields = [
        ("name", "Model name", "High"),
        ("provider", "Model provider", "High"),
        ("context_window", "Context window", "Medium"),
        ("temperature", "Temperature", "Medium"),
        ("max_tokens", "Max tokens", "Low"),
        ("version", "Model version", "Low"),
    ]
    for key, label, severity in fields:
        old_val = old.model.get(key)
        new_val = new.model.get(key)
        if old_val != new_val and not (old_val is None and new_val is None):
            changes.append(Change(
                category="model",
                field=key,
                old_value=old_val,
                new_value=new_val,
                description=f"{label} changed: {old_val!r} → {new_val!r}",
                severity=severity,
                recommendation=f"Validate behavior with new {label.lower()} before production deployment.",
            ))


def _compare_network(old: SkillModel, new: SkillModel, changes: list[Change]) -> None:
    """Detect new domains, removed domains, or modified endpoints."""
    old_domains = set(old.network.get("allowed_domains", []))
    new_domains = set(new.network.get("allowed_domains", []))

    for domain in sorted(new_domains - old_domains):
        changes.append(Change(
            category="network",
            field=domain,
            old_value=None,
            new_value=domain,
            description=f"Network access to '{domain}' was added",
            severity="Medium",
            recommendation=f"Verify '{domain}' is a trusted and necessary endpoint.",
        ))

    for domain in sorted(old_domains - new_domains):
        changes.append(Change(
            category="network",
            field=domain,
            old_value=domain,
            new_value=None,
            description=f"Network access to '{domain}' was removed",
            severity="Low",
            recommendation="Confirm this domain removal is intentional.",
        ))


def _compare_resources(old: SkillModel, new: SkillModel, changes: list[Change]) -> None:
    """Detect changes to files, databases, or knowledge sources."""
    old_res = {str(r): r for r in old.resources}
    new_res = {str(r): r for r in new.resources}

    for key in sorted(set(new_res) - set(old_res)):
        changes.append(Change(
            category="resources",
            field=key,
            old_value=None,
            new_value=new_res[key],
            description=f"Resource added: {key}",
            severity="Medium",
            recommendation="Verify the new resource is intentionally accessible.",
        ))

    for key in sorted(set(old_res) - set(new_res)):
        changes.append(Change(
            category="resources",
            field=key,
            old_value=old_res[key],
            new_value=None,
            description=f"Resource removed: {key}",
            severity="Low",
            recommendation="Confirm resource removal is intentional.",
        ))


def compare(old: SkillModel, new: SkillModel) -> DiffResult:
    """Compare two normalized SkillModels and return a DiffResult."""
    changes: list[Change] = []

    _compare_prompts(old, new, changes)
    _compare_tools(old, new, changes)
    _compare_permissions(old, new, changes)
    _compare_model(old, new, changes)
    _compare_network(old, new, changes)
    _compare_resources(old, new, changes)

    result = DiffResult(old_skill=old, new_skill=new, changes=changes)
    return result
