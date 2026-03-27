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


def score_disk_performance(perf_info: Dict[str, Any]) -> int:
    """Score disk performance from read/write throughput metrics.

    Uses quick benchmark throughput in MB/s and maps to a deterministic band.
    """
    read_mbps = perf_info.get("read_mbps") if perf_info else None
    write_mbps = perf_info.get("write_mbps") if perf_info else None

    if read_mbps is None and write_mbps is None:
        return 70

    try:
        read_mbps = float(read_mbps or 0)
        write_mbps = float(write_mbps or 0)
    except Exception:
        return 70

    avg_mbps = (read_mbps + write_mbps) / 2
    if avg_mbps >= 400:
        return 95
    if avg_mbps >= 250:
        return 85
    if avg_mbps >= 120:
        return 70
    return 45


def score_cpu_thermal(thermal_info: Dict[str, Any]) -> int:
    """Score CPU category from benchmark and thermal signals.

    Considers both CPU benchmark performance and thermal stress results.
    Penalties applied for throttling or excessive temperatures.
    """
    # Start with benchmark-based score
    events_per_second = thermal_info.get("events_per_second") if thermal_info else None

    if events_per_second is None:
        base_score = 85
    else:
        try:
            eps = float(events_per_second)
            if eps >= 2000:
                base_score = 95
            elif eps >= 1200:
                base_score = 85
            elif eps >= 700:
                base_score = 70
            else:
                base_score = 50
        except Exception:
            base_score = 85

    # Apply thermal stress penalties if data available
    peak_temp = thermal_info.get("peak_temp")
    throttled = thermal_info.get("throttled")

    if peak_temp is not None or throttled is not None:
        # Thermal stress data available
        penalties = 0

        # Temperature-based penalties
        if peak_temp:
            if peak_temp >= 95:
                penalties += 30  # Critical temp
            elif peak_temp >= 85:
                penalties += 15  # High temp
            elif peak_temp >= 75:
                penalties += 5  # Moderate temp

        # Throttling penalties
        if throttled:
            penalties += 20  # Throttling detected

        # Apply penalties but don't go below 0
        final_score = max(0, base_score - penalties)
        return final_score

    # No thermal data, return base score
    return base_score


def score_gpu(gpu_info: Dict[str, Any]) -> int:
    """Score GPU health and performance.

    Placeholder: return 85 for now.
    """
    return 85


def score_network(network_info: Dict[str, Any]) -> int:
    """Score network connectivity and hardware.

    Placeholder: return 90 for now.
    """
    return 90


def score_security(security_info: Dict[str, Any]) -> int:
    """Score security posture (firmware, TPM, secure boot, etc).

    Placeholder: return 75 for now.
    """
    return 75


def compute_overall_score(
    scores: Dict[str, int], profile: str = "default"
) -> tuple[int, str]:
    """Compute overall score and grade from category scores.

    Args:
        scores: Dictionary of category scores (storage, battery, etc)
        profile: User profile (Office, Developer, Gamer, Server, default)

    Returns:
        Tuple of (overall_score, grade)
    """
    # Category weights based on profile
    weights = get_profile_weights(profile)

    # Compute weighted average
    total_weighted = 0
    total_weight = 0
    for category, weight in weights.items():
        if category in scores:
            total_weighted += scores[category] * weight
            total_weight += weight

    overall = int(total_weighted / total_weight) if total_weight > 0 else 50

    # Determine grade
    if overall >= 90:
        grade = "Excellent"
    elif overall >= 75:
        grade = "Good"
    elif overall >= 50:
        grade = "Fair"
    else:
        grade = "Poor"

    return overall, grade


def get_profile_weights(profile: str) -> Dict[str, float]:
    """Get category weights for a specific user profile.

    Args:
        profile: User profile (Office, Developer, Gamer, Server, default)

    Returns:
        Dictionary mapping category names to weights (0-1)
    """
    profiles = {
        "Office": {
            "storage": 0.20,
            "battery": 0.25,
            "memory": 0.15,
            "cpu_thermal": 0.15,
            "gpu": 0.05,
            "network": 0.10,
            "security": 0.10,
        },
        "Developer": {
            "storage": 0.25,
            "battery": 0.15,
            "memory": 0.20,
            "cpu_thermal": 0.20,
            "gpu": 0.05,
            "network": 0.10,
            "security": 0.05,
        },
        "Gamer": {
            "storage": 0.20,
            "battery": 0.05,
            "memory": 0.15,
            "cpu_thermal": 0.25,
            "gpu": 0.25,
            "network": 0.05,
            "security": 0.05,
        },
        "Server": {
            "storage": 0.30,
            "battery": 0.05,
            "memory": 0.25,
            "cpu_thermal": 0.20,
            "gpu": 0.00,
            "network": 0.15,
            "security": 0.05,
        },
        "default": {
            "storage": 0.22,
            "battery": 0.15,
            "memory": 0.12,
            "cpu_thermal": 0.15,
            "gpu": 0.10,
            "network": 0.08,
            "security": 0.18,
        },
    }

    return profiles.get(profile, profiles["default"])


def get_profile_recommendation(
    overall_score: int, grade: str, profile: str, scores: Dict[str, int]
) -> str:
    """Generate a recommendation based on profile and scores.

    Args:
        overall_score: Overall device score (0-100)
        grade: Overall grade (Excellent, Good, Fair, Poor)
        profile: User profile
        scores: Dictionary of category scores

    Returns:
        Recommendation string
    """
    if overall_score >= 90:
        return f"Excellent condition — ready for {profile} use"
    elif overall_score >= 75:
        return f"Good condition — suitable for {profile} use with minor issues"
    elif overall_score >= 50:
        # Identify weak areas
        weak_areas = [k for k, v in scores.items() if v < 60]
        if weak_areas:
            areas_str = ", ".join(weak_areas)
            return f"Fair condition for {profile} — consider repairs ({areas_str})"
        return f"Fair condition — may require attention for {profile} use"
    else:
        return f"Poor condition — not recommended for {profile} use without repairs"
