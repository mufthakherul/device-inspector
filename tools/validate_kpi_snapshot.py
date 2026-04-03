"""Validate KPI snapshot payload quality gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_METRICS = {
    "tests_passed": int,
    "coverage_percent": (int, float),
    "release_green_rate": int,
    "bundle_verify_rate": int,
}


def validate_kpi_payload(
    payload: dict, min_coverage: float, min_tests: int
) -> list[str]:
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    if payload.get("source") != "kpi-snapshot/ci":
        errors.append("source must be 'kpi-snapshot/ci'")

    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        return errors + ["metrics must be an object"]

    for key, expected_type in REQUIRED_METRICS.items():
        value = metrics.get(key)
        if not isinstance(value, expected_type):
            errors.append(f"metrics.{key} missing or invalid type")

    coverage = metrics.get("coverage_percent")
    if isinstance(coverage, (int, float)) and coverage < min_coverage:
        errors.append(
            f"coverage_percent {coverage} is below minimum threshold {min_coverage}"
        )

    tests = metrics.get("tests_passed")
    if isinstance(tests, int) and tests < min_tests:
        errors.append(f"tests_passed {tests} is below minimum threshold {min_tests}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate docs-site KPI snapshot")
    parser.add_argument("--kpi-json", default="docs-site/data/kpi.json")
    parser.add_argument("--min-coverage", type=float, default=35.0)
    parser.add_argument("--min-tests", type=int, default=1)
    args = parser.parse_args()

    path = Path(args.kpi_json)
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_kpi_payload(payload, args.min_coverage, args.min_tests)

    print("[kpi-quality-gate] validation")
    print(f"  kpi_json: {path}")
    print(f"  min_coverage: {args.min_coverage}")
    print(f"  min_tests: {args.min_tests}")

    if errors:
        print("  status: failed")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("  status: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
