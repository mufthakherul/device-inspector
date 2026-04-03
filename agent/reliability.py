# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Probe reliability scoring helpers.

This supports Sprint 3 roadmap work for degraded probe-set scoring and a
simple parity index derived from test execution health.
"""

from __future__ import annotations

from typing import Any


def _canonical_probe_name(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("smartctl"):
        return "smartctl"
    if lowered.startswith("inventory"):
        return "inventory"
    if lowered.startswith("cpu_benchmark"):
        return "cpu_benchmark"
    if lowered.startswith("disk_performance"):
        return "disk_performance"
    if lowered.startswith("memory_test"):
        return "memory_test"
    if lowered.startswith("battery_health"):
        return "battery_health"
    if lowered.startswith("sensors"):
        return "sensors"
    if lowered.startswith("thermal_stress"):
        return "thermal_stress"
    return lowered


def expected_probe_contract(
    os_family: str = "linux", mode: str = "quick"
) -> dict[str, list[str]]:
    """Return expected probe contracts by OS family and mode."""
    normalized_os = (os_family or "linux").lower()
    normalized_mode = (mode or "quick").lower()

    critical = [
        "inventory",
        "smartctl",
        "cpu_benchmark",
        "disk_performance",
        "memory_test",
    ]

    optional_by_os = {
        "linux": ["battery_health", "sensors"],
        "windows": ["battery_health", "sensors"],
        "macos": ["battery_health", "sensors"],
    }
    optional = optional_by_os.get(normalized_os, ["battery_health", "sensors"])

    if normalized_mode == "full":
        optional = [*optional, "thermal_stress"]

    return {
        "critical": critical,
        "optional": optional,
    }


def _build_probe_status_index(tests: list[dict[str, Any]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for test in tests:
        probe_name = _canonical_probe_name(str(test.get("name", "")))
        status = str(test.get("status", "")).lower()
        # Keep first meaningful status to ensure deterministic behavior.
        if probe_name and probe_name not in index:
            index[probe_name] = status
    return index


def _calibration_penalty(
    tests: list[dict[str, Any]],
    *,
    os_family: str,
    mode: str,
) -> tuple[int, int, dict[str, Any]]:
    contract = expected_probe_contract(os_family=os_family, mode=mode)
    index = _build_probe_status_index(tests)

    missing_critical: list[str] = []
    missing_optional: list[str] = []
    error_critical: list[str] = []

    for probe in contract["critical"]:
        status = index.get(probe)
        if status in {"skip", "missing"}:
            missing_critical.append(probe)
        elif status == "error":
            error_critical.append(probe)

    for probe in contract["optional"]:
        status = index.get(probe)
        if status in {"skip", "missing"}:
            missing_optional.append(probe)

    reliability_penalty = (
        len(missing_critical) * 12
        + len(error_critical) * 10
        + len(missing_optional) * 4
    )
    parity_penalty = (
        len(missing_critical) * 14
        + len(error_critical) * 12
        + len(missing_optional) * 6
    )

    profile = {
        "os_family": os_family,
        "mode": mode,
        "critical_probes": contract["critical"],
        "optional_probes": contract["optional"],
        "missing_critical": missing_critical,
        "error_critical": error_critical,
        "missing_optional": missing_optional,
    }

    return reliability_penalty, parity_penalty, profile


def compute_probe_reliability(
    tests: list[dict[str, Any]],
    *,
    os_family: str = "linux",
    mode: str = "quick",
) -> dict[str, Any]:
    """Compute a deterministic reliability score from probe outcomes."""
    if not tests:
        _, _, calibration_profile = _calibration_penalty(
            tests,
            os_family=os_family,
            mode=mode,
        )
        return {
            "reliability_score": 100,
            "parity_index": 100,
            "executed": 0,
            "passed": 0,
            "warned": 0,
            "skipped": 0,
            "failed": 0,
            "status": "no_probes",
            "calibration_profile": calibration_profile,
        }

    executed = 0
    passed = 0
    warned = 0
    skipped = 0
    failed = 0

    for test in tests:
        status = str(test.get("status", "")).lower()
        if status in {"ok", "missing", "skip", "error"}:
            executed += 1
        if status == "ok":
            passed += 1
        elif status in {"missing", "skip"}:
            skipped += 1
        elif status == "error":
            failed += 1
        else:
            warned += 1

    reliability_score = 100
    reliability_score -= failed * 18
    reliability_score -= skipped * 7
    reliability_score -= warned * 3

    calibration_reliability_penalty, calibration_parity_penalty, calibration_profile = (
        _calibration_penalty(
            tests,
            os_family=os_family,
            mode=mode,
        )
    )
    reliability_score -= calibration_reliability_penalty
    reliability_score = max(0, reliability_score)

    parity_index = 100
    parity_index -= skipped * 10
    parity_index -= failed * 15
    parity_index -= warned * 4
    parity_index -= calibration_parity_penalty
    parity_index = max(0, parity_index)

    if failed > 0:
        status = "degraded"
    elif skipped > 0 or warned > 0:
        status = "partial"
    else:
        status = "healthy"

    return {
        "reliability_score": reliability_score,
        "parity_index": parity_index,
        "executed": executed,
        "passed": passed,
        "warned": warned,
        "skipped": skipped,
        "failed": failed,
        "status": status,
        "calibration_profile": calibration_profile,
    }
