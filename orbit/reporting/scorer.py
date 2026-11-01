"""Severity weights, overall posture score and top-N selection."""
from __future__ import annotations

from dataclasses import dataclass

from orbit.reporting.parser import RANK, SEVERITIES, Finding

WEIGHTS = {"Critical": 10, "High": 7, "Medium": 4, "Low": 1, "Pass": 0}


@dataclass
class Summary:
    total_controls: int
    passed_controls: int
    posture: float            # (passed / total) * 100
    risk_points: int          # sum of severity weights across findings
    counts: dict[str, int]


def weight(f: Finding) -> int:
    return WEIGHTS[f.severity]


def summarize(findings: list[Finding]) -> Summary:
    counts = {s: 0 for s in SEVERITIES}
    for f in findings:
        counts[f.severity] += 1
    total = len(findings)
    passed = counts["Pass"]
    posture = round(passed / total * 100, 1) if total else 0.0
    return Summary(total, passed, posture, sum(weight(f) for f in findings), counts)


def top_n(findings: list[Finding], n: int = 3, min_severity: str = "High") -> list[Finding]:
    """Top-N non-pass findings by severity, then weight, then more CVE refs, then control ID."""
    pool = [f for f in findings if RANK[f.severity] >= RANK[min_severity]]
    pool.sort(key=lambda f: (-RANK[f.severity], -weight(f), -len(f.cve_ids), f.control_id))
    return pool[:n]


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (-RANK[f.severity], f.control_id))
