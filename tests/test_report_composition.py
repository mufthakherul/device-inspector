from __future__ import annotations

from agent.report import compose_report


def test_compose_report_uses_battery_health_score():
    report = compose_report(
        agent_version="0.1.0",
        device={"vendor": "Test", "model": "Laptop"},
        artifacts=[],
        tests=[
            {
                "name": "battery_health",
                "status": "ok",
                "data": {"health_pct": 60, "cycle_count": 300},
            }
        ],
        mode="quick",
        profile="default",
    )

    assert report["scores"]["battery"] == 60


def test_compose_report_sets_battery_100_when_missing():
    report = compose_report(
        agent_version="0.1.0",
        device={"vendor": "Test", "model": "Desktop"},
        artifacts=[],
        tests=[
            {
                "name": "battery_health",
                "status": "missing",
                "error": "No battery device detected by upower",
            }
        ],
        mode="quick",
        profile="default",
    )

    assert report["scores"]["battery"] == 100


def test_compose_report_uses_cpu_and_disk_benchmarks():
    report = compose_report(
        agent_version="0.1.0",
        device={"vendor": "Test", "model": "Laptop"},
        artifacts=[],
        tests=[
            {
                "name": "smartctl_nvme0n1",
                "status": "ok",
                "data": {"attributes": {}, "nvme_percentage_used": 5},
            },
            {
                "name": "disk_performance",
                "status": "ok",
                "data": {"read_mbps": 450, "write_mbps": 350},
            },
            {
                "name": "cpu_benchmark",
                "status": "ok",
                "data": {"events_per_second": 1600},
            },
        ],
        mode="quick",
        profile="default",
    )

    # Storage blends SMART and fio performance scores.
    assert report["scores"]["storage"] == 92
    assert report["scores"]["cpu_thermal"] == 85


def test_compose_report_adds_failure_classification_for_tooling_missing():
    report = compose_report(
        agent_version="0.1.0",
        device={"vendor": "Test", "model": "Laptop"},
        artifacts=[],
        tests=[
            {
                "name": "memory_test",
                "status": "skip",
                "reason": "memtester not found. Install with apt",
            }
        ],
        mode="full",
        profile="default",
    )

    assert "tooling_missing" in report["summary"]["failure_classification"]


def test_compose_report_adds_hardware_risk_for_critical_thermal():
    report = compose_report(
        agent_version="0.1.0",
        device={"vendor": "Test", "model": "Laptop"},
        artifacts=[],
        tests=[
            {
                "name": "cpu_benchmark",
                "status": "ok",
                "data": {"events_per_second": 1600},
            },
            {
                "name": "thermal_stress",
                "status": "ok",
                "data": {
                    "peak_temp": 97.0,
                    "throttled": True,
                    "thermal_severity": "critical",
                },
            },
        ],
        mode="full",
        profile="default",
    )

    assert "hardware_risk" in report["summary"]["failure_classification"]
    assert report["scores"]["cpu_thermal"] < 85
