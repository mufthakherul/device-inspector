from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REPORT_SCHEMA_VERSION = "1.0.0"
SUPPORTED_REPORT_MAJOR = 1


@dataclass(frozen=True)
class SchemaCompatibility:
    version: str
    major: int
    minor: int
    patch: int
    supported: bool


def _parse_semver(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid semantic version: {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def parse_report_version(version: str) -> SchemaCompatibility:
    major, minor, patch = _parse_semver(version)
    return SchemaCompatibility(
        version=version,
        major=major,
        minor=minor,
        patch=patch,
        supported=major == SUPPORTED_REPORT_MAJOR,
    )


def ensure_supported_report_version(version: str) -> None:
    compat = parse_report_version(version)
    if not compat.supported:
        raise ValueError(
            "Unsupported report schema major version "
            f"{version}. Supported major: {SUPPORTED_REPORT_MAJOR}."
        )


def migrate_legacy_report(report: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy report shapes for downstream formatters.

    Migration guards intentionally keep behavior permissive so old reports can
    still render via `inspecta report` while preserving original payload data.
    """
    normalized = dict(report)

    # Legacy shape: top-level `agent_version` instead of nested `agent` object.
    if "agent" not in normalized:
        normalized["agent"] = {
            "name": "inspecta",
            "version": str(normalized.get("agent_version", "unknown")),
        }

    normalized.setdefault("report_version", REPORT_SCHEMA_VERSION)
    normalized.setdefault("generated_at", "unknown")
    normalized.setdefault("device", {})
    normalized.setdefault("mode", "quick")
    normalized.setdefault("profile", "default")
    normalized.setdefault("scores", {})
    normalized.setdefault("tests", [])
    normalized.setdefault("artifacts", [])

    summary = normalized.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    summary.setdefault("overall_score", 0)
    summary.setdefault("grade", "unknown")
    summary.setdefault("recommendation", "N/A")
    summary.setdefault("failure_classification", [])
    normalized["summary"] = summary

    evidence = normalized.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
    evidence.setdefault("manifest_sha256", None)
    evidence.setdefault("signed", False)
    normalized["evidence"] = evidence

    return normalized
