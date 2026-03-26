from __future__ import annotations

from typing import Any

from agent import native_bridge


class FakeCompletedProcess:
    def __init__(self, stdout: str = "") -> None:
        self.stdout = stdout


def test_native_helper_missing(monkeypatch):
    """Returns unavailable when the binary is not present."""
    monkeypatch.setattr(native_bridge.shutil, "which", lambda _name: None)

    result = native_bridge.detect_native_capabilities()

    assert result["available"] is False
    assert result["reason"] == "not_found"


def test_native_helper_invalid_json(monkeypatch):
    """Handles bad JSON gracefully."""

    def fake_run(*_args: Any, **_kwargs: Any):
        return FakeCompletedProcess(stdout="{not-json")

    monkeypatch.setattr(
        native_bridge.shutil, "which", lambda _name: "/tmp/inspecta-native"
    )
    monkeypatch.setattr(native_bridge.subprocess, "run", fake_run)

    result = native_bridge.detect_native_capabilities()

    assert result["available"] is False
    assert "invalid_json" in result["reason"]


def test_native_helper_parsed_payload(monkeypatch):
    """Parses the handshake payload when the helper exists."""

    def fake_run(*_args: Any, **_kwargs: Any):
        payload = '{"status":"ok","tool":"inspecta-native"}'
        return FakeCompletedProcess(stdout=payload)

    monkeypatch.setattr(
        native_bridge.shutil, "which", lambda _name: "/tmp/inspecta-native"
    )
    monkeypatch.setattr(native_bridge.subprocess, "run", fake_run)

    result = native_bridge.detect_native_capabilities()

    assert result["available"] is True
    assert result["status"] == "ok"
    assert result["payload"]["tool"] == "inspecta-native"
    assert result["binary"] == "/tmp/inspecta-native"
