"""DOCX summary report (python-docx, with Jinja2 templates for text sections)."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import RGBColor
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from orbit.reporting.context import ReportContext, output_path
from orbit.reporting.parser import SEVERITIES

TEMPLATES = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATES)), undefined=StrictUndefined,
                   autoescape=False, keep_trailing_newline=False)
SEV_RGB = {"Critical": "EF4444", "High": "FACC15", "Medium": "60A5FA", "Low": "9CA3AF",
           "Pass": "22C55E"}


def render(name: str, **kw) -> list[str]:
    return _env.get_template(name).render(**kw).splitlines()


def generate_docx(ctx: ReportContext, folder: Path) -> Path:
    doc = Document()
    # 1. Cover
    lines = render("cover.txt.j2", ctx=ctx)
    doc.add_heading(lines[0], 0)
    for ln in lines[1:]:
        doc.add_paragraph(ln)
    if ctx.dry_run:
        p = doc.add_paragraph()
        r = p.add_run("(DRY RUN) Fixture data - not a real assessment")
        r.bold, r.font.color.rgb = True, RGBColor.from_string(SEV_RGB["Critical"])
    doc.add_page_break()

    # 2. Posture
    doc.add_heading("Overall Posture", 1)
    for ln in render("posture.txt.j2", s=ctx.summary):
        doc.add_paragraph(ln)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Light Grid Accent 1"
    table.rows[0].cells[0].text, table.rows[0].cells[1].text = "Severity", "Count"
    for sev in SEVERITIES:
        cells = table.add_row().cells
        cells[0].text, cells[1].text = sev, str(ctx.summary.counts[sev])

    # 3. Top findings
    doc.add_heading("Top Priority Findings", 1)
    if not ctx.top:
        doc.add_paragraph("No Critical or High findings.")
    for f in ctx.top:
        h = doc.add_heading(f"[{f.severity}] {f.title}", 2)
        for run in h.runs:
            run.font.color.rgb = RGBColor.from_string(SEV_RGB[f.severity])
        for ln in render("finding.txt.j2", f=f, cve_text=ctx.cve_text(f)):
            doc.add_paragraph(ln)
        doc.add_paragraph("Remediation:")
        for b in ctx.bullets(f):
            doc.add_paragraph(b, style="List Bullet")

    # 4. Full table
    doc.add_heading("All Findings", 1)
    t = doc.add_table(rows=1, cols=5)
    t.style = "Light Grid Accent 1"
    for c, h in zip(t.rows[0].cells, ("ID", "Severity", "Title", "Tool", "Control")):
        c.text = h
    for f in ctx.sorted:
        for c, v in zip(t.add_row().cells, (f.id, f.severity, f.title, f.tool, f.control_id)):
            c.text = v

    # 5. Footer
    doc.sections[0].footer.paragraphs[0].text = ctx.footer
    out = output_path(folder, "docx", ctx)
    doc.save(str(out))
    return out
