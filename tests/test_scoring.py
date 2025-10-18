from __future__ import annotations

from agent import scoring


def test_score_storage_good():
    parsed = {"attributes": {}}
    # NVMe percentage used low
    parsed["nvme_percentage_used"] = 5
    assert scoring.score_storage(parsed) == 90


def test_score_storage_reallocated():
    parsed = {"attributes": {"Reallocated_Sector_Ct": 1}}
    assert scoring.score_storage(parsed) == 30


def test_score_battery_ranges():
    assert scoring.score_battery({}) == 80
    assert scoring.score_battery({"health_pct": 95}) == 95
    assert scoring.score_battery({"health_pct": 60}) == 60
