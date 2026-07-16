"""Report Generator — CLI (Rich), JSON, and HTML outputs."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from .models import DiffResult, Change

console = Console()

_SEVERITY_COLORS = {
    "Critical": "bold red",
    "High": "red",
    "Medium": "yellow",
    "Low": "cyan",
    "Info": "dim",
}

_RISK_COLORS = {
    "Critical": "bold red",
    "High": "red",
    "Medium": "yellow",
    "Low": "green",
    "None": "green",
}


def _severity_badge(severity: str) -> Text:
    color = _SEVERITY_COLORS.get(severity, "white")
    return Text(f" {severity} ", style=f"{color} on black")


def print_cli_report(result: DiffResult, old_path: str, new_path: str) -> None:
    """Print a rich, enterprise-grade CLI report."""
    ts = datetime.now().strftime("%Y-%m-%d %Human:%M:%S")

    # Header
    console.print()
    console.print(Panel(
        f"[bold white]SkillDiff Report[/bold white]\n"
        f"[dim]{ts}[/dim]\n\n"
        f"[dim]Old:[/dim] {old_path}\n"
        f"[dim]New:[/dim] {new_path}",
        border_style="blue",
        padding=(1, 2),
    ))

    if not result.has_changes:
        console.print(Panel(
            "[bold green]✓ No behavioral changes detected.[/bold green]",
            border_style="green",
        ))
        return

    # Risk score
    risk_color = _RISK_COLORS.get(result.risk_level, "white")
    console.print(Panel(
        f"[bold]Risk Score:[/bold] [{risk_color}]{result.risk_score}/100[/{risk_color}]  "
        f"[bold]Risk Level:[/bold] [{risk_color}]{result.risk_level}[/{risk_color}]\n"
        f"[dim]{len(result.changes)} change(s) detected — "
        f"{len(result.critical_changes)} critical, {len(result.high_changes)} high[/dim]",
        border_style=risk_color,
        title="[bold]Risk Summary[/bold]",
    ))

    # Changes table
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on dark_blue",
        border_style="dim",
        expand=True,
    )
    table.add_column("Category", style="bold", width=14)
    table.add_column("Field", width=22)
    table.add_column("Severity", width=10, justify="center")
    table.add_column("Description")
    table.add_column("Recommendation", style="dim")

    for change in sorted(result.changes, key=lambda c: list(_SEVERITY_COLORS).index(c.severity)):
        table.add_row(
            change.category.upper(),
            change.field,
            _severity_badge(change.severity),
            change.description,
            change.recommendation,
        )

    console.print()
    console.print(table)
    console.print()


def to_json(result: DiffResult, old_path: str, new_path: str) -> str:
    """Serialize DiffResult to a JSON string."""
    def _change_dict(c: Change) -> dict[str, Any]:
        return {
            "category": c.category,
            "field": c.field,
            "severity": c.severity,
            "description": c.description,
            "recommendation": c.recommendation,
            "old_value": str(c.old_value) if c.old_value is not None else None,
            "new_value": str(c.new_value) if c.new_value is not None else None,
        }

    return json.dumps({
        "generated_at": datetime.now().isoformat(),
        "old_skill": old_path,
        "new_skill": new_path,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "total_changes": len(result.changes),
        "changes": [_change_dict(c) for c in result.changes],
    }, indent=2)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SkillDiff Report</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f1117; color: #e6e9f0; margin: 0; padding: 2rem; }
  .container { max-width: 1100px; margin: 0 auto; }
  h1 { color: #fff; font-size: 1.6rem; margin-bottom: 0.25rem; }
  .meta { color: #6b7280; font-size: 0.85rem; margin-bottom: 2rem; }
  .risk-card { border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem;
               border: 1px solid; }
  .risk-None, .risk-Low { border-color: #22c55e; background: #052e16; }
  .risk-Medium { border-color: #f59e0b; background: #1c1002; }
  .risk-High { border-color: #ef4444; background: #1c0202; }
  .risk-Critical { border-color: #dc2626; background: #1c0000; }
  .score { font-size: 2rem; font-weight: 700; }
  table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
  th { background: #1e2333; color: #9ca3af; font-size: 0.75rem;
       text-transform: uppercase; letter-spacing: 0.05em;
       padding: 0.75rem 1rem; text-align: left; }
  td { padding: 0.75rem 1rem; border-bottom: 1px solid #1f2937;
       font-size: 0.875rem; vertical-align: top; }
  tr:hover td { background: #1a1f2e; }
  .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
           font-size: 0.75rem; font-weight: 600; }
  .Critical { background: #7f1d1d; color: #fca5a5; }
  .High { background: #431407; color: #fdba74; }
  .Medium { background: #422006; color: #fcd34d; }
  .Low { background: #052e16; color: #86efac; }
  .Info { background: #1e3a5f; color: #93c5fd; }
  .no-changes { text-align: center; padding: 3rem; color: #22c55e; font-size: 1.1rem; }
</style>
</head>
<body>
<div class="container">
  <h1>SkillDiff Report</h1>
  <div class="meta">Generated: {generated_at} &nbsp;|&nbsp;
    Old: <code>{old_path}</code> &nbsp;|&nbsp; New: <code>{new_path}</code>
  </div>
  <div class="risk-card risk-{risk_level}">
    <div class="score">{risk_score}/100</div>
    <div>Risk Level: <strong>{risk_level}</strong> &nbsp;|&nbsp;
      {total_changes} change(s)</div>
  </div>
  {body}
</div>
</body>
</html>"""


def to_html(result: DiffResult, old_path: str, new_path: str) -> str:
    """Generate an HTML report."""
    if not result.has_changes:
        body = '<div class="no-changes">✓ No behavioral changes detected.</div>'
    else:
        rows = ""
        for c in sorted(result.changes, key=lambda x: list(_SEVERITY_COLORS).index(x.severity)):
            rows += (
                f"<tr><td>{c.category.upper()}</td>"
                f"<td><code>{c.field}</code></td>"
                f"<td><span class='badge {c.severity}'>{c.severity}</span></td>"
                f"<td>{c.description}</td>"
                f"<td style='color:#9ca3af'>{c.recommendation}</td></tr>\n"
            )
        body = (
            "<table><thead><tr>"
            "<th>Category</th><th>Field</th><th>Severity</th>"
            "<th>Description</th><th>Recommendation</th>"
            "</tr></thead><tbody>"
            + rows
            + "</tbody></table>"
        )

    return _HTML_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        old_path=old_path,
        new_path=new_path,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        total_changes=len(result.changes),
        body=body,
    )
