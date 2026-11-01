import json

from orbit.core.hash_checker import (
    HashStatus,
    check_tool,
    gate_run,
    hash_tree,
    load_manifest,
    sha256_file,
)
from orbit.core.platform_check import PlatformInfo, compat_flags
from orbit.core.tools import ToolStatus, all_tools, get_tool


def _manifest(tool, ver, files):
    return {"tools": {tool: {"versions": {ver: {"files": files}}}}}


def test_sha256_known(tmp_path):
    p = tmp_path / "a"
    p.write_bytes(b"abc")
    assert sha256_file(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_ok_mismatch_unverified(tmp_path):
    (tmp_path / "m.psm1").write_text("good")
    good = hash_tree(tmp_path)
    assert check_tool("t", "1.0", tmp_path, _manifest("t", "1.0", good)).status is HashStatus.OK
    (tmp_path / "m.psm1").write_text("evil")
    r = check_tool("t", "1.0", tmp_path, _manifest("t", "1.0", good))
    assert r.status is HashStatus.MISMATCH and r.blocks_run and "m.psm1" in r.explain()
    assert check_tool("t", "9.9", tmp_path, _manifest("t", "1.0", good)).status is HashStatus.UNVERIFIED


def test_missing_file_is_mismatch(tmp_path):
    r = check_tool("t", "1", tmp_path, _manifest("t", "1", {"gone.txt": "00"}))
    assert r.status is HashStatus.MISMATCH and r.missing == ["gone.txt"]


def test_gate_blocks_unless_override(tmp_path):
    (tmp_path / "f").write_text("x")
    r = check_tool("t", "1", tmp_path, _manifest("t", "1", {"f": "00"}))
    assert gate_run([r])[0] is False
    assert gate_run([r], override=True)[0] is True
    assert gate_run([])[0] is True


def test_bundled_manifest_loads():
    m = load_manifest()
    assert set(m["tools"]) == {t.name for t in all_tools()}
    json.dumps(m)


def test_tool_status():
    win = PlatformInfo("windows", "pwsh", (7, 4), compat_flags("windows", True))
    mac = PlatformInfo("macos", "pwsh", (7, 4), compat_flags("macos", True))
    scuba = get_tool("scubagear")
    assert scuba.status(win, None) is ToolStatus.NOT_INSTALLED
    assert scuba.status(win, "1.0.0") is ToolStatus.INSTALLED
    assert scuba.status(win, "1.0.0", "1.2.0") is ToolStatus.UPDATE
    assert scuba.status(mac, "1.0.0") is ToolStatus.INCOMPATIBLE


def test_launch_specs_keep_secrets_out_of_argv(tmp_path):
    creds = {"tenant_id": "tid", "client_id": "cid", "client_secret": "TOPSECRET",
             "cert_thumbprint": "AB12CD34EF"}
    for t in all_tools():
        spec = t.launch_spec(creds, tmp_path)
        assert "TOPSECRET" not in " ".join(spec.argv) and "AB12CD34EF" not in " ".join(spec.argv)
