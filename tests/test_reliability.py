from __future__ import annotations

from agent.reliability import compute_probe_reliability
from agent.report import compose_report


def test_compute_probe_reliability_happy_path():
    result = compute_probe_reliability(
        [
            {"name": "inventory", "status": "ok"},
            {"name": "smartctl_sda", "status": "ok"},
            {"name": "battery_health", "status": "ok"},
        ]
    )

    assert result["reliability_score"] == 100
    assert result["parity_index"] == 100
    assert result["status"] == "healthy"


def test_compute_probe_reliability_degrades_for_skips_and_errors():
    result = compute_probe_reliability(
        [
            {"name": "inventory", "status": "ok"},
            {"name": "disk_performance", "status": "skip"},
            {"name": "cpu_benchmark", "status": "error"},
        ]
    )

    assert result["reliability_score"] < 100
    assert result["parity_index"] < 100
    assert result["failed"] == 1
    assert result["skipped"] == 1
    assert result["status"] == "degraded"


def test_compose_report_exposes_probe_reliability_metrics():
    report = compose_report(
        agent_version="0.1.0",
        device={"vendor": "Test", "model": "Laptop"},
        artifacts=[],
        tests=[
            {"name": "inventory", "status": "ok"},
            {"name": "memory_test", "status": "skip", "reason": "not found"},
        ],
        mode="quick",
        profile="default",
    )

    assert "probe_reliability" in report["summary"]
    assert "probe_parity_index" in report["summary"]
    assert report["summary"]["probe_reliability"] < 100
    assert report["summary"]["probe_health"]["skipped"] == 1
