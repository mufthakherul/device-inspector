from __future__ import annotations

import json

from click.testing import CliRunner

from agent.cli import cli


def _policy_pack_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "pack_id": "enterprise_policy",
        "display_name": "Enterprise Policy",
        "target_profile": "enterprise_it",
        "rules": [
            {
                "id": "LOW_SECURITY",
                "title": "Security score low",
                "severity": "warning",
                "condition": "scores.security < 80",
                "action": "warn",
                "message": "Security score below target",
            }
        ],
    }


def test_policy_export_command(tmp_path):
    source = tmp_path / "policy.json"
    target = tmp_path / "exports" / "policy.export.json"
    source.write_text(json.dumps(_policy_pack_payload()), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["policy-export", str(source), "--output", str(target)],
    )

    assert result.exit_code == 0
    assert target.exists()
    exported = json.loads(target.read_text(encoding="utf-8"))
    assert exported["pack_id"] == "enterprise_policy"


def test_policy_import_command(tmp_path):
    source = tmp_path / "policy.json"
    out_dir = tmp_path / "imported"
    source.write_text(json.dumps(_policy_pack_payload()), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["policy-import", str(source), "--output-dir", str(out_dir)],
    )

    assert result.exit_code == 0
    imported = out_dir / "enterprise_policy.json"
    assert imported.exists()


def test_policy_import_command_rejects_existing_without_force(tmp_path):
    source = tmp_path / "policy.json"
    out_dir = tmp_path / "imported"
    out_dir.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(_policy_pack_payload()), encoding="utf-8")
    (out_dir / "enterprise_policy.json").write_text("{}", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["policy-import", str(source), "--output-dir", str(out_dir)],
    )

    assert result.exit_code != 0
    assert "already exists" in result.output
