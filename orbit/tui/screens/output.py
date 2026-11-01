"""Output directory, format selection and encryption options."""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Checkbox, DirectoryTree, Footer, Input, Static

from orbit.core.outputs import FORMATS


class OutputScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        cfg = self.app.state.output
        yield Static("[bold cyan]Output configuration[/bold cyan]")
        with Horizontal():
            yield Input(str(cfg.base_dir), id="out-dir")
            yield Button("Browse", id="browse")
        yield Static("Client name (for report cover)")
        yield Input(self.app.state.client_name, placeholder="Confidential", id="client-name")
        yield Static("[dim]A timestamped subfolder output/YYYY-MM-DD_HH-MM/ is created per run.[/dim]")
        for f in FORMATS:
            label = f"{f} (ORBIT summary)" if f in ("PDF", "DOCX") else f"{f} (native tool output)"
            yield Checkbox(label, value=f in cfg.formats, id=f"fmt-{f}")
        yield Checkbox("Encrypt output folder to ZIP (Fernet / PBKDF2)", cfg.encrypt, id="encrypt")
        yield Input(placeholder="Passphrase", password=True, id="passphrase")
        yield Checkbox("Save unencrypted copy as well", cfg.keep_unencrypted, id="keep")
        yield DirectoryTree(str(Path.home()), id="tree", classes="hidden")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "browse":
            self.query_one("#tree").toggle_class("hidden")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.query_one("#out-dir", Input).value = str(event.path / "output")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "out-dir":
            self.app.state.output.base_dir = Path(event.value or "output")
            self.app.save_config()
        elif event.input.id == "client-name":
            self.app.state.client_name = event.value.strip()
        elif event.input.id == "passphrase":
            self.app.state.passphrase = event.value or None

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        cid, cfg = event.checkbox.id or "", self.app.state.output
        if cid.startswith("fmt-"):
            fmt = cid.removeprefix("fmt-")
            cfg.formats.add(fmt) if event.value else cfg.formats.discard(fmt)
        elif cid == "encrypt":
            cfg.encrypt = event.value
        elif cid == "keep":
            cfg.keep_unencrypted = event.value
        if cid.startswith("fmt-"):
            self.app.save_config()
