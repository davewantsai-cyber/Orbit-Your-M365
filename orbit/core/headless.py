"""Headless (no TUI) run: execute tools, score, return a JSON-serialisable summary."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from orbit.config import VERSION
from orbit.core import config_store
from orbit.core.outputs import FORMATS, OutputConfig, make_run_folder
from orbit.core.pipeline import finalize
from orbit.core.runner import Runner, RunStatus
from orbit.core.secrets import SecretStore
from orbit.core.tools import all_tools
from orbit.reporting import scorer


class HeadlessError(Exception):
    """Bad arguments or configuration (reported on stderr, exit 1)."""


def select_tools(names: list[str], configured: list[str], dry_run: bool):
    tools = all_tools()
    known = {t.name for t in tools}
    unknown = [n for n in names if n not in known]
    if unknown:
        raise HeadlessError(f"Unknown tool(s): {', '.join(unknown)}. Choose from: "
                            f"{', '.join(sorted(known))}")
    wanted = names or configured
    chosen = [t for t in tools if t.name in wanted]
    if not chosen and dry_run:
        chosen = [t for t in tools if t.fixture]
    if not chosen:
        raise HeadlessError("No tools selected; pass --tools or select tools in ~/.orbit/config.toml")
    return chosen


async def _run(tools, folder: Path, dry_run: bool):
    creds, secrets = {}, {}
    if not dry_run:
        store = SecretStore()
        for t in tools:
            creds[t.name] = store.load(t.name)
            secrets[t.name] = store.secret_values(t.name)
    runner = Runner(folder, creds, secrets, dry_run)
    return await runner.run_all(tools)


def run_headless(dry_run: bool = False, tool_names: list[str] | None = None) -> tuple[dict, int]:
    """Returns (payload, exit_code); exit_code is 1 if any tool failed or was skipped."""
    cfg = config_store.load()
    tools = select_tools(tool_names or [], cfg["tools"]["selected"], dry_run)
    base = Path(cfg["output"]["directory"] or "output")
    formats = {f.upper() for f in cfg["output"]["formats"]} & set(FORMATS)
    out_cfg = OutputConfig(base_dir=base, formats=formats)
    folder = make_run_folder(base)

    try:
        runs = asyncio.run(_run(tools, folder, dry_run))
    except PermissionError as exc:
        raise HeadlessError(f"Cannot load credentials: {exc}") from exc
    failed = [r.tool.name for r in runs.values() if r.status is not RunStatus.COMPLETE]

    findings, _ = finalize(folder, [t.display for t in tools], out_cfg, dry_run)
    s = scorer.summarize(findings)
    payload = {
        "orbit_version": VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "score": round(s.posture),
        "total_controls": s.total_controls,
        "passed": s.passed_controls,
        "critical": s.counts["Critical"],
        "high": s.counts["High"],
        "medium": s.counts["Medium"],
        "low": s.counts["Low"],
        "top_findings": [
            {"control_id": f.control_id, "tool": f.tool, "severity": f.severity,
             "title": f.title, "remediation": f.remediation, "cve_ids": f.cve_ids}
            for f in scorer.top_n(findings, 3)
        ],
        "output_dir": str(folder.resolve()),
        "dry_run": dry_run,
        "failed_tools": failed,
    }
    return payload, (1 if failed else 0)
