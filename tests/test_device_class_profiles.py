from __future__ import annotations

from agent.device_class_profiles import (
    detect_device_class,
    get_device_class_assessment,
    load_device_class_profiles,
)


def test_load_device_class_profiles_contains_expected_classes():
    profiles = load_device_class_profiles()

    assert "laptop-desktop" in profiles
    assert "tablet-mobile" in profiles
    assert "arm-rpi-linux" in profiles
    assert "edge-mini-pc" in profiles
    assert "fireos-companion" in profiles


def test_detect_device_class_prefers_tablet_and_arm():
    assert detect_device_class({"model": "Galaxy Tab S8"}) == "tablet-mobile"
    assert detect_device_class({"arch": "aarch64"}) == "arm-rpi-linux"


def test_get_device_class_assessment_returns_profile_fields():
    assessment = get_device_class_assessment({"model": "Kindle Fire HD"})

    assert assessment["class_id"] == "fireos-companion"
    assert assessment["validation_pack"] == "fireos-companion-mvp"
