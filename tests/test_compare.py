from orbit.core.compare import compare


def _rec(score, c, h, m, l, total, passed):
    return {"score": score, "critical": c, "high": h, "medium": m, "low": l,
            "total_controls": total, "passed": passed}


def test_compare_deltas():
    a = _rec(68, 3, 9, 14, 6, 100, 68)
    b = _rec(74, 2, 8, 14, 7, 100, 71)
    d = compare(a, b)
    assert d == {"score_delta": 6, "critical_delta": -1, "high_delta": -1, "medium_delta": 0,
                 "low_delta": 1, "resolved": 3}


def test_compare_regression():
    d = compare(_rec(80, 0, 1, 1, 1, 50, 45), _rec(70, 1, 2, 1, 1, 50, 40))
    assert d["score_delta"] == -10 and d["critical_delta"] == 1 and d["resolved"] == -5
