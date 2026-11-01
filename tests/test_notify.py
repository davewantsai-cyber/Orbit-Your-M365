import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

from orbit.core import config_store, notify


def _fake_plyer(monkeypatch, notify_fn):
    mod = ModuleType("plyer")
    mod.notification = SimpleNamespace(notify=notify_fn)
    monkeypatch.setitem(sys.modules, "plyer", mod)


def test_notification_title_and_message(monkeypatch):
    fn = MagicMock()
    _fake_plyer(monkeypatch, fn)
    assert notify.notify_complete(74, enabled=True) is True
    kw = fn.call_args.kwargs
    assert kw["title"] == "ORBIT" and kw["message"] == "ORBIT run complete — Score: 74/100"


def test_disabled_explicitly(monkeypatch):
    fn = MagicMock()
    _fake_plyer(monkeypatch, fn)
    assert notify.notify_complete(74, enabled=False) is False
    fn.assert_not_called()


def test_config_flag_respected(monkeypatch):
    config_store.update("notifications", os_notify=False)
    fn = MagicMock()
    _fake_plyer(monkeypatch, fn)
    assert notify.notify_complete(10) is False and not fn.called


def test_failure_is_swallowed(monkeypatch):
    _fake_plyer(monkeypatch, MagicMock(side_effect=NotImplementedError("no backend")))
    assert notify.notify_complete(74, enabled=True) is False


def test_plyer_missing_is_swallowed(monkeypatch):
    monkeypatch.setitem(sys.modules, "plyer", None)  # makes the import raise ImportError
    assert notify.notify_complete(74, enabled=True) is False
