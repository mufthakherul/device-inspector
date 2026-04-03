from __future__ import annotations

from inspecta_plugin_sdk.contracts import PluginContext, PluginResult


def run(context: PluginContext) -> PluginResult:
    """Example plugin entrypoint."""
    warnings: list[str] = []
    if "report.enrich" not in context.capabilities:
        warnings.append("report.enrich capability not granted")

    return PluginResult(
        status="ok",
        data={"plugin": "health-example", "surface": context.surface},
        warnings=warnings,
    )
