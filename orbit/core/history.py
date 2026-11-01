"""Run history: one record per run appended to ~/.orbit/history.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from orbit.core.config_store import orbit_home
from orbit.reporting import scorer
from orbit.reporting.parser import Finding


def history_path() -> Path:
    return orbit_home() / "history.json"


def make_record(findings: list[Finding], tools_run: list[str], client: str = "",
                dry_run: bool = False, now: datetime | None = None) -> dict:
    s = scorer.summarize(findings)
    now = now or datetime.now(timezone.utc)
    return {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "client": client,
        "tools_run": tools_run,
        "score": round(s.posture),
        "total_controls": s.total_controls,
        "passed": s.passed_controls,
        "critical": s.counts["Critical"],
        "high": s.counts["High"],
        "medium": s.counts["Medium"],
        "low": s.counts["Low"],
        "dry_run": dry_run,
    }


def read(path: Path | None = None) -> list[dict]:
    path = path or history_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def append(record: dict, path: Path | None = None) -> None:
    path = path or history_path()
    records = read(path)
    records.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def delta(path: Path | None = None) -> tuple[dict, int | None] | None:
    """(latest record, score change vs. the run before it or None) or None without history."""
    records = read(path)
    if not records:
        return None
    last = records[-1]
    prev = records[-2]["score"] if len(records) > 1 else None
    return last, (None if prev is None else last["score"] - prev)


def last_run_markup(path: Path | None = None) -> str:
    d = delta(path)
    if d is None:
        return "[dim]No previous runs recorded.[/dim]"
    last, change = d
    line = f"[dim]Last run:[/dim] [green]{last['timestamp'][:10]}[/green]  "
    if change is None:
        return line + f"Score [cyan]{last['score']}[/cyan]"
    prev = last["score"] - change
    if change > 0:
        arrow = f"[green]↑{change}[/green]"
    elif change < 0:
        arrow = f"[red]↓{-change}[/red]"
    else:
        arrow = "[yellow]→[/yellow]"
    return line + f"Score [cyan]{prev}[/cyan] → [cyan]{last['score']}[/cyan] {arrow}"
