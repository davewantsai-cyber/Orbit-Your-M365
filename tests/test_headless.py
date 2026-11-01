import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _orbit(tmp_path, *args):
    env = {**os.environ, "ORBIT_HOME": str(tmp_path / "home")}
    return subprocess.run([sys.executable, str(ROOT / "orbit.py"), *args], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=120)


def test_dry_run_headless_emits_valid_json(tmp_path):
    r = _orbit(tmp_path, "--dry-run", "--headless")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)  # stdout must be only the JSON document
    assert data["orbit_version"] and data["timestamp"].endswith("Z")
    assert data["total_controls"] == 16 and data["score"] == 50 and data["passed"] == 8
    assert data["critical"] == 1
    assert len(data["top_findings"]) == 3 and data["top_findings"][0]["severity"] == "Critical"
    assert Path(data["output_dir"]).is_dir()
    assert (tmp_path / "home" / "history.json").exists()


def test_tools_flag_and_unknown_tool(tmp_path):
    r = _orbit(tmp_path, "--dry-run", "--headless", "--json", "--tools", "scubagear")
    assert r.returncode == 0 and json.loads(r.stdout)["total_controls"] < 16
    bad = _orbit(tmp_path, "--dry-run", "--headless", "--tools", "nope")
    assert bad.returncode == 1 and bad.stdout == "" and "Unknown tool" in bad.stderr


def test_failing_tool_exits_1(tmp_path):
    r = _orbit(tmp_path, "--headless", "--tools", "hawk")  # real run, no pwsh/module/creds
    assert r.returncode == 1
