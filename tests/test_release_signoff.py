from __future__ import annotations

import pytest

from tools.validate_release_signoff import classify_channel, validate_signoff_payload


@pytest.mark.parametrize(
    ("tag", "channel"),
    [
        ("v1.0.0", "stable"),
        ("v1.0.0-alpha.1", "alpha"),
        ("v1.0.0-beta.2", "beta"),
    ],
)
def test_classify_channel(tag: str, channel: str):
    assert classify_channel(tag) == channel


def test_validate_signoff_payload_passes_for_stable_with_two_approvals():
    payload = {
        "approved_by": ["release-manager", "security-lead"],
        "checks": {
            "release_channel_gates": True,
            "build_release": True,
            "sbom_security": True,
            "distribution_manifest": True,
        },
        "risk_acknowledgement": "No blocking release risks.",
    }

    errors = validate_signoff_payload("v1.2.3", payload)
    assert errors == []


def test_validate_signoff_payload_fails_when_checks_missing():
    payload = {
        "approved_by": ["release-manager"],
        "checks": {
            "release_channel_gates": True,
            "build_release": False,
            "sbom_security": True,
        },
        "risk_acknowledgement": "pending",
    }

    errors = validate_signoff_payload("v1.2.3", payload)
    assert any("requires at least" in err for err in errors)
    assert any("checks.build_release" in err for err in errors)
    assert any("checks.distribution_manifest" in err for err in errors)
