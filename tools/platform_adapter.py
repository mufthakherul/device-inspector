"""Platform packaging adapter layer for inspecta release orchestration.

Sprint 10 introduces a simple, testable adapter abstraction that maps each
supported platform to expected packaging outputs and support level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PlatformTarget:
    """Represents packaging output expectations for a platform."""

    name: str
    outputs: List[str]
    support_level: str
    notes: str


_TARGETS: Dict[str, PlatformTarget] = {
    "windows": PlatformTarget(
        name="windows",
        outputs=[".exe", ".msix"],
        support_level="stable",
        notes="Desktop installer outputs via desktop and release pipelines.",
    ),
    "macos": PlatformTarget(
        name="macos",
        outputs=[".dmg", ".pkg"],
        support_level="stable",
        notes="macOS desktop installer outputs via CI matrix.",
    ),
    "linux": PlatformTarget(
        name="linux",
        outputs=[".AppImage", ".deb", ".rpm"],
        support_level="stable",
        notes="Linux desktop and CLI package outputs are automated.",
    ),
    "android": PlatformTarget(
        name="android",
        outputs=[".apk", ".aab"],
        support_level="stable",
        notes="Flutter Android pipeline supports unsigned and optional signed builds.",
    ),
    "ios": PlatformTarget(
        name="ios",
        outputs=[".ipa"],
        support_level="stable",
        notes="Flutter iOS pipeline supports unsigned and optional signed IPA builds.",
    ),
    "harmonyos": PlatformTarget(
        name="harmonyos",
        outputs=[".hap"],
        support_level="scaffold",
        notes=(
            "HarmonyOS workflow scaffold is present; production HAP build "
            "depends on Harmony toolchain availability."
        ),
    ),
}


def supported_platforms() -> List[str]:
    """Return normalized platform keys in deterministic order."""
    return sorted(_TARGETS.keys())


def get_platform_target(platform_name: str) -> PlatformTarget:
    """Resolve platform target metadata.

    Raises:
        KeyError: if the platform is unknown.
    """
    normalized = platform_name.strip().lower()
    return _TARGETS[normalized]


def build_release_matrix() -> List[dict]:
    """Build machine-readable release matrix rows for documentation export."""
    rows: List[dict] = []
    for name in supported_platforms():
        target = _TARGETS[name]
        rows.append(
            {
                "platform": target.name,
                "outputs": ", ".join(target.outputs),
                "support_level": target.support_level,
                "notes": target.notes,
            }
        )
    return rows
