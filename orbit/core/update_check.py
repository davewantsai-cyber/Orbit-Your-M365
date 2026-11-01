"""Check GitHub for a newer ORBIT release. Opt-out via [notifications] update_check = false."""
from __future__ import annotations

import json
import urllib.request

from orbit.config import VERSION

RELEASES_URL = "https://api.github.com/repos/OpenSourceByReece/OrbitSecurityM365/releases/latest"


def check_latest(timeout: int = 3) -> str | None:
    """Return latest version string if newer than current, else None. Never raises."""
    try:
        with urllib.request.urlopen(RELEASES_URL, timeout=timeout) as r:
            data = json.loads(r.read())
        latest = data.get("tag_name", "").lstrip("v")
        if latest and latest != VERSION:
            return latest
    except Exception:
        pass
    return None
