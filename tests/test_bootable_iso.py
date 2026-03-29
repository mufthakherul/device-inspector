from pathlib import Path

from tools.bootable_iso import build_bootable_iso, stage_iso_tree


def test_stage_iso_tree_writes_manifest_and_scripts(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    manifest = stage_iso_tree(
        staging_dir=staging, profile="ubuntu-minimal", forensic_mode=True
    )

    assert manifest["status"] == "build-ready"
    assert (staging / "opt" / "inspecta" / "run-full.sh").exists()
    assert (staging / "opt" / "inspecta" / "forensic-write-minimization.sh").exists()
    assert (staging / "opt" / "inspecta" / "iso-build-manifest.json").exists()


def test_build_bootable_iso_creates_iso_and_checksums(
    tmp_path: Path, monkeypatch
) -> None:
    output = tmp_path / "out"

    # Monkeypatch backend command execution to avoid requiring external ISO tools.
    def fake_build(staging_dir, output_iso, volume_id):
        output_iso.write_bytes(b"FAKE_ISO")
        return "fake-iso"

    monkeypatch.setattr("tools.bootable_iso._build_iso_image", fake_build)

    result = build_bootable_iso(output_dir=output, iso_name="test.iso")
    assert result.iso_path.exists()
    assert result.manifest_path.exists()
    assert result.checksums_path.exists()

    checksums = result.checksums_path.read_text(encoding="utf-8")
    assert "test.iso" in checksums
    assert "iso-build-manifest.json" in checksums
