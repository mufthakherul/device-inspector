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
    smart: Dict[str, Any],
    mode: str = "quick",
    profile: str = "default",
    smart_status: Optional[str] = None,
) -> Dict[str, Any]:
    """Compose a minimal report dict.

    The returned dictionary should validate against `schemas/report-schema-1.0.0.json`.
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
        "tests": [],
        "artifacts": artifacts,
        "evidence": {"manifest_sha256": None, "signed": False},
    }

    # include smart result as a test entry
    test_entry = {
        "name": "smartctl",
        "status": "ok" if smart else "warn",
        "data": smart,
    }
    if smart_status:
        test_entry["status_detail"] = smart_status
    report["tests"].append(test_entry)

    # simple scoring heuristics placeholder
    report["scores"] = {
        "storage": 80 if smart else 50,
        "battery": 80,
        "memory": 90,
        "cpu_thermal": 85,
    }
    # compute overall
    report["summary"]["overall_score"] = int(
        sum(report["scores"].values()) / len(report["scores"])
    )
    overall = report["summary"]["overall_score"]
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
