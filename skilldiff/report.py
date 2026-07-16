"""
report.py — Report generation for SkillDiff results.

Produces three outputs:
  - Rich CLI report (terminal)
  - JSON report (machine-readable)
  - HTML report (printable enterprise report)
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from skilldiff.models import Change, DiffResult

console = Console()

_SEVERITY_COLORS = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "cyan",
    "info": "dim",
}

_RISK_COLORS = {
    "none": "green",
    "low": "cyan",
    "medium": "yellow",
    "high": "red",
    "critical": "bold red",
}


# ── CLI Report ─────────────────────────────────────────────────────────────────

def render_cli(result: DiffResult) -> None:
    """Print a Rich CLI report to stdout."""

    # Header
    console.print()
    console.print(Panel(
        f"[bold]SkillDiff[/bold] — Behavioral Change Report\n"
        f"[dim]Old:[/dim] {result.old_path}\n"
        f"[dim]New:[/dim] {result.new_path}",
        title="[bold blue]SKILLDIFF[/bold blue]",
        border_style="blue",
    ))

    if not result.has_changes:
        console.print("\n[green]✓ No behavioral changes detected.[/green]\n")
        return

    # Risk summary
    risk_color = _RISK_COLORS.get(result.risk_level, "white")
    console.print(
        f"\n[bold]Risk Score:[/bold] [{risk_color}]{result.risk_score}[/{risk_color}]  "
        f"[bold]Risk Level:[/bold] [{risk_color}]{result.risk_level.upper()}[/{risk_color}]  "
        f"[bold]Changes:[/bold] {len(result.changes)}  "
        f"[red]Critical: {result.critical_count}[/red]  "
        f"[yellow]High: {result.high_count}[/yellow]"
    )
    console.print()

    # Changes table
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on dark_blue",
        expand=True,
    )
    table.add_column("Field", style="bold", min_width=20)
    table.add_column("Type", min_width=10)
    table.add_column("Severity", min_width=10)
    table.add_column("Description", ratio=2)
    table.add_column("Recommendation", ratio=2)

    for change in result.changes:
        color = _SEVERITY_COLORS.get(change.severity, "white")
        table.add_row(
            change.field,
            change.change_type,
            f"[{color}]{change.severity.upper()}[/{color}]",
            change.description,
            change.recommendation,
        )

    console.print(table)
    console.print()


# ── JSON Report ────────────────────────────────────────────────────────────────

def render_json(result: DiffResult) -> str:
    """Serialize DiffResult to a JSON string."""

    def _change_to_dict(c: Change) -> dict[str, Any]:
        return {
            "field": c.field,
            "change_type": c.change_type,
            "old_value": c.old_value,
            "new_value": c.new_value,
            "description": c.description,
            "severity": c.severity,
            "recommendation": c.recommendation,
        }

    payload = {
        "skilldiff_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_path": result.old_path,
        "new_path": result.new_path,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "change_count": len(result.changes),
        "critical_count": result.critical_count,
        "high_count": result.high_count,
        "changes": [_change_to_dict(c) for c in result.changes],
    }
    return json.dumps(payload, indent=2, default=str)


# ── HTML Report ────────────────────────────────────────────────────────────────

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SkillDiff Report</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f4f6f9; color: #1a1a2e; font-size: 14px; }
  header { background: #1a2b4c; color: white; padding: 24px 32px; }
  header h1 { font-size: 22px; font-weight: 700; letter-spacing: 1px; }
  header p  { font-size: 12px; opacity: 0.7; margin-top: 4px; }
  .container { max-width: 1100px; margin: 32px auto; padding: 0 24px; }
  .summary { background: white; border-radius: 8px; padding: 20px 24px;
             margin-bottom: 24px; display: flex; gap: 40px;
             box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  .metric label { font-size: 11px; text-transform: uppercase; letter-spacing: .5px;
                  color: #666; display: block; margin-bottom: 4px; }
  .metric value { font-size: 28px; font-weight: 700; }
  .none    { color: #22c55e; }
  .low     { color: #06b6d4; }
  .medium  { color: #f59e0b; }
  .high    { color: #ef4444; }
  .critical{ color: #dc2626; }
  table { width: 100%; border-collapse: collapse; background: white;
          border-radius: 8px; overflow: hidden;
          box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  th { background: #1a2b4c; color: white; padding: 12px 16px;
       text-align: left; font-size: 12px; text-transform: uppercase; }
  td { padding: 12px 16px; border-bottom: 1px solid #f0f0f0;
       vertical-align: top; font-size: 13px; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #f8f9fb; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
           font-size: 11px; font-weight: 600; text-transform: uppercase; }
  .badge-critical { background: #fee2e2; color: #dc2626; }
  .badge-high     { background: #fee2e2; color: #ef4444; }
  .badge-medium   { background: #fef3c7; color: #d97706; }
  .badge-low      { background: #cffafe; color: #0891b2; }
  .badge-info     { background: #f3f4f6; color: #6b7280; }
  .no-changes { background: white; border-radius: 8px; padding: 32px;
                text-align: center; color: #22c55e; font-size: 16px;
                box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  footer { text-align: center; color: #999; font-size: 11px;
           margin: 32px 0; }
</style>
</head>
<body>
<header>
  <h1>SKILLDIFF — Behavioral Change Report</h1>
  <p>Generated {{ generated_at }}</p>
</header>
<div class="container">
  <div class="summary">
    <div class="metric">
      <label>Risk Score</label>
      <value class="{{ risk_level }}">{{ risk_score }}</value>
    </div>
    <div class="metric">
      <label>Risk Level</label>
      <value class="{{ risk_level }}">{{ risk_level|upper }}</value>
    </div>
    <div class="metric">
      <label>Changes</label>
      <value>{{ change_count }}</value>
    </div>
    <div class="metric">
      <label>Critical</label>
      <value class="critical">{{ critical_count }}</value>
    </div>
    <div class="metric">
      <label>Old Skill</label>
      <value style="font-size:14px;margin-top:6px">{{ old_path }}</value>
    </div>
    <div class="metric">
      <label>New Skill</label>
      <value style="font-size:14px;margin-top:6px">{{ new_path }}</value>
    </div>
  </div>

  {% if changes %}
  <table>
    <thead>
      <tr>
        <th>Field</th>
        <th>Type</th>
        <th>Severity</th>
        <th>Description</th>
        <th>Recommendation</th>
      </tr>
    </thead>
    <tbody>
    {% for c in changes %}
      <tr>
        <td><strong>{{ c.field }}</strong></td>
        <td>{{ c.change_type }}</td>
        <td><span class="badge badge-{{ c.severity }}">{{ c.severity }}</span></td>
        <td>{{ c.description }}</td>
        <td>{{ c.recommendation }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="no-changes">✓ No behavioral changes detected.</div>
  {% endif %}
</div>
<footer>SkillDiff 0.1.0 — Air-gap compatible • No LLM required • Deterministic</footer>
</body>
</html>
"""


def render_html(result: DiffResult) -> str:
    """Render an HTML report for the diff result."""
    from jinja2 import Environment

    env = Environment(autoescape=True)
    template = env.from_string(_HTML_TEMPLATE)

    changes_dicts = [
        {
            "field": c.field,
            "change_type": c.change_type,
            "severity": c.severity,
            "description": c.description,
            "recommendation": c.recommendation,
        }
        for c in result.changes
    ]

    return template.render(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        change_count=len(result.changes),
        critical_count=result.critical_count,
        old_path=result.old_path,
        new_path=result.new_path,
        changes=changes_dicts,
    )
