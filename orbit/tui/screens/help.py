"""Help screen: keyboard shortcuts and reference."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Static

from orbit.config import VERSION

HELP_TEXT = f"""[bold cyan]ORBIT — Keyboard Shortcuts & Reference[/bold cyan]

[bold]NAVIGATION[/bold]
  ?          Toggle this help screen
  q          Quit ORBIT
  Escape     Go back / close screen

[bold]SCREENS[/bold]
  Credentials    Enter and save M365 tenant credentials
  Tools          Select which tools to run
  Install        Install or update tools from official sources
  Output         Set output directory, report formats, client name
  Email          Configure SMTP email delivery on completion
  Run ▶          Execute selected tools and stream live logs
  Report         View and export the summary report
  Findings       Browse, filter and compare findings

[bold]TOOLS INTEGRATED[/bold]
  ScubaGear     CISA SCuBA M365 baseline (Windows only) — github.com/cisagov/ScubaGear
  Maester       280+ Microsoft security tests              — maester.dev
  Monkey365     CIS M365/Azure benchmarks                 — github.com/silverhack/monkey365
  ROADtools     Entra ID enumeration (Python)             — github.com/dirkjanm/ROADtools
  Hawk          M365 incident response & threat hunting    — github.com/T0pCyber/hawk

[bold]REQUIREMENTS[/bold]
  • Run as Administrator (Windows) or sudo (Linux/macOS)
  • Global Administrator or equivalent M365 role
  • PowerShell 7+ for ScubaGear / Maester / Monkey365
  • Python 3.10+ for ROADtools

[bold]REPORTS[/bold]
  Output folder: set in Output screen, remembered in ~/.orbit/config.toml
  Formats: PDF, DOCX, HTML, JSON — select in Output screen
  Encryption: optional Fernet AES-256 with PBKDF2 passphrase

[bold]PRIVACY[/bold]
  ORBIT is 100% client-side. No data is transmitted externally.
  Credentials stored in OS keychain. See docs/PRIVACY.md.

[bold]VERSION[/bold]   v{VERSION}
[bold]AUTHOR[/bold]    Reece Gabriel Dickson — Independent Cybersecurity Research Analyst
[bold]LICENSE[/bold]   MIT — github.com/OrbitalSecurity/OrbitM365
"""


class HelpScreen(Screen):
    BINDINGS = [
        ("question_mark", "close", "Close"),
        ("q", "close", "Close"),
        ("escape", "close", "Close"),
    ]

    DEFAULT_CSS = """
    HelpScreen #help-body { padding: 1 3; }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="help-body"):
            yield Static(HELP_TEXT)
        yield Footer()

    def action_close(self) -> None:
        self.app.pop_screen()
