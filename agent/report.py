# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Report composition utilities.

Compose a canonical report.json following the project REPORT_SCHEMA.md.
The scaffold produces minimal fields sufficient for schema validation and
testing.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from . import scoring


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat()


def compose_report(
    agent_version: str,
    device: Dict[str, Any],
    artifacts: List[str],
    tests: List[Dict[str, Any]],
    mode: str = "quick",
    profile: str = "default",
    smart_status: Optional[str] = None,
    native: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compose a minimal report dict.

    The returned dictionary should validate against `schemas/report-schema-1.0.0.json`.

    Args:
        agent_version: Version of the agent
        device: Device information dictionary
        artifacts: List of artifact file paths
        tests: List of test result dictionaries
        mode: Inspection mode (quick/full)
        profile: Buyer profile
        smart_status: Overall SMART status (ok/sample/missing)
        native: Optional native helper metadata/capabilities
    """
    report: Dict[str, Any] = {
        "report_version": "1.0.0",
        "generated_at": _now_iso(),
        "agent": {"name": "inspecta", "version": agent_version},
        "device": device,
        "mode": mode,
        "profile": profile,
        "summary": {
            "overall_score": 0,
            "grade": "unknown",
            "recommendation": "",
        },
        "scores": {},
        "tests": tests,
        "artifacts": artifacts,
        "evidence": {"manifest_sha256": None, "signed": False},
    }

    if native is not None:
        report["native"] = native

    # Simple scoring heuristics based on tests
    storage_score = 50  # Default
    battery_score = scoring.score_battery({})
    cpu_score = scoring.score_cpu_thermal({})
    if tests:
        # Check for SMART test results
        smart_tests = [t for t in tests if t.get("name", "").startswith("smartctl")]
        if smart_tests:
            ok_tests = [t for t in smart_tests if t.get("status") == "ok"]
            if ok_tests:
                smart_score = min(
                    scoring.score_storage(test.get("data", {})) for test in ok_tests
                )
                storage_score = smart_score

        disk_tests = [t for t in tests if t.get("name") == "disk_performance"]
        if disk_tests and disk_tests[0].get("status") == "ok":
            disk_score = scoring.score_disk_performance(disk_tests[0].get("data", {}))
            # Blend SMART health and measured throughput for storage score.
            storage_score = int(round(storage_score * 0.7 + disk_score * 0.3))

        battery_tests = [t for t in tests if t.get("name") == "battery_health"]
        if battery_tests:
            battery_test = battery_tests[0]
            if battery_test.get("status") == "ok":
                battery_score = scoring.score_battery(battery_test.get("data", {}))
            elif battery_test.get("status") == "missing":
                # Desktops/no-battery devices should not be penalized.
                battery_score = 100

        cpu_tests = [t for t in tests if t.get("name") == "cpu_benchmark"]
        thermal_stress_tests = [t for t in tests if t.get("name") == "thermal_stress"]

        # Merge CPU benchmark and thermal stress data
        cpu_thermal_data = {}
        if cpu_tests and cpu_tests[0].get("status") == "ok":
            cpu_thermal_data = cpu_tests[0].get("data", {})

        if thermal_stress_tests and thermal_stress_tests[0].get("status") == "ok":
            # Add thermal stress data to CPU thermal info
            stress_data = thermal_stress_tests[0].get("data", {})
            cpu_thermal_data.update(
                {
                    "peak_temp": stress_data.get("peak_temp"),
                    "throttled": stress_data.get("throttled"),
                }
            )

        if cpu_thermal_data:
            cpu_score = scoring.score_cpu_thermal(cpu_thermal_data)

    report["scores"] = {
        "storage": storage_score,
        "battery": battery_score,
        "memory": scoring.score_memory({}),
        "cpu_thermal": cpu_score,
        "gpu": scoring.score_gpu({}),
        "network": scoring.score_network({}),
        "security": scoring.score_security({}),
    }

    # Compute overall score using profile weights
    overall, grade = scoring.compute_overall_score(report["scores"], profile)

    report["summary"]["overall_score"] = overall
    report["summary"]["grade"] = grade
    report["summary"]["recommendation"] = scoring.get_profile_recommendation(
        overall, grade, profile, report["scores"]
    )

    return report
