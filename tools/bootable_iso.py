"""Bootable ISO backend for inspecta (Sprint 11).

Builds a reproducible ISO image containing offline diagnostics tooling metadata,
launch scripts, and runbook artifacts for technician workflows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

DEFAULT_PROFILE = "ubuntu-minimal"
DEFAULT_TOOLS = [
    "smartmontools",
    "fio",
    "stress-ng",
    "memtester",
    "memtest86-plus",
    "nvme-cli",
]


@dataclass(frozen=True)
class BuildResult:
    iso_path: Path
    manifest_path: Path
    checksums_path: Path
    backend_tool: str


def _utc_now_iso() -> str:
    epoch = os.getenv("SOURCE_DATE_EPOCH")
    if epoch:
        return (
            datetime.fromtimestamp(int(epoch), tz=UTC)
            .replace(microsecond=0)
            .isoformat()
        )
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_file(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def stage_iso_tree(
    staging_dir: Path,
    profile: str = DEFAULT_PROFILE,
    forensic_mode: bool = True,
    required_tools: Iterable[str] = DEFAULT_TOOLS,
) -> dict:
    """Create deterministic staging tree for ISO content."""
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    tools_list = list(required_tools)
    generated_at = _utc_now_iso()

    run_script = """#!/usr/bin/env bash
set -euo pipefail

OUTDIR="${1:-/tmp/inspecta-run}"
mkdir -p "$OUTDIR"

echo "[inspecta-live] running full diagnostics"
python -m agent.cli run --mode full --output "$OUTDIR" --no-auto-open
python -m agent.cli verify "$OUTDIR" --json

echo "[inspecta-live] run complete: $OUTDIR"
"""

    forensic_script = """#!/usr/bin/env bash
set -euo pipefail

# Write-minimization profile for forensic use:
# - discourage swap writes
# - preserve source media integrity through read-only mount guidance

echo "[inspecta-live] enabling forensic write-minimization guidance"
echo "Use: mount -o ro /dev/<source> /mnt/source"
echo "Use tmpfs output paths when possible: /dev/shm/inspecta-run"
"""

    packages_txt = "\n".join(tools_list) + "\n"

    _write_file(
        staging_dir / "opt" / "inspecta" / "run-full.sh", run_script, executable=True
    )
    _write_file(
        staging_dir / "opt" / "inspecta" / "forensic-write-minimization.sh",
        forensic_script,
        executable=True,
    )
    _write_file(
        staging_dir / "opt" / "inspecta" / "required-packages.txt", packages_txt
    )

    readme = f"""Inspecta Live ISO
=================

Profile: {profile}
Generated at: {generated_at}
Forensic mode default: {forensic_mode}

Included diagnostics dependencies:
{packages_txt}

Run full diagnostics:
  /opt/inspecta/run-full.sh <output-dir>

Forensic guidance:
  /opt/inspecta/forensic-write-minimization.sh
"""
    _write_file(staging_dir / "README.txt", readme)

    manifest = {
        "manifest_version": "1.0.0",
        "generated_at": generated_at,
        "profile": profile,
        "forensic_write_minimization": forensic_mode,
        "required_tools": tools_list,
        "secure_boot_uefi_guidance": (
            "See docs/BOOTABLE.md for Secure Boot + UEFI flow."
        ),
        "status": "build-ready",
    }

    manifest_path = staging_dir / "opt" / "inspecta" / "iso-build-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )
    return manifest


def _iso_commands(
    tool: str, iso_path: Path, staging_dir: Path, volume_id: str
) -> list[str]:
    if tool == "xorriso":
        return [
            "xorriso",
            "-as",
            "mkisofs",
            "-r",
            "-J",
            "-V",
            volume_id,
            "-o",
            str(iso_path),
            str(staging_dir),
        ]
    return [
        tool,
        "-r",
        "-J",
        "-V",
        volume_id,
        "-o",
        str(iso_path),
        str(staging_dir),
    ]


def _build_iso_image(staging_dir: Path, output_iso: Path, volume_id: str) -> str:
    backends = ["xorriso", "genisoimage", "mkisofs"]
    for backend in backends:
        if not shutil.which(backend):
            continue

        cmd = _iso_commands(backend, output_iso, staging_dir, volume_id)
        subprocess.run(cmd, check=True)
        return backend

    raise RuntimeError(
        "No ISO backend available. Install xorriso or genisoimage/mkisofs."
    )


def build_bootable_iso(
    output_dir: Path,
    profile: str = DEFAULT_PROFILE,
    forensic_mode: bool = True,
    iso_name: str = "inspecta-live.iso",
    volume_id: str = "INSPECTA_LIVE",
) -> BuildResult:
    """Build ISO plus manifest and checksum outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = output_dir / "staging"

    stage_iso_tree(
        staging_dir=staging_dir,
        profile=profile,
        forensic_mode=forensic_mode,
    )

    iso_path = output_dir / iso_name
    if iso_path.exists():
        iso_path.unlink()

    backend = _build_iso_image(
        staging_dir=staging_dir, output_iso=iso_path, volume_id=volume_id
    )

    manifest_path = output_dir / "iso-build-manifest.json"
    shutil.copy2(
        staging_dir / "opt" / "inspecta" / "iso-build-manifest.json", manifest_path
    )

    checksums_path = output_dir / "SHA256SUMS"
    checksums_path.write_text(
        f"{_sha256_file(iso_path)}  {iso_path.name}\n"
        f"{_sha256_file(manifest_path)}  {manifest_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )

    return BuildResult(
        iso_path=iso_path,
        manifest_path=manifest_path,
        checksums_path=checksums_path,
        backend_tool=backend,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build inspecta bootable ISO")
    parser.add_argument(
        "--output", default="dist/bootable-iso", help="Output directory"
    )
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="ISO profile name")
    parser.add_argument("--iso-name", default="inspecta-live.iso", help="ISO file name")
    parser.add_argument("--volume-id", default="INSPECTA_LIVE", help="ISO volume ID")
    parser.add_argument(
        "--forensic",
        action="store_true",
        default=True,
        help="Enable forensic write-minimization guidance artifacts",
    )
    args = parser.parse_args()

    result = build_bootable_iso(
        output_dir=Path(args.output),
        profile=args.profile,
        forensic_mode=args.forensic,
        iso_name=args.iso_name,
        volume_id=args.volume_id,
    )

    print("[inspecta-iso] build complete")
    print(f"  ISO: {result.iso_path}")
    print(f"  Manifest: {result.manifest_path}")
    print(f"  Checksums: {result.checksums_path}")
    print(f"  Backend: {result.backend_tool}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
