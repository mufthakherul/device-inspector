from __future__ import annotations

import pytest

from agent.plugin_negotiation import (
    PluginNegotiationError,
    negotiate_plugin_capabilities,
)


def test_negotiate_plugin_capabilities_accepts_supported_capabilities():
    manifest = {
        "capabilities": ["smart.parse", "report.enrich"],
        "compatibility": {"inspecta_min": "0.1.0", "inspecta_max": "1.0.0"},
    }

    result = negotiate_plugin_capabilities(
        manifest=manifest,
        surface="cli",
        inspecta_version="0.1.0",
    )

    assert result["status"] == "accepted"
    assert result["version_compatible"] is True
    assert result["rejected_capabilities"] == []


def test_negotiate_plugin_capabilities_rejects_unknown_capability():
    manifest = {
        "capabilities": ["smart.parse", "gpu.oc"],
    }

    result = negotiate_plugin_capabilities(
        manifest=manifest,
        surface="cli",
        inspecta_version="0.1.0",
    )

    assert result["status"] == "rejected"
    assert result["rejected_capabilities"] == ["gpu.oc"]
    assert any(
        "Unsupported plugin capabilities" in item for item in result["diagnostics"]
    )


def test_negotiate_plugin_capabilities_rejects_out_of_range_version():
    manifest = {
        "capabilities": ["smart.parse"],
        "compatibility": {"inspecta_min": "0.2.0", "inspecta_max": "0.3.0"},
    }

    result = negotiate_plugin_capabilities(
        manifest=manifest,
        surface="cli",
        inspecta_version="0.1.0",
    )

    assert result["status"] == "rejected"
    assert result["version_compatible"] is False


def test_negotiate_plugin_capabilities_invalid_compatibility_range():
    manifest = {
        "capabilities": ["smart.parse"],
        "compatibility": {"inspecta_min": "0.3.0", "inspecta_max": "0.2.0"},
    }

    with pytest.raises(PluginNegotiationError):
        negotiate_plugin_capabilities(
            manifest=manifest,
            surface="cli",
            inspecta_version="0.2.5",
        )


def test_negotiate_plugin_capabilities_unknown_surface():
    manifest = {"capabilities": ["smart.parse"]}
    with pytest.raises(ValueError):
        negotiate_plugin_capabilities(
            manifest=manifest,
            surface="wearable",
            inspecta_version="0.1.0",
        )
