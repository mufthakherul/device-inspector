# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Deterministic scoring utilities for quick-mode.

Provides simple, auditable heuristics to convert parsed metrics into
0-100 integer subscores. These are intentionally small so unit tests can
assert exact outputs.
"""
from __future__ import annotations

from typing import Any, Dict


def score_storage(smart_parsed: Dict[str, Any]) -> int:
    """Score storage health based on parsed SMART attributes.

    Heuristics:
    - If `Current_Pending_Sector` or `Reallocated_Sector_Ct` > 0 -> score 30
    - If NVMe percentage_used exists and >= 70 -> score 40
    - Else return 90 when attributes present, 50 if missing
    """
    attrs = smart_parsed.get("attributes", {}) if smart_parsed else {}
    # check common keys
    if not attrs and smart_parsed.get("nvme_percentage_used") is None:
        return 50
    # simple checks
    try:
        pending = int(attrs.get("Current_Pending_Sector", 0) or 0)
        reallo = int(attrs.get("Reallocated_Sector_Ct", 0) or 0)
    except Exception:
        pending = 0
        reallo = 0
    if pending > 0 or reallo > 0:
        return 30
    nvme_pct = smart_parsed.get("nvme_percentage_used")
    if nvme_pct is not None:
        try:
            pct = int(nvme_pct)
            if pct >= 70:
                return 40
        except Exception:
            pass
    return 90


def score_battery(battery_info: Dict[str, Any]) -> int:
    """Score battery health from battery_info.

    Placeholder: return 80 for now unless explicit health_pct provided.
    """
    pct = battery_info.get("health_pct") if battery_info else None
    if pct is None:
        return 80
    try:
        pct = int(pct)
        if pct >= 90:
            return 95
        if pct >= 70:
            return 80
        if pct >= 50:
            return 60
        return 30
    except Exception:
        return 80


def score_memory(mem_info: Dict[str, Any]) -> int:
    """Score memory stability. Placeholder: return 90 unless errors reported."""
    if mem_info.get("errors"):
        return 20
    return 90


def score_cpu_thermal(thermal_info: Dict[str, Any]) -> int:
    """Score CPU thermal behavior from sampled temps.

    Placeholder: return 85 for now.
    """
    return 85
