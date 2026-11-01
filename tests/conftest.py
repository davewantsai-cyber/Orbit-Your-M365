import pytest


@pytest.fixture(autouse=True)
def _isolated_orbit_home(tmp_path_factory, monkeypatch):
    """Keep tests from reading or writing the real ~/.orbit, or popping real notifications."""
    monkeypatch.setenv("ORBIT_HOME", str(tmp_path_factory.mktemp("orbit_home")))
    from orbit.core import config_store
    config_store.update("notifications", os_notify=False, email_notify=False)
