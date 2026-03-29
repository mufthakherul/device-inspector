from __future__ import annotations

import json
from pathlib import Path

from agent.upload_client import _normalize_upload_endpoint, upload_report_bundle


def test_normalize_upload_endpoint():
    assert (
        _normalize_upload_endpoint("https://example.com")
        == "https://example.com/reports"
    )
    assert (
        _normalize_upload_endpoint("https://example.com/")
        == "https://example.com/reports"
    )
    assert (
        _normalize_upload_endpoint("https://example.com/reports")
        == "https://example.com/reports"
    )


def test_upload_report_bundle_raises_when_no_files(tmp_path: Path):
    # No report.json/artifacts present
    try:
        upload_report_bundle(
            upload_url="https://example.com",
            token="token",
            output_dir=tmp_path,
        )
    except Exception as exc:  # UploadError type not required for this assertion
        assert "No uploadable files found" in str(exc)
    else:
        raise AssertionError("Expected upload_report_bundle to raise")


def test_upload_bundle_discovers_files(tmp_path: Path, monkeypatch):
    # Create expected report files
    (tmp_path / "report.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "agent.log").write_text("log", encoding="utf-8")

    captured = {"url": None, "headers": {}}

    class DummyResponse:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"id":"abc","status":201}'

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        return DummyResponse()

    monkeypatch.setattr("agent.upload_client.request.urlopen", fake_urlopen)

    result = upload_report_bundle(
        upload_url="https://example.com",
        token="secret",
        output_dir=tmp_path,
        metadata={"mode": "quick"},
    )

    assert captured["url"] == "https://example.com/reports"
    assert result["id"] == "abc"
    assert result["status"] == 201
