from __future__ import annotations

import pytest

from agent.schema_compat import (
    REPORT_SCHEMA_VERSION,
    ensure_supported_report_version,
    migrate_legacy_report,
    parse_report_version,
)


def test_parse_report_version_supports_major_v1():
    compat = parse_report_version("1.2.3")
    assert compat.major == 1
    assert compat.minor == 2
    assert compat.patch == 3
    assert compat.supported is True


def test_ensure_supported_report_version_rejects_other_major():
    with pytest.raises(ValueError):
        ensure_supported_report_version("2.0.0")


def test_migrate_legacy_report_adds_guarded_defaults():
    legacy = {
        "agent_version": "0.0.9",
        "summary": {"overall_score": 42},
    }

    migrated = migrate_legacy_report(legacy)

    assert migrated["report_version"] == REPORT_SCHEMA_VERSION
    assert migrated["agent"]["version"] == "0.0.9"
    assert migrated["summary"]["grade"] == "unknown"
    assert migrated["summary"]["failure_classification"] == []
    assert migrated["tests"] == []
    assert migrated["artifacts"] == []
    assert migrated["evidence"]["signed"] is False
