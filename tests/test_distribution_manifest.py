from __future__ import annotations

from pathlib import Path

from tools.generate_distribution_manifest import build_distribution_manifest


def test_build_distribution_manifest_includes_channels_and_groups(tmp_path: Path):
    (tmp_path / "packaging" / "winget").mkdir(parents=True)
    (tmp_path / "packaging" / "homebrew").mkdir(parents=True)
    (tmp_path / "packaging" / "winget" / "inspecta-agent.yaml").write_text(
        "id: inspecta",
        encoding="utf-8",
    )
    (tmp_path / "packaging" / "homebrew" / "inspecta.rb").write_text(
        "class Inspecta < Formula; end",
        encoding="utf-8",
    )

    payload = {
        "latest": {
            "tag_name": "v1.2.3",
            "published_at": "2026-04-04T00:00:00Z",
            "html_url": "https://example.invalid/release/v1.2.3",
        },
        "groups": {
            "Windows": [
                {
                    "name": "inspecta-1.2.3-windows.zip",
                    "size_bytes": 123,
                    "browser_download_url": "https://example.invalid/windows.zip",
                }
            ],
            "Linux": [],
        },
    }

    manifest = build_distribution_manifest(repo_root=tmp_path, release_payload=payload)

    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["release"]["tag_name"] == "v1.2.3"
    assert any(group["group"] == "Windows" for group in manifest["artifact_groups"])

    channels = {entry["channel"]: entry for entry in manifest["channels"]}
    assert channels["winget"]["status"] == "available"
    assert channels["homebrew"]["status"] == "available"
    assert channels["chocolatey"]["status"] == "scaffold"
