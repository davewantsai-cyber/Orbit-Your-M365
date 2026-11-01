"""Detect whether the process is running elevated."""
import os
import sys

ADMIN_WARNING = (
    "ScubaGear and Maester require Global Administrator rights in your M365 tenant. "
    "Run as Administrator on Windows."
)


def is_elevated() -> bool:
    if sys.platform == "win32":
        import ctypes
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        except Exception:
            return False
    return os.geteuid() == 0


def current_user() -> str:
    """Return the logged-in username, cross-platform."""
    try:
        if sys.platform == "win32":
            return os.environ.get("USERNAME") or os.environ.get("USER") or "Unknown"
        return os.environ.get("USER") or os.environ.get("LOGNAME") or os.getlogin()
    except Exception:
        return "Unknown"


def permission_level() -> tuple[str, str]:
    """Return (label, colour) for the current user's privilege level."""
    if is_elevated():
        return "Administrator", "#00c840"
    return "Standard User", "#c87000"

