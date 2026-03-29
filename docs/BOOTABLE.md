# Bootable Diagnostics (Sprint 6 scaffold)

This document defines the current bootable-image workflow and next implementation steps.

## Current status

- `tools/build-live-iso.sh` exists and prepares reproducible build metadata.
- Full distro-specific ISO assembly is **not yet complete**.

## Goals

- Build a live image with:
  - smartmontools
  - fio
  - stress-ng
  - memtester
  - memtest86+/MemTest86 integration guidance
- Generate signed/hashed evidence bundle from runs.

## Quick start (scaffold)

1. Run builder scaffold:
   - `bash tools/build-live-iso.sh`
2. Review generated manifest:
   - `dist/live-iso/iso-build-manifest.json`

## Technician checklist

- Verify target machine boots from USB.
- Confirm test tools are available in live shell.
- Run quick diagnostics and export `report.json` + `artifacts/`.
- Validate bundle integrity:
  - `python tools/verify_bundle.py <output_dir>`

## Next implementation steps

- Add distro-specific live image build backend.
- Add package-install phase and automated smoke checks.
- Add optional signature support (Ed25519) for evidence manifests.
- Add memtest full-run import helper into `report.json`.
