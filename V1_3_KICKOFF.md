# ORBIT — v1.3.0 Feature Build

Read this entire file before touching any code. Run `pytest tests/ -v` after each feature. All 58 existing tests must continue to pass. Do not break anything.

## Scope — 9 features

---

### Feature 1 — Help screen (`?` key)

**New file:** `orbit/tui/screens/help.py`

Full-screen overlay, dismiss with `?`, `q`, or `Escape`.

Content (use a `ScrollableContainer` with `Static` rich markup):

```
ORBIT — Keyboard Shortcuts & Reference

NAVIGATION
  ?          Toggle this help screen
  q          Quit ORBIT
  Escape     Go back / close screen

SCREENS
  Credentials    Enter and save M365 tenant credentials
  Tools          Select which tools to run
  Install        Install or update tools from official sources
  Output         Set output directory, report formats, client name
  Email          Configure SMTP email delivery on completion
  Run ▶          Execute selected tools and stream live logs
  Report         View and export the summary report

TOOLS INTEGRATED
  ScubaGear     CISA SCuBA M365 baseline (Windows only) — github.com/cisagov/ScubaGear
  Maester       280+ Microsoft security tests              — maester.dev
  Monkey365     CIS M365/Azure benchmarks                 — github.com/silverhack/monkey365
  ROADtools     Entra ID enumeration (Python)             — github.com/dirkjanm/ROADtools
  Hawk          M365 incident response & threat hunting    — github.com/T0pCyber/hawk

REQUIREMENTS
  • Run as Administrator (Windows) or sudo (Linux/macOS)
  • Global Administrator or equivalent M365 role
  • PowerShell 7+ for ScubaGear / Maester / Monkey365
  • Python 3.10+ for ROADtools

REPORTS
  Output folder: set in Output screen, remembered in ~/.orbit/config.toml
  Formats: PDF, DOCX, HTML, JSON — select in Output screen
  Encryption: optional Fernet AES-256 with PBKDF2 passphrase

PRIVACY
  ORBIT is 100% client-side. No data is transmitted externally.
  Credentials stored in OS keychain. See docs/PRIVACY.md.

VERSION   v1.2.0
AUTHOR    Reece Gabriel Dickson — Independent Cybersecurity Research Analyst
LICENSE   MIT — github.com/OpenSourceByReece/OrbitSecurityM365
```

Register `HelpScreen` in `orbit/tui/app.py` SCREENS dict and bind `?` globally in `OrbitApp` to toggle it.

**Test:** `tests/test_help.py` — instantiate HelpScreen, assert it composes without error.

---

### Feature 2 — Onboarding wizard (skippable)

**New file:** `orbit/tui/screens/onboarding.py`

Show only when `~/.orbit/config.toml` has no credentials saved and this is the first launch (track with a `first_run: true` flag in config).

3-step wizard using Textual `TabbedContent` or just `Static` + `Button`:
- Step 1: Welcome — what ORBIT does, time saved, authorised-use reminder. Buttons: "Get Started →" / "Skip"
- Step 2: Quick setup — tenant ID input, app ID input. "I'll set this up later" skip link.
- Step 3: Choose tools — checkboxes for each tool. "Continue →"

Each step has a visible **"Skip setup →"** button that goes straight to home. The wizard must never block — if skipped, everything works normally.

Mark `first_run: false` in config after wizard completes or is skipped.

Launch the wizard from `OrbitApp.on_mount` before pushing `HomeScreen` when `first_run` is true.

**Test:** `tests/test_onboarding.py` — assert wizard composes, assert skip sets `first_run: false`.

---

### Feature 3 — Scrollable live log during run

**Where:** `orbit/tui/screens/run.py`

Replace the existing `Static` log widget with `textual.widgets.RichLog` (or `Log` in older Textual). Set `max_lines=2000`, `highlight=True`, `markup=True`.

Keep the same interface — `runner.py` should call `log_widget.write_line(text)` or equivalent. Ensure the log auto-scrolls to bottom but the user can scroll up without it jumping back down until they scroll back to the bottom.

**Test:** existing `tests/test_runner_tui.py` — ensure it still passes.

---

### Feature 4 — Findings viewer screen

**New file:** `orbit/tui/screens/findings.py`

After a run, display findings in a sortable, filterable `DataTable`:

Columns: `Severity | Tool | Control ID | Title | CVEs`

Rows sorted by severity (Critical first). Row colours:
- Critical: `#cc2222`
- High: `#cc6600`
- Medium: `#ccaa00`
- Low: `#2a6070`

Filter bar at top — text input, filters rows by any column content.
Keyboard: `c` = sort by CVE count, `s` = sort by severity, `t` = sort by tool, `Enter` on a row = show full finding detail in a modal (title, description, remediation, CVEs, NIST refs).

Add "Findings" button to home nav bar.
Register `FindingsScreen` in `orbit/tui/app.py`.
Only show findings if `app.state.findings` is non-empty; otherwise show "No findings yet — run an assessment first."

**Test:** `tests/test_findings.py` — instantiate with sample findings, assert DataTable has correct row count.

---

### Feature 5 — Run comparison / delta

**New file:** `orbit/core/compare.py`

```python
def compare(a: dict, b: dict) -> dict:
    """Compare two history entries. Returns delta dict."""
    return {
        "score_delta": b["score"] - a["score"],
        "critical_delta": b["critical"] - a["critical"],
        "high_delta": b["high"] - a["high"],
        "medium_delta": b["medium"] - a["medium"],
        "low_delta": b["low"] - a["low"],
        "resolved": a["total_controls"] - a["passed"] - (b["total_controls"] - b["passed"]),
    }
```

**Where consumed:** `orbit/tui/screens/findings.py` — add a "Compare with last run" button that calls `compare()` on the last two history entries and shows a Rich `Table` in a modal:

```
Run comparison: 2026-10-15 → 2026-11-01
Score        68 → 74  ↑ +6
Critical      3 → 2   ✓ -1
High          9 → 8   ✓ -1
Medium       14 → 14  → 0
Low           6 → 7   ↑ +1
Issues resolved: 3
```

If fewer than 2 history entries exist, show "Need at least 2 runs to compare."

**Test:** `tests/test_compare.py` — assert delta values are correct.

---

### Feature 6 — Auto-update checker

**New file:** `orbit/core/update_check.py`

```python
import urllib.request, json
from orbit.config import VERSION

RELEASES_URL = "https://api.github.com/repos/OpenSourceByReece/OrbitSecurityM365/releases/latest"

def check_latest(timeout: int = 3) -> str | None:
    """Return latest version string if newer than current, else None. Never raises."""
    try:
        with urllib.request.urlopen(RELEASES_URL, timeout=timeout) as r:
            data = json.loads(r.read())
        latest = data.get("tag_name", "").lstrip("v")
        if latest and latest != VERSION:
            return latest
    except Exception:
        pass
    return None
```

**Where consumed:** `orbit/tui/screens/home.py` — run `check_latest()` in a background `asyncio` worker on mount. If a newer version is found, show a dim one-liner below the last-run line:

`[dim]Update available: v1.3.0 — github.com/OpenSourceByReece/OrbitSecurityM365/releases[/dim]`

Respect `config["notifications"].get("update_check", True)` — if false, skip entirely.

**Test:** `tests/test_update_check.py` — mock `urllib.request.urlopen`, assert returns version string when newer, None when same or on error.

---

### Feature 7 — Minimum terminal size warning

**Where:** `orbit/tui/app.py` — in `on_mount`, check `self.size`:

```python
def on_mount(self) -> None:
    if self.size.width < 100 or self.size.height < 32:
        self.push_screen(SizeWarningScreen())
    else:
        self.push_screen(HomeScreen())
```

**New file:** `orbit/tui/screens/size_warning.py`

Simple screen with message:
```
⚠  Terminal too small

ORBIT requires at least 100 × 32 characters.
Current size: {w} × {h}

Please resize your terminal window and relaunch,
or press [Continue anyway] to proceed with reduced layout.

[Continue anyway]
```

"Continue anyway" pushes `HomeScreen`. No auto-dismiss — user must acknowledge.

**Test:** `tests/test_size_warning.py` — assert screen composes without error.

---

### Feature 8 — `--list-tools` flag

**Where:** `orbit/cli.py` — add `--list-tools` argument.

When set, print a table to stdout and exit:

```
ORBIT v1.2.0 — Tool Status

Tool         Installed    Compatible    Version
-----------  -----------  ------------  -------
ScubaGear    ✓ Yes        ✓ Windows     5.4.0
Maester      ✓ Yes        ✓ Yes         0.4.2
Monkey365    ✗ No         ✓ Yes         —
ROADtools    ✓ Yes        ✓ Yes         1.5.0
Hawk         ✗ No         ✓ Yes         —
```

Use Rich `Table` printed to console (not TUI). Exit 0.

**Test:** `tests/test_cli.py` — invoke with `--list-tools`, assert exit 0 and table header in output.

---

### Feature 9 — Report filename includes client name

**Where:** `orbit/reporting/pdf_report.py` and `orbit/reporting/docx_report.py`

Change filename from `ORBIT_Summary_DRYRUN.pdf` to:
- If client name set: `ORBIT_Summary_{client_slug}_{date}.pdf`
- If no client: `ORBIT_Summary_{date}.pdf`
- In dry-run: `ORBIT_Summary_DRYRUN_{date}.pdf`

Where `client_slug` is the client name with spaces replaced by underscores, non-alphanumeric characters stripped, max 24 chars.

Example: `ORBIT_Summary_Acme_Ltd_2026-11-01.pdf`

Update `tests/test_reports.py` to assert the new filename pattern.

---

## Nav bar update

After adding HelpScreen and FindingsScreen, the nav has 9 items — too many for one row. Split into two rows using `Vertical` containing two `Horizontal` containers:

Row 1: Credentials, Tools, Install, Output, Email
Row 2: Run ▶, Report, Findings, Help (?)

Update `#nav` CSS to `height: 9` to accommodate two button rows.

---

## pyproject.toml

Add entry point so `orbit` works as a CLI command:

```toml
[project.scripts]
orbit = "orbit.cli:main"
```

Ensure `orbit/cli.py` has a `main()` function that is the entry point.

---

## Validation

```bash
cd /Users/reece/Projects/orbit-m365
.venv/bin/pip install -e .
.venv/bin/pytest tests/ -v
.venv/bin/python orbit.py --dry-run --headless    # JSON output, exit 0
.venv/bin/orbit --list-tools                       # table output, exit 0
```

All 58 existing tests must pass. New tests must pass.

---

## Stop conditions

- Do not push to any remote.
- Do not expand scope beyond these 9 features.
- If a feature blocks, skip it, note why, continue with others.
- Do not break existing tests.

## Builder report

List: files changed/created, new tests added, final pytest count, anything skipped and why.
