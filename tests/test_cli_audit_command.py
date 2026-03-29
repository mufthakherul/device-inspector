from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from agent.cli import cli
from agent.evidence import write_evidence_manifest


def test_audit_command_returns_reproducible_json_for_valid_bundle(tmp_path: Path):
    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()

    target = artifacts / "agent.log"
    target.write_text("ok", encoding="utf-8")

    rel, _ = write_evidence_manifest(
        output_dir=out,
        relative_paths=["artifacts/agent.log"],
        agent_version="0.1.0",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["audit", str(out), "--manifest", rel, "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["integrity_ok"] is True
    assert payload["deterministic_entries"] is True
    assert payload["reindexed_entries_match"] is True
    assert payload["exit_reason"] == "reproducible"


def test_audit_command_detects_tampered_bundle(tmp_path: Path):
    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()

    target = artifacts / "agent.log"
    target.write_text("ok", encoding="utf-8")

    rel, _ = write_evidence_manifest(
        output_dir=out,
        relative_paths=["artifacts/agent.log"],
        agent_version="0.1.0",
    )

    target.write_text("tampered", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["audit", str(out), "--manifest", rel, "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["integrity_ok"] is False
    assert payload["exit_reason"] == "reproducibility_check_failed"
