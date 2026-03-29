#!/usr/bin/env bash
set -euo pipefail

# inspecta bootable image builder scaffold
# This script prepares a reproducible work directory and records
# required packages/tools for a live diagnostic image.

WORKDIR="${WORKDIR:-./dist/live-iso}"
PROFILE="${PROFILE:-ubuntu-minimal}"
OUTPUT_MANIFEST="${OUTPUT_MANIFEST:-$WORKDIR/iso-build-manifest.json}"

mkdir -p "$WORKDIR"

cat > "$OUTPUT_MANIFEST" <<EOF
{
  "version": "0.1.0",
  "profile": "$PROFILE",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "required_tools": [
    "smartmontools",
    "fio",
    "stress-ng",
    "memtester",
    "memtest86-plus"
  ],
  "status": "scaffold",
  "notes": [
    "This script is an implementation scaffold for Sprint 6.",
    "Integrate distro-specific ISO tooling (xorriso/live-build) as next step.",
    "Use docs/BOOTABLE.md for manual build/test checklist."
  ]
}
EOF

echo "[inspecta] Bootable ISO scaffold prepared"
echo "  Workdir: $WORKDIR"
echo "  Manifest: $OUTPUT_MANIFEST"
