"""Shown when the terminal is smaller than ORBIT's minimum layout size."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

MIN_WIDTH = 100
MIN_HEIGHT = 32


class SizeWarningScreen(Screen):
    DEFAULT_CSS = """
    SizeWarningScreen { align: center middle; }
    SizeWarningScreen Vertical { width: auto; height: auto; padding: 1 3; }
    SizeWarningScreen Button { margin-top: 1; width: 24; }
    """

    def compose(self) -> ComposeResult:
        w, h = self.app.size
        with Vertical():
            yield Static(
                "[bold yellow]⚠  Terminal too small[/bold yellow]\n\n"
                f"ORBIT requires at least {MIN_WIDTH} × {MIN_HEIGHT} characters.\n"
                f"Current size: {w} × {h}\n\n"
                "Please resize your terminal window and relaunch,\n"
                "or press \\[Continue anyway] to proceed with reduced layout."
            )
            yield Button("Continue anyway", id="continue-anyway", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue-anyway":
            self.app.pop_screen()
            self.app.start_session()
