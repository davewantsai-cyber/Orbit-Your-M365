"""Checkbox tool selection."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Checkbox, Footer, Static

from orbit.core.tools import all_tools


class ToolSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Select tools to run[/bold cyan]")
        for t in all_tools():
            yield Checkbox(t.display, value=t.name in self.app.state.selected, id=f"sel-{t.name}")
        yield Footer()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        name = (event.checkbox.id or "").removeprefix("sel-")
        sel = self.app.state.selected
        sel.add(name) if event.value else sel.discard(name)
