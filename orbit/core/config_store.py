"""Persistent user settings in ~/.orbit/config.toml (read with tomllib, written by hand)."""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

DEFAULTS: dict = {
    "output": {"directory": "", "formats": ["html", "json", "pdf"]},
    "tools": {"selected": []},
    "email": {
        "enabled": False, "smtp_host": "", "smtp_port": 587, "smtp_tls": True,
        "from_address": "", "to_addresses": [], "cc_addresses": [],
    },
    "notifications": {"os_notify": True, "email_notify": False, "update_check": True},
    "app": {"first_run": True},
}


def orbit_home() -> Path:
    """~/.orbit, overridable with ORBIT_HOME (used by tests)."""
    return Path(os.environ.get("ORBIT_HOME") or Path.home() / ".orbit")


def config_path() -> Path:
    return orbit_home() / "config.toml"


def _scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    return f'"{s}"'


def dumps(cfg: dict) -> str:
    out: list[str] = []
    for section, values in cfg.items():
        out.append(f"[{section}]")
        for k, v in values.items():
            rendered = "[" + ", ".join(_scalar(x) for x in v) + "]" if isinstance(v, list) \
                else _scalar(v)
            out.append(f"{k} = {rendered}")
        out.append("")
    return "\n".join(out)


def _merge(base: dict, over: dict) -> dict:
    for section, values in over.items():
        if isinstance(values, dict) and isinstance(base.get(section), dict):
            base[section].update({k: v for k, v in values.items() if k in base[section]})
    return base


def save(cfg: dict, path: Path | None = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(cfg), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def load(path: Path | None = None) -> dict:
    """Load config merged over defaults; creates the file with defaults on first launch."""
    path = path or config_path()
    cfg = copy.deepcopy(DEFAULTS)
    if not path.exists():
        save(cfg, path)
        return cfg
    try:
        return _merge(cfg, tomllib.loads(path.read_text(encoding="utf-8")))
    except (tomllib.TOMLDecodeError, OSError):
        return cfg  # corrupt file: fall back to defaults without overwriting it


def update(section: str, path: Path | None = None, **values) -> dict:
    """Load, change keys in one section, save."""
    cfg = load(path)
    cfg[section].update(values)
    save(cfg, path)
    return cfg
