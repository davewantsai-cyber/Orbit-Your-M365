"""Shared TUI helpers."""
from __future__ import annotations

from orbit.core.platform_check import check_platform
from orbit.core.tools.base import STATUS_GLYPH, Tool


def dashboard_text(tools: list[Tool]) -> str:
    plat = check_platform()
    lines = ["[bold cyan]Tool status[/bold cyan]"]
    for t in tools:
        # Version probes shell out (pwsh / pip); latest-version lookup is left to the installer screen.
        installed = t.installed_version() if t.compatible(plat) else None
        st = t.status(plat, installed)
        ver = f" [bright_blue]{installed}[/bright_blue]" if installed else ""
        lines.append(f"  {t.display:<10} {STATUS_GLYPH[st]}{ver}")
    return "\n".join(lines)
