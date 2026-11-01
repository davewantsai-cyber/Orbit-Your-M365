"""Home screen — full-width responsive layout."""
from __future__ import annotations

from rich.markup import escape
from rich.table import Table
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from orbit.core.admin_check import ADMIN_WARNING, is_elevated
from orbit.core.platform_check import check_platform
from orbit.tui.banner import AnimatedBanner


def _tool_table(tools: list) -> Table:
    """Rich Table of tool status — renders at full widget width."""
    from orbit.core.tools.base import STATUS_GLYPH, ToolStatus
    plat = check_platform()
    t = Table.grid(expand=True, padding=(0, 2))
    t.add_column("Tool",    style="#2a5a6a", min_width=12)
    t.add_column("Status",  min_width=22)
    t.add_column("Tool",    style="#2a5a6a", min_width=12)
    t.add_column("Status",  min_width=22)

    rows = []
    for tool in tools:
        inst = tool.installed_version() if tool.compatible(plat) else None
        st   = tool.status(plat, inst)
        ver  = f" [bright_blue]{inst}[/]" if inst else ""
        rows.append((f"[#4a8090]{tool.display}[/]", STATUS_GLYPH[st] + ver))

    # pair into 2-column rows
    for i in range(0, len(rows), 2):
        a = rows[i]
        b = rows[i + 1] if i + 1 < len(rows) else ("", "")
        t.add_row(a[0], a[1], b[0], b[1])
    return t


class HomeScreen(Screen):
    BINDINGS = [("q", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield AnimatedBanner(id="banner")
        yield Static("", id="admin-warning")
        with Horizontal(id="info-row"):
            yield Static("", id="sys-info")
            yield Static("", id="dashboard")
        with Horizontal(id="nav"):
            for label, target in [
                ("Credentials", "credentials"), ("Tools", "tool_select"),
                ("Installer", "installer"), ("Output", "output"),
                ("Run", "run"), ("Report", "report"),
            ]:
                yield Button(label, id=f"nav-{target}")
        yield Footer()

    def on_mount(self) -> None:
        info = check_platform()
        pw   = ".".join(map(str, info.pwsh_version)) if info.pwsh_version else "not found"
        self.query_one("#sys-info", Static).update(
            f"[dim]OS[/dim]          [bright_blue]{info.os_name}[/]\n"
            f"[dim]PowerShell[/dim]  [bright_blue]{escape(pw)}[/]\n"
            f"[dim]Python[/dim]      [bright_blue]{info.python_version}[/]"
            if hasattr(info, "python_version") else
            f"[dim]OS[/dim]          [bright_blue]{info.os_name}[/]\n"
            f"[dim]PowerShell[/dim]  [bright_blue]{escape(pw)}[/]"
        )
        if not is_elevated():
            self.query_one("#admin-warning", Static).update(
                "[bold red]⚠  NOT ELEVATED[/bold red]  "
                f"[dim]{ADMIN_WARNING}[/dim]"
            )
        self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        from orbit.core.tools import all_tools
        tbl = _tool_table(all_tools())
        self.query_one("#dashboard", Static).update(tbl)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        target = (event.button.id or "").removeprefix("nav-")
        if target in self.app.SCREENS:
            self.app.push_screen(target)
