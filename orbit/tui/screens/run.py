"""Run screen: hash gate, per-tool progress/log/elapsed/status, stop controls."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Collapsible, Footer, Input, ProgressBar, RichLog, Static

from orbit.core import config_store, emailer, notify
from orbit.core.hash_checker import check_tool
from orbit.core.outputs import make_run_folder
from orbit.core.pipeline import finalize
from orbit.core.runner import Runner, RunStatus, ToolRun
from orbit.core.secrets import SecretStore
from orbit.core.tools import all_tools
from orbit.reporting import scorer
from orbit.reporting.context import ReportContext
from orbit.reporting.pdf_report import generate_pdf

STATUS_STYLE = {RunStatus.PENDING: "dim", RunStatus.RUNNING: "cyan", RunStatus.COMPLETE: "green",
                RunStatus.FAILED: "red", RunStatus.SKIPPED: "yellow"}


class RunScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self) -> None:
        super().__init__()
        self.runner: Runner | None = None

    def _tools(self):
        sel = self.app.state.selected
        tools = [t for t in all_tools() if t.name in sel]
        if not tools and self.app.state.dry_run:
            tools = [t for t in all_tools() if t.fixture]
        return tools

    def compose(self) -> ComposeResult:
        mode = "[red](DRY RUN)[/red] " if self.app.state.dry_run else ""
        yield Static(f"[bold cyan]Run[/bold cyan] {mode}")
        yield Static("[dim]Client / engagement name (appears on report cover)[/dim]")
        yield Input(self.app.state.client_name, placeholder="Confidential", id="client-name")
        yield Checkbox("Override hash-check mismatch (I accept the risk)", id="override")
        yield Checkbox("Email results when complete", id="email-run",
                       value=config_store.load()["notifications"]["email_notify"])
        with Horizontal():
            yield Button("Start", id="start", variant="success")
            yield Button("Stop all", id="stop-all", variant="error")
        for t in self._tools():
            with Collapsible(title=t.display, collapsed=False):
                yield Static("Pending", id=f"status-{t.name}")
                yield ProgressBar(total=100, show_eta=False, id=f"bar-{t.name}")
                yield Button(f"Stop {t.display}", id=f"stop-{t.name}")
                yield RichLog(id=f"log-{t.name}", max_lines=2000, highlight=True, markup=True,
                              wrap=True)
        yield Static("", id="result")
        yield Static("", id="email-status")
        yield Footer()

    def _update(self, run: ToolRun) -> None:
        n = run.tool.name
        style = STATUS_STYLE[run.status]
        self.query_one(f"#status-{n}", Static).update(
            f"[{style}]{run.status.value}[/{style}]  {run.elapsed:5.1f}s {run.note}")
        self.query_one(f"#bar-{n}", ProgressBar).update(progress=run.progress)
        log = self.query_one(f"#log-{n}", RichLog)
        shown = getattr(log, "_shown", 0)
        # Follow output only while the user is at the bottom; scrolling up pauses auto-scroll.
        follow = log.is_vertical_scroll_end
        for line in run.log[shown:]:
            log.write(escape(line), scroll_end=follow)  # tool output is not Rich markup
        log._shown = len(run.log)  # type: ignore[attr-defined]

    def _email(self, findings, written: list[Path], tools) -> bool:
        """Send the summary PDF (generated into a temp dir if PDF output is off). Never raises."""
        st = self.app.state
        try:
            settings = emailer.load_settings(config_store.load(), SecretStore(st.passphrase))
            if not settings.configured:
                return False
            ctx = ReportContext(findings, [t.display for t in tools], dry_run=st.dry_run,
                                client=st.client_name.strip() or "Confidential")
            pdf = next((p for p in written if p.suffix == ".pdf" and p.exists()), None)
            if pdf:
                return emailer.send_results(ctx, pdf, settings)
            with tempfile.TemporaryDirectory() as tmp:
                return emailer.send_results(ctx, generate_pdf(ctx, Path(tmp)), settings)
        except Exception:
            return False

    @work(exclusive=True)
    async def start_run(self) -> None:
        st, tools = self.app.state, self._tools()
        if not tools:
            self.notify("Select at least one tool first", severity="warning")
            return
        store = None if st.dry_run else SecretStore(st.passphrase)
        creds, secrets = {}, {}
        if store:
            for t in tools:
                creds[t.name] = store.load(t.name)
                secrets[t.name] = store.secret_values(t.name)
        hashes = []
        if not st.dry_run:
            for t in tools:
                v = t.installed_version()
                hashes.append(check_tool(t.name, v, t.install_dir()))
        st.hash_override = self.query_one("#override", Checkbox).value
        st.run_folder = make_run_folder(st.output.base_dir)
        self.runner = Runner(st.run_folder, creds, secrets, st.dry_run, hashes, st.hash_override,
                             on_update=self._update)
        st.runs = await self.runner.run_all(tools)
        findings, written = await asyncio.to_thread(
            finalize, st.run_folder, [t.display for t in tools], st.output, st.dry_run, st.passphrase,
            st.client_name)
        st.findings = findings
        self.query_one("#result", Static).update(
            f"[green]Done.[/green] {len(findings)} controls. Output: {st.run_folder}\n"
            + "\n".join(str(p) for p in written))
        score = round(scorer.summarize(findings).posture)
        await asyncio.to_thread(notify.notify_complete, score)
        if self.query_one("#email-run", Checkbox).value:
            ok = await asyncio.to_thread(self._email, findings, written, tools)
            self.query_one("#email-status", Static).update(
                "[green]Email sent ✓[/green]" if ok else "[red]Email failed ✗[/red]")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "client-name":
            self.app.state.client_name = event.value.strip()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "start":
            self.start_run()
        elif bid == "stop-all" and self.runner:
            self.runner.stop_all()
        elif bid.startswith("stop-") and self.runner:
            self.runner.stop(bid.removeprefix("stop-"))
