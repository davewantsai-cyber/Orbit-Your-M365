"""Findings viewer: sortable, filterable table with detail, run-comparison, and remediation plan."""
from __future__ import annotations

from rich.markup import escape
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Input, Static

from orbit.core import history
from orbit.core.compare import compare
from orbit.reporting.parser import RANK, Finding

SEV_COLOUR = {"Critical": "#cc2222", "High": "#cc6600", "Medium": "#ccaa00", "Low": "#2a6070"}
COLUMNS = ("Severity", "Tool", "Control ID", "Title", "CVEs")
EMPTY_MSG = "No findings yet — run an assessment first."


def _cells(f: Finding) -> tuple[str, ...]:
    return (f.severity, f.tool, f.control_id, f.title, ", ".join(f.cve_ids))


def sort_findings(findings: list[Finding], mode: str) -> list[Finding]:
    """mode: severity (Critical first) | cve (most CVEs first) | tool (A-Z)."""
    if mode == "cve":
        return sorted(findings, key=lambda f: (-len(f.cve_ids), -RANK[f.severity]))
    if mode == "tool":
        return sorted(findings, key=lambda f: (f.tool.lower(), -RANK[f.severity]))
    return sorted(findings, key=lambda f: (-RANK[f.severity], f.control_id))


def remediation_plan(findings: list[Finding]) -> Table:
    """Prioritised remediation action plan: Critical first, CVE-enriched."""
    ordered = sort_findings([f for f in findings if f.severity != "Pass"], "severity")
    t = Table(title="Remediation Action Plan", box=None, padding=(0, 2), show_lines=True)
    t.add_column("#",           style="dim",      width=3)
    t.add_column("Priority",    style="bold",     width=10)
    t.add_column("Control",     style="#2a6070",  width=12)
    t.add_column("Finding",     style="white",    ratio=2)
    t.add_column("Action",      style="#1a4a5a",  ratio=3)
    t.add_column("CVEs",        style="#cc6600",  width=14)

    SEV_STYLE = {"Critical": "bold red", "High": "bold #cc6600",
                 "Medium": "bold yellow", "Low": "dim"}
    for i, f in enumerate(ordered[:20], 1):  # cap at 20 to keep readable
        sty = SEV_STYLE.get(f.severity, "")
        action = f.remediation[:80] + "…" if f.remediation and len(f.remediation) > 80 \
            else (f.remediation or "See vendor documentation")
        cves = ", ".join(f.cve_ids[:2]) + ("…" if len(f.cve_ids) > 2 else "") if f.cve_ids else "—"
        t.add_row(str(i), f"[{sty}]{f.severity}[/{sty}]",
                  f.control_id, f.title, action, cves)
    return t


def comparison_table(a: dict, b: dict) -> Table:
    d = compare(a, b)

    def row(label: str, key: str, d_key: str, higher_is_better: bool) -> tuple[str, str, str]:
        delta = d[d_key]
        if delta == 0:
            mark = "[yellow]→ 0[/yellow]"
        else:
            good = (delta > 0) == higher_is_better
            arrow = "✓" if good and not higher_is_better else ("↑" if delta > 0 else "↓")
            colour = "green" if good else "red"
            mark = f"[{colour}]{arrow} {delta:+d}[/{colour}]"
        return label, f"{a[key]} → {b[key]}", mark

    t = Table(title=f"Run comparison: {a['timestamp'][:10]} → {b['timestamp'][:10]}",
              show_header=False, box=None, padding=(0, 2))
    for r in (row("Score", "score", "score_delta", True),
              row("Critical", "critical", "critical_delta", False),
              row("High", "high", "high_delta", False),
              row("Medium", "medium", "medium_delta", False),
              row("Low", "low", "low_delta", False)):
        t.add_row(*r)
    t.add_row("Issues resolved:", str(d["resolved"]), "")
    return t


class FindingDetailModal(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]
    DEFAULT_CSS = """
    FindingDetailModal { align: center middle; }
    FindingDetailModal > VerticalScroll {
        width: 90%; max-width: 110; height: 80%; padding: 1 2;
        background: #080e18; border: tall #0d3a55;
    }
    """

    def __init__(self, finding: Finding) -> None:
        super().__init__()
        self.finding = finding

    def compose(self) -> ComposeResult:
        f = self.finding
        col = SEV_COLOUR.get(f.severity, "white")
        body = (
            f"[bold {col}]{escape(f.severity)}[/bold {col}]  [bold]{escape(f.title)}[/bold]\n"
            f"[dim]{escape(f.tool)} · {escape(f.control_id)}[/dim]\n\n"
            f"[bold]Description[/bold]\n{escape(f.description) or '—'}\n\n"
            f"[bold]Remediation[/bold]\n{escape(f.remediation) or '—'}\n\n"
            f"[bold]CVEs[/bold]\n{escape(', '.join(f.cve_ids)) or 'None mapped'}\n\n"
            f"[bold]NIST references[/bold]\n{escape(', '.join(f.nist_refs)) or '—'}\n\n"
            "[dim]Esc to close[/dim]"
        )
        with VerticalScroll():
            yield Static(body)


class CompareModal(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]
    DEFAULT_CSS = """
    CompareModal { align: center middle; }
    CompareModal > Static {
        width: auto; min-width: 50; height: auto; padding: 1 3;
        background: #080e18; border: tall #0d3a55;
    }
    """

    def __init__(self, renderable) -> None:
        super().__init__()
        self.renderable = renderable

    def compose(self) -> ComposeResult:
        yield Static(self.renderable)


class FindingsScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("s", "sort('severity')", "Sort severity"),
        ("c", "sort('cve')", "Sort CVEs"),
        ("t", "sort('tool')", "Sort tool"),
        ("r", "remediation", "Remediation plan"),
        ("slash", "focus_filter", "Filter"),
    ]

    DEFAULT_CSS = """
    FindingsScreen #filter { margin: 0 0 1 0; }
    FindingsScreen DataTable { height: 1fr; }
    FindingsScreen #findings-actions { height: 3; }
    """

    def __init__(self, findings: list[Finding] | None = None) -> None:
        super().__init__()
        self._explicit = findings
        self._mode = "severity"
        self._shown: list[Finding] = []

    @property
    def findings(self) -> list[Finding]:
        src = self._explicit if self._explicit is not None else self.app.state.findings
        return [f for f in src if f.severity != "Pass"]

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Findings[/bold cyan]  "
                     "[dim]s severity · c CVEs · t tool · r remediation · Enter detail[/dim]")
        if not self.findings:
            yield Static(f"[dim]{EMPTY_MSG}[/dim]", id="no-findings")
        else:
            yield Input(placeholder="Filter by any column…", id="filter")
            yield DataTable(id="findings-table", cursor_type="row")
            with Horizontal(id="findings-actions"):
                yield Button("Compare with last run", id="compare-runs")
                yield Button("Remediation plan (r)", id="remediation-plan")
        yield Footer()

    def on_mount(self) -> None:
        if self.findings:
            table = self.query_one(DataTable)
            table.add_columns(*COLUMNS)
            self._populate()
            table.focus()

    def _populate(self) -> None:
        table = self.query_one(DataTable)
        needle = self.query_one("#filter", Input).value.strip().lower()
        rows = [f for f in sort_findings(self.findings, self._mode)
                if not needle or any(needle in c.lower() for c in _cells(f))]
        self._shown = rows
        table.clear()
        for i, f in enumerate(rows):
            style = SEV_COLOUR.get(f.severity, "")
            table.add_row(*(Text(c, style=style) for c in _cells(f)), key=str(i))

    def action_sort(self, mode: str) -> None:
        if self.findings:
            self._mode = mode
            self._populate()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter":
            self._populate()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = int(event.row_key.value or 0)
        if 0 <= idx < len(self._shown):
            self.app.push_screen(FindingDetailModal(self._shown[idx]))

    def action_focus_filter(self) -> None:
        try:
            self.query_one("#filter", Input).focus()
        except Exception:
            pass

    def action_remediation(self) -> None:
        self.app.push_screen(CompareModal(remediation_plan(self.findings)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "remediation-plan":
            self.action_remediation()
        elif event.button.id != "compare-runs":
            return
        records = history.read()
        if len(records) < 2:
            self.app.push_screen(CompareModal("Need at least 2 runs to compare."))
        else:
            self.app.push_screen(CompareModal(comparison_table(records[-2], records[-1])))
