"""Shared report context built once and consumed by the PDF and DOCX writers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path

from orbit.config import AUTHOR, FOOTER, ROLE, VERSION
from orbit.reporting import cve_map, scorer
from orbit.reporting.parser import Finding


@dataclass
class ReportContext:
    findings: list[Finding]
    tools_used: list[str]
    dry_run: bool = False
    client: str = "[Client Name]"
    report_date: str = field(default_factory=lambda: _date.today().isoformat())
    assessor: str = AUTHOR
    role: str = ROLE
    version: str = VERSION
    footer: str = FOOTER

    def __post_init__(self) -> None:
        self.summary = scorer.summarize(self.findings)
        self.top = scorer.top_n(self.findings, 3)
        self.sorted = scorer.sort_findings(self.findings)

    @property
    def title(self) -> str:
        return "ORBIT Assessment Summary" + (" (DRY RUN)" if self.dry_run else "")

    def bullets(self, f: Finding) -> list[str]:
        return [b.strip() for b in f.remediation.splitlines() if b.strip()][:4]

    def cve_text(self, f: Finding) -> str:
        if not f.cve_ids:
            return "None mapped"
        parts = []
        for c in f.cve_ids:
            s = cve_map.cvss_for(c)
            parts.append(f"{c} (CVSS {s})" if s is not None else c)
        return ", ".join(parts)


def report_filename(stem: str, ext: str, dry_run: bool) -> str:
    return f"{stem}{'_DRYRUN' if dry_run else ''}.{ext}"


def output_path(folder: Path, ext: str, dry_run: bool) -> Path:
    return Path(folder) / report_filename("ORBIT_Summary", ext, dry_run)
