"""Summary preview + Executive Summary PDF generation."""
from __future__ import annotations

import asyncio

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, ProgressBar, Static

from orbit.reporting import scorer
from orbit.reporting.parser import parse_folder


class ReportScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    DEFAULT_CSS = """
    ReportScreen { padding: 1 3; }
    #summary      { margin-bottom: 1; }
    #exec-section { height: auto; margin-top: 1; border-top: solid #0d2a40; padding-top: 1; }
    #exec-desc    { color: #1a4a5a; margin-bottom: 1; }
    #exec-bar     { height: 1; margin: 1 0; display: none; }
    #exec-bar.active { display: block; }
    #exec-status  { height: 1; color: #2a6070; }
    #exec-btn     { width: auto; min-width: 28; }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Summary preview[/bold cyan]", id="title")
        yield Static("", id="summary")
        yield Static(
            "[bold]Executive Summary PDF[/bold]\n"
            "[dim]A 2-page plain-English report for non-technical stakeholders — "
            "posture score, top findings, remediation priorities, and a written summary. "
            "Generated on demand; does not replace the full technical report.[/dim]",
            id="exec-section"
        )
        yield Button("⬇  Generate Executive Summary PDF", id="exec-btn")
        yield ProgressBar(total=100, show_eta=False, id="exec-bar")
        yield Static("", id="exec-status")
        yield Footer()

    def on_mount(self) -> None:
        folder = self.app.state.run_folder
        box = self.query_one("#summary", Static)
        if not folder:
            box.update("[dim]No run yet — use Run ▶ first.[/dim]")
            self.query_one("#exec-btn", Button).disabled = True
            return
        findings = parse_folder(folder)
        s = scorer.summarize(findings)
        lines = [
            f"Posture: [bold]{s.posture}%[/bold] ({s.passed_controls}/{s.total_controls})",
            "  ".join(f"{k}: {v}" for k, v in s.counts.items()),
            "",
            "[bold]Top findings[/bold]",
        ]
        for f in scorer.top_n(findings, 3):
            col = "red" if f.severity == "Critical" else "yellow"
            lines.append(f"[{col}]{f.severity}[/{col}] {f.title} ({f.control_id}) - {f.tool}")
        box.update("\n".join(lines))

    @work(exclusive=True)
    async def _generate_exec(self) -> None:
        btn    = self.query_one("#exec-btn", Button)
        bar    = self.query_one("#exec-bar", ProgressBar)
        status = self.query_one("#exec-status", Static)

        btn.disabled = True
        bar.add_class("active")
        bar.update(progress=10)
        status.update("[dim]Preparing findings…[/dim]")

        st = self.app.state
        findings = st.findings or (parse_folder(st.run_folder) if st.run_folder else [])

        if not findings:
            status.update("[red]No findings available — run an assessment first.[/red]")
            bar.remove_class("active")
            btn.disabled = False
            return

        bar.update(progress=30)
        status.update("[dim]Generating PDF…[/dim]")

        from orbit.reporting.exec_summary import generate_exec_summary
        out_dir = st.run_folder or st.output.base_dir

        try:
            out = await asyncio.to_thread(
                generate_exec_summary,
                findings,
                out_dir,
                st.client_name,
                st.dry_run,
            )
            bar.update(progress=100)
            status.update(f"[green]✓ Saved:[/green] [dim]{out}[/dim]")
        except Exception as e:
            status.update(f"[red]✗ Failed: {e}[/red]")
        finally:
            bar.remove_class("active")
            btn.disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exec-btn":
            self._generate_exec()
