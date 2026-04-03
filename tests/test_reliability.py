from __future__ import annotations

from agent.reliability import compute_probe_reliability, expected_probe_contract
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


def test_expected_probe_contract_by_os_family_and_mode():
    linux_quick = expected_probe_contract("linux", "quick")
    windows_full = expected_probe_contract("windows", "full")
    macos_quick = expected_probe_contract("macos", "quick")

    assert "inventory" in linux_quick["critical"]
    assert "smartctl" in linux_quick["critical"]
    assert "thermal_stress" in windows_full["optional"]
    assert "battery_health" in macos_quick["optional"]


def test_compute_probe_reliability_calibration_profile_tracks_missing_critical():
    result = compute_probe_reliability(
        [
            {"name": "inventory", "status": "ok"},
            {"name": "smartctl_sda", "status": "missing"},
        ],
        os_family="linux",
        mode="quick",
    )

    profile = result["calibration_profile"]
    assert profile["os_family"] == "linux"
    assert "smartctl" in profile["missing_critical"]
    assert result["parity_index"] < 100


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
    assert isinstance(report["summary"]["degraded_mode_recommendations"], list)
