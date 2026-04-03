from __future__ import annotations

from pathlib import Path

from tools.release_signing import (
    build_signing_report,
    discover_signable_artifacts,
    sign_artifact,
)


def test_discover_signable_artifacts_filters_expected_files(tmp_path: Path):
    files = [
        "a.zip",
        "b.deb",
        "c.rpm",
        "d.AppImage",
        "e.whl",
        "f.tar.gz",
        "SHA256SUMS",
        "ignore.txt",
        "already.asc",
    ]
    for name in files:
        (tmp_path / name).write_text("x", encoding="utf-8")

    artifacts = discover_signable_artifacts(tmp_path)
    names = [p.name for p in artifacts]

    assert "a.zip" in names
    assert "d.AppImage" in names
    assert "f.tar.gz" in names
    assert "SHA256SUMS" in names
    assert "ignore.txt" not in names
    assert "already.asc" not in names


def test_sign_artifact_dry_run_creates_signature_file(tmp_path: Path):
    artifact = tmp_path / "pkg.zip"
    artifact.write_text("payload", encoding="utf-8")

    output_dir = tmp_path / "sigs"
    result = sign_artifact(
        artifact=artifact,
        output_dir=output_dir,
        gpg_passphrase="",
        dry_run=True,
    )

    assert result.status == "simulated"
    assert (output_dir / "pkg.zip.asc").exists()


def test_build_signing_report_counts_failures_and_successes(tmp_path: Path):
    artifact = tmp_path / "pkg.whl"
    artifact.write_text("payload", encoding="utf-8")

    output_dir = tmp_path / "sigs"
    result_ok = sign_artifact(
        artifact=artifact,
        output_dir=output_dir,
        gpg_passphrase="",
        dry_run=True,
    )

    report = build_signing_report([result_ok])
    assert report["total"] == 1
    assert report["signed_or_simulated"] == 1
    assert report["failed"] == 0
