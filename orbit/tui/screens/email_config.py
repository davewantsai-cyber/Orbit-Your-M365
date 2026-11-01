"""SMTP configuration for emailing results. Credentials go to the keyring, the rest to config.toml."""
from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Input, Label, Static

from orbit.core import config_store, emailer
from orbit.core.secrets import SecretStore


class EmailConfigScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self, store: SecretStore | None = None) -> None:
        super().__init__()
        self.store = store

    def _store(self) -> SecretStore:
        if self.store is None:
            self.store = SecretStore(self.app.state.passphrase)
        return self.store

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Email[/bold cyan]  [dim]From address and password are kept in the "
                     "OS keychain (orbit-m365/smtp)[/dim]")
        with VerticalScroll():
            yield Label("[dim]SMTP host[/dim]")
            yield Input(id="smtp-host")
            yield Label("[dim]Port[/dim]")
            yield Input("587", id="smtp-port")
            yield Checkbox("Use TLS (STARTTLS / SSL on 465)", True, id="smtp-tls")
            yield Label("[dim]From address[/dim]")
            yield Input(id="smtp-from")
            yield Label("[dim]SMTP password[/dim]")
            yield Input(password=True, id="smtp-password")
            yield Label("[dim]To addresses (comma-separated)[/dim]")
            yield Input(id="smtp-to")
            yield Label("[dim]CC addresses (comma-separated, optional)[/dim]")
            yield Input(id="smtp-cc")
            with Horizontal():
                yield Button("Save", id="email-save", variant="primary")
                yield Button("Send test email", id="email-test")
            yield Static("", id="email-result")
        yield Footer()

    def on_mount(self) -> None:
        cfg = config_store.load()["email"]
        self.query_one("#smtp-host", Input).value = cfg["smtp_host"]
        self.query_one("#smtp-port", Input).value = str(cfg["smtp_port"])
        self.query_one("#smtp-tls", Checkbox).value = cfg["smtp_tls"]
        self.query_one("#smtp-to", Input).value = ", ".join(cfg["to_addresses"])
        self.query_one("#smtp-cc", Input).value = ", ".join(cfg["cc_addresses"])
        try:
            secret = self._store().load(emailer.SECRET_KEY)
        except Exception:
            secret = {}
        self.query_one("#smtp-from", Input).value = secret.get("from_address", "")
        if secret.get("password"):
            self.query_one("#smtp-password", Input).placeholder = "(saved — leave blank to keep)"

    def _read(self) -> emailer.EmailSettings:
        """Current form values; raises ValueError on bad input."""
        q = lambda i: self.query_one(i, Input).value.strip()
        try:
            port = int(q("#smtp-port") or 587)
        except ValueError:
            raise ValueError("Port must be a number") from None
        sender = q("#smtp-from")
        if sender:
            emailer.parse_addresses(sender)
        password = self.query_one("#smtp-password", Input).value
        if not password:
            try:
                password = self._store().load(emailer.SECRET_KEY).get("password", "")
            except Exception:
                password = ""
        return emailer.EmailSettings(
            q("#smtp-host"), port, self.query_one("#smtp-tls", Checkbox).value, sender, password,
            emailer.parse_addresses(q("#smtp-to")), emailer.parse_addresses(q("#smtp-cc")))

    def _show(self, text: str, ok: bool) -> None:
        colour = "green" if ok else "red"
        self.query_one("#email-result", Static).update(f"[{colour}]{text}[/{colour}]")

    def _save(self, s: emailer.EmailSettings) -> None:
        self._store().save(emailer.SECRET_KEY, {"from_address": s.from_address,
                                                "password": s.password})
        cfg = config_store.load()
        cfg["email"].update(enabled=s.configured, smtp_host=s.smtp_host, smtp_port=s.smtp_port,
                            smtp_tls=s.smtp_tls, from_address="",  # kept in keyring only
                            to_addresses=s.to_addresses, cc_addresses=s.cc_addresses)
        config_store.save(cfg)

    @work(thread=True, exclusive=True, group="email-test")
    def _send_test(self, s: emailer.EmailSettings) -> None:
        ok, detail = emailer.send_test(s)
        self.app.call_from_thread(self._show, detail, ok)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid not in ("email-save", "email-test"):
            return
        try:
            settings = self._read()
            if bid == "email-save":
                self._save(settings)
                self._show("Saved", True)
            else:
                self._show("Sending test email…", True)
                self._send_test(settings)
        except Exception as exc:  # validation or keyring/storage errors, shown in the form
            self._show(str(exc), False)
