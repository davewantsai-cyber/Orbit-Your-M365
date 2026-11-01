"""Executive summary PDF — single page, plain-English, for non-technical stakeholders."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

from orbit.config import AUTHOR, ROLE, VERSION
from orbit.reporting.parser import Finding
from orbit.reporting import scorer

SEV_RGB = {
    "Critical": (220, 38,  38),
    "High":     (234, 179, 8),
    "Medium":   (96,  165, 250),
    "Low":      (156, 163, 175),
    "Pass":     (34,  197, 94),
}

_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _find_font() -> str | None:
    return next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)


def _risk_label(posture: float) -> tuple[str, tuple[int, int, int]]:
    if posture >= 80:
        return "LOW RISK",      (34, 197, 94)
    if posture >= 60:
        return "MEDIUM RISK",   (234, 179, 8)
    if posture >= 40:
        return "HIGH RISK",     (249, 115, 22)
    return     "CRITICAL RISK", (220, 38, 38)


def generate_exec_summary(findings: list[Finding], out_dir: Path,
                           client: str = "", dry_run: bool = False) -> Path:
    """Generate a 1-2 page executive summary PDF."""
    font_path = _find_font()
    unicode_ok = bool(font_path)

    pdf = FPDF()
    pdf.set_auto_page_break(True, 20)
    fam = "U" if unicode_ok else "Helvetica"
    if unicode_ok:
        pdf.add_font("U", "", font_path)
        pdf.add_font("U", "B", font_path)

    def t(text: str) -> str:
        if unicode_ok:
            return text
        return (text.replace("\u2014", "-").replace("\u2013", "-")
                .replace("\u2022", "-").replace("\u2192", "->")
                .encode("latin-1", "replace").decode("latin-1"))

    def txt(size: int, bold: bool = False, rgb: tuple = (20, 30, 40)) -> None:
        pdf.set_font(fam, "B" if bold else "", size)
        pdf.set_text_color(*rgb)

    s = scorer.summarize(findings)
    risk_label, risk_rgb = _risk_label(s.posture)
    client_name = client.strip() or "Confidential"
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%d %B %Y")
    real_findings = [f for f in findings if f.severity != "Pass"]
    critical_high = [f for f in real_findings if f.severity in ("Critical", "High")]

    # ── Page 1: Cover + score ─────────────────────────────────────────────────
    pdf.add_page()

    # Header band
    pdf.set_fill_color(4, 6, 10)
    pdf.rect(0, 0, 210, 38, "F")
    txt(22, True, (0, 200, 255))
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, t("ORBIT"), new_x="LMARGIN", new_y="NEXT")
    txt(10, False, (30, 100, 130))
    pdf.set_xy(10, 22)
    pdf.cell(0, 7, t("M365 Security Assessment — Executive Summary"), new_x="LMARGIN", new_y="NEXT")
    txt(9, False, (20, 80, 100))
    pdf.set_xy(10, 30)
    pdf.cell(0, 6, t("Orbiting your M365. Nothing escapes."), new_x="LMARGIN", new_y="NEXT")

    # Client / meta
    pdf.set_xy(10, 44)
    txt(11, True, (20, 30, 40))
    pdf.cell(60, 7, t("Client:"), border="B")
    txt(11, False, (20, 30, 40))
    pdf.cell(0, 7, t(f"  {client_name}", ), new_x="LMARGIN", new_y="NEXT")

    for label, val in (
        ("Date:", date_str),
        ("Assessor:", AUTHOR),
        ("Role:", ROLE),
        ("ORBIT version:", f"v{VERSION}"),
        ("Tools used:", ", ".join({f.tool for f in findings}) or "none"),
    ):
        pdf.set_x(10)
        txt(10, True, (60, 80, 90))
        pdf.cell(60, 6, t(label))
        txt(10, False, (40, 50, 60))
        pdf.cell(0, 6, t(f"  {val}"), new_x="LMARGIN", new_y="NEXT")

    if dry_run:
        pdf.set_xy(10, pdf.get_y() + 2)
        txt(10, True, (220, 38, 38))
        pdf.cell(0, 7, t("(DRY RUN) Fixture data — not a real assessment"),
                 new_x="LMARGIN", new_y="NEXT")

    # Score gauge
    pdf.set_xy(10, pdf.get_y() + 8)
    txt(13, True, (20, 30, 40))
    pdf.cell(0, 8, t("Security Posture"), new_x="LMARGIN", new_y="NEXT")

    # Bar
    bar_x, bar_y, bar_w, bar_h = 10, pdf.get_y(), 140, 10
    pdf.set_fill_color(220, 225, 230)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")
    pdf.set_fill_color(*SEV_RGB["Pass"])
    pdf.rect(bar_x, bar_y, bar_w * s.posture / 100, bar_h, "F")
    pdf.set_xy(bar_x + bar_w + 4, bar_y)
    txt(18, True, risk_rgb)
    pdf.cell(0, bar_h, t(f"{round(s.posture)}/100"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(10, bar_y + bar_h + 2)
    txt(14, True, risk_rgb)
    pdf.cell(0, 9, t(risk_label), new_x="LMARGIN", new_y="NEXT")

    # Severity summary
    pdf.set_xy(10, pdf.get_y() + 4)
    txt(10, True, (20, 30, 40))
    pdf.cell(0, 7, t(f"{s.passed_controls} of {s.total_controls} controls passed"),
             new_x="LMARGIN", new_y="NEXT")
    col_w = 40
    pdf.set_x(10)
    for sev in ("Critical", "High", "Medium", "Low"):
        txt(10, False, SEV_RGB[sev])
        pdf.cell(col_w, 6, t(f"{sev}: {s.counts[sev]}"))
    pdf.ln()

    # ── Page 2: top findings + plain-English summary ──────────────────────────
    pdf.add_page()
    txt(14, True, (20, 30, 40))
    pdf.set_xy(10, 15)
    pdf.cell(0, 9, t("Priority Findings"), new_x="LMARGIN", new_y="NEXT")

    if not critical_high:
        txt(10, False, (40, 120, 60))
        pdf.cell(0, 7, t("No Critical or High severity findings identified."),
                 new_x="LMARGIN", new_y="NEXT")
    else:
        for i, f in enumerate(critical_high[:8], 1):
            sev_col = SEV_RGB[f.severity]
            txt(10, True, sev_col)
            pdf.set_x(10)
            pdf.cell(0, 7, t(f"{i}. [{f.severity}] {f.title}  ({f.control_id})"),
                     new_x="LMARGIN", new_y="NEXT")
            txt(9, False, (60, 80, 90))
            pdf.set_x(14)
            rem = f.remediation or "See vendor documentation."
            if len(rem) > 120:
                rem = rem[:117] + "..."
            pdf.multi_cell(0, 6, t(rem), new_x="LMARGIN", new_y="NEXT")
            if f.cve_ids:
                pdf.set_x(14)
                txt(8, False, (180, 100, 30))
                pdf.cell(0, 5, t("CVEs: " + ", ".join(f.cve_ids[:3])),
                         new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # Plain-English paragraph
    pdf.set_xy(10, pdf.get_y() + 6)
    txt(12, True, (20, 30, 40))
    pdf.cell(0, 8, t("Summary"), new_x="LMARGIN", new_y="NEXT")

    crit_count = s.counts["Critical"]
    high_count  = s.counts["High"]
    if crit_count:
        urgency = f"{crit_count} critical finding{'s' if crit_count > 1 else ''} requiring immediate action"
    elif high_count:
        urgency = f"{high_count} high-severity finding{'s' if high_count > 1 else ''} requiring prompt attention"
    else:
        urgency = "no critical or high severity findings"

    para = (
        f"This assessment evaluated {s.total_controls} security controls across the "
        f"{client_name} Microsoft 365 tenant using ORBIT v{VERSION}. "
        f"The tenant achieved a posture score of {round(s.posture)}/100, "
        f"rated {risk_label.lower()}, with {urgency}. "
        f"{s.passed_controls} controls passed. "
        f"Immediate remediation priority should be given to the findings listed above. "
        f"All findings, remediation steps, and control mappings are detailed in the "
        f"full technical report provided alongside this summary."
    )
    txt(10, False, (30, 40, 50))
    pdf.set_x(10)
    pdf.multi_cell(0, 6, t(para), new_x="LMARGIN", new_y="NEXT")

    # Footer strip
    pdf.set_y(-20)
    pdf.set_fill_color(4, 6, 10)
    pdf.rect(0, pdf.get_y(), 210, 20, "F")
    txt(8, False, (30, 90, 110))
    pdf.set_xy(10, pdf.get_y() + 4)
    pdf.cell(0, 6, t(f"Generated by ORBIT v{VERSION}  |  {AUTHOR}  |  {date_str}  |  "
                     "github.com/OrbitalSecurity/Orbit-Your-M365"))

    # Write file
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = client_name.replace(" ", "_")[:20] if client_name != "Confidential" else "DRYRUN" if dry_run else ""
    date_slug = now.strftime("%Y-%m-%d")
    fname = f"ORBIT_ExecSummary_{slug}_{date_slug}.pdf".replace("__", "_")
    out = out_dir / fname
    pdf.output(str(out))
    return out
