"""
cli.py — Command-line interface for SkillDiff.

Commands:
  skilldiff compare <old> <new>   — Compare two skill files, print CLI report
  skilldiff report <old> <new>    — Generate JSON + HTML reports to disk
  skilldiff version               — Print version
"""

from __future__ import annotations
import sys
from pathlib import Path

import click
from rich.console import Console

from skilldiff import __version__
from skilldiff.loader import LoadError, load_skill_file
from skilldiff.normalizer import normalize
from skilldiff.semantic_engine import compare as semantic_compare
from skilldiff.risk_engine import score
from skilldiff import report as reports

console = Console()
err_console = Console(stderr=True)


def _run_diff(old_path: str, new_path: str):
    """Shared pipeline: load -> normalize -> compare -> score."""
    try:
        old_raw = load_skill_file(old_path)
        new_raw = load_skill_file(new_path)
    except LoadError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    old_model = normalize(old_raw)
    new_model = normalize(new_raw)

    result = semantic_compare(old_model, new_model, old_path, new_path)
    result = score(result)
    return result


@click.group()
def main():
    """SkillDiff — Behavioral diff for AI skills.

    Detects what an AI can now do differently, assesses security implications,
    and generates enterprise-ready risk reports.

    Air-gap compatible. No LLM required. Deterministic.
    """


@main.command(name="compare")
@click.argument("old_skill", metavar="OLD")
@click.argument("new_skill", metavar="NEW")
def compare_cmd(old_skill: str, new_skill: str):
    """Compare OLD and NEW skill files and print a behavioral change report."""
    result = _run_diff(old_skill, new_skill)
    reports.render_cli(result)

    if result.risk_level in ("critical", "high"):
        sys.exit(2)
    elif result.has_changes:
        sys.exit(1)


@main.command(name="report")
@click.argument("old_skill", metavar="OLD")
@click.argument("new_skill", metavar="NEW")
@click.option("--out-dir", default=".", show_default=True,
              help="Directory to write report files into.")
def report_cmd(old_skill: str, new_skill: str, out_dir: str):
    """Generate JSON and HTML reports for OLD vs NEW skill comparison."""
    result = _run_diff(old_skill, new_skill)
    reports.render_cli(result)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "skilldiff_report.json"
    html_path = out / "skilldiff_report.html"

    json_path.write_text(reports.render_json(result), encoding="utf-8")
    html_path.write_text(reports.render_html(result), encoding="utf-8")

    console.print(f"\n[green]v[/green] JSON report -> {json_path}")
    console.print(f"[green]v[/green] HTML report -> {html_path}\n")


@main.command(name="version")
def version():
    """Print the SkillDiff version."""
    console.print(f"SkillDiff {__version__}")
