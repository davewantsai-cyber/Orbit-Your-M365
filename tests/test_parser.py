from pathlib import Path

from orbit.reporting import parser
from orbit.reporting.parser import Finding

FIX = Path(__file__).parent / "fixtures"
SCUBA, MAESTER = FIX / "scubagear_sample.json", FIX / "maester_sample.json"


def test_scubagear_count_matches_fixture():
    f = parser.parse_scubagear(SCUBA)
    assert len(f) == 11  # 12 controls minus 1 N/A
    assert sum(x.severity == "Pass" for x in f) == 5
    assert sum(x.severity == "High" for x in f) == 5
    assert sum(x.severity == "Low" for x in f) == 1  # warning


def test_maester_count_matches_fixture():
    f = parser.parse_maester(MAESTER)
    assert len(f) == 7  # 8 tests minus 1 skipped
    assert sum(x.severity == "Pass" for x in f) == 3
    assert {x.control_id for x in f} >= {"MT.1009", "MT.1007"}


def test_finding_shape():
    f = parser.parse_maester(MAESTER)[0]
    assert isinstance(f, Finding)
    assert f.tool == "Maester" and f.cve_ids == [] and f.nist_refs == []


def test_cross_tool_dedupe():
    raw = parser.parse_scubagear(SCUBA) + parser.parse_maester(MAESTER)
    merged = parser.dedupe(raw)
    assert len(raw) == 18 and len(merged) == 16
    legacy = next(f for f in merged if f.control_id == "LEGACY_AUTH")
    assert legacy.tool == "Maester, ScubaGear"


def test_parse_files_enriches():
    f = parser.parse_files({"scubagear": SCUBA, "maester": MAESTER})
    mfa = next(x for x in f if x.control_id == "ADMIN_MFA")
    assert mfa.severity == "Critical" and "CVE-2022-21972" in mfa.cve_ids


def test_monkey365_json_and_csv(tmp_path):
    j = tmp_path / "m.json"
    j.write_text('[{"id":"M1","level":"high","displayName":"Bad","description":"d","remediation":"fix"},'
                 '{"id":"M2","level":"low","status":"pass","displayName":"Good"}]')
    c = tmp_path / "m.csv"
    c.write_text("id,level,displayName\nM1,high,Bad\nM2,medium,Meh\nM3,low,Low\n")
    assert [x.severity for x in parser.parse_monkey365(j)] == ["High", "Pass"]
    assert len(parser.parse_monkey365(c)) == 3
