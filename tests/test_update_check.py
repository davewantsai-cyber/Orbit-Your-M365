import io
import json

from orbit.config import VERSION
from orbit.core import update_check


def _resp(tag):
    return io.BytesIO(json.dumps({"tag_name": tag}).encode())


def test_newer_version_returned(monkeypatch):
    monkeypatch.setattr(update_check.urllib.request, "urlopen", lambda *a, **k: _resp("v9.9.9"))
    assert update_check.check_latest() == "9.9.9"


def test_same_version_returns_none(monkeypatch):
    monkeypatch.setattr(update_check.urllib.request, "urlopen", lambda *a, **k: _resp(f"v{VERSION}"))
    assert update_check.check_latest() is None


def test_error_returns_none(monkeypatch):
    def boom(*a, **k):
        raise OSError("offline")
    monkeypatch.setattr(update_check.urllib.request, "urlopen", boom)
    assert update_check.check_latest() is None


def test_bad_json_returns_none(monkeypatch):
    monkeypatch.setattr(update_check.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"nope"))
    assert update_check.check_latest() is None
