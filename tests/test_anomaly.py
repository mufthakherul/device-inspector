from __future__ import annotations

from agent.anomaly import analyze_offline_anomalies


def test_analyze_offline_anomalies_detects_critical_thermal_and_memory():
    result = analyze_offline_anomalies(
        tests=[
            {
                "name": "thermal_stress",
                "status": "ok",
                "data": {"peak_temp": 96.2, "throttled": True},
            },
            {
                "name": "memory_test",
                "status": "ok",
                "data": {"error_count": 2},
            },
        ],
        scores={
            "storage": 90,
            "battery": 80,
            "memory": 30,
            "cpu_thermal": 45,
            "gpu": 85,
            "network": 90,
            "security": 75,
        },
    )

    ids = {a["id"] for a in result["anomalies"]}
    assert "THERMAL_PEAK_CRITICAL" in ids
    assert "MEMORY_ERRORS_DETECTED" in ids
    assert result["confidence_score"] < 90
    assert result["explainability"]["engine"] == "offline-rule-analyzer"


def test_analyze_offline_anomalies_detects_disk_throughput_warning():
    result = analyze_offline_anomalies(
        tests=[
            {
                "name": "disk_performance",
                "status": "ok",
                "data": {"read_mbps": 80.0, "write_mbps": 70.0},
            }
        ],
        scores={
            "storage": 50,
            "battery": 80,
            "memory": 90,
            "cpu_thermal": 85,
            "gpu": 85,
            "network": 90,
            "security": 75,
        },
    )

    assert any(a["id"] == "DISK_THROUGHPUT_LOW" for a in result["anomalies"])
