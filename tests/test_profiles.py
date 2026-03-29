# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for full-mode runtime profiles.

Validates profile definitions, timeouts, configurations, and get_profile()
behavior across balanced, deep, and forensic profiles.
"""

from __future__ import annotations

import pytest

from agent.profiles import (
    BALANCED,
    DEEP,
    FORENSIC,
    get_profile,
    is_valid_profile,
    list_profiles,
)


class TestProfileDefinitions:
    """Test profile constant definitions."""

    def test_balanced_profile_configuration(self):
        """Balanced profile has expected timeout and settings."""
        assert BALANCED.name == "balanced"
        assert BALANCED.timeout_seconds == 600  # 10 minutes
        assert BALANCED.stress_duration_seconds == 120  # 2 minutes
        assert BALANCED.enable_memtest is True
        assert BALANCED.enable_thermal_cycles == 2
        assert BALANCED.retry_max_attempts == 2
        assert BALANCED.safe_stop_enabled is True

    def test_deep_profile_configuration(self):
        """Deep profile has expected timeout and settings."""
        assert DEEP.name == "deep"
        assert DEEP.timeout_seconds == 1800  # 30 minutes
        assert DEEP.stress_duration_seconds == 600  # 10 minutes
        assert DEEP.enable_memtest is True
        assert DEEP.enable_thermal_cycles == 5
        assert DEEP.retry_max_attempts == 3
        assert DEEP.safe_stop_enabled is True

    def test_forensic_profile_configuration(self):
        """Forensic profile has maximum timeout and settings."""
        assert FORENSIC.name == "forensic"
        assert FORENSIC.timeout_seconds == 3600  # 60 minutes
        assert FORENSIC.stress_duration_seconds == 1200  # 20 minutes
        assert FORENSIC.enable_memtest is True
        assert FORENSIC.enable_thermal_cycles == 10
        assert FORENSIC.retry_max_attempts == 5
        assert FORENSIC.safe_stop_enabled is False  # Forensic: never interrupt


class TestGetProfile:
    """Test get_profile() lookup function."""

    def test_get_balanced_profile(self):
        """get_profile('balanced') returns BALANCED."""
        profile = get_profile("balanced")
        assert profile.name == "balanced"
        assert profile.timeout_seconds == 600

    def test_get_deep_profile(self):
        """get_profile('deep') returns DEEP."""
        profile = get_profile("deep")
        assert profile.name == "deep"
        assert profile.timeout_seconds == 1800

    def test_get_forensic_profile(self):
        """get_profile('forensic') returns FORENSIC."""
        profile = get_profile("forensic")
        assert profile.name == "forensic"
        assert profile.timeout_seconds == 3600

    def test_get_profile_invalid(self):
        """get_profile() with invalid name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_profile("invalid_profile")
        assert "Unknown full-mode profile" in str(exc_info.value)
        assert "balanced, deep, forensic" in str(exc_info.value)

    def test_get_profile_case_sensitive(self):
        """get_profile() is case-sensitive."""
        with pytest.raises(ValueError):
            get_profile("BALANCED")
        with pytest.raises(ValueError):
            get_profile("Balanced")


class TestIsValidProfile:
    """Test is_valid_profile() validation function."""

    def test_valid_profiles(self):
        """is_valid_profile() returns True for valid profile names."""
        assert is_valid_profile("balanced") is True
        assert is_valid_profile("deep") is True
        assert is_valid_profile("forensic") is True

    def test_invalid_profiles(self):
        """is_valid_profile() returns False for invalid profile names."""
        assert is_valid_profile("invalid") is False
        assert is_valid_profile("quick") is False
        assert is_valid_profile("") is False
        assert is_valid_profile("BALANCED") is False


class TestListProfiles:
    """Test list_profiles() enumeration function."""

    def test_list_profiles_returns_all(self):
        """list_profiles() returns all three profiles."""
        profiles = list_profiles()
        assert len(profiles) == 3
        names = {p["name"] for p in profiles}
        assert names == {"balanced", "deep", "forensic"}

    def test_list_profiles_structure(self):
        """list_profiles() returns correct metadata structure."""
        profiles = list_profiles()
        for profile in profiles:
            assert "name" in profile
            assert "description" in profile
            assert "timeout_minutes" in profile
            assert "stress_duration_seconds" in profile
            assert "enable_memtest" in profile
            assert "thermal_cycles" in profile

    def test_list_profiles_timeouts_in_minutes(self):
        """list_profiles() returns timeouts converted to minutes."""
        profiles = list_profiles()
        timeout_map = {p["name"]: p["timeout_minutes"] for p in profiles}
        assert timeout_map["balanced"] == 10
        assert timeout_map["deep"] == 30
        assert timeout_map["forensic"] == 60


class TestProfileProgression:
    """Test that profiles progress from balanced -> deep -> forensic."""

    def test_timeout_progression(self):
        """Timeouts increase: balanced < deep < forensic."""
        assert BALANCED.timeout_seconds < DEEP.timeout_seconds
        assert DEEP.timeout_seconds < FORENSIC.timeout_seconds

    def test_stress_duration_progression(self):
        """Stress durations increase: balanced < deep < forensic."""
        assert BALANCED.stress_duration_seconds < DEEP.stress_duration_seconds
        assert DEEP.stress_duration_seconds < FORENSIC.stress_duration_seconds

    def test_thermal_cycles_progression(self):
        """Thermal cycles increase: balanced < deep < forensic."""
        assert (
            BALANCED.enable_thermal_cycles
            < DEEP.enable_thermal_cycles
            < FORENSIC.enable_thermal_cycles
        )

    def test_retry_attempts_progression(self):
        """Retry attempts increase: balanced < deep < forensic."""
        assert BALANCED.retry_max_attempts < DEEP.retry_max_attempts
        assert DEEP.retry_max_attempts < FORENSIC.retry_max_attempts
