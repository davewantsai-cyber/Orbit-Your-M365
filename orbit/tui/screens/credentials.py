"""Credentials screen: one collapsible panel per tool; secret fields masked with show/hide."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Collapsible, Footer, Input, Label, Select, Static

from orbit.core.secrets import TOOL_FIELDS, SecretStore


class CredentialsScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self, store: SecretStore | None = None) -> None:
        super().__init__()
        self.store = store

    def _store(self) -> SecretStore:
        if self.store is None:
            self.store = SecretStore()
        return self.store

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Credentials[/bold cyan]  [dim]stored in OS keychain / encrypted file[/dim]")
        with VerticalScroll():
            for tool, fields in TOOL_FIELDS.items():
                with Collapsible(title=tool, id=f"acc-{tool}"):
                    for f in fields:
                        yield Label(f"[dim]{f.label}[/dim]")
                        wid = f"{tool}--{f.name}"
                        if f.kind == "bool":
                            yield Checkbox(f.label, id=wid)
                        elif f.kind == "choice":
                            yield Select([(c, c) for c in f.choices], id=wid, allow_blank=True)
                        elif f.secret:
                            with Horizontal():
                                yield Input(password=True, id=wid)
                                yield Button("show", id=f"toggle--{wid}")
                        else:
                            yield Input(id=wid)
                    yield Button(f"Save {tool}", id=f"save--{tool}", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("toggle--"):
            inp = self.query_one("#" + bid.removeprefix("toggle--"), Input)
            inp.password = not inp.password
            event.button.label = "show" if inp.password else "hide"
        elif bid.startswith("save--"):
            tool = bid.removeprefix("save--")
            values: dict = {}
            for f in TOOL_FIELDS[tool]:
                w = self.query_one(f"#{tool}--{f.name}")
                v = w.value  # type: ignore[attr-defined]
                values[f.name] = None if v is Select.BLANK else v
            try:
                self._store().save(tool, values)
                self.notify(f"Saved {tool} credentials ({self._store().backend})")
            except PermissionError as exc:
                self.notify(str(exc), severity="error")
