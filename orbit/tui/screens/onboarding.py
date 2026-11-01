"""First-run onboarding wizard. Always skippable; never blocks the rest of the app."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Input, Static

from orbit.core import config_store
from orbit.core.tools import all_tools

STEPS = ("step-1", "step-2", "step-3")

WELCOME = (
    "[bold cyan]Welcome to ORBIT[/bold cyan]\n\n"
    "ORBIT runs the leading open-source Microsoft 365 security assessment tools from one\n"
    "place, merges their results and produces a client-ready report. A multi-tool audit\n"
    "that normally takes hours of manual work is reduced to a single run.\n\n"
    "[bold yellow]Authorised use only:[/bold yellow] only assess tenants you own or have\n"
    "explicit written permission to test.\n\n"
    "[dim]No credentials are saved yet. Complete setup or skip — you can return to\n"
    "the Credentials screen at any time from the main menu.[/dim]"
)


def has_saved_credentials() -> bool:
    """Best-effort check for saved credentials without prompting for a passphrase."""
    from orbit.core.secrets import DEFAULT_FALLBACK, TOOL_FIELDS, SecretStore
    try:
        store = SecretStore()
        if not store.use_keyring:
            return DEFAULT_FALLBACK.exists()
        return any(store.load(t) for t in TOOL_FIELDS)
    except Exception:
        return False


def should_show() -> bool:
    """Show wizard whenever credentials are missing — not just on first run."""
    return not has_saved_credentials()


def mark_done() -> None:
    """No longer used to gate the wizard — kept for config_store compatibility."""
    try:
        config_store.update("app", first_run=False)
    except OSError:
        pass


class OnboardingScreen(Screen):
    DEFAULT_CSS = """
    OnboardingScreen { padding: 2 4; }
    OnboardingScreen .wiz-buttons { height: 5; margin-top: 1; }
    OnboardingScreen Input { margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="step-1"):
            yield Static(WELCOME)
            with Horizontal(classes="wiz-buttons"):
                yield Button("Get Started →", id="next-1", variant="success")
                yield Button("Skip setup →", id="skip-1")
        with Vertical(id="step-2"):
            yield Static("[bold cyan]Quick setup[/bold cyan]  [dim]Step 2 of 3[/dim]\n")
            yield Static("[dim]Tenant ID[/dim]")
            yield Input(id="wiz-tenant")
            yield Static("[dim]App (client) ID[/dim]")
            yield Input(id="wiz-app")
            with Horizontal(classes="wiz-buttons"):
                yield Button("Continue →", id="next-2", variant="success")
                yield Button("I'll set this up later", id="later-2")
                yield Button("Skip setup →", id="skip-2")
        with Vertical(id="step-3"):
            yield Static("[bold cyan]Choose tools[/bold cyan]  [dim]Step 3 of 3[/dim]\n")
            for t in all_tools():
                yield Checkbox(t.display, value=t.name in self.app.state.selected, id=f"wiz-{t.name}")
            with Horizontal(classes="wiz-buttons"):
                yield Button("Continue →", id="next-3", variant="success")
                yield Button("Skip setup →", id="skip-3")

    def on_mount(self) -> None:
        self._show("step-1")

    def _show(self, step: str) -> None:
        for s in STEPS:
            self.query_one(f"#{s}").display = s == step

    def _save_credentials(self) -> None:
        tenant = self.query_one("#wiz-tenant", Input).value.strip()
        app_id = self.query_one("#wiz-app", Input).value.strip()
        if not (tenant or app_id):
            return
        from orbit.core.secrets import SecretStore
        try:
            store = SecretStore()
            for tool in ("scubagear", "maester"):
                store.save(tool, {"tenant_id": tenant, "client_id": app_id})
        except Exception:
            self.notify("Couldn't save credentials here; add them later on the Credentials screen.",
                        severity="warning")

    def _save_tools(self) -> None:
        sel = self.app.state.selected
        for t in all_tools():
            if self.query_one(f"#wiz-{t.name}", Checkbox).value:
                sel.add(t.name)
            else:
                sel.discard(t.name)
        self.app.save_config()

    def finish(self) -> None:
        mark_done()
        from orbit.tui.screens.home import HomeScreen
        self.app.switch_screen(HomeScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("skip-"):
            self.finish()
        elif bid == "next-1":
            self._show("step-2")
        elif bid == "later-2":
            self._show("step-3")
        elif bid == "next-2":
            self._save_credentials()
            self._show("step-3")
        elif bid == "next-3":
            self._save_tools()
            self.finish()
