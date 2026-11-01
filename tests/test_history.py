from pathlib import Path

from orbit.core import history
from orbit.reporting import parser

FIX = Path(__file__).parent / "fixtures"


def _findings():
    return parser.parse_files({"scubagear": FIX / "scubagear_sample.json",
                               "maester": FIX / "maester_sample.json"})


def test_append_and_read_back(tmp_path):
    p = tmp_path / "history.json"
    assert history.read(p) == []
    rec = history.make_record(_findings(), ["scubagear", "maester"], "Acme", True)
    history.append(rec, p)
    history.append(rec, p)
    got = history.read(p)
    assert len(got) == 2 and got[0] == rec
    assert rec["client"] == "Acme" and rec["dry_run"] is True
    assert rec["total_controls"] == 16 and rec["score"] == 50 and rec["critical"] == 1


def test_default_path_uses_orbit_home():
    history.append({"timestamp": "2026-01-01T00:00:00Z", "score": 1})
    assert history.history_path().exists()


def test_delta_and_markup(tmp_path):
    p = tmp_path / "h.json"
    assert history.delta(p) is None and "Pending first run" in history.last_run_markup(p)
    history.append({"timestamp": "2026-10-01T00:00:00Z", "score": 68, "dry_run": False}, p)
    assert history.delta(p)[1] is None
    history.append({"timestamp": "2026-10-15T00:00:00Z", "score": 74, "dry_run": False}, p)
    assert history.delta(p)[1] == 6
    m = history.last_run_markup(p)
    assert "2026-10-15" in m and "68" in m and "74" in m and "↑6" in m
    history.append({"timestamp": "2026-10-20T00:00:00Z", "score": 70, "dry_run": False}, p)
    assert "↓4" in history.last_run_markup(p)
    history.append({"timestamp": "2026-10-21T00:00:00Z", "score": 70, "dry_run": False}, p)
    assert "→" in history.last_run_markup(p).split("70")[-1]
