# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Validate a report.json against a provided JSON Schema.

Usage: python scripts/validate_report.py <report.json> <schema.json>
Exits with code 0 on success, non-zero on validation error.
"""
from __future__ import annotations

import json
import sys

from jsonschema import Draft7Validator


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: validate_report.py <report.json> <schema.json>")
        return 2
    report_path = argv[1]
    schema_path = argv[2]
    with open(report_path, "r", encoding="utf-8") as fh:
        report = json.load(fh)
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(report), key=lambda e: e.path)
    if errors:
        for err in errors:
            print(f"Validation error: {err.message} at {list(err.path)}")
        return 3
    print("OK: report validates against schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
