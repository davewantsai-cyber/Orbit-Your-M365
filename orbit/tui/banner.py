"""Animated banner — wide strip, photo-style Earth + large ORBIT logo.

Layout:
  Left ~42%  : large ORBIT block logo, tagline, metadata, clock
  Right ~58% : space field, stars, shooting stars, spinning Earth, satellite
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timezone

from rich.text import Text
from textual.widget import Widget

from orbit.config import AUTHOR, ROLE, VERSION, YEAR
from orbit.core.admin_check import current_user, permission_level

# ── Sun direction (upper-left, matches reference photo) ───────────────────────
_sx, _sy, _sz = -0.45, -0.55, 0.70
_sm = math.sqrt(_sx**2 + _sy**2 + _sz**2)
_SUN = (_sx / _sm, _sy / _sm, _sz / _sm)

# ── City lights on night side ─────────────────────────────────────────────────
_cr = random.Random(77)
_CITIES: list[tuple[float, float]] = [
    (_cr.uniform(-0.85, 0.85), _cr.uniform(-0.55, 0.55)) for _ in range(45)
]

# ── Fixed star field ──────────────────────────────────────────────────────────
_sr = random.Random(42)
_STARS: list[tuple[float, float, float]] = [
    (_sr.uniform(0.01, 0.99), _sr.uniform(0.04, 0.96), _sr.random() * math.tau)
    for _ in range(90)
]

# ── Large ORBIT block logo (6 rows × 38 cols) ─────────────────────────────────
_LOGO = [
    " ██████╗ ██████╗ ██████╗ ██╗████████╗",
    "██╔═══██╗██╔══██╗██╔══██╗██║╚══██╔══╝",
    "██║   ██║██████╔╝██████╔╝██║   ██║   ",
    "██║   ██║██╔══██╗██╔══██╗██║   ██║   ",
    "╚██████╔╝██║  ██║████████╗██║   ██║  ",
    " ╚═════╝ ╚═╝  ╚═╝╚═══════╝╚═╝   ╚═╝  ",
]

# Per-char colouring: █ and ╗/╝ lines = bright, spaces = skip
_LOGO_BRIGHT = "#00c8ff"
_LOGO_DIM    = "#005878"


def _cloud(nx: float, ny: float, t: float) -> float:
    v = (
        math.sin(nx * 4.2 + t * 0.22) * 0.35
        + math.sin(ny * 5.8 - t * 0.17) * 0.28
        + math.sin((nx + ny) * 3.4 + t * 0.13) * 0.22
        + math.sin(nx * 8.5 - ny * 2.2 + t * 0.28) * 0.15
    )
    return (v + 1.0) * 0.5


class AnimatedBanner(Widget):
    """Full-width animated banner with spinning photo-style Earth."""

    DEFAULT_CSS = """
    AnimatedBanner {
        height: 22;
        width: 100%;
        background: #04060a;
    }
    """

    def on_mount(self) -> None:
        self._f: int = 0
        self._ss: list[tuple[float, float, int]] = []
        self._cd: int = 0
        self._cached_size: tuple[int, int] = (0, 0)
        self._static_layer: list[list[tuple[str, str]]] | None = None
        self._clock_row: int = 0
        self._left_end: int = 0
        self.set_interval(0.10, self._tick)   # 10 fps — smooth and cheap

    def _tick(self) -> None:
        self._f += 1
        step = 3.5 / max(self.size.width or 120, 80)
        self._ss = [(x + step, y, n) for x, y, n in self._ss if x < 1.12]
        self._cd += 1
        if self._cd >= 15 and len(self._ss) < 3:
            if random.random() < 0.28:
                self._ss.append((
                    random.uniform(0.42, 0.55),
                    random.uniform(0.04, 0.40),
                    random.randint(4, 9),
                ))
                self._cd = 0
        self.refresh()

    def render(self) -> Text:
        f = self._f
        t = f * 0.08

        w = max(self.size.width  or 120, 80)
        h = max(self.size.height or 20,  16)

        # left panel limit — logo is 38 chars; give it a margin
        logo_w   = len(_LOGO[0])
        left_end = logo_w + 6          # ~44 cols for left panel
        left_end = min(left_end, w // 2 + 4)

        cv: list[list[tuple[str, str]]] = [[(" ", "#04060a")] * w for _ in range(h)]

        def p(r: int, c: int, ch: str, s: str) -> None:
            if 0 <= r < h and 0 <= c < w:
                cv[r][c] = (ch, s)

        # ── Earth geometry ────────────────────────────────────────────────────
        R   = max(6, (h - 3) // 2)
        RC  = R * 2
        ECX = w - RC - 6
        ECY = h // 2

        # Clamp earth not to overlap left panel
        ECX = max(ECX, left_end + RC + 4)

        # ── Star field (right panel only) ─────────────────────────────────────
        for sx_n, sy_n, ph in _STARS:
            sc = int(sx_n * w)
            sr = int(sy_n * h)
            if sc < left_end + 2:
                continue
            dx = (sc - ECX) / 2.0
            dy = float(sr - ECY)
            if dx * dx + dy * dy < (R + 4) ** 2:
                continue
            b = (math.sin(t * 1.3 + ph) + 1.0) * 0.5
            if b < 0.22:
                pass
            elif b < 0.45:
                p(sr, sc, "·", "#0c1c2a")
            elif b < 0.68:
                p(sr, sc, "·", "#182e40")
            elif b < 0.87:
                p(sr, sc, "*", "#26485c")
            else:
                p(sr, sc, "✦", "#3a6a84")

        # ── Shooting stars (right panel) ─────────────────────────────────────
        for ss_x, ss_y, ss_n in self._ss:
            cx = int(ss_x * w)
            cy = int(ss_y * h)
            if cx < left_end:
                continue
            for idx in range(ss_n + 1):
                cc = cx + idx
                if idx == ss_n:
                    p(cy, cc, "✦", "#c8e0f4")
                elif idx >= ss_n - 2:
                    p(cy, cc, "─", "#4a6070")
                else:
                    p(cy, cc, "─", "#182430")

        # ── Atmosphere glow ───────────────────────────────────────────────────
        for dr in range(-R - 3, R + 4):
            for dc in range(-RC - 5, RC + 6):
                dist = math.sqrt(float(dr * dr) + (dc / 2.0) ** 2)
                if not (R + 0.3 < dist < R + 2.5):
                    continue
                ndx = (dc / 2.0) / max(dist, 0.01)
                ndy = float(dr) / max(dist, 0.01)
                sun_d = ndx * _SUN[0] + ndy * _SUN[1]
                if sun_d < -0.1:
                    continue
                atm = max(0.0, sun_d + 0.35) * ((R + 2.5 - dist) / 2.2)
                r, c = ECY + dr, ECX + dc
                if c < left_end:
                    continue
                if atm > 0.65:
                    p(r, c, "▒", "#00c8f0")
                elif atm > 0.38:
                    p(r, c, "░", "#0090c8")
                elif atm > 0.14:
                    p(r, c, "·", "#004e70")

        # ── Earth surface ─────────────────────────────────────────────────────
        rot = t * 0.14
        cos_r, sin_r = math.cos(rot), math.sin(rot)

        for dr in range(-R, R + 1):
            for dc in range(-RC, RC + 1):
                dx = dc / 2.0
                dy = float(dr)
                dist_sq = dx * dx + dy * dy
                if dist_sq >= R * R:
                    continue
                r, c = ECY + dr, ECX + dc
                if c < left_end:
                    continue
                nz_val = math.sqrt(max(0.0, R * R - dist_sq))
                nx = dx / R; ny = dy / R; nz = nz_val / R
                diff = nx * _SUN[0] + ny * _SUN[1] + nz * _SUN[2]
                nx_r = nx * cos_r - nz * sin_r
                cd = _cloud(nx_r * 2.8, ny * 3.2, t)

                if diff > 0.06:
                    fade = min(1.0, (diff - 0.06) / 0.30)
                    if cd > 0.66:
                        if fade > 0.78:
                            ch, col = "█", "#d4ecff"
                        elif fade > 0.50:
                            ch, col = "▓", "#8aaec4"
                        elif fade > 0.25:
                            ch, col = "▒", "#5a7890"
                        else:
                            ch, col = "░", "#304458"
                    elif cd > 0.52:
                        ch, col = ("▒", "#506880") if fade > 0.45 else ("░", "#303e50")
                    else:
                        if fade > 0.72:
                            ch, col = "░", "#0e3c72"
                        elif fade > 0.42:
                            ch, col = "░", "#092c58"
                        else:
                            ch, col = "░", "#061a34"
                elif diff > -0.08:
                    ch, col = ("▒", "#252e3a") if cd > 0.62 else ("░", "#0a1420")
                else:
                    ch, col = "░", "#030608"
                    for cx_n, cy_n in _CITIES:
                        if (nx_r - cx_n) ** 2 + (ny - cy_n) ** 2 < 0.005:
                            ch, col = ("·", "#c89020") if random.random() < 0.65 else ("*", "#ffd040")
                            break
                p(r, c, ch, col)

        # ── Orbital path ──────────────────────────────────────────────────────
        OA = RC + 7
        OB = R  + 4
        for k in range(90):
            a   = k * math.tau / 90
            oc  = int(ECX + OA * math.cos(a))
            or_ = int(ECY + OB * math.sin(a))
            if oc < left_end:
                continue
            if 0 <= or_ < h and 0 <= oc < w:
                dx_ = (oc - ECX) / 2.0
                dy_ = float(or_ - ECY)
                if dx_ * dx_ + dy_ * dy_ < R * R:
                    continue
                if cv[or_][oc][0] == " ":
                    p(or_, oc, "·", "#071622")

        # ── Orbiting satellite ────────────────────────────────────────────────
        angle = t * 0.52
        sat_c = int(ECX + OA * math.cos(angle))
        sat_r = int(ECY + OB * math.sin(angle))
        dx_s  = (sat_c - ECX) / 2.0
        dy_s  = float(sat_r - ECY)
        behind = math.sin(angle) > 0.08 and dx_s * dx_s + dy_s * dy_s < (R + 1) ** 2

        if not behind and sat_c >= left_end:
            for trail in range(1, 11):
                ta  = angle - trail * 0.11
                tc  = int(ECX + OA * math.cos(ta))
                tr_ = int(ECY + OB * math.sin(ta))
                if tc < left_end:
                    continue
                fade = 1.0 - trail / 11.0
                p(tr_, tc, "·", "#0c3050" if fade > 0.5 else "#06182a")
            body = "►" if math.cos(angle) >= 0 else "◄"
            p(sat_r, sat_c,     body, "#d4a800")
            p(sat_r, sat_c - 1, "▓",  "#a07c00")
            p(sat_r, sat_c - 2, "▓",  "#785c00")
            p(sat_r, sat_c + 1, "▓",  "#a07c00")
            p(sat_r, sat_c + 2, "▓",  "#785c00")

        # ── Left panel: ORBIT block logo ──────────────────────────────────────
        logo_top = max(1, (h - len(_LOGO) - 5) // 2)
        for li, line in enumerate(_LOGO):
            row = logo_top + li
            for ci, ch in enumerate(line):
                col = 2 + ci
                if col >= left_end or row >= h:
                    continue
                if ch in ("█", "╗", "╔", "╝", "╚", "═", "║"):
                    p(row, col, ch, _LOGO_BRIGHT)
                elif ch not in (" ",):
                    p(row, col, ch, _LOGO_DIM)

        # Thin rule under logo
        rule_row = logo_top + len(_LOGO)
        for j in range(min(logo_w, left_end - 2)):
            p(rule_row, 2 + j, "─", "#0a2030")

        # Tagline
        tag = "M365 Risk & Baseline Intelligence Toolkit"
        tag_row = rule_row + 1
        for j, ch in enumerate(tag[:left_end - 3]):
            p(tag_row, 2 + j, ch, "#1a4a5a")

        # Metadata rows
        user = current_user()
        perm_label, perm_col = permission_level()
        meta = [
            ("Author  ", AUTHOR,      "#2a6070"),
            ("Version ", f"v{VERSION}", "#2a6070"),
            ("User    ", user,         "#2a8070"),
            ("Access  ", perm_label,   perm_col),
        ]
        for mi, (label, val, val_col) in enumerate(meta):
            mr = tag_row + 2 + mi
            for j, ch in enumerate((label + val)[:left_end - 3]):
                col_c = "#0d3040" if j < len(label) else val_col
                p(mr, 2 + j, ch, col_c)

        # Live clock
        now = datetime.now(timezone.utc)
        clk = f"⏱  {now:%Y-%m-%d  %H:%M:%S} UTC"
        clk_row = tag_row + 6
        for j, ch in enumerate(clk[:left_end - 3]):
            p(clk_row, 2 + j, ch, "#0d4a22")

        # Faint vertical divider
        for r in range(1, h - 1):
            if cv[r][left_end][0] == " ":
                p(r, left_end, "│", "#08182a")

        # ── Assemble ──────────────────────────────────────────────────────────
        out = Text(no_wrap=True)
        for row in range(h):
            for col_ in range(w):
                ch, s = cv[row][col_]
                out.append(ch, style=s)
            if row < h - 1:
                out.append("\n")
        return out


def render_banner() -> str:
    """Legacy shim."""
    return (
        "[#00c8ff]" + "\n".join(_LOGO) + "[/]\n"
        f"[#1a4a5a]v{VERSION}  {ROLE}[/]\n"
        f"[#2a6070]{AUTHOR} © {YEAR}[/]\n"
    )
