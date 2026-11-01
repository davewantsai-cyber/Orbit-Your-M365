"""Command-line entry point."""
import json
import sys

import click

from orbit.config import VERSION


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
@click.version_option(VERSION, prog_name="ORBIT")
def main(dry_run: bool, headless: bool, json_out: bool, tools_arg: str) -> None:
    """ORBIT - Office 365 Risk & Baseline Intelligence Toolkit (TUI)."""
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
