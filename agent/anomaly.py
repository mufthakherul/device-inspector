from __future__ import annotations

from typing import Any


def analyze_offline_anomalies(
    tests: list[dict[str, Any]],
    scores: dict[str, int],
) -> dict[str, Any]:
    """Detect offline anomalies from already-collected probe outputs.

    The analyzer is deterministic and local-only. It does not call external
    services and can run during report composition in constrained environments.
    """
    anomalies: list[dict[str, Any]] = []

    def add_anomaly(
        anomaly_id: str,
        category: str,
        severity: str,
        message: str,
        evidence: dict[str, Any],
    ) -> None:
        anomalies.append(
            {
                "id": anomaly_id,
                "category": category,
                "severity": severity,
                "message": message,
                "evidence": evidence,
            }
        )

    for test in tests:
        name = str(test.get("name", ""))
        status = str(test.get("status", ""))
        data = test.get("data", {}) or {}

        if name.startswith("smartctl_") and status == "ok":
            nvme_pct = data.get("nvme_percentage_used")
            if isinstance(nvme_pct, int) and nvme_pct >= 80:
                add_anomaly(
                    "STORAGE_WEAR_HIGH",
                    "storage",
                    "warning",
                    "NVMe wear indicator is high.",
                    {"nvme_percentage_used": nvme_pct},
                )

        if name == "thermal_stress" and status == "ok":
            peak_temp = data.get("peak_temp")
            throttled = bool(data.get("throttled"))
            if isinstance(peak_temp, (int, float)) and peak_temp >= 90:
                add_anomaly(
                    "THERMAL_PEAK_CRITICAL",
                    "thermal",
                    "critical",
                    "Peak temperature reached critical range.",
                    {"peak_temp": peak_temp, "throttled": throttled},
                )
            elif throttled:
                add_anomaly(
                    "THERMAL_THROTTLE",
                    "thermal",
                    "warning",
                    "CPU throttling detected during stress.",
                    {"peak_temp": peak_temp, "throttled": throttled},
                )

        if name == "disk_performance" and status == "ok":
            read_mbps = data.get("read_mbps")
            write_mbps = data.get("write_mbps")
            if isinstance(read_mbps, (int, float)) and isinstance(
                write_mbps, (int, float)
            ):
                avg_mbps = (float(read_mbps) + float(write_mbps)) / 2
                if avg_mbps < 120:
                    add_anomaly(
                        "DISK_THROUGHPUT_LOW",
                        "performance",
                        "warning",
                        "Disk throughput is below expected baseline.",
                        {
                            "read_mbps": read_mbps,
                            "write_mbps": write_mbps,
                            "avg_mbps": round(avg_mbps, 2),
                        },
                    )

        if name == "memory_test" and status in {"error", "ok"}:
            error_count = data.get("error_count")
            if isinstance(error_count, int) and error_count > 0:
                add_anomaly(
                    "MEMORY_ERRORS_DETECTED",
                    "memory",
                    "critical",
                    "Memory test reported one or more errors.",
                    {"error_count": error_count},
                )

    confidence_score = 95
    for anomaly in anomalies:
        if anomaly["severity"] == "critical":
            confidence_score -= 18
        else:
            confidence_score -= 8

    # Add soft penalty for broad score weakness to keep confidence bounded.
    low_scores = sum(1 for value in scores.values() if value < 60)
    confidence_score -= low_scores * 3
    confidence_score = max(35, min(99, confidence_score))

    explainability = {
        "engine": "offline-rule-analyzer",
        "inputs": ["tests", "scores"],
        "rules_version": "1.0.0",
        "anomaly_count": len(anomalies),
    }

    return {
        "anomalies": anomalies,
        "confidence_score": confidence_score,
        "explainability": explainability,
    }
