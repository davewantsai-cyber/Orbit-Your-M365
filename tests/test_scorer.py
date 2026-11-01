from pathlib import Path

import pytest

from orbit.reporting import cve_map, parser, scorer

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture()
def findings():
    return parser.parse_files({"scubagear": FIX / "scubagear_sample.json",
                               "maester": FIX / "maester_sample.json"})


def test_weights():
    assert scorer.WEIGHTS == {"Critical": 10, "High": 7, "Medium": 4, "Low": 1, "Pass": 0}


def test_deterministic_summary(findings):
    s = scorer.summarize(findings)
    assert s.total_controls == 16 and s.passed_controls == 8
    assert s.posture == 50.0
    assert s.counts == {"Critical": 1, "High": 5, "Medium": 1, "Low": 1, "Pass": 8}
    assert s.risk_points == 10 + 5 * 7 + 4 + 1
    assert scorer.summarize(findings).posture == s.posture  # repeatable


def test_empty():
    assert scorer.summarize([]).posture == 0.0


def test_top_n_ordering(findings):
    top = scorer.top_n(findings, 3)
    assert top[0].control_id == "ADMIN_MFA" and top[0].severity == "Critical"
    assert all(f.severity in ("Critical", "High") for f in top) and len(top) == 3
    # tie-break by CVE count, then control id: EXT_FORWARDING/LEGACY_AUTH/CA_NOT_ENFORCED have CVEs
    assert [f.control_id for f in top[1:]] == ["CA_NOT_ENFORCED", "EXT_FORWARDING"]


def test_cve_lookups():
    expected = {
        "MS.AAD.1.1v1": ["CVE-2019-1372"], "MT.1007": ["CVE-2022-21972"],
        "MS.EXO.1.1v1": ["CVE-2023-23397"], "MT.1006": ["CVE-2022-21966"],
    }
    for cid, cves in expected.items():
        assert cve_map.cves_for(cid) == cves
    assert cve_map.nist_for("MT.1010") == ["AU-11"]
    assert cve_map.nist_for("MT.1021") == ["IA-5"]
    assert cve_map.nist_for("MS.SHAREPOINT.1.1v1") == ["AC-3"]
    assert cve_map.nist_for("MS.TEAMS.1.1v1") == ["AC-17"]
    assert cve_map.cves_for("UNKNOWN.1") == []
    assert cve_map.cvss_for("CVE-2023-23397") == 9.8
