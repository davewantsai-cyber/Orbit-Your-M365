"""Native OS completion notification (plyer). Failures are logged, never raised."""
from __future__ import annotations

import logging

from orbit.core import config_store

log = logging.getLogger(__name__)


def notify_complete(score: int, enabled: bool | None = None) -> bool:
    """Send 'ORBIT run complete'. Returns True if a notification was dispatched."""
    if enabled is None:
        enabled = config_store.load()["notifications"]["os_notify"]
    if not enabled:
        return False
    try:
        from plyer import notification

        notification.notify(title="ORBIT", message=f"ORBIT run complete — Score: {score}/100",
                            app_name="ORBIT", timeout=10)
        return True
    except Exception as exc:  # plyer missing, no backend, platform error
        log.warning("OS notification failed: %s", exc)
        return False
