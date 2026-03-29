# HarmonyOS Strategy (Sprint 10)

This document defines the initial HarmonyOS support strategy for `inspecta`.

## Scope

- Target package format: **HAP**
- Current state: **workflow scaffold**
- Objective: move from scaffold to production HAP packaging when Harmony toolchain is available in CI.

## Planned architecture

1. Reuse the Flutter-based mobile companion UX where feasible.
2. Introduce a Harmony adapter in release orchestration (`tools/platform_adapter.py`).
3. Keep offline-first behavior and local bundle verification as non-negotiable platform requirements.

## CI scaffold workflow

- Workflow: `.github/workflows/build-harmonyos.yml`
- Behavior:
  - Packages source + platform docs as scaffold artifacts.
  - Performs optional `hvigorw` probe if toolchain is present.

## Migration path to production

1. Add Harmony SDK/toolchain bootstrap in CI image.
2. Add `hvigorw` build command for HAP generation.
3. Add signed and unsigned HAP lanes via repository/environment secrets.
4. Attach `.hap` artifacts to release jobs and update capability matrix state to `beta/stable`.

## Security and support policy

- Signing secrets must be environment-scoped and never committed.
- Use least-privilege CI permissions.
- Maintain parity with Android/iOS offline verification behavior.
