"""Command-line entry point."""
import click

from orbit.config import VERSION


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--dry-run", is_flag=True,
              help="Skip real tool execution; play back fixture JSON and run the full pipeline.")
@click.version_option(VERSION, prog_name="ORBIT")
def main(dry_run: bool) -> None:
    """ORBIT - Office 365 Risk & Baseline Intelligence Toolkit (TUI)."""
    from orbit.tui.app import OrbitApp

    OrbitApp(dry_run=dry_run).run()
