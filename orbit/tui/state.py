"""Session state shared between screens."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from orbit.core.outputs import OutputConfig
from orbit.core.runner import ToolRun


@dataclass
class SessionState:
    dry_run: bool = False
    selected: set[str] = field(default_factory=set)
    output: OutputConfig = field(default_factory=OutputConfig)
    passphrase: str | None = None
    run_folder: Path | None = None
    runs: dict[str, ToolRun] = field(default_factory=dict)
    hash_override: bool = False
    client_name: str = ""
