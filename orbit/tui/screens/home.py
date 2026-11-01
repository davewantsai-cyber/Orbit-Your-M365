"""Home screen — full-width responsive layout."""
from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from rich.markup import escape
from rich.table import Table
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Static
from rich.text import Text

from orbit.core import config_store
from orbit.core.admin_check import ADMIN_WARNING, is_elevated
from orbit.core.update_check import check_latest
from orbit.core.platform_check import check_platform
from orbit.tui.banner import AnimatedBanner
from orbit.tui.screens.findings import FindingsScreen

# ── Quotes ────────────────────────────────────────────────────────────────────
_QUOTES: list[tuple[str, str]] = [
    ("Security is a process, not a product.",
     "Bruce Schneier"),
    ("Given enough eyeballs, all bugs are shallow.",
     "Linus's Law — Eric S. Raymond, The Cathedral and the Bazaar"),
    ("Amateurs hack systems, professionals hack people.",
     "Bruce Schneier"),
    ("The only truly secure system is one that is powered off, cast in a block of concrete "
     "and sealed in a lead-lined room with armed guards.",
     "Gene Spafford"),
    ("If you think technology can solve your security problems, then you don't understand "
     "the problems and you don't understand the technology.",
     "Bruce Schneier"),
    ("There are only two types of companies: those that have been hacked, "
     "and those that don't know they have been hacked.",
     "John Chambers, Cisco"),
    ("The hacker mindset doesn't actually see what happens on the other side, "
     "to the victim.",
     "Kevin Mitnick"),
    ("Hacking is not a crime — it is a skill. What you do with it defines you.",
     "Anon."),
    ("The best defence is a thorough understanding of the offence.",
     "Anon."),
    ("Complexity is the enemy of security.",
     "Bruce Schneier"),
    ("The weakest link in any security chain is almost always the human.",
     "Anon."),
    ("Defenders think in lists. Attackers think in graphs.",
     "John Lambert, Microsoft"),
    ("It takes 20 years to build a reputation and a few minutes of a cyber incident "
     "to ruin it.",
     "Stephane Nappo"),
    ("The question is no longer if you will be breached, but when — and how prepared you are.",
     "Anon."),
    ("In security, the more you know about how something breaks, "
     "the better you can build it to last.",
     "Anon."),
    ("Software never was perfect and won't get perfect. But is that a license "
     "to shoot the messenger?",
     "Wietse Venema"),
    ("We are all connected. In cyber, that connectivity is both our greatest strength "
     "and our greatest vulnerability.",
     "Anon."),
    ("Any sufficiently advanced bug is indistinguishable from a feature.",
     "Rich Kulawiec"),
    ("Open source is not just a development model; it is a philosophy of freedom.",
     "Richard Stallman"),
    ("Arguing that you don't care about the right to privacy because you have nothing to hide "
     "is no different than saying you don't care about free speech because you have nothing to say.",
     "Edward Snowden"),
    ("Privacy is not something that I'm merely entitled to, it's an absolute prerequisite.",
     "Marlon Brando"),
    ("Security without privacy is just surveillance.",
     "Anon."),
    ("Encryption works. Properly implemented strong crypto systems are one of the few things "
     "you can rely on.",
     "Edward Snowden"),
    ("The strength of open source is that it lets anyone audit the code. "
     "Security through obscurity is no security at all.",
     "Anon."),
    ("Cyber security is much more than an IT topic — it is a business risk.",
     "Anon."),
    ("In God we trust. All others we monitor.",
     "Anon. — NSA parody"),
    ("The art of war teaches us to rely not on the likelihood of the enemy not coming, "
     "but on our own readiness to receive him.",
     "Sun Tzu"),
    ("It's not about having the right answers. It's about asking the right questions "
     "before the attacker does.",
     "Anon."),
    ("Patch early, patch often. The attackers are not waiting.",
     "Anon."),
    ("Every system has a vulnerability. The goal is to find it before someone else does.",
     "Anon."),
    ("Knowing your enemy's tools is the first step to building your defence.",
     "Anon."),
    ("A misconfigured cloud is an open door. This tool exists to find them.",
     "ORBIT"),
    ("The cloud is just someone else's computer — secure it like it's yours.",
     "Anon."),
    ("Identity is the new perimeter.",
     "Anon. — Zero Trust principle"),
    ("Assume breach. Verify everything. Trust nothing.",
     "Zero Trust Architecture — NIST"),
    ("There is no patch for human stupidity — but there is for misconfiguration.",
     "Anon."),
    ("Your attack surface is larger than you think. Always.",
     "Anon."),
]


class QuotesWidget(Widget):
    """Rotates through security/privacy quotes, fading in and out."""

    DEFAULT_CSS = """
    QuotesWidget {
        width: 1fr;
        height: 1fr;
        padding: 1 4;
        content-align: center middle;
    }
    """

    def on_mount(self) -> None:
        self._idx = 0
        self._phase = 0          # 0=fade-in, 1=hold, 2=fade-out
        self._phase_tick = 0
        self._FADE  = 6          # ticks to fade in/out
        self._HOLD  = 40         # ticks to hold (≈6 s at 6fps)
        self.set_interval(0.15, self._tick)  # 6fps — purely cosmetic

    def _tick(self) -> None:
        self._phase_tick += 1
        if self._phase == 0 and self._phase_tick >= self._FADE:
            self._phase = 1
            self._phase_tick = 0
        elif self._phase == 1 and self._phase_tick >= self._HOLD:
            self._phase = 2
            self._phase_tick = 0
        elif self._phase == 2 and self._phase_tick >= self._FADE:
            self._idx = (self._idx + 1) % len(_QUOTES)
            self._phase = 0
            self._phase_tick = 0
        self.refresh()

    def render(self) -> Text:
        quote, author = _QUOTES[self._idx]
        w = max(self.size.width or 80, 40)

        # opacity 0→1→1→0
        if self._phase == 0:
            alpha = self._phase_tick / self._FADE
        elif self._phase == 1:
            alpha = 1.0
        else:
            alpha = 1.0 - self._phase_tick / self._FADE
        alpha = max(0.0, min(1.0, alpha))

        def _blend(hex_col: str, alpha: float) -> str:
            r = int(int(hex_col[1:3], 16) * alpha)
            g = int(int(hex_col[3:5], 16) * alpha)
            b = int(int(hex_col[5:7], 16) * alpha)
            return f"#{r:02x}{g:02x}{b:02x}"

        q_col  = _blend("#1a4a5a", alpha)
        a_col  = _blend("#0d3040", alpha)
        d_col  = _blend("#071820", alpha)

        # word-wrap the quote to terminal width minus padding
        max_w = max(w - 10, 30)
        words = quote.split()
        lines: list[str] = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= max_w:
                current = (current + " " + word).strip()
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        # centre-pad each line
        out = Text(no_wrap=False)
        out.append("\n")
        out.append("  ❝  ", style=d_col)
        out.append("\n")
        for line in lines:
            pad = max(0, (w - len(line)) // 2)
            out.append(" " * pad + line + "\n", style=q_col)
        attr_line = f"— {author}"
        pad = max(0, (w - len(attr_line)) // 2)
        out.append(" " * pad + attr_line + "\n", style=a_col)
        return out


def _tool_table(tools: list) -> Table:
    """Rich Table of tool status — renders at full widget width."""
    from orbit.core.tools.base import STATUS_GLYPH
    plat = check_platform()
    t = Table.grid(expand=True, padding=(0, 2))
    t.add_column("Tool",   style="#2a5a6a", ratio=1)
    t.add_column("Status", ratio=2)
    t.add_column("Tool",   style="#2a5a6a", ratio=1)
    t.add_column("Status", ratio=2)

    rows = []
    for tool in tools:
        inst = tool.installed_version() if tool.compatible(plat) else None
        st   = tool.status(plat, inst)
        ver  = f" [bright_blue]{inst}[/]" if inst else ""
        rows.append((f"[#4a8090]{tool.display}[/]", STATUS_GLYPH[st] + ver))

    for i in range(0, len(rows), 2):
        a = rows[i]
        b = rows[i + 1] if i + 1 < len(rows) else ("", "")
        t.add_row(a[0], a[1], b[0], b[1])
    return t


NAV_ROWS = [
    [("Credentials", "credentials"), ("Tools", "tool_select"), ("Install", "installer"),
     ("Output", "output"), ("Email", "email")],
    [("Run ▶", "run"), ("Report", "report"), ("Findings", "findings"), ("Help (?)", "help")],
]


class HomeScreen(Screen):
    BINDINGS = [("q", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield AnimatedBanner(id="banner")
        yield Static("", id="admin-warning")
        with Horizontal(id="info-row"):
            yield Static("", id="sys-info")
            yield Static("", id="dashboard")
        yield Static("", id="last-run")
        yield Static("", id="update-notice")
        yield QuotesWidget(id="quotes")
        with Vertical(id="nav"):
            for row in NAV_ROWS:
                with Horizontal():
                    for label, target in row:
                        yield Button(label, id=f"nav-{target}")
        yield Footer()

    def _refresh_dashboard(self) -> None:
        from orbit.core.tools import all_tools
        from orbit.core import history
        tbl = _tool_table(all_tools())
        markup = history.last_run_markup()
        spark = history.sparkline()
        if spark:
            markup += f"  [dim]Trend: {spark}[/dim]"
        self.query_one("#dashboard", Static).update(tbl)
        self.query_one("#last-run", Static).update(markup)

    def on_mount(self) -> None:
        info = check_platform()
        pw   = ".".join(map(str, info.pwsh_version)) if info.pwsh_version else "not found"
        self.query_one("#sys-info", Static).update(
            f"[dim]OS[/dim]          [bright_blue]{info.os_name}[/]\n"
            f"[dim]PowerShell[/dim]  [bright_blue]{escape(pw)}[/]\n"
            f"[dim]Python[/dim]      [bright_blue]{info.python_version}[/]"
            if hasattr(info, "python_version") else
            f"[dim]OS[/dim]          [bright_blue]{info.os_name}[/]\n"
            f"[dim]PowerShell[/dim]  [bright_blue]{escape(pw)}[/]"
        )
        if not is_elevated():
            self.query_one("#admin-warning", Static).update(
                "[bold red]⚠  NOT ELEVATED[/bold red]  "
                f"[dim]{ADMIN_WARNING}[/dim]"
            )
        self._refresh_dashboard()
        if config_store.load()["notifications"].get("update_check", True):
            self._check_update()

    @work(exclusive=True, group="update-check")
    async def _check_update(self) -> None:
        latest = await asyncio.to_thread(check_latest)
        if latest:
            self.query_one("#update-notice", Static).update(
                f"[dim]Update available: v{escape(latest)} — "
                "github.com/OpenSourceByReece/OrbitSecurityM365/releases[/dim]")

    def on_screen_resume(self) -> None:
        self._refresh_dashboard()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        target = (event.button.id or "").removeprefix("nav-")
        if target == "findings":
            self.app.push_screen(FindingsScreen())
        elif target == "run":
            self.app.push_screen("preflight")
        elif target in self.app.SCREENS:
            self.app.push_screen(target)
