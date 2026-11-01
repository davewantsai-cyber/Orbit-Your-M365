"""Installer: compact table, spacer fills gap, bottom bar always in view."""
from __future__ import annotations

import shutil
import sys

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, RichLog, Static

from orbit.core.platform_check import check_platform
from orbit.core.runner import stream_process
from orbit.core.tools import all_tools


def prereq_report() -> list[tuple[str, bool, str]]:
    info = check_platform()
    pw = ".".join(map(str, info.pwsh_version)) if info.pwsh_version else ""
    return [
        ("PowerShell 7", info.pwsh7,              pw or "not found"),
        ("pip",          True,                    "available"),
        ("OPA",          bool(shutil.which("opa")), "found" if shutil.which("opa") else "not on PATH"),
    ]


class InstallerScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    DEFAULT_CSS = """
    InstallerScreen { padding: 0; }

    #prereq-strip {
        height: 1; width: 1fr;
        padding: 0 2;
        background: #050c14;
        border-bottom: solid #0d3a55;
    }
    #prereq-strip Static { width: auto; color: #2a5a6a; margin-right: 4; }

    /* tool rows — fixed height, auto-sized to content */
    #tool-table { height: auto; width: 1fr; padding: 0 2; }

    .tool-row {
        height: 3; width: 1fr;
        border-bottom: solid #060e18;
    }
    .tool-row:hover { background: #06101c; }

    .t-name   { width: 14; content-align: left middle; padding: 0 1; color: #00c8ff; }
    .t-status { width: 1fr; content-align: left middle; padding: 0 1; }
    .badge-ok  { color: #00c840; }
    .badge-no  { color: #cc4444; }
    .badge-dim { color: #2a5a6a; }
    .t-ver    { width: 12; content-align: left middle; padding: 0 1; color: #0d3040; }

    .t-btns { width: 42; content-align: left middle; }
    .t-btns Button {
        width: 12; height: 3; min-width: 0;
        margin: 0 1 0 0;
        background: #06101c;
        border: tall #0d2a40;
        color: #2a6070;
    }
    .t-btns Button:hover  { color: #00c8ff; border: tall #00c8ff; background: #0a1a2c; }
    .btn-inst             { color: #00c840 !important; border: tall #004a20 !important; }
    .btn-inst:hover       { color: #00ff60 !important; background: #001a0a !important; }
    .btn-uninst           { color: #883333 !important; border: tall #3a1010 !important; }
    .btn-uninst:hover     { color: #ff6060 !important; background: #1a0808 !important; }

    /* spacer pushes bottom content down */
    #spacer { height: 1fr; width: 1fr; }

    /* log — hidden until output, sits above bottom bar */
    #log-section        { height: 0; width: 1fr; }
    #log-section.active { height: 6; border-top: solid #0d2a40; }
    #log                { height: 1fr; width: 1fr; padding: 0 2; }

    /* bottom bar — always last, always visible */
    #bottom-bar {
        height: 3; width: 1fr;
        padding: 0 2;
        border-top: solid #0d2a40;
        background: #050c14;
    }
    #bottom-bar Button {
        width: 1fr; height: 3;
        margin: 0 1 0 0;
        background: #080e18;
        border: tall #0d3a55;
        color: #2a6070;
    }
    #bottom-bar Button:hover { color: #00c8ff; border: tall #00c8ff; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="prereq-strip"):
            for name, ok, detail in prereq_report():
                icon = "[green]✓[/]" if ok else "[red]✗[/]"
                yield Static(f"{icon} [dim]{name}:[/dim] {detail}")

        with Vertical(id="tool-table"):
            for t in all_tools():
                with Horizontal(classes="tool-row", id=f"row-{t.name}"):
                    yield Static(t.display, classes="t-name")
                    yield Static("…", classes="t-status badge-dim", id=f"status-{t.name}")
                    yield Static("",  classes="t-ver",              id=f"ver-{t.name}")
                    with Horizontal(classes="t-btns"):
                        yield Button("⬇ Install",  id=f"install-{t.name}",   classes="btn-inst")
                        yield Button("↑ Update",   id=f"update-{t.name}")
                        yield Button("✕ Remove",   id=f"uninstall-{t.name}", classes="btn-uninst")

        # fills leftover vertical space
        yield Static("", id="spacer")

        with Vertical(id="log-section"):
            yield RichLog(id="log", markup=False, wrap=True, max_lines=300)

        with Horizontal(id="bottom-bar"):
            yield Button("⬇ Install all", id="install-all")
            yield Button("⬇ Install OPA", id="install-opa")
            yield Button("↺ Refresh",     id="refresh")

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_versions()

    @work(thread=True)
    def refresh_versions(self) -> None:
        plat = check_platform()
        for t in all_tools():
            compat   = t.compatible(plat)
            inst_ver = t.installed_version() if compat else None
            if not compat:
                st, sc, vt = "◌ Incompatible OS", "t-status badge-dim", ""
            elif inst_ver:
                st, sc, vt = "● Installed",       "t-status badge-ok",  inst_ver
            else:
                st, sc, vt = "○ Not installed",   "t-status badge-no",  ""

            def _up(name=t.name, s=st, c=sc, v=vt):
                try:
                    w = self.query_one(f"#status-{name}", Static)
                    w.update(s); w.set_classes(c)
                    self.query_one(f"#ver-{name}", Static).update(v)
                except Exception:
                    pass

            self.app.call_from_thread(_up)

    def _log(self, msg: str) -> None:
        self.query_one("#log-section").add_class("active")
        self.query_one("#log", RichLog).write(msg)

    @work(exclusive=True)
    async def _run(self, argv: list[str], label: str = "") -> None:
        if label:
            self._log(f"── {label} ──")
        self._log("$ " + " ".join(argv))
        try:
            rc = await stream_process(argv, {}, self._log)
            self._log(f"exit {rc}" + (" ✓" if rc == 0 else " ✗"))
        except FileNotFoundError:
            self._log(f"✗  Command not found: {argv[0]}")
            self._log("   Install PowerShell 7 (pwsh) to use this feature on macOS/Linux.")
        except Exception as e:
            self._log(f"✗  Error: {e}")
        self.refresh_versions()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        tools = {t.name: t for t in all_tools()}

        if bid == "refresh":
            self.refresh_versions()
        elif bid == "install-opa":
            pw = shutil.which("pwsh") or "pwsh"
            self._run([pw, "-NoProfile", "-Command",
                       "Import-Module ScubaGear; Initialize-SCuBA"], "Install OPA")
        elif bid == "install-all":
            for t in tools.values():
                self._run(t.install_command(update=False), f"Install {t.display}")
        elif bid.startswith("install-"):
            t = tools.get(bid[len("install-"):])
            if t: self._run(t.install_command(update=False), f"Install {t.display}")
        elif bid.startswith("update-"):
            t = tools.get(bid[len("update-"):])
            if t: self._run(t.install_command(update=True), f"Update {t.display}")
        elif bid.startswith("uninstall-"):
            t = tools.get(bid[len("uninstall-"):])
            if not t: return
            cmd = t.uninstall_command() if hasattr(t, "uninstall_command") else None
            if cmd:
                self._run(cmd, f"Uninstall {t.display}")
            else:
                self._log(f"No automated uninstall for {t.display} — remove manually.")
