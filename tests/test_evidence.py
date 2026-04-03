from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.evidence import (
    audit_evidence_bundle,
    build_evidence_manifest,
    verify_evidence_manifest,
    write_evidence_manifest,
)


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


def test_build_manifest_is_deterministic_with_fixed_timestamp(tmp_path: Path):
    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()
    (artifacts / "b.txt").write_text("beta", encoding="utf-8")
    (artifacts / "a.txt").write_text("alpha", encoding="utf-8")

    fixed_generated_at = "2026-03-30T00:00:00+00:00"

    manifest_a, sha_a = build_evidence_manifest(
        base_dir=out,
        relative_paths=["artifacts/b.txt", "artifacts/a.txt", "artifacts/b.txt"],
        agent_version="0.1.0",
        generated_at=fixed_generated_at,
    )
    manifest_b, sha_b = build_evidence_manifest(
        base_dir=out,
        relative_paths=["artifacts/a.txt", "artifacts/b.txt"],
        agent_version="0.1.0",
        generated_at=fixed_generated_at,
    )

    assert sha_a == sha_b
    assert manifest_a == manifest_b
    assert [e["path"] for e in manifest_a["entries"]] == [
        "artifacts/a.txt",
        "artifacts/b.txt",
    ]


def test_audit_evidence_bundle_reports_reproducible_for_valid_bundle(tmp_path: Path):
    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()
    (artifacts / "agent.log").write_text("ok", encoding="utf-8")

    rel, _ = write_evidence_manifest(
        output_dir=out,
        relative_paths=["artifacts/agent.log"],
        agent_version="0.1.0",
    )

    result = audit_evidence_bundle(out, rel)
    assert result["ok"] is True
    assert result["integrity_ok"] is True
    assert result["deterministic_entries"] is True
    assert result["entry_metadata_complete"] is True
    assert result["reindexed_entries_match"] is True
    assert result["exit_code"] == 0
    assert result["exit_reason"] == "reproducible"


def test_verify_manifest_accepts_legacy_hash_and_dot_slash_path(tmp_path: Path):
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

    manifest_path = out / rel
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["entries"][0]
    entry["path"] = f"./{entry['path']}"
    entry["hash"] = entry.pop("sha256")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    result = verify_evidence_manifest(out, rel)
    assert result["ok"] is True
    assert result["exit_reason"] == "verified"


def test_signed_manifest_includes_attestation_metadata(tmp_path: Path):
    cryptography = pytest.importorskip("cryptography")
    _ = cryptography
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    out = tmp_path
    artifacts = out / "artifacts"
    artifacts.mkdir()

    (artifacts / "agent.log").write_text("ok", encoding="utf-8")

    private_key = Ed25519PrivateKey.generate()
    private_key_path = out / "attestor.pem"
    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    rel, sha = write_evidence_manifest(
        output_dir=out,
        relative_paths=["artifacts/agent.log"],
        agent_version="0.1.0",
        sign_key_path=private_key_path,
    )

    manifest_path = out / rel
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(sha) == 64
    assert manifest["signature"]["detached"] is True
    assert manifest["attestation"]["signature_model"] == "detached-ed25519"
    assert len(manifest["attestation"]["canonical_hash_sha256"]) == 64
    assert len(manifest["attestation"]["signer_id"]) == 64
