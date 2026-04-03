"""Generate docs-site KPI snapshot JSON from test and coverage artifacts."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _read_coverage_percent(path: Path) -> float:
    if not path.exists():
        return 0.0
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    line_rate = float(root.attrib.get("line-rate", "0") or 0)
    return round(line_rate * 100, 2)


def _read_tests_passed(path: Path) -> int:
    if not path.exists():
        return 0

    root = ET.fromstring(path.read_text(encoding="utf-8"))
    # Pytest junit output may use testsuite root or testsuites wrapper.
    if root.tag == "testsuite":
        tests = int(root.attrib.get("tests", "0") or 0)
        failures = int(root.attrib.get("failures", "0") or 0)
        errors = int(root.attrib.get("errors", "0") or 0)
        skipped = int(root.attrib.get("skipped", "0") or 0)
        return max(0, tests - failures - errors - skipped)

    suites = root.findall("testsuite")
    passed = 0
    for suite in suites:
        tests = int(suite.attrib.get("tests", "0") or 0)
        failures = int(suite.attrib.get("failures", "0") or 0)
        errors = int(suite.attrib.get("errors", "0") or 0)
        skipped = int(suite.attrib.get("skipped", "0") or 0)
        passed += max(0, tests - failures - errors - skipped)
    return passed


def _read_report_summary(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    summary = payload.get("summary") if isinstance(payload, dict) else None
    if not isinstance(summary, dict):
        return None

    result: dict[str, int] = {}
    for key in ("probe_reliability", "probe_parity_index", "confidence_score"):
        value = summary.get(key)
        if isinstance(value, int):
            result[key] = value

    return result or None


def build_payload(
    coverage_percent: float,
    tests_passed: int,
    release_green_rate: int,
    bundle_verify_rate: int,
    probe_reliability: int | None = None,
    probe_parity_index: int | None = None,
    confidence_score: int | None = None,
) -> dict:
    metrics = {
        "tests_passed": tests_passed,
        "coverage_percent": coverage_percent,
        "release_green_rate": release_green_rate,
        "bundle_verify_rate": bundle_verify_rate,
    }

    if probe_reliability is not None:
        metrics["probe_reliability"] = probe_reliability
    if probe_parity_index is not None:
        metrics["probe_parity_index"] = probe_parity_index
    if confidence_score is not None:
        metrics["confidence_score"] = confidence_score

    return {
        "source": "kpi-snapshot/ci",
        "generated_at": _now_iso(),
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate docs-site KPI snapshot")
    parser.add_argument("--coverage-xml", default="coverage.xml")
    parser.add_argument("--junit-xml", default="test-output/junit.xml")
    parser.add_argument("--report-json", default="report.json")
    parser.add_argument("--release-green-rate", type=int, default=100)
    parser.add_argument("--bundle-verify-rate", type=int, default=100)
    parser.add_argument("--probe-reliability", type=int, default=None)
    parser.add_argument("--probe-parity-index", type=int, default=None)
    parser.add_argument("--confidence-score", type=int, default=None)
    parser.add_argument("--output", default="docs-site/data/kpi.json")
    args = parser.parse_args()

    coverage_percent = _read_coverage_percent(Path(args.coverage_xml))
    tests_passed = _read_tests_passed(Path(args.junit_xml))
    report_summary = _read_report_summary(Path(args.report_json))

    payload = build_payload(
        coverage_percent=coverage_percent,
        tests_passed=tests_passed,
        release_green_rate=args.release_green_rate,
        bundle_verify_rate=args.bundle_verify_rate,
        probe_reliability=(
            args.probe_reliability
            if args.probe_reliability is not None
            else (report_summary or {}).get("probe_reliability")
        ),
        probe_parity_index=(
            args.probe_parity_index
            if args.probe_parity_index is not None
            else (report_summary or {}).get("probe_parity_index")
        ),
        confidence_score=(
            args.confidence_score
            if args.confidence_score is not None
            else (report_summary or {}).get("confidence_score")
        ),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("[kpi-snapshot] generated")
    print(f"  tests_passed: {tests_passed}")
    print(f"  coverage_percent: {coverage_percent}")
    print(f"  output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
