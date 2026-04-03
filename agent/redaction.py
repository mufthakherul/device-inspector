# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Report redaction and retention helpers.

Implements Sprint 10 retention controls and evidence redaction presets.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _mask(value: Any, prefix: int = 2, suffix: int = 2) -> Any:
    if not isinstance(value, str):
        return value
    if len(value) <= prefix + suffix:
        return "*" * len(value)
    return f"{value[:prefix]}{'*' * (len(value) - prefix - suffix)}{value[-suffix:]}"


def apply_redaction(report: dict[str, Any], preset: str) -> dict[str, Any]:
    """Apply a redaction preset to a report dict.

    Presets:
    - none: no redaction
    - basic: mask identity fields
    - strict: basic + redact test payloads and host fingerprint
    """
    preset = (preset or "none").lower()
    if preset not in {"none", "basic", "strict"}:
        raise ValueError(f"Unsupported redaction preset: {preset}")

    if preset == "none":
        return report

    redacted = deepcopy(report)

    device = redacted.get("device", {})
    if isinstance(device, dict):
        for key in ("serial", "uuid", "sku", "family"):
            if key in device and device[key] is not None:
                device[key] = _mask(device[key])

    run_metadata = redacted.get("run_metadata", {})
    if isinstance(run_metadata, dict):
        if "os_fingerprint_sha256" in run_metadata:
            run_metadata["os_fingerprint_sha256"] = "redacted"

    if preset == "strict":
        tests = redacted.get("tests", [])
        if isinstance(tests, list):
            for test in tests:
                if not isinstance(test, dict):
                    continue
                if "data" in test:
                    test["data"] = {"redacted": True}
                if "error" in test and isinstance(test["error"], str):
                    test["error"] = "redacted"

    redacted.setdefault("evidence", {})
    redacted["evidence"]["redaction"] = {
        "preset": preset,
        "applied": True,
    }
    return redacted


def apply_retention_policy(report: dict[str, Any], retention_days: int | None) -> None:
    """Attach retention policy metadata to the report evidence section."""
    if retention_days is None:
        return

    report.setdefault("evidence", {})
    report["evidence"]["retention_policy"] = {
        "retention_days": retention_days,
        "auto_purge_recommended": True,
    }
