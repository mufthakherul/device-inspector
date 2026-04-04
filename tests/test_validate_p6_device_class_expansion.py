from __future__ import annotations

from pathlib import Path

from tools.validate_p6_device_class_expansion import validate_p6_assets


def test_validate_p6_assets_happy_path():
    errors = validate_p6_assets(
        profiles_dir=Path("profiles/device-class"),
        fireos_doc=Path("docs/FIRE_OS_FEASIBILITY_MVP.md"),
        matrix_doc=Path("docs/HARDWARE_CLASS_CERTIFICATION_MATRIX.md"),
    )

    assert errors == []


def test_validate_p6_assets_detects_missing_docs(tmp_path):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "laptop.json").write_text(
        '{"class_id":"laptop-desktop","profile_version":"1.0.0","support_level":"stable","recommended_mode":"full","validation_pack":"core"}',
        encoding="utf-8",
    )

    errors = validate_p6_assets(
        profiles_dir=profiles_dir,
        fireos_doc=tmp_path / "missing-fireos.md",
        matrix_doc=tmp_path / "missing-matrix.md",
    )

    assert any("missing documentation" in err for err in errors)
