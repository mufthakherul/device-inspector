#!/usr/bin/env bash
set -euo pipefail

# Inspecta bootable ISO build entrypoint.
# Delegates to Python backend that performs staging + ISO generation + checksums.

WORKDIR="${WORKDIR:-./dist/bootable-iso}"
PROFILE="${PROFILE:-ubuntu-minimal}"
ISO_NAME="${ISO_NAME:-inspecta-live.iso}"
VOLUME_ID="${VOLUME_ID:-INSPECTA_LIVE}"

python -m tools.bootable_iso \
  --output "$WORKDIR" \
  --profile "$PROFILE" \
  --iso-name "$ISO_NAME" \
  --volume-id "$VOLUME_ID" \
  --forensic
