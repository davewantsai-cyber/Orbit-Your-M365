"""OS detection, PowerShell version check and per-tool compatibility flags."""
from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass
class PlatformInfo:
    os_name: str
    pwsh_path: str | None
    pwsh_version: tuple[int, ...] | None
    compat: dict[str, bool] = field(default_factory=dict)

    @property
    def pwsh7(self) -> bool:
        return bool(self.pwsh_version and self.pwsh_version[0] >= 7)


def detect_os() -> str:
    return {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(
        platform.system(), "other"
    )


def pwsh_version(pwsh: str | None = None) -> tuple[int, ...] | None:
    exe = pwsh or shutil.which("pwsh")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
            capture_output=True, text=True, timeout=20,
        ).stdout.strip()
        return tuple(int(p) for p in out.split("-")[0].split(".") if p.isdigit())
    except Exception:
        return None


def compat_flags(os_name: str, pwsh7: bool) -> dict[str, bool]:
    """ScubaGear is Windows-only; Maester/Monkey365/Hawk need PowerShell 7; ROADtools is Python."""
    return {
        "scubagear": os_name == "windows" and pwsh7,
        "maester": pwsh7,
        "monkey365": pwsh7,
        "hawk": pwsh7,
        "roadtools": True,
    }


def check_platform() -> PlatformInfo:
    os_name = detect_os()
    path = shutil.which("pwsh")
    ver = pwsh_version(path)
    info = PlatformInfo(os_name, path, ver)
    info.compat = compat_flags(os_name, info.pwsh7)
    return info
