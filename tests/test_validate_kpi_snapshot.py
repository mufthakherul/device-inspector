from __future__ import annotations

from tools.validate_kpi_snapshot import validate_kpi_payload


def test_validate_kpi_payload_passes_with_valid_input() -> None:
    payload = {
        "source": "kpi-snapshot/ci",
        "metrics": {
            "tests_passed": 247,
            "coverage_percent": 73.33,
            "release_green_rate": 100,
            "bundle_verify_rate": 100,
        },
    }

    errors = validate_kpi_payload(payload, min_coverage=35.0, min_tests=1)
    assert errors == []


def test_validate_kpi_payload_fails_below_thresholds() -> None:
    payload = {
        "source": "kpi-snapshot/ci",
        "metrics": {
            "tests_passed": 0,
            "coverage_percent": 10.0,
            "release_green_rate": 100,
            "bundle_verify_rate": 100,
        },
    }

    errors = validate_kpi_payload(payload, min_coverage=35.0, min_tests=1)
    assert any("coverage_percent" in err for err in errors)
    assert any("tests_passed" in err for err in errors)
