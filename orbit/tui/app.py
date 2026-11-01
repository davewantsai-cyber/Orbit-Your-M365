"""Main Textual application."""
from __future__ import annotations

from textual.app import App

from orbit.tui.screens.credentials import CredentialsScreen
from orbit.tui.screens.home import HomeScreen
from orbit.tui.screens.installer import InstallerScreen
from orbit.tui.screens.output import OutputScreen
from orbit.tui.screens.report import ReportScreen
from orbit.tui.screens.run import RunScreen
from orbit.tui.screens.tool_select import ToolSelectScreen
from orbit.tui.state import SessionState

CSS = """
Screen        { background: #04060a; }

/* ── Banner ── */
#banner       { height: 22; width: 1fr; }

/* ── Admin warning ── */
#admin-warning {
    width: 1fr;
    padding: 0 3;
    color: #cc3333;
    background: #0d0608;
}

/* ── Info row: sys-info left, dashboard right ── */
#info-row     { height: auto; width: 1fr; padding: 1 3 0 3; }
#sys-info     { width: 26; color: #1a4a5a; }
#dashboard    { width: 1fr; }

/* ── Nav bar ── */
#nav          { height: 5; width: 1fr; padding: 1 2; }
Button        {
    width: 1fr;
    margin: 0 1;
    background: #080e18;
    border: tall #0d3a55;
    color: #2a6070;
}
Button:hover  { background: #0c1e30; color: #00c8ff; border: tall #00c8ff; }
Button:focus  { background: #0c1e30; color: #00c8ff; border: tall #006080; }

/* ── Footer ── */
Footer        { background: #04060a; color: #0d2535; }
"""


class OrbitApp(App):
    CSS = CSS
    TITLE = "ORBIT"
    SCREENS = {
        "credentials": CredentialsScreen, "tool_select": ToolSelectScreen,
        "installer": InstallerScreen, "output": OutputScreen,
        "run": RunScreen, "report": ReportScreen,
    }

    def __init__(self, dry_run: bool = False) -> None:
        super().__init__()
        self.state = SessionState(dry_run=dry_run)
        self.sub_title = "DRY RUN" if dry_run else ""

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())
