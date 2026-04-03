from __future__ import annotations

from agent.analytics_profile import get_offline_analytics_profile


def test_analytics_profile_invalid_env_override_falls_back(monkeypatch):
    monkeypatch.setenv("INSPECTA_ANALYTICS_RUNTIME", "gpu-fast")

    profile = get_offline_analytics_profile(prefer_onnx=True)

    assert profile["engine"] == "rules-only"
    assert profile["source"] == "env-override-invalid"
    assert profile["offline"] is True


def test_analytics_profile_accepts_rules_only_override(monkeypatch):
    monkeypatch.setenv("INSPECTA_ANALYTICS_RUNTIME", "rules-only")

    profile = get_offline_analytics_profile(prefer_onnx=True)

    assert profile["engine"] == "rules-only"
    assert profile["source"] == "env-override"


def test_analytics_profile_default_without_onnx_runtime_is_rules_only(monkeypatch):
    monkeypatch.delenv("INSPECTA_ANALYTICS_RUNTIME", raising=False)

    profile = get_offline_analytics_profile(prefer_onnx=False)

    assert profile["engine"] == "rules-only"
    assert profile["source"] == "auto-fallback"
