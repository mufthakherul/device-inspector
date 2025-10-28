# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Report composition utilities.

Compose a canonical report.json following the project REPORT_SCHEMA.md.
The scaffold produces minimal fields sufficient for schema validation and
testing.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def compose_report(
    agent_version: str,
    device: Dict[str, Any],
    artifacts: List[str],
    tests: List[Dict[str, Any]],
    mode: str = "quick",
    profile: str = "default",
    smart_status: Optional[str] = None,
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

    # Simple scoring heuristics based on tests
    storage_score = 50  # Default
    if tests:
        # Check for SMART test results
        smart_tests = [t for t in tests if t.get("name", "").startswith("smartctl")]
        if smart_tests:
            # If we have successful SMART results, score higher
            ok_tests = [t for t in smart_tests if t.get("status") == "ok"]
            if ok_tests:
                storage_score = 80
                # Check for warning signs in SMART data
                for test in ok_tests:
                    data = test.get("data", {})
                    attrs = data.get("attributes", {})
                    # Check for reallocated sectors
                    if "Reallocated_Sector_Ct" in attrs:
                        if attrs["Reallocated_Sector_Ct"] > 10:
                            storage_score = 40  # Failing drive
                        elif attrs["Reallocated_Sector_Ct"] > 0:
                            storage_score = 60  # Warning

    report["scores"] = {
        "storage": storage_score,
        "battery": 80,
        "memory": 90,
        "cpu_thermal": 85,
    }

    # Compute overall score
    report["summary"]["overall_score"] = int(
        sum(report["scores"].values()) / len(report["scores"])
    )
    overall = report["summary"]["overall_score"]

    # Determine grade
    if overall >= 90:
        grade = "Excellent"
    elif overall >= 75:
        grade = "Good"
    elif overall >= 50:
        grade = "Fair"
    else:
        grade = "Poor"

    report["summary"]["grade"] = grade
    report["summary"]["recommendation"] = "Profile: %s" % profile

    return report
