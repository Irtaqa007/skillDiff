"""CLI entry point for SkillDiff."""
from __future__ import annotations
import sys
from pathlib import Path

import click
from rich.console import Console

from .utils import diff_files
from .report import print_cli_report, to_json, to_html
from .loader import LoadError

console = Console()
__version__ = "0.1.0"


@click.group()
@click.version_option(version=__version__, prog_name="skilldiff")
def cli() -> None:
    """SkillDiff — compare AI skill versions and detect behavioral changes."""


@cli.command()
@click.argument("old_skill", type=click.Path(exists=True))
@click.argument("new_skill", type=click.Path(exists=True))
@click.option("--rules", default=None, help="Path to custom rules YAML file.")
@click.option("--json", "output_json", is_flag=True, help="Output JSON report to stdout.")
@click.option("--html", "output_html", default=None, help="Write HTML report to file.")
def compare(old_skill: str, new_skill: str, rules: str | None,
            output_json: bool, output_html: str | None) -> None:
    """Compare two skill files and report behavioral changes.

    \b
    Examples:
      skilldiff compare old.yaml new.yaml
      skilldiff compare old.yaml new.yaml --json
      skilldiff compare old.yaml new.yaml --html report.html
    """
    try:
        result = diff_files(old_skill, new_skill, rules_path=rules)
    except LoadError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    if output_json:
        click.echo(to_json(result, old_skill, new_skill))
        return

    if output_html:
        html = to_html(result, old_skill, new_skill)
        Path(output_html).write_text(html, encoding="utf-8")
        console.print(f"[green]HTML report written to:[/green] {output_html}")

    print_cli_report(result, old_skill, new_skill)

    # Exit code 1 if critical changes found
    if result.critical_changes:
        sys.exit(1)


@cli.command()
@click.argument("old_skill", type=click.Path(exists=True))
@click.argument("new_skill", type=click.Path(exists=True))
@click.option("--output", "-o", default="report.html", help="Output HTML file path.")
@click.option("--rules", default=None, help="Path to custom rules YAML file.")
def report(old_skill: str, new_skill: str, output: str, rules: str | None) -> None:
    """Generate an HTML report for two skill files.

    \b
    Example:
      skilldiff report old.yaml new.yaml -o report.html
    """
    try:
        result = diff_files(old_skill, new_skill, rules_path=rules)
    except LoadError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    html = to_html(result, old_skill, new_skill)
    Path(output).write_text(html, encoding="utf-8")
    console.print(f"[green]✓ HTML report written to:[/green] {output}")
    print_cli_report(result, old_skill, new_skill)
