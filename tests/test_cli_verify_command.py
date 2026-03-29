from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from agent.cli import cli
from agent.evidence import write_evidence_manifest


def test_verify_command_returns_taxonomy_output(tmp_path: Path):
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
        ["verify", str(out), "--manifest", rel, "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["exit_code"] == 0
    assert payload["exit_reason"] == "verified"


def test_verify_command_manifest_missing_exit_code(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["verify", str(tmp_path), "--manifest", "artifacts/missing.json", "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["exit_reason"] == "manifest_not_found"
