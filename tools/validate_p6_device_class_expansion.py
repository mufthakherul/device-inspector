"""Validate P6 multi-device expansion assets and profile packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_CLASS_IDS = {
    "laptop-desktop",
    "tablet-mobile",
    "arm-rpi-linux",
    "edge-mini-pc",
    "fireos-companion",
}


def _load_profiles(profiles_dir: Path) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for file in sorted(profiles_dir.glob("*.json")):
        payload = json.loads(file.read_text(encoding="utf-8"))
        class_id = payload.get("class_id")
        if isinstance(class_id, str):
            profiles[class_id] = payload
    return profiles


def validate_p6_assets(
    profiles_dir: Path,
    fireos_doc: Path,
    matrix_doc: Path,
) -> list[str]:
    errors: list[str] = []

    if not profiles_dir.exists():
        return [f"profiles directory missing: {profiles_dir}"]

    profiles = _load_profiles(profiles_dir)
    missing_ids = sorted(REQUIRED_CLASS_IDS - set(profiles.keys()))
    if missing_ids:
        errors.append(f"missing device class profiles: {missing_ids}")

    for class_id in REQUIRED_CLASS_IDS.intersection(profiles.keys()):
        payload = profiles[class_id]
        for key in (
            "profile_version",
            "support_level",
            "recommended_mode",
            "validation_pack",
        ):
            if key not in payload:
                errors.append(f"profile '{class_id}' missing key: {key}")

    for doc in (fireos_doc, matrix_doc):
        if not doc.exists():
            errors.append(f"missing documentation: {doc}")

    if fireos_doc.exists():
        text = fireos_doc.read_text(encoding="utf-8").lower()
        for token in ("fire os", "mvp", "offline"):
            if token not in text:
                errors.append(f"fire os doc missing token: {token}")

    if matrix_doc.exists():
        text = matrix_doc.read_text(encoding="utf-8").lower()
        for token in ("tablet", "arm", "edge", "fire os"):
            if token not in text:
                errors.append(f"certification matrix missing token: {token}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate P6 expansion assets")
    parser.add_argument(
        "--profiles-dir",
        default="profiles/device-class",
    )
    parser.add_argument(
        "--fireos-doc",
        default="docs/FIRE_OS_FEASIBILITY_MVP.md",
    )
    parser.add_argument(
        "--matrix-doc",
        default="docs/HARDWARE_CLASS_CERTIFICATION_MATRIX.md",
    )
    parser.add_argument(
        "--report",
        default="test-output/p6-device-class-expansion-report.json",
    )
    args = parser.parse_args()

    profiles_dir = Path(args.profiles_dir)
    fireos_doc = Path(args.fireos_doc)
    matrix_doc = Path(args.matrix_doc)

    errors = validate_p6_assets(
        profiles_dir=profiles_dir,
        fireos_doc=fireos_doc,
        matrix_doc=matrix_doc,
    )

    report = {
        "report_version": "1.0.0",
        "ok": len(errors) == 0,
        "errors": errors,
        "profiles_dir": str(profiles_dir),
        "fireos_doc": str(fireos_doc),
        "matrix_doc": str(matrix_doc),
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("[p6-device-class-expansion] validation")
    print(f"  ok: {report['ok']}")
    print(f"  report: {report_path}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
