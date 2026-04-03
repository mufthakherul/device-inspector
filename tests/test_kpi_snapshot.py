from __future__ import annotations

from pathlib import Path

from tools.generate_kpi_snapshot import (
    _read_coverage_percent,
    _read_report_summary,
    _read_tests_passed,
    build_payload,
)


def test_build_payload_contains_expected_metric_fields() -> None:
    payload = build_payload(
        coverage_percent=73.22,
        tests_passed=212,
        release_green_rate=100,
        bundle_verify_rate=98,
        probe_reliability=91,
        probe_parity_index=88,
        confidence_score=84,
    )

    assert payload["source"] == "kpi-snapshot/ci"
    assert payload["metrics"]["coverage_percent"] == 73.22
    assert payload["metrics"]["tests_passed"] == 212
    assert payload["metrics"]["release_green_rate"] == 100
    assert payload["metrics"]["bundle_verify_rate"] == 98
    assert payload["metrics"]["probe_reliability"] == 91
    assert payload["metrics"]["probe_parity_index"] == 88
    assert payload["metrics"]["confidence_score"] == 84


def test_read_coverage_percent_from_xml(tmp_path: Path) -> None:
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        '<coverage line-rate="0.8125"></coverage>',
        encoding="utf-8",
    )

    assert _read_coverage_percent(coverage_xml) == 81.25


def test_read_tests_passed_from_junit_suite(tmp_path: Path) -> None:
    junit_xml = tmp_path / "junit.xml"
    junit_xml.write_text(
        '<testsuite tests="10" failures="1" errors="1" skipped="2"></testsuite>',
        encoding="utf-8",
    )

    assert _read_tests_passed(junit_xml) == 6


def test_read_report_summary_from_report_json(tmp_path: Path) -> None:
    report_json = tmp_path / "report.json"
    report_json.write_text(
        """
        {
          "summary": {
            "probe_reliability": 93,
            "probe_parity_index": 89,
            "confidence_score": 82
          }
        }
        """,
        encoding="utf-8",
    )

    summary = _read_report_summary(report_json)

    assert summary == {
        "probe_reliability": 93,
        "probe_parity_index": 89,
        "confidence_score": 82,
    }
