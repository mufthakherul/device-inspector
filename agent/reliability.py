# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Probe reliability scoring helpers.

This supports Sprint 3 roadmap work for degraded probe-set scoring and a
simple parity index derived from test execution health.
"""

from __future__ import annotations

from typing import Any


def compute_probe_reliability(tests: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute a deterministic reliability score from probe outcomes."""
    if not tests:
        return {
            "reliability_score": 100,
            "parity_index": 100,
            "executed": 0,
            "passed": 0,
            "warned": 0,
            "skipped": 0,
            "failed": 0,
            "status": "no_probes",
        }

    executed = 0
    passed = 0
    warned = 0
    skipped = 0
    failed = 0

    for test in tests:
        status = str(test.get("status", "")).lower()
        if status in {"ok", "missing", "skip", "error"}:
            executed += 1
        if status == "ok":
            passed += 1
        elif status in {"missing", "skip"}:
            skipped += 1
        elif status == "error":
            failed += 1
        else:
            warned += 1

    reliability_score = 100
    reliability_score -= failed * 18
    reliability_score -= skipped * 7
    reliability_score -= warned * 3
    reliability_score = max(0, reliability_score)

    parity_index = 100
    parity_index -= skipped * 10
    parity_index -= failed * 15
    parity_index -= warned * 4
    parity_index = max(0, parity_index)

    if failed > 0:
        status = "degraded"
    elif skipped > 0 or warned > 0:
        status = "partial"
    else:
        status = "healthy"

    return {
        "reliability_score": reliability_score,
        "parity_index": parity_index,
        "executed": executed,
        "passed": passed,
        "warned": warned,
        "skipped": skipped,
        "failed": failed,
        "status": status,
    }
