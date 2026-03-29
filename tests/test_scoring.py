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


def test_score_disk_performance_ranges():
    assert scoring.score_disk_performance({}) == 70
    assert scoring.score_disk_performance({"read_mbps": 500, "write_mbps": 450}) == 95
    assert scoring.score_disk_performance({"read_mbps": 260, "write_mbps": 250}) == 85
    assert scoring.score_disk_performance({"read_mbps": 150, "write_mbps": 120}) == 70
    assert scoring.score_disk_performance({"read_mbps": 80, "write_mbps": 60}) == 45


def test_score_cpu_thermal_from_sysbench_events():
    assert scoring.score_cpu_thermal({}) == 85
    assert scoring.score_cpu_thermal({"events_per_second": 2200}) == 95
    assert scoring.score_cpu_thermal({"events_per_second": 1500}) == 85
    assert scoring.score_cpu_thermal({"events_per_second": 900}) == 70
    assert scoring.score_cpu_thermal({"events_per_second": 400}) == 50


def test_score_memory_from_importer_fields():
    assert (
        scoring.score_memory({"pass_count": 2, "error_count": 0, "status": "ok"}) == 95
    )
    assert (
        scoring.score_memory({"pass_count": 1, "error_count": 0, "status": "ok"}) == 90
    )
    assert (
        scoring.score_memory({"pass_count": 1, "error_count": 2, "status": "error"})
        == 20
    )


def test_score_cpu_thermal_applies_severity_penalty():
    base = scoring.score_cpu_thermal({"events_per_second": 1500})
    penalized = scoring.score_cpu_thermal(
        {
            "events_per_second": 1500,
            "peak_temp": 92,
            "throttled": True,
            "thermal_severity": "critical",
        }
    )

    assert base == 85
    assert penalized < base
