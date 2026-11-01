"""Compare two run-history entries."""
from __future__ import annotations


def compare(a: dict, b: dict) -> dict:
    """Compare two history entries (a = older, b = newer). Returns delta dict."""
    return {
        "score_delta": b["score"] - a["score"],
        "critical_delta": b["critical"] - a["critical"],
        "high_delta": b["high"] - a["high"],
        "medium_delta": b["medium"] - a["medium"],
        "low_delta": b["low"] - a["low"],
        "resolved": a["total_controls"] - a["passed"] - (b["total_controls"] - b["passed"]),
    }
