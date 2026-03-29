from __future__ import annotations

from pathlib import Path

from agent.evidence import verify_evidence_manifest, write_evidence_manifest


def test_tamper_simulation_multiple_files(tmp_path: Path):
    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()

    file_a = artifacts / "a.txt"
    file_b = artifacts / "b.txt"
    file_a.write_text("alpha", encoding="utf-8")
    file_b.write_text("beta", encoding="utf-8")

    rel, _ = write_evidence_manifest(
        output_dir=out,
        relative_paths=["artifacts/a.txt", "artifacts/b.txt"],
        agent_version="0.1.0",
    )

    # Simulate tamper + deletion
    file_a.write_text("alpha-modified", encoding="utf-8")
    file_b.unlink()

    result = verify_evidence_manifest(out, rel)

    assert result["ok"] is False
    assert result["exit_code"] == 1
    assert any(m["reason"] == "hash mismatch" for m in result["mismatches"])
    assert any(m["reason"] == "missing file" for m in result["mismatches"])
