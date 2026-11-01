"""Command-line entry point."""
import json
import sys

import click

from orbit.config import VERSION


def print_tool_table() -> None:
    """Print a Rich table of tool install/compatibility status (no TUI)."""
    from rich.console import Console
    from rich.table import Table

    from orbit.core.platform_check import check_platform
    from orbit.core.tools import all_tools

    plat = check_platform()
    table = Table(box=None, pad_edge=False, header_style="bold")
    for col in ("Tool", "Installed", "Compatible", "Version"):
        table.add_column(col)
    for tool in all_tools():
        ok = tool.compatible(plat)
        version = tool.installed_version() if ok else None
        if not ok:
            compat = "[red]✗ No[/red]"
        elif len(tool.supported_os) == 1:
            compat = f"[green]✓ {tool.supported_os[0].title()}[/green]"
        else:
            compat = "[green]✓ Yes[/green]"
        table.add_row(tool.display,
                      "[green]✓ Yes[/green]" if version else "[red]✗ No[/red]",
                      compat, version or "—")
    console = Console()
    console.print(f"[bold]ORBIT v{VERSION} — Tool Status[/bold]\n")
    console.print(table)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--dry-run", is_flag=True,
              help="Skip real tool execution; play back fixture JSON and run the full pipeline.")
@click.option("--headless", is_flag=True,
              help="Run without the TUI and print a JSON summary to stdout (exit 1 on tool failure).")
@click.option("--json", "json_out", is_flag=True,
              help="With --headless: print JSON (this is the default headless output).")
@click.option("--tools", "tools_arg", default="", metavar="NAMES",
              help="With --headless: comma-separated tools, e.g. scubagear,maester "
                   "(default: selection from ~/.orbit/config.toml).")
@click.option("--list-tools", "list_tools", is_flag=True,
              help="Print installed/compatibility status for each tool and exit.")
@click.option("--export-profile", "export_profile", default="", metavar="FILE",
              help="Export current settings to a JSON profile file and exit.")
@click.option("--import-profile", "import_profile", default="", metavar="FILE",
              help="Import settings from a JSON profile file and exit.")
@click.version_option(VERSION, prog_name="ORBIT")
def main(dry_run: bool, headless: bool, json_out: bool, tools_arg: str,
         list_tools: bool, export_profile: str, import_profile: str) -> None:
    """ORBIT - Office 365 Risk & Baseline Intelligence Toolkit (TUI)."""
    if export_profile:
        from pathlib import Path
        from orbit.core.profile import export_profile as do_export
        dest = Path(export_profile)
        do_export(dest)
        click.echo(f"Profile exported to {dest}")
        sys.exit(0)

    if import_profile:
        from pathlib import Path
        from orbit.core.profile import import_profile as do_import
        src = Path(import_profile)
        if not src.exists():
            click.echo(f"orbit: file not found: {src}", err=True)
            sys.exit(1)
        do_import(src)
        click.echo(f"Profile imported from {src}")
        sys.exit(0)

    if list_tools:
        print_tool_table()
        sys.exit(0)

    if headless:
        from orbit.core.headless import HeadlessError, run_headless

        names = [n.strip().lower() for n in tools_arg.split(",") if n.strip()]
        try:
            payload, code = run_headless(dry_run, names)
        except HeadlessError as exc:
            click.echo(f"orbit: {exc}", err=True)
            sys.exit(1)
        click.echo(json.dumps(payload, indent=2))
        sys.exit(code)

    from orbit.tui.app import OrbitApp

    OrbitApp(dry_run=dry_run).run()
