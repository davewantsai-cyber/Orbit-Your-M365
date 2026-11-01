"""Parse ScubaGear / Maester / Monkey365 output into the unified Finding model."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from orbit.reporting import cve_map

SEVERITIES = ("Critical", "High", "Medium", "Low", "Pass")
RANK = {s: i for i, s in enumerate(reversed(SEVERITIES))}  # Pass=0 ... Critical=4


@dataclass
class Finding:
    id: str
    tool: str
    severity: str  # Critical/High/Medium/Low/Pass
    title: str
    description: str
    control_id: str
    remediation: str
    cve_ids: list[str] = field(default_factory=list)
    nist_refs: list[str] = field(default_factory=list)


def _norm_sev(value: str | None, default: str = "Medium") -> str:
    v = (value or "").strip().lower()
    return {"critical": "Critical", "high": "High", "medium": "Medium", "moderate": "Medium",
            "low": "Low", "info": "Low", "informational": "Low", "pass": "Pass",
            "passed": "Pass", "ok": "Pass"}.get(v, default)


def parse_scubagear(path: Path) -> list[Finding]:
    """ScubaResults.json: Results -> product -> groups -> Controls. N/A and Omitted are dropped."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: list[Finding] = []
    for product, groups in data.get("Results", {}).items():
        for group in groups:
            for c in group.get("Controls", []):
                result = str(c.get("Result", "")).lower()
                if result in ("n/a", "omitted", "incorrect result", ""):
                    continue
                crit = str(c.get("Criticality", "")).lower()
                if result == "pass":
                    sev = "Pass"
                elif result == "fail":
                    sev = "High" if crit.startswith("shall") else "Medium"
                else:  # warning / manual review
                    sev = "Low"
                cid = c.get("Control ID", "")
                out.append(Finding(
                    id=f"scubagear:{cid}", tool="ScubaGear", severity=sev,
                    title=f"[{product}] {group.get('GroupName', '')}".strip(),
                    description=f"{c.get('Requirement', '')} {c.get('Details', '')}".strip(),
                    control_id=cid, remediation=c.get("Requirement", ""),
                ))
    return out


def parse_maester(path: Path) -> list[Finding]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: list[Finding] = []
    for t in data.get("Tests", []):
        result = str(t.get("Result", "")).lower()
        if result in ("skipped", "notrun", "inconclusive", ""):
            continue
        name = t.get("Name", "")
        m = re.match(r"\s*([A-Za-z]+\.\d+(?:\.\d+)*)\s*:\s*(.*)", name)
        cid, title = (m.group(1), m.group(2)) if m else (name, name)
        detail = t.get("ResultDetail") or {}
        sev = "Pass" if result == "passed" else _norm_sev(t.get("Severity"))
        out.append(Finding(
            id=f"maester:{cid}", tool="Maester", severity=sev, title=title,
            description=" ".join(x for x in (detail.get("TestDescription"), detail.get("TestResult")) if x),
            control_id=cid, remediation=str(detail.get("TestResult", "")),
        ))
    return out


def _monkey_row(row: dict, i: int) -> Finding | None:
    g = lambda *keys: next((str(row[k]) for k in keys if row.get(k) not in (None, "")), "")
    level = g("level", "severity", "Level", "Severity")
    status = g("status", "result", "Status", "Result").lower()
    if status in ("skipped", "n/a", "notapplicable"):
        return None
    sev = "Pass" if status in ("pass", "passed", "ok") else _norm_sev(level)
    cid = g("ruleId", "id", "idSuffix", "control_id", "Id") or f"MONKEY-{i}"
    return Finding(
        id=f"monkey365:{cid}", tool="Monkey365", severity=sev,
        title=g("displayName", "title", "rule", "ruleName", "Title") or cid,
        description=g("description", "rationale", "Description"),
        control_id=cid, remediation=g("remediation", "recommendation", "Remediation"),
    )


def parse_monkey365(path: Path) -> list[Finding]:
    """Best-effort: JSON list (or {'findings'|'results': [...]}) or CSV with common header names."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else data.get("findings") or data.get("results") or []
    return [f for i, r in enumerate(rows) if (f := _monkey_row(r, i))]


def dedupe(findings: list[Finding]) -> list[Finding]:
    """Merge findings sharing a control (via alias map / normalised ID); worst severity wins."""
    groups: dict[str, list[Finding]] = {}
    for f in findings:
        groups.setdefault(cve_map.canonical(f.control_id), []).append(f)
    merged: list[Finding] = []
    for key, items in groups.items():
        best = max(items, key=lambda f: RANK[f.severity])
        tools = sorted({f.tool for f in items})
        merged.append(Finding(
            id=key, tool=", ".join(tools), severity=best.severity, title=best.title,
            description=best.description, control_id=key,
            remediation=max((f.remediation for f in items), key=len),
            cve_ids=sorted({c for f in items for c in f.cve_ids}),
            nist_refs=sorted({n for f in items for n in f.nist_refs}),
        ))
    return merged


def enrich(findings: list[Finding]) -> list[Finding]:
    """Attach CVEs / NIST refs / remediation from the static map; apply severity floors to non-passes."""
    for f in findings:
        e = cve_map.lookup(f.control_id)
        if not e:
            continue
        if f.severity != "Pass":
            f.cve_ids = sorted(set(f.cve_ids) | set(e["cve_ids"]))
            floor = e.get("severity_floor")
            if floor and RANK[floor] > RANK[f.severity]:
                f.severity = floor
            if e.get("remediation"):
                f.remediation = "\n".join(e["remediation"])
        f.nist_refs = sorted(set(f.nist_refs) | set(e["nist_refs"]))
    return findings


PARSERS = {"scubagear": parse_scubagear, "maester": parse_maester, "monkey365": parse_monkey365}
_PATTERNS = {"scubagear": ["ScubaResults*.json", "*.json"], "maester": ["maester*.json", "*.json"],
             "monkey365": ["*.json", "*.csv"]}


def parse_folder(run_folder: Path) -> list[Finding]:
    """Parse each <run_folder>/<tool>/ output dir, then dedupe + enrich."""
    raw: list[Finding] = []
    for tool, parser in PARSERS.items():
        d = Path(run_folder) / tool
        if not d.is_dir():
            continue
        for pat in _PATTERNS[tool]:
            hit = sorted(d.glob(pat))
            if hit:
                raw.extend(parser(hit[0]))
                break
    return enrich(dedupe(raw))


def parse_files(files: dict[str, Path]) -> list[Finding]:
    raw = [f for tool, p in files.items() for f in PARSERS[tool](p)]
    return enrich(dedupe(raw))
