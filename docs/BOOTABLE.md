# Bootable Diagnostics (Sprint 11)

This document defines the bootable ISO production backend and technician flow.

## Current status

- `tools/bootable_iso.py` provides a reproducible ISO backend (staging + ISO + checksums).
- `tools/build-live-iso.sh` is a shell entrypoint delegating to the Python backend.
- CI workflow `.github/workflows/build-bootable-iso.yml` builds ISO artifacts nightly and on tag.

## Included diagnostics payload metadata

The ISO staging payload includes required tool declarations for live diagnostics:

- smartmontools
- fio
- stress-ng
- memtester
- memtest86-plus
- nvme-cli

## Build locally

### Prerequisites

- Linux build host
- `xorriso` (or `genisoimage`/`mkisofs`)

### Command

- `bash tools/build-live-iso.sh`

Artifacts are generated in `dist/bootable-iso/`:

- `inspecta-live.iso`
- `iso-build-manifest.json`
- `SHA256SUMS`

## Forensic write-minimization mode

The ISO payload includes `/opt/inspecta/forensic-write-minimization.sh` with guidance to:

- prefer read-only source mounts
- use tmpfs output paths when feasible
- minimize writes on target evidence media

## Secure Boot and UEFI guidance

1. Validate target firmware mode (UEFI preferred).
2. If Secure Boot is enabled, use signed boot chain media appropriate to your distro/toolchain.
3. If unsigned custom boot chain is required for lab workflows, temporarily disable Secure Boot under approved SOP.
4. Always record firmware/security mode in inspection notes for audit traceability.

## Technician checklist

- Verify target machine boots from USB in UEFI mode.
- Confirm required probe tools are present per ISO manifest.
- Run full diagnostics and export `report.json` + `artifacts/`.
- Validate bundle integrity:
  - `python -m agent.cli verify <output_dir> --json`

## CI reproducibility notes

- Workflow pins `SOURCE_DATE_EPOCH` to stabilize timestamps in manifest generation.
- SHA256 checksums are generated for ISO and manifest for artifact validation.
