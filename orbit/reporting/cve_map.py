"""Static mapping of M365 control IDs to CVEs / NIST refs (data/cve_mappings.json). Offline only."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from orbit.config import DATA_DIR

MAP_PATH = DATA_DIR / "cve_mappings.json"
_VERSION_SUFFIX = re.compile(r"v\d+$", re.IGNORECASE)


def normalize_control_id(cid: str) -> str:
    return _VERSION_SUFFIX.sub("", cid.strip()).upper()


@lru_cache(maxsize=4)
def _load(path: str) -> tuple[dict, dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    by_key = {e["canonical"]: e for e in data["controls"]}
    by_alias = {normalize_control_id(a): e for e in data["controls"] for a in e["aliases"]}
    by_alias.update({k.upper(): e for k, e in by_key.items()})
    return by_key, by_alias


def lookup(control_id: str, path: Path = MAP_PATH) -> dict | None:
    """Return the mapping entry for a tool control ID (or canonical key), else None."""
    return _load(str(path))[1].get(normalize_control_id(control_id))


def canonical(control_id: str, path: Path = MAP_PATH) -> str:
    entry = lookup(control_id, path)
    return entry["canonical"] if entry else normalize_control_id(control_id)


def cves_for(control_id: str) -> list[str]:
    e = lookup(control_id)
    return list(e["cve_ids"]) if e else []


def nist_for(control_id: str) -> list[str]:
    e = lookup(control_id)
    return list(e["nist_refs"]) if e else []


def cvss_for(cve_id: str) -> float | None:
    for e in _load(str(MAP_PATH))[0].values():
        if cve_id in e.get("cvss", {}):
            return e["cvss"][cve_id]
    return None
