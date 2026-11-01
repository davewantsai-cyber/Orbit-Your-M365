"""Config profile export / import — portable JSON snapshot of ORBIT settings."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from orbit.core import config_store
from orbit.config import VERSION


def export_profile(path: Path) -> None:
    """Write current config + version stamp to *path* as JSON."""
    cfg = config_store.load()
    # Never export secrets / passphrase — only non-sensitive settings
    safe = {
        "orbit_version": VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "output": {k: v for k, v in cfg["output"].items() if k != "directory"},
        "tools": cfg["tools"],
        "notifications": {k: v for k, v in cfg["notifications"].items()
                          if k != "email_notify"},
        "email": {k: v for k, v in cfg["email"].items()
                  if k not in ("smtp_host", "from_address", "to_addresses", "cc_addresses")},
        "app": cfg["app"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(safe, indent=2), encoding="utf-8")


def import_profile(path: Path) -> dict:
    """Load a JSON profile and merge into current config. Returns the merged config."""
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = config_store.load()
    # Merge only known safe sections; never overwrite secrets
    for section in ("output", "tools", "notifications", "app"):
        if section in data and isinstance(data[section], dict):
            cfg[section].update(
                {k: v for k, v in data[section].items() if k in cfg[section]}
            )
    config_store.save(cfg)
    return cfg
