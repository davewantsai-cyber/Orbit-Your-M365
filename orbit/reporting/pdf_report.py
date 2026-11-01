"""PDF summary report (fpdf2)."""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from orbit.reporting.context import ReportContext, output_path
from orbit.reporting.parser import SEVERITIES

SEV_RGB = {"Critical": (239, 68, 68), "High": (250, 204, 21), "Medium": (96, 165, 250),
           "Low": (156, 163, 175), "Pass": (34, 197, 94)}
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def find_unicode_font() -> str | None:
    return next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)


class _PDF(FPDF):
    def __init__(self, ctx: ReportContext, unicode_ok: bool):
        super().__init__()
        self.ctx, self.unicode_ok = ctx, unicode_ok

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font(self.fam, "", 8)
        self.set_text_color(110, 120, 130)
        self.cell(0, 8, self.t(self.ctx.footer), align="C")

    fam = "Helvetica"

    def t(self, text: str) -> str:
        """Core fonts are latin-1 only; degrade gracefully when no Unicode font is available."""
        if self.unicode_ok:
            return text
        return (text.replace("\u2014", "-").replace("\u2013", "-")
                .encode("latin-1", "replace").decode("latin-1"))


def generate_pdf(ctx: ReportContext, folder: Path, use_unicode: bool = True) -> Path:
    font = find_unicode_font() if use_unicode else None
    pdf = _PDF(ctx, bool(font))
    pdf.set_auto_page_break(True, 20)
    if font:
        pdf.add_font("U", "", font)
        pdf.add_font("U", "B", font)  # no bold face available; same file is used
        pdf.fam = "U"
    else:
        pdf.set_compression(False)
    fam = pdf.fam
    t = pdf.t

    def text(size: int, bold: bool = False, rgb=(20, 30, 40)) -> None:
        pdf.set_font(fam, "B" if bold else "", size)
        pdf.set_text_color(*rgb)

    # 1. Cover
    pdf.add_page()
    pdf.ln(40)
    text(26, True)
    pdf.multi_cell(0, 12, t(ctx.title), align="C", new_x="LMARGIN", new_y="NEXT")
    text(12)
    for line in (f"Client: {ctx.client}", f"Date: {ctx.report_date}",
                 f"Assessor: {ctx.assessor}", ctx.role,
                 "Tools used: " + (", ".join(ctx.tools_used) or "none")):
        pdf.multi_cell(0, 8, t(line), align="C", new_x="LMARGIN", new_y="NEXT")
    if ctx.dry_run:
        text(12, True, SEV_RGB["Critical"])
        pdf.multi_cell(0, 10, t("(DRY RUN) Fixture data - not a real assessment"), align="C",
                       new_x="LMARGIN", new_y="NEXT")

    # 2. Posture
    pdf.add_page()
    s = ctx.summary
    text(16, True)
    pdf.cell(0, 10, t("Overall Posture"), new_x="LMARGIN", new_y="NEXT")
    text(12)
    pdf.cell(0, 8, t(f"{s.posture}% ({s.passed_controls} of {s.total_controls} controls passed)"),
             new_x="LMARGIN", new_y="NEXT")
    filled = round(s.posture / 5)
    if font:
        text(14, False, SEV_RGB["Pass"])
        pdf.cell(0, 9, "\u2588" * filled, new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(pdf.get_y() - 9)
        text(14, False, (200, 205, 210))
        pdf.set_x(pdf.l_margin + pdf.get_string_width("\u2588" * filled))
        pdf.cell(0, 9, "\u2588" * (20 - filled), new_x="LMARGIN", new_y="NEXT")
    else:  # glyph unavailable in core fonts: draw the bar with rectangles
        x, y, w = pdf.l_margin, pdf.get_y() + 1, 120
        pdf.set_fill_color(200, 205, 210)
        pdf.rect(x, y, w, 6, "F")
        pdf.set_fill_color(*SEV_RGB["Pass"])
        pdf.rect(x, y, w * s.posture / 100, 6, "F")
        pdf.ln(9)
    text(11)
    for sev in SEVERITIES:
        pdf.set_text_color(*SEV_RGB[sev])
        pdf.cell(0, 7, t(f"{sev}: {s.counts[sev]}"), new_x="LMARGIN", new_y="NEXT")

    # 3. Top findings
    pdf.ln(6)
    text(16, True)
    pdf.cell(0, 10, t("Top Priority Findings"), new_x="LMARGIN", new_y="NEXT")
    if not ctx.top:
        text(11)
        pdf.cell(0, 8, t("No Critical or High findings."), new_x="LMARGIN", new_y="NEXT")
    for f in ctx.top:
        text(12, True, SEV_RGB[f.severity])
        pdf.multi_cell(0, 7, t(f"[{f.severity}] {f.title}"), new_x="LMARGIN", new_y="NEXT")
        text(10)
        for line in (f"Source tool: {f.tool}", f"Control ID: {f.control_id}",
                     f"CVE(s): {ctx.cve_text(f)}", "Remediation:"):
            pdf.multi_cell(0, 6, t(line), new_x="LMARGIN", new_y="NEXT")
        for b in ctx.bullets(f):
            pdf.set_x(pdf.l_margin + 6)
            pdf.multi_cell(0, 6, t("- " + b), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # 4. Full table
    pdf.add_page()
    text(16, True)
    pdf.cell(0, 10, t("All Findings"), new_x="LMARGIN", new_y="NEXT")
    widths = (38, 20, 72, 30, 30)
    text(9, True)
    for h, w in zip(("ID", "Severity", "Title", "Tool", "Control"), widths):
        pdf.cell(w, 7, t(h), border=1)
    pdf.ln()
    for f in ctx.sorted:
        text(8)
        row_y = pdf.get_y()
        cells = (f.id, f.severity, f.title, f.tool, f.control_id)
        for val, w in zip(cells, widths):
            val = t(val)
            while pdf.get_string_width(val) > w - 2 and len(val) > 1:
                val = val[:-2] + "\u2026" if font else val[:-1]
            pdf.cell(w, 6, val, border=1)
        pdf.ln()
        if pdf.get_y() < row_y:  # page break handled by auto page break
            pass

    out = output_path(folder, "pdf", ctx)
    pdf.output(str(out))
    return out
