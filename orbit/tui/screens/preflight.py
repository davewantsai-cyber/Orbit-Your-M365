"""Pre-flight check screen — local checks only, no network calls."""
from __future__ import annotations

import shutil
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from orbit.core.admin_check import is_elevated
from orbit.core.hash_checker import HashStatus, load_manifest
from orbit.core.platform_check import check_platform
from orbit.core.secrets import SecretStore
from orbit.core.tools import all_tools


_NETWORK_NOTE = (
    "[dim]Network connectivity and tenant credential validity are not tested here.\n"
    "A live check would require contacting Microsoft's servers and could expose\n"
    "credentials to network logging. Verify tenant access manually before running.[/dim]"
)


def _check_output_writable(base_dir: Path) -> tuple[bool, str]:
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        test = base_dir / ".orbit_write_test"
        test.touch()
        test.unlink()
        return True, str(base_dir)
    except OSError as e:
        return False, str(e)


def run_preflight(state) -> list[tuple[bool, str, str]]:
    """
    Returns list of (passed, label, detail) tuples.
    All checks are local — no network calls.
    """
    results: list[tuple[bool, str, str]] = []
    plat = check_platform()

    # 1. Elevation
    elevated = is_elevated()
    results.append((
        elevated,
        "Administrator / elevated",
        "OK" if elevated else "Not elevated — ScubaGear and Maester require Global Admin"
    ))

    # 2. PowerShell 7
    pw_ok = plat.pwsh7
    pw_ver = ".".join(map(str, plat.pwsh_version)) if plat.pwsh_version else "not found"
    results.append((pw_ok, "PowerShell 7", pw_ver if pw_ok else f"{pw_ver} — install pwsh 7+"))

    # 3. OPA binary
    opa = bool(shutil.which("opa"))
    results.append((opa, "OPA binary", shutil.which("opa") or "not on PATH — required by ScubaGear"))

    # 4. Selected tools installed
    selected_names = state.selected or set()
    tools = [t for t in all_tools() if t.name in selected_names]
    if not tools and state.dry_run:
        tools = [t for t in all_tools() if t.fixture]
    if not tools:
        results.append((False, "Tools selected", "No tools selected — use Tools screen"))
    else:
        for t in tools:
            if not t.compatible(plat):
                results.append((False, f"{t.display} compatible", f"Not compatible with {plat.os_name}"))
                continue
            ver = t.installed_version()
            if state.dry_run:
                results.append((True, f"{t.display}", "dry-run mode (fixture data)"))
            elif ver:
                results.append((True, f"{t.display}", f"v{ver}"))
            else:
                results.append((False, f"{t.display}", "not installed — use Install screen"))

    # 5. Credentials loaded (skip in dry-run)
    if not state.dry_run:
        try:
            store = SecretStore(state.passphrase)
            for t in tools:
                creds = store.load(t.name)
                has = bool(creds and any(creds.values()))
                results.append((has, f"{t.display} credentials", "loaded" if has else "missing — use Credentials screen"))
        except Exception as e:
            results.append((False, "Credentials", f"Could not read credential store: {e}"))

    # 6. Output folder writable
    ok, detail = _check_output_writable(state.output.base_dir)
    results.append((ok, "Output folder writable", detail))

    # 7. Tool integrity manifest
    try:
        manifest = load_manifest()
        tools_section = manifest.get("tools", {})
        populated = any(
            v.get("versions")
            for v in tools_section.values()
        )
        if populated:
            results.append((True, "Tool integrity manifest", "populated — hashes will be verified"))
        else:
            # Treat as a non-blocking warning: use None to signal amber
            results.append((None, "Tool integrity manifest",
                            "NOT CONFIGURED — hashes unverified; populate data/tool_hashes.json"))
    except Exception as e:
        results.append((False, "Tool integrity manifest", f"Could not read manifest: {e}"))

    return results


class PreflightScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("r", "recheck", "Re-check"),
    ]

    DEFAULT_CSS = """
    PreflightScreen { padding: 1 3; }

    #title    { margin-bottom: 1; }
    #checks   { height: auto; width: 1fr; margin-bottom: 1; }
    .chk-row  { height: 1; width: 1fr; }
    #note     { margin-top: 1; }
    #actions  { height: 3; margin-top: 1; }
    #actions Button { width: auto; min-width: 16; margin-right: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Pre-flight checks[/bold cyan]  "
                     "[dim]Local checks only — see note below[/dim]", id="title")
        yield Vertical(id="checks")
        yield Static(_NETWORK_NOTE, id="note")
        from textual.containers import Horizontal
        with Horizontal(id="actions"):
            yield Button("↺ Re-check", id="recheck")
            yield Button("▶ Proceed to Run", id="proceed")
        yield Footer()

    def on_mount(self) -> None:
        self._run_checks()

    @work(thread=True)
    def _run_checks(self) -> None:
        results = run_preflight(self.app.state)

        def _render():
            container = self.query_one("#checks", Vertical)
            container.remove_children()
            for ok, label, detail in results:
                if ok is True:
                    icon  = "[green]✓[/green]"
                    style = "#2a6070"
                elif ok is None:
                    icon  = "[yellow]⚠[/yellow]"
                    style = "#b07800"
                else:
                    icon  = "[red]✗[/red]"
                    style = "#cc4444"
                row = Static(
                    f"{icon}  [{style}]{label}[/{style}]  [dim]{detail}[/dim]",
                    classes="chk-row"
                )
                container.mount(row)

        self.app.call_from_thread(_render)

    def action_recheck(self) -> None:
        self._run_checks()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "recheck":
            self._run_checks()
        elif event.button.id == "proceed":
            self.app.pop_screen()
            self.app.push_screen("run")
