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
