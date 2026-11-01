"""Async subprocess runner for PowerShell and Python tools.

Secrets reach child processes only through environment variables (never argv) and every
output line is redacted before it is surfaced.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from orbit.config import FIXTURES_DIR
from orbit.core.hash_checker import HashResult, gate_run
from orbit.core.secrets import redact
from orbit.core.tools.base import Tool

LineCb = Callable[[str], None]


class RunStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETE = "Complete"
    FAILED = "Failed"
    SKIPPED = "Skipped"


@dataclass
class ToolRun:
    tool: Tool
    status: RunStatus = RunStatus.PENDING
    progress: float = 0.0
    started: float | None = None
    finished: float | None = None
    log: list[str] = field(default_factory=list)
    output_dir: Path | None = None
    note: str = ""

    @property
    def elapsed(self) -> float:
        if self.started is None:
            return 0.0
        return (self.finished or time.monotonic()) - self.started


async def stream_process(argv: list[str], env: dict[str, str], on_line: LineCb,
                         secrets: list[str] | None = None, cwd: Path | None = None,
                         handle: dict | None = None) -> int:
    """Run argv with env overlay, stream redacted merged output; terminate on cancellation."""
    secrets = secrets or []
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, **env}, cwd=str(cwd) if cwd else None,
    )
    if handle is not None:
        handle["proc"] = proc
    try:
        assert proc.stdout is not None
        async for raw in proc.stdout:
            on_line(redact(raw.decode(errors="replace").rstrip(), secrets))
        return await proc.wait()
    except asyncio.CancelledError:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), 5)
            except asyncio.TimeoutError:
                proc.kill()
        raise


class Runner:
    def __init__(self, out_dir: Path, creds: dict[str, dict], secrets: dict[str, list[str]] | None = None,
                 dry_run: bool = False, hash_results: list[HashResult] | None = None,
                 hash_override: bool = False, fixtures_dir: Path = FIXTURES_DIR,
                 on_update: Callable[[ToolRun], None] | None = None):
        self.out_dir = out_dir
        self.creds = creds
        self.secrets = secrets or {}
        self.dry_run = dry_run
        self.hash_results = hash_results or []
        self.hash_override = hash_override
        self.fixtures_dir = fixtures_dir
        self.on_update = on_update or (lambda r: None)
        self.runs: dict[str, ToolRun] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def _emit(self, run: ToolRun, line: str | None = None) -> None:
        if line is not None:
            run.log.append(line)
        self.on_update(run)

    async def run_tool(self, tool: Tool) -> ToolRun:
        run = self.runs.setdefault(tool.name, ToolRun(tool))
        run.output_dir = self.out_dir / tool.name
        run.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.dry_run:
            relevant = [r for r in self.hash_results if r.tool == tool.name]
            ok, msg = gate_run(relevant, self.hash_override)
            if not ok:
                run.status, run.note = RunStatus.SKIPPED, "integrity unverified" if not relevant or relevant[0].status.value == "unverified" else "hash mismatch"
                self._emit(run, "BLOCKED: " + msg)
                return run
        run.status, run.started = RunStatus.RUNNING, time.monotonic()
        self._emit(run)
        try:
            if self.dry_run:
                rc = await self._dry(tool, run)
            else:
                spec = tool.launch_spec(self.creds.get(tool.name, {}), run.output_dir)
                rc = await stream_process(spec.argv, spec.env, lambda l: self._emit(run, l),
                                          self.secrets.get(tool.name, []), spec.cwd, None)
            run.status = RunStatus.COMPLETE if rc == 0 else RunStatus.FAILED
            run.progress = 100.0 if rc == 0 else run.progress
        except asyncio.CancelledError:
            run.status, run.note = RunStatus.FAILED, "stopped by user"
            self._emit(run, "Stopped by user")
        except FileNotFoundError as exc:
            run.status, run.note = RunStatus.FAILED, str(exc)
            self._emit(run, f"Cannot launch: {exc}")
        finally:
            run.finished = time.monotonic()
            self._emit(run)
        return run

    async def _dry(self, tool: Tool, run: ToolRun) -> int:
        steps = [f"(DRY RUN) Simulating {tool.display}", "(DRY RUN) Authenticating (skipped)",
                 "(DRY RUN) Collecting configuration (fixture playback)"]
        for i, line in enumerate(steps, 1):
            self._emit(run, line)
            run.progress = i / (len(steps) + 1) * 100
            await asyncio.sleep(0.05)
        if tool.fixture and (self.fixtures_dir / tool.fixture).exists():
            shutil.copy(self.fixtures_dir / tool.fixture, run.output_dir / tool.output_name)
            self._emit(run, f"(DRY RUN) Wrote {tool.output_name}")
        else:
            self._emit(run, "(DRY RUN) No fixture for this tool; nothing to play back")
        return 0

    async def run_all(self, tools: list[Tool]) -> dict[str, ToolRun]:
        for t in tools:
            self.runs.setdefault(t.name, ToolRun(t))
        for t in tools:
            self._tasks[t.name] = asyncio.create_task(self.run_tool(t))
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        return self.runs

    def stop(self, name: str) -> None:
        task = self._tasks.get(name)
        if task and not task.done():
            task.cancel()

    def stop_all(self) -> None:
        for name in list(self._tasks):
            self.stop(name)
