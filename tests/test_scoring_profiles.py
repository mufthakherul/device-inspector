# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for profile-based scoring and recommendations."""

from agent.scoring import (
    compute_overall_score,
    get_profile_recommendation,
    get_profile_weights,
    score_gpu,
    score_network,
    score_security,
)


def test_score_gpu():
    """Test GPU scoring function."""
    assert score_gpu({}) == 85


def test_score_network():
    """Test network scoring function."""
    assert score_network({}) == 90


def test_score_security():
    """Test security scoring function."""
    assert score_security({}) == 75


def test_get_profile_weights_default():
    """Test default profile weights."""
    weights = get_profile_weights("default")
    assert weights["storage"] == 0.22
    assert weights["battery"] == 0.15
    assert weights["memory"] == 0.12
    assert weights["cpu_thermal"] == 0.15
    assert weights["gpu"] == 0.10
    assert weights["network"] == 0.08
    assert weights["security"] == 0.18
    # Sum should be 1.0
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_get_profile_weights_office():
    """Test Office profile weights."""
    weights = get_profile_weights("Office")
    assert weights["battery"] == 0.25  # Higher battery weight for office
    assert weights["gpu"] == 0.05  # Lower GPU weight
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_get_profile_weights_developer():
    """Test Developer profile weights."""
    weights = get_profile_weights("Developer")
    assert weights["storage"] == 0.25
    assert weights["memory"] == 0.20  # Higher memory weight
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_get_profile_weights_gamer():
    """Test Gamer profile weights."""
    weights = get_profile_weights("Gamer")
    assert weights["gpu"] == 0.25  # High GPU weight
    assert weights["cpu_thermal"] == 0.25  # High thermal weight
    assert weights["battery"] == 0.05  # Low battery weight (plugged in)
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_get_profile_weights_server():
    """Test Server profile weights."""
    weights = get_profile_weights("Server")
    assert weights["storage"] == 0.30  # Highest storage weight
    assert weights["memory"] == 0.25  # High memory weight
    assert weights["gpu"] == 0.00  # No GPU needed
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_compute_overall_score_excellent():
    """Test overall score computation for excellent device."""
    scores = {
        "storage": 95,
        "battery": 95,
        "memory": 90,
        "cpu_thermal": 90,
        "gpu": 90,
        "network": 95,
        "security": 90,
    }
    overall, grade = compute_overall_score(scores, "default")
    assert overall >= 90
    assert grade == "Excellent"


def test_compute_overall_score_good():
    """Test overall score computation for good device."""
    scores = {
        "storage": 80,
        "battery": 75,
        "memory": 85,
        "cpu_thermal": 80,
        "gpu": 75,
        "network": 85,
        "security": 80,
    }
    overall, grade = compute_overall_score(scores, "default")
    assert 75 <= overall < 90
    assert grade == "Good"


def test_compute_overall_score_fair():
    """Test overall score computation for fair device."""
    scores = {
        "storage": 60,
        "battery": 55,
        "memory": 65,
        "cpu_thermal": 60,
        "gpu": 55,
        "network": 70,
        "security": 65,
    }
    overall, grade = compute_overall_score(scores, "default")
    assert 50 <= overall < 75
    assert grade == "Fair"


def test_compute_overall_score_poor():
    """Test overall score computation for poor device."""
    scores = {
        "storage": 30,
        "battery": 40,
        "memory": 35,
        "cpu_thermal": 30,
        "gpu": 40,
        "network": 45,
        "security": 35,
    }
    overall, grade = compute_overall_score(scores, "default")
    assert overall < 50
    assert grade == "Poor"


def test_compute_overall_score_profile_weighted():
    """Test that different profiles produce different scores."""
    scores = {
        "storage": 80,
        "battery": 50,  # Low battery
        "memory": 80,
        "cpu_thermal": 80,
        "gpu": 80,
        "network": 80,
        "security": 80,
    }
    # Office profile weights battery heavily, so should score lower
    office_score, _ = compute_overall_score(scores, "Office")
    # Gamer profile doesn't care about battery, so should score higher
    gamer_score, _ = compute_overall_score(scores, "Gamer")
    assert gamer_score > office_score


def test_get_profile_recommendation_excellent():
    """Test recommendation for excellent device."""
    rec = get_profile_recommendation(95, "Excellent", "Office", {})
    assert "Excellent" in rec
    assert "ready for Office use" in rec


def test_get_profile_recommendation_good():
    """Test recommendation for good device."""
    rec = get_profile_recommendation(80, "Good", "Developer", {})
    assert "Good" in rec
    assert "suitable for Developer use" in rec
    assert "minor issues" in rec


def test_get_profile_recommendation_fair():
    """Test recommendation for fair device."""
    scores = {"storage": 40, "battery": 50, "memory": 70}
    rec = get_profile_recommendation(55, "Fair", "Gamer", scores)
    assert "Fair" in rec
    assert "Gamer" in rec


def test_get_profile_recommendation_poor():
    """Test recommendation for poor device."""
    rec = get_profile_recommendation(30, "Poor", "Server", {})
    assert "Poor" in rec
    assert "not recommended" in rec
    assert "Server" in rec
