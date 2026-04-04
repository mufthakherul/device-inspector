from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _profiles_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "profiles" / "device-class"


def load_device_class_profiles() -> dict[str, dict[str, Any]]:
    base = _profiles_dir()
    if not base.exists():
        return {}

    profiles: dict[str, dict[str, Any]] = {}
    for file in sorted(base.glob("*.json")):
        payload = json.loads(file.read_text(encoding="utf-8"))
        class_id = payload.get("class_id")
        if isinstance(class_id, str) and class_id:
            profiles[class_id] = payload
    return profiles


def detect_device_class(device: dict[str, Any]) -> str:
    source = " ".join(
        [
            str(device.get("model", "")),
            str(device.get("vendor", "")),
            str(device.get("chassis", "")),
            str(device.get("device_type", "")),
            str(device.get("platform", "")),
            str(device.get("arch", "")),
        ]
    ).lower()

    if any(token in source for token in ("tablet", "tab")):
        return "tablet-mobile"

    if any(token in source for token in ("raspberry", "rpi", "arm", "aarch64")):
        return "arm-rpi-linux"

    if any(token in source for token in ("edge", "mini pc", "minipc", "iot")):
        return "edge-mini-pc"

    if any(token in source for token in ("fire os", "fireos", "kindle")):
        return "fireos-companion"

    return "laptop-desktop"


def get_device_class_assessment(device: dict[str, Any]) -> dict[str, Any]:
    class_id = detect_device_class(device)
    profiles = load_device_class_profiles()
    profile = profiles.get(class_id, {})

    return {
        "class_id": class_id,
        "support_level": profile.get("support_level", "unknown"),
        "recommended_mode": profile.get("recommended_mode", "quick"),
        "validation_pack": profile.get("validation_pack", "default"),
        "profile_version": profile.get("profile_version"),
    }
