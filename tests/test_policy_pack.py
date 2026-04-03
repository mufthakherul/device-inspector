from __future__ import annotations

import json

from agent.policy_pack import evaluate_policy_pack, load_policy_pack
from agent.report import compose_report


def _sample_policy_pack() -> dict:
    return {
        "schema_version": "1.0.0",
        "pack_id": "enterprise-baseline",
        "display_name": "Enterprise Baseline",
        "target_profile": "enterprise_it",
        "rules": [
            {
                "id": "LOW_STORAGE",
                "title": "Storage score must be >= 60",
                "severity": "critical",
                "condition": "scores.storage < 60",
                "action": "fail",
                "message": "Storage health is below enterprise threshold",
            },
            {
                "id": "LOW_SECURITY",
                "title": "Security should be reviewed",
                "severity": "warning",
                "condition": "scores.security < 80",
                "action": "warn",
                "message": "Security posture needs review",
            },
        ],
    }


def test_load_policy_pack_schema_validation(tmp_path):
    policy_path = tmp_path / "policy-pack.json"
    policy_path.write_text(
        json.dumps(_sample_policy_pack(), indent=2), encoding="utf-8"
    )

    loaded = load_policy_pack(policy_path)
    assert loaded["pack_id"] == "enterprise-baseline"


def test_evaluate_policy_pack_matches_rules_and_penalty():
    policy = _sample_policy_pack()
    result = evaluate_policy_pack(
        policy,
        context={
            "scores": {"storage": 40, "security": 70},
            "summary": {},
            "tests": [],
            "mode": "quick",
            "profile": "default",
        },
    )

    assert result["rules_triggered"] == 2
    assert result["status"] == "fail"
    assert result["score_delta"] < 0
    assert {rule["id"] for rule in result["triggered_rules"]} == {
        "LOW_STORAGE",
        "LOW_SECURITY",
    }


def test_compose_report_applies_policy_pack_adjustment():
    tests = [
        {
            "name": "smartctl_sda",
            "status": "ok",
            "data": {
                "attributes": {
                    "Current_Pending_Sector": 3,
                    "Reallocated_Sector_Ct": 0,
                }
            },
        }
    ]

    report = compose_report(
        agent_version="0.1.0",
        device={"vendor": "Test", "model": "Device"},
        artifacts=[],
        tests=tests,
        mode="quick",
        profile="default",
        policy_pack_payload=_sample_policy_pack(),
    )

    policy_summary = report["summary"]["policy_pack"]
    assert policy_summary["status"] == "fail"
    assert policy_summary["rules_triggered"] >= 1
    assert "policy_violation" in report["summary"]["failure_classification"]
