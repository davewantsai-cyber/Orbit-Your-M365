import tomllib

from orbit.core import config_store as cs


def test_first_load_creates_defaults(tmp_path):
    p = tmp_path / "sub" / "config.toml"
    assert cs.load(p) == cs.DEFAULTS and p.exists()
    assert tomllib.loads(p.read_text()) == cs.DEFAULTS


def test_round_trip(tmp_path):
    p = tmp_path / "config.toml"
    cfg = cs.load(p)
    cfg["output"]["directory"] = 'C:\\out "dir"'
    cfg["tools"]["selected"] = ["scubagear", "maester"]
    cfg["email"].update(smtp_host="smtp.example.com", smtp_port=2525, smtp_tls=False,
                        to_addresses=["a@x.com", "b@x.com"])
    cfg["notifications"]["os_notify"] = False
    cs.save(cfg, p)
    assert cs.load(p) == cfg


def test_update_and_partial_file_merges_defaults(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('[tools]\nselected = ["hawk"]\n')
    cfg = cs.load(p)
    assert cfg["tools"]["selected"] == ["hawk"] and cfg["email"]["smtp_port"] == 587
    cs.update("output", p, directory="/tmp/x")
    assert cs.load(p)["output"]["directory"] == "/tmp/x"


def test_corrupt_file_falls_back(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text("not [valid toml")
    assert cs.load(p) == cs.DEFAULTS and p.read_text() == "not [valid toml"
