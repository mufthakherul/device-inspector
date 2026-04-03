"""Generate machine-readable distribution manifest for release channels."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _channel_roots() -> dict[str, tuple[str, str]]:
    return {
        "winget": ("packaging/winget", "windows"),
        "chocolatey": ("packaging/chocolatey", "windows"),
        "scoop": ("packaging/scoop", "windows"),
        "homebrew": ("packaging/homebrew", "macos-linux"),
    }


def _collect_channels(repo_root: Path) -> list[dict[str, Any]]:
    channels: list[dict[str, Any]] = []
    for channel, (relative_root, platform) in _channel_roots().items():
        root = repo_root / relative_root
        files = sorted(
            str(path.relative_to(repo_root)).replace("\\", "/")
            for path in root.rglob("*")
            if path.is_file()
        )
        channels.append(
            {
                "channel": channel,
                "platform": platform,
                "root": relative_root,
                "status": "available" if files else "scaffold",
                "files": files,
            }
        )

    channels.sort(key=lambda item: item["channel"])
    return channels


def _group_summary(release_payload: dict[str, Any]) -> list[dict[str, Any]]:
    groups = release_payload.get("groups", {})
    if not isinstance(groups, dict):
        return []

    summary: list[dict[str, Any]] = []
    for group_name, assets in sorted(groups.items()):
        assets = assets if isinstance(assets, list) else []
        summary.append(
            {
                "group": group_name,
                "asset_count": len(assets),
                "assets": [
                    {
                        "name": asset.get("name"),
                        "size_bytes": asset.get("size_bytes"),
                        "browser_download_url": asset.get("browser_download_url"),
                    }
                    for asset in assets
                    if isinstance(asset, dict)
                ],
            }
        )
    return summary


def build_distribution_manifest(
    *, repo_root: Path, release_payload: dict[str, Any]
) -> dict[str, Any]:
    latest = release_payload.get("latest", {})
    if not isinstance(latest, dict):
        latest = {}

    return {
        "manifest_version": "1.0.0",
        "source": "distribution-manifest/release-sync",
        "generated_at": _now_iso(),
        "release": {
            "tag_name": latest.get("tag_name"),
            "published_at": latest.get("published_at"),
            "html_url": latest.get("html_url"),
        },
        "artifact_groups": _group_summary(release_payload),
        "channels": _collect_channels(repo_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate distribution manifest")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--releases-json", default="docs-site/data/releases.json")
    parser.add_argument("--output", default="docs-site/data/distribution-manifest.json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    releases_json = (repo_root / args.releases_json).resolve()
    output = (repo_root / args.output).resolve()

    release_payload = json.loads(releases_json.read_text(encoding="utf-8"))
    manifest = build_distribution_manifest(
        repo_root=repo_root, release_payload=release_payload
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("[distribution-manifest] generated")
    print(f"  output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
