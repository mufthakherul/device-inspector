# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Report composition utilities.

Compose a canonical report.json following the project REPORT_SCHEMA.md.
The scaffold produces minimal fields sufficient for schema validation and
testing.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from . import anomaly, policy_pack, scoring
from .schema_compat import REPORT_SCHEMA_VERSION


def _classify_failures(tests: List[Dict[str, Any]]) -> List[str]:
    """Classify failures for Sprint 2 report semantics.

    Categories:
    - hardware_risk: Deep diagnostics indicate actual hardware faults
    - tooling_missing: Probe skipped due to missing tools
    - environment_limited: Environment/permission/timeouts constrained execution
    """
    categories: set[str] = set()

    for test in tests:
        status = test.get("status")
        name = test.get("name", "")
        reason = str(test.get("reason", "")).lower()
        error = str(test.get("error", "")).lower()
        data = test.get("data", {}) or {}

        if status in {"skip", "missing"}:
            if (
                "not found" in reason
                or "not available" in reason
                or "install" in reason
            ):
                categories.add("tooling_missing")
            else:
                categories.add("environment_limited")

        if status == "error":
            if "permission" in error or "timeout" in error:
                categories.add("environment_limited")
            elif "not found" in error or "install" in error:
                categories.add("tooling_missing")
            else:
                categories.add("hardware_risk")

        if name == "memory_test" and int(data.get("error_count", 0) or 0) > 0:
            categories.add("hardware_risk")

        if name == "thermal_stress" and data.get("thermal_severity") in {
            "high",
            "critical",
        }:
            categories.add("hardware_risk")

    return sorted(categories)


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
    policy_pack_payload: Optional[Dict[str, Any]] = None,
    plugin_manifest_verification: Optional[Dict[str, Any]] = None,
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
        "report_version": REPORT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "agent": {"name": "inspecta", "version": agent_version},
        "device": device,
        "mode": mode,
        "profile": profile,
        "summary": {
            "overall_score": 0,
            "grade": "unknown",
            "recommendation": "",
            "failure_classification": [],
            "confidence_score": 0,
            "anomalies": [],
            "explainability": {},
        },
        "scores": {},
        "tests": tests,
        "artifacts": artifacts,
        "evidence": {"manifest_sha256": None, "signed": False},
    }

    if native is not None:
        report["native"] = native

    if plugin_manifest_verification is not None:
        report.setdefault("evidence", {})[
            "plugin_manifest"
        ] = plugin_manifest_verification

    # Simple scoring heuristics based on tests
    storage_score = 50  # Default
    battery_score = scoring.score_battery({})
    memory_score = scoring.score_memory({})
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
        memory_tests = [t for t in tests if t.get("name") == "memory_test"]

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
                    "thermal_severity": stress_data.get("thermal_severity"),
                }
            )

        if cpu_thermal_data:
            cpu_score = scoring.score_cpu_thermal(cpu_thermal_data)

        if memory_tests and memory_tests[0].get("status") in {"ok", "error"}:
            memory_score = scoring.score_memory(memory_tests[0].get("data", {}))

    failure_classification = _classify_failures(tests)

    report["scores"] = {
        "storage": storage_score,
        "battery": battery_score,
        "memory": memory_score,
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
    report["summary"]["failure_classification"] = failure_classification

    if policy_pack_payload is not None:
        context = {
            "scores": report["scores"],
            "summary": report["summary"],
            "mode": mode,
            "profile": profile,
            "tests": tests,
        }
        policy_result = policy_pack.evaluate_policy_pack(policy_pack_payload, context)
        adjusted_score = max(0, min(100, overall + int(policy_result["score_delta"])))
        adjusted_grade = scoring.grade_from_score(adjusted_score)

        report["summary"]["overall_score"] = adjusted_score
        report["summary"]["grade"] = adjusted_grade

        base_recommendation = report["summary"].get("recommendation", "")
        if policy_result["status"] == "fail":
            report["summary"]["recommendation"] = (
                f"{base_recommendation}. Policy pack marked this "
                "device as non-compliant "
                f"for target profile '{policy_result['target_profile']}'."
            )
            if "policy_violation" not in report["summary"]["failure_classification"]:
                report["summary"]["failure_classification"].append("policy_violation")
        elif policy_result["status"] in {"warn", "recommend"}:
            report["summary"]["recommendation"] = (
                f"{base_recommendation}. Policy pack produced additional "
                f"{policy_result['status']} guidance."
            )

        report["summary"]["policy_pack"] = {
            "pack_id": policy_result["pack_id"],
            "display_name": policy_result["display_name"],
            "target_profile": policy_result["target_profile"],
            "status": policy_result["status"],
            "rules_evaluated": policy_result["rules_evaluated"],
            "rules_triggered": policy_result["rules_triggered"],
            "score_delta": policy_result["score_delta"],
            "triggered_rules": policy_result["triggered_rules"],
        }

    anomaly_result = anomaly.analyze_offline_anomalies(
        tests=tests,
        scores=report["scores"],
    )
    report["summary"]["confidence_score"] = anomaly_result["confidence_score"]
    report["summary"]["anomalies"] = anomaly_result["anomalies"]
    report["summary"]["explainability"] = anomaly_result["explainability"]

    return report
