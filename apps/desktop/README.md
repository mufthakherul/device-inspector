# Inspecta Desktop (Sprint 8 MVP)

Cross-platform Electron desktop shell for local diagnostics and evidence workflows.

## Features

- Run manager (quick/full + profile selection)
- Artifact explorer (bundle file listing)
- Report viewer (summary from `report.json`)
- Verification UI (`inspecta verify --json` integration)
- Local-only mode toggle (network deny policy enabled by default)
- Shared local engine adapter contract for dual-shell tracks (`engine/adapter-contract.json`)

## Experimental Tauri track (Sprint 5)

The repository now includes a dual-shell migration contract for Electron and
Tauri to consume the same local engine semantics. This keeps optional
Electron -> Tauri migration gated by parity and stability evidence.

Migration gate criteria and validation tooling:

- Criteria spec: `engine/migration-gate-criteria-1.0.0.json`
- Validator: `python tools/validate_desktop_migration_gate.py`

## Local development

```bash
cd apps/desktop
npm install
npm start
```

## Build installers

```bash
cd apps/desktop
npm install
npm run dist
```

Targets are configured for:

- Windows: NSIS (`.exe`)
- macOS: `.dmg`, `.pkg`
- Linux: `.AppImage`, `.deb`, `.rpm`

## Notes

The desktop shell invokes the local Python CLI (`python -m agent.cli`).
Set `INSPECTA_PYTHON` to override interpreter selection.
