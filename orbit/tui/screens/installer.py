"""Installer: per-tool versions, install/update buttons, live log; prerequisite check."""
from __future__ import annotations

import shutil
import sys

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, RichLog, Static

from orbit.core.platform_check import check_platform
from orbit.core.runner import stream_process
from orbit.core.tools import Tool, all_tools


def prereq_report() -> list[tuple[str, bool, str]]:
    info = check_platform()
    pw = ".".join(map(str, info.pwsh_version)) if info.pwsh_version else ""
    return [
        ("PowerShell 7 (pwsh)", info.pwsh7, pw or "not found"),
        ("pip", True, f"python -m pip via {sys.executable}"),
        ("OPA binary (ScubaGear)", bool(shutil.which("opa")), shutil.which("opa") or "not on PATH"),
    ]


class InstallerScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Installer[/bold cyan]")
        yield Static("", id="prereq")
        for t in all_tools():
            with Horizontal():
                yield Static(f"{t.display}", id=f"info-{t.name}")
                yield Button("Install", id=f"install-{t.name}")
                yield Button("Update", id=f"update-{t.name}")
        yield Button("Install OPA (via ScubaGear)", id="install-opa")
        yield Button("Refresh versions", id="refresh")
        yield RichLog(id="log", markup=False, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        lines = [f"{'[green]✓' if ok else '[red]✗'}[/] {n}: {d}" for n, ok, d in prereq_report()]
        self.query_one("#prereq", Static).update("\n".join(lines))
        self.refresh_versions()

    @work(thread=True)
    def refresh_versions(self) -> None:
        for t in all_tools():
            text = f"{t.display}  installed: {t.installed_version() or '-'}  latest: {t.latest_version() or '?'}"
            self.app.call_from_thread(self.query_one(f"#info-{t.name}", Static).update, text)

    @work(exclusive=True)
    async def _run(self, argv: list[str]) -> None:
        log = self.query_one("#log", RichLog)
        log.write("$ " + " ".join(argv))
        rc = await stream_process(argv, {}, log.write)
        log.write(f"exit code {rc}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "refresh":
            self.refresh_versions()
        elif bid == "install-opa":
            pw = shutil.which("pwsh") or "pwsh"
            # OPA is fetched by ScubaGear's own installer, not by ORBIT.
            self._run([pw, "-NoProfile", "-Command", "Import-Module ScubaGear; Initialize-SCuBA"])
        elif bid.startswith(("install-", "update-")):
            verb, name = bid.split("-", 1)
            tool: Tool = next(t for t in all_tools() if t.name == name)
            self._run(tool.install_command(update=verb == "update"))
