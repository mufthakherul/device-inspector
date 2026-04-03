from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capability_matrix import get_surface_plugin_capabilities


class PluginNegotiationError(Exception):
    """Raised when plugin capability/version negotiation fails."""


@dataclass(frozen=True)
class VersionTriplet:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str, label: str) -> "VersionTriplet":
        chunks = value.split(".")
        if len(chunks) < 3:
            raise PluginNegotiationError(
                f"Invalid {label} version '{value}'. Expected semver like 1.2.3"
            )
        try:
            major = int(chunks[0])
            minor = int(chunks[1])
            patch_part = chunks[2].split("-")[0].split("+")[0]
            patch = int(patch_part)
        except ValueError as exc:
            raise PluginNegotiationError(
                f"Invalid {label} version '{value}'. Expected numeric semver."
            ) from exc
        return cls(major=major, minor=minor, patch=patch)

    def __lt__(self, other: "VersionTriplet") -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )


def _is_capability_allowed(requested: str, allowed: list[str]) -> bool:
    for rule in allowed:
        if rule == requested:
            return True
        if rule.endswith(".*") and requested.startswith(rule[:-1]):
            return True
    return False


def negotiate_plugin_capabilities(
    manifest: dict[str, Any],
    *,
    surface: str,
    inspecta_version: str,
) -> dict[str, Any]:
    """Negotiate plugin compatibility and capability policy.

    Rules:
        - Plugin requested capabilities must be allowed by the
            capability matrix for surface.
    - If compatibility block exists, inspecta_version must be within [min, max].
    """
    policy = get_surface_plugin_capabilities(surface)
    allowed_caps = policy["allowed_plugin_capabilities"]

    requested_raw = manifest.get("capabilities", [])
    requested = [str(item) for item in requested_raw if isinstance(item, str)]

    rejected = [
        cap for cap in requested if not _is_capability_allowed(cap, allowed_caps)
    ]

    compatible = True
    compatibility_message = "compatible"
    compatibility_block = manifest.get("compatibility")

    if isinstance(compatibility_block, dict):
        inspecta_semver = VersionTriplet.parse(inspecta_version, "inspecta")
        min_version = VersionTriplet.parse(
            str(compatibility_block.get("inspecta_min", "")),
            "plugin inspecta_min",
        )
        max_version = VersionTriplet.parse(
            str(compatibility_block.get("inspecta_max", "")),
            "plugin inspecta_max",
        )

        if max_version < min_version:
            raise PluginNegotiationError(
                "Plugin compatibility range is invalid: inspecta_max is lower "
                "than inspecta_min."
            )

        if inspecta_semver < min_version or max_version < inspecta_semver:
            compatible = False
            compatibility_message = (
                "inspecta version out of supported plugin range "
                f"[{compatibility_block.get('inspecta_min')}, "
                f"{compatibility_block.get('inspecta_max')}]"
            )

    diagnostics: list[str] = []
    if rejected:
        diagnostics.append(
            "Unsupported plugin capabilities for "
            f"surface '{surface}': {', '.join(sorted(rejected))}"
        )
    if not compatible:
        diagnostics.append(compatibility_message)

    status = "accepted" if not diagnostics else "rejected"

    return {
        "status": status,
        "surface": surface,
        "matrix_version": policy["matrix_version"],
        "allowed_capabilities": allowed_caps,
        "requested_capabilities": requested,
        "rejected_capabilities": sorted(rejected),
        "version_compatible": compatible,
        "compatibility_message": compatibility_message,
        "diagnostics": diagnostics,
    }
