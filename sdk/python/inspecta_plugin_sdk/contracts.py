from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PluginContext:
    """Runtime context passed to plugin entrypoints."""

    surface: str
    inspecta_version: str
    capabilities: list[str]


@dataclass(frozen=True)
class PluginResult:
    """Deterministic plugin response contract."""

    status: str
    data: dict[str, Any]
    warnings: list[str]
