from __future__ import annotations

import json
from pathlib import Path

from agent.evidence import verify_evidence_manifest, write_evidence_manifest


def test_write_and_verify_evidence_manifest(tmp_path: Path):
    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()

    (artifacts / "agent.log").write_text("ok", encoding="utf-8")
    (out / "report.txt").write_text("report", encoding="utf-8")

    rel, sha = write_evidence_manifest(
        output_dir=out,
        relative_paths=["artifacts/agent.log", "report.txt"],
        agent_version="0.1.0",
    )

    assert Path(rel).as_posix() == "artifacts/manifest.json"
    assert len(sha) == 64

    manifest_path = out / rel
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["algorithm"] == "sha256"
    assert len(manifest["entries"]) == 2

    result = verify_evidence_manifest(out, rel)
    assert result["ok"] is True
    assert result["checked"] == 2
    assert result["exit_code"] == 0
    assert result["exit_reason"] == "verified"


def test_verify_manifest_detects_tampering(tmp_path: Path):
    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()

    target = artifacts / "agent.log"
    target.write_text("original", encoding="utf-8")

    rel, _ = write_evidence_manifest(
        output_dir=out,
        relative_paths=["artifacts/agent.log"],
        agent_version="0.1.0",
    )

    target.write_text("changed", encoding="utf-8")

    result = verify_evidence_manifest(out, rel)
    assert result["ok"] is False
    assert result["checked"] == 1
    assert result["mismatches"][0]["reason"] == "hash mismatch"
    assert result["exit_code"] == 1
    assert result["exit_reason"] == "integrity_mismatch"


def test_verify_manifest_missing_file_taxonomy(tmp_path: Path):
    out = tmp_path
    result = verify_evidence_manifest(out, "artifacts/manifest.json")

    assert result["ok"] is False
    assert result["exit_code"] == 2
    assert result["exit_reason"] == "manifest_not_found"
