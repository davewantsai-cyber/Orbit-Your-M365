"""Abstract Tool: install metadata, version detection, launch command, credential env mapping."""
from __future__ import annotations

import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from orbit.core.platform_check import PlatformInfo


class ToolStatus(str, Enum):
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    UPDATE = "update_available"
    INCOMPATIBLE = "incompatible"


STATUS_GLYPH = {
    ToolStatus.INSTALLED: "[green]✓ installed[/green]",
    ToolStatus.NOT_INSTALLED: "[red]✗ not installed[/red]",
    ToolStatus.UPDATE: "[yellow]↑ update available[/yellow]",
    ToolStatus.INCOMPATIBLE: "[yellow]⚠ incompatible OS[/yellow]",
}


@dataclass
class LaunchSpec:
    """argv contains NO secrets; secrets travel only in env."""
    argv: list[str]
    env: dict[str, str]
    cwd: Path | None = None


def ver_tuple(v: str | None) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def run_capture(argv: list[str], timeout: int = 60) -> str:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


class Tool(ABC):
    name: str            # key, e.g. "scubagear"
    display: str
    github: str
    route: str           # "psgallery" | "pypi"
    package: str         # PS module name or pip package
    needs_admin: bool = False
    needs_pwsh: bool = True
    supported_os: tuple[str, ...] = ("windows", "macos", "linux")
    fixture: str = ""    # dry-run fixture filename in tests/fixtures
    output_name: str = ""  # file the tool writes inside its output dir

    # --- compatibility / version ----------------------------------------
    def compatible(self, platform: PlatformInfo) -> bool:
        return platform.compat.get(self.name, False) and platform.os_name in self.supported_os

    def installed_version(self) -> str | None:
        if self.route == "psgallery":
            pw = shutil.which("pwsh")
            if not pw:
                return None
            out = run_capture([pw, "-NoProfile", "-Command",
                               f"(Get-Module -ListAvailable {self.package} | "
                               "Sort-Object Version -Descending | Select-Object -First 1)"
                               ".Version.ToString()"])
            return out or None
        out = run_capture([_python(), "-m", "pip", "show", self.package])
        m = re.search(r"^Version:\s*(\S+)", out, re.MULTILINE)
        return m.group(1) if m else None

    def latest_version(self) -> str | None:
        """Ask the package source via the tool's own installer (pwsh/pip), never ORBIT itself."""
        if self.route == "psgallery":
            pw = shutil.which("pwsh")
            if not pw:
                return None
            return run_capture([pw, "-NoProfile", "-Command",
                                f"(Find-Module {self.package}).Version.ToString()"]) or None
        out = run_capture([_python(), "-m", "pip", "index", "versions", self.package])
        m = re.search(r"\((\S+)\)", out)
        return m.group(1) if m else None

    def install_dir(self) -> Path | None:
        """Directory holding installed files for hash verification (None if unknown)."""
        return None

    def status(self, platform: PlatformInfo, installed: str | None = None,
               latest: str | None = None) -> ToolStatus:
        if not self.compatible(platform):
            return ToolStatus.INCOMPATIBLE
        if installed is None:
            return ToolStatus.NOT_INSTALLED
        if latest and ver_tuple(latest) > ver_tuple(installed):
            return ToolStatus.UPDATE
        return ToolStatus.INSTALLED

    # --- install ----------------------------------------------------------
    def install_command(self, update: bool = False) -> list[str]:
        if self.route == "psgallery":
            verb = "Update-Module" if update else "Install-Module"
            extra = "" if update else " -Scope CurrentUser -Force"
            return [shutil.which("pwsh") or "pwsh", "-NoProfile", "-Command",
                    f"{verb} -Name {self.package}{extra}"]
        return [_python(), "-m", "pip", "install", "--upgrade", self.package]

    # --- run ----------------------------------------------------------------
    @abstractmethod
    def launch_spec(self, creds: dict, out_dir: Path) -> LaunchSpec:
        """Build argv (secret-free) and env (carries secrets) for running the tool."""


def _python() -> str:
    import sys
    return sys.executable


def ps_command(script: str) -> list[str]:
    return [shutil.which("pwsh") or "pwsh", "-NoProfile", "-NonInteractive", "-Command", script]


def cred_env(prefix: str, creds: dict) -> dict[str, str]:
    """Map credential fields to ORBIT_<PREFIX>_<FIELD> env vars (only non-empty values)."""
    return {f"ORBIT_{prefix}_{k.upper()}": str(v) for k, v in creds.items()
            if v not in (None, "", False)}
