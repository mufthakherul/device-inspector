from tools.sync_release_metadata import build_payload


def test_build_payload_groups_assets() -> None:
    latest = {
        "tag_name": "v1.2.3",
        "published_at": "2026-03-29T00:00:00Z",
        "html_url": "https://example.invalid/release",
        "assets": [
            {
                "name": "inspecta-1.2.3-windows.zip",
                "size": 12,
                "browser_download_url": "https://example/windows",
            },
            {
                "name": "inspecta-1.2.3-linux.AppImage",
                "size": 34,
                "browser_download_url": "https://example/linux",
            },
            {
                "name": "inspecta-1.2.3.ipa",
                "size": 56,
                "browser_download_url": "https://example/ios",
            },
            {
                "name": "inspecta-1.2.3.iso",
                "size": 78,
                "browser_download_url": "https://example/iso",
            },
        ],
    }

    payload = build_payload(latest)

    assert payload["latest"]["tag_name"] == "v1.2.3"
    assert "Windows" in payload["groups"]
    assert "Linux" in payload["groups"]
    assert "iOS" in payload["groups"]
    assert "Bootable ISO" in payload["groups"]
