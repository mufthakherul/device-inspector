"""Sync latest GitHub release metadata for docs-site download cards."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _group_for_asset(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["windows", ".exe", ".msix"]):
        return "Windows"
    if any(x in n for x in ["macos", ".dmg", ".pkg"]):
        return "macOS"
    if any(x in n for x in ["linux", ".appimage", ".deb", ".rpm"]):
        return "Linux"
    if any(x in n for x in ["android", ".apk", ".aab"]):
        return "Android"
    if any(x in n for x in ["ios", ".ipa"]):
        return "iOS"
    if ".hap" in n or "harmony" in n:
        return "HarmonyOS"
    if any(x in n for x in [".whl", ".tar.gz"]):
        return "Python"
    if ".iso" in n:
        return "Bootable ISO"
    return "Other"


def fetch_latest_release(owner: str, repo: str, token: str | None = None) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "inspecta-release-sync",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    with urlopen(
        request, timeout=30
    ) as response:  # nosec B310 (trusted GitHub API endpoint)
        return json.loads(response.read().decode("utf-8"))


def build_payload(latest: dict) -> dict:
    assets = latest.get("assets", [])
    groups: dict[str, list[dict]] = {}

    for asset in assets:
        name = asset.get("name", "")
        group = _group_for_asset(name)
        groups.setdefault(group, []).append(
            {
                "name": name,
                "size_bytes": asset.get("size", 0),
                "browser_download_url": asset.get("browser_download_url", ""),
            }
        )

    for key in groups:
        groups[key].sort(key=lambda item: item["name"].lower())

    return {
        "source": "github-releases/latest",
        "generated_at": _now_iso(),
        "latest": {
            "tag_name": latest.get("tag_name"),
            "published_at": latest.get("published_at"),
            "html_url": latest.get("html_url"),
        },
        "groups": groups,
    }


def write_payload(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync docs-site release metadata")
    parser.add_argument("--owner", default="mufthakherul")
    parser.add_argument("--repo", default="inspecta-nexus")
    parser.add_argument("--output", default="docs-site/data/releases.json")
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")

    try:
        latest = fetch_latest_release(args.owner, args.repo, token=token)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"[release-sync] failed to fetch latest release: {exc}")
        return 1

    payload = build_payload(latest)
    output_path = Path(args.output)
    write_payload(payload, output_path)

    print("[release-sync] metadata updated")
    print(f"  tag: {payload['latest']['tag_name']}")
    print(f"  output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
