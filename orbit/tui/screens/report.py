"""Summary preview."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Static

from orbit.reporting import scorer
from orbit.reporting.parser import parse_folder


class ReportScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Summary preview[/bold cyan]")
        yield Static("", id="summary")
        yield Footer()

    def on_mount(self) -> None:
        folder = self.app.state.run_folder
        box = self.query_one("#summary", Static)
        if not folder:
            box.update("[dim]No run yet. Use Run first.[/dim]")
            return
        findings = parse_folder(folder)
        s = scorer.summarize(findings)
        lines = [f"Posture: [bold]{s.posture}%[/bold] ({s.passed_controls}/{s.total_controls})",
                 "  ".join(f"{k}: {v}" for k, v in s.counts.items()), "", "[bold]Top findings[/bold]"]
        for f in scorer.top_n(findings, 3):
            col = "red" if f.severity == "Critical" else "yellow"
            lines.append(f"[{col}]{f.severity}[/{col}] {f.title} ({f.control_id}) - {f.tool}")
        box.update("\n".join(lines))
