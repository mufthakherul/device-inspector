# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Full-mode runtime profiles for inspecta diagnostics.

Defines execution profiles for full-mode runs with different depths, timeouts,
and stress test configurations:
- balanced: Default full-mode experience with moderate stress testing
- deep: Extended testing with higher stress duration and thermal cycling
- forensic: Maximum duration forensic analysis with all probes enabled
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RuntimeProfile:
    """Configuration for full-mode execution."""

    name: str
    description: str
    timeout_seconds: int
    stress_duration_seconds: int
    enable_memtest: bool
    enable_thermal_cycles: int  # number of thermal cycles (0 = none)
    enable_smart_timeline: bool
    retry_max_attempts: int
    safe_stop_enabled: bool
    skip_tests_on_error: list[str]


# ============================================================================
# Profile Definitions
# ============================================================================

BALANCED: RuntimeProfile = RuntimeProfile(
    name="balanced",
    description=(
        "Default full-mode profile. Runs moderate stress tests with safe timeout. "
        "Suitable for most device diagnostics workflows."
    ),
    timeout_seconds=600,  # 10 minutes
    stress_duration_seconds=120,  # 2 minutes CPU/IO stress
    enable_memtest=True,
    enable_thermal_cycles=2,  # 2 thermal cycle measurements
    enable_smart_timeline=True,
    retry_max_attempts=2,
    safe_stop_enabled=True,
    skip_tests_on_error=["thermal_stress"],  # Allow continued test if thermal fails
)

DEEP: RuntimeProfile = RuntimeProfile(
    name="deep",
    description=(
        "Extended full-mode profile. Runs longer stress tests and extended "
        "diagnostics. Recommended for thorough device health assessment."
    ),
    timeout_seconds=1800,  # 30 minutes
    stress_duration_seconds=600,  # 10 minutes CPU/IO stress
    enable_memtest=True,
    enable_thermal_cycles=5,  # 5 thermal cycle measurements
    enable_smart_timeline=True,
    retry_max_attempts=3,
    safe_stop_enabled=True,
    skip_tests_on_error=[],  # Do not skip tests; fail hard on errors
)

FORENSIC: RuntimeProfile = RuntimeProfile(
    name="forensic",
    description=(
        "Maximum-duration forensic analysis profile. "
        "Comprehensive suite with all probes enabled and extended measurements. "
        "Use for critical devices or litigation scenarios."
    ),
    timeout_seconds=3600,  # 60 minutes
    stress_duration_seconds=1200,  # 20 minutes CPU/IO stress
    enable_memtest=True,
    enable_thermal_cycles=10,  # 10 thermal cycle measurements
    enable_smart_timeline=True,
    retry_max_attempts=5,
    safe_stop_enabled=False,  # Forensic mode: never interrupt; wait for full result
    skip_tests_on_error=[],
)

# ============================================================================
# Profile Registry
# ============================================================================

PROFILES: dict[str, RuntimeProfile] = {
    "balanced": BALANCED,
    "deep": DEEP,
    "forensic": FORENSIC,
}


def get_profile(profile_name: str) -> RuntimeProfile:
    """Retrieve a profile by name.

    Args:
        profile_name: Profile name (balanced, deep, forensic)

    Returns:
        RuntimeProfile instance

    Raises:
        ValueError: If profile name is not recognized
    """
    if profile_name not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise ValueError(
            f"Unknown full-mode profile '{profile_name}'. Available: {available}"
        )
    return PROFILES[profile_name]


def is_valid_profile(profile_name: str) -> bool:
    """Check if profile name is valid."""
    return profile_name in PROFILES


def list_profiles() -> list[dict[str, Any]]:
    """List all available profiles with metadata.

    Returns:
        List of profile dictionaries with name, description, and settings
    """
    return [
        {
            "name": profile.name,
            "description": profile.description,
            "timeout_minutes": profile.timeout_seconds // 60,
            "stress_duration_seconds": profile.stress_duration_seconds,
            "enable_memtest": profile.enable_memtest,
            "thermal_cycles": profile.enable_thermal_cycles,
        }
        for profile in PROFILES.values()
    ]


def get_profile_help_text() -> str:
    """Generate help text for full-mode profiles.

    Returns:
        Formatted help text describing all profiles
    """
    lines = [
        "Full-mode runtime profiles (use with --mode full):",
        "",
    ]
    for profile in PROFILES.values():
        timeout_min = profile.timeout_seconds // 60
        lines.append(f"  {profile.name:15} ({timeout_min}min) — {profile.description}")
    return "\n".join(lines)
