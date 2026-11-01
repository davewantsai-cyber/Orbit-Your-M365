from textual.app import App
from textual.widgets import DataTable, Input

from orbit.core import history
from orbit.reporting.parser import Finding
from orbit.tui.screens.findings import CompareModal, FindingDetailModal, FindingsScreen, sort_findings


def _f(i, sev, tool="Maester", cves=()):
    return Finding(id=f"x{i}", tool=tool, severity=sev, title=f"Title {i}", description="d",
                   control_id=f"C.{i}", remediation="r", cve_ids=list(cves))


SAMPLE = [_f(1, "Low"), _f(2, "Critical", cves=["CVE-1", "CVE-2"]), _f(3, "High", "ScubaGear"),
          _f(4, "Medium", cves=["CVE-3"]), _f(5, "Pass")]


class Host(App):
    def __init__(self, findings):
        super().__init__()
        self._findings = findings

    def on_mount(self):
        self.push_screen(FindingsScreen(self._findings))


async def test_table_rows_sorted_and_pass_excluded():
    app = Host(SAMPLE)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        table = app.screen.query_one(DataTable)
        assert table.row_count == 4
        assert table.get_row_at(0)[0].plain == "Critical"
        await pilot.press("t")
        assert table.get_row_at(0)[1].plain == "Maester"
        await pilot.press("c")
        assert table.get_row_at(0)[2].plain == "C.2"


async def test_filter_and_detail_modal():
    app = Host(SAMPLE)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.screen.query_one(Input).value = "scuba"
        await pilot.pause()
        table = app.screen.query_one(DataTable)
        assert table.row_count == 1
        table.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, FindingDetailModal)


async def test_empty_state_and_compare_needs_two_runs():
    app = Host([])
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert "No findings yet" in str(app.screen.query_one("#no-findings").render())
    app = Host(SAMPLE)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#compare-runs")
        await pilot.pause()
        assert "at least 2 runs" in str(app.screen.query_one("Static").render())


def test_sort_findings_modes():
    assert [f.severity for f in sort_findings(SAMPLE, "severity")][:2] == ["Critical", "High"]
    assert sort_findings(SAMPLE, "cve")[0].control_id == "C.2"


async def test_compare_modal_with_history():
    for score, crit in ((68, 3), (74, 2)):
        history.append({"timestamp": "2026-10-15T00:00:00Z", "score": score, "critical": crit,
                        "high": 1, "medium": 1, "low": 1, "total_controls": 10, "passed": 5})
    app = Host(SAMPLE)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#compare-runs")
        await pilot.pause()
        assert isinstance(app.screen, CompareModal)
        assert "Run comparison" in app.screen.renderable.title
