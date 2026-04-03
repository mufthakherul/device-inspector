# Quarterly Architecture Review — 2026 Q2

Date: 2026-04-04

## Scope

This review captures architecture posture across orchestration, evidence integrity, cross-platform execution, and modernization lanes.

## Snapshot

- Python remains the orchestration control plane and report/evidence source of truth.
- Native acceleration remains optional and gracefully degradable via `agent/native_bridge.py`.
- Evidence pipeline (`inspecta verify` and `inspecta audit`) is production-path and covered by tests.
- CI matrix now includes polyglot and WASM scaffolding lanes in addition to core release/security lanes.

## Decisions and rationale

1. **No forced rewrite policy retained**
   - Keep stable Python orchestration while incrementally adopting Rust/other lanes where measurable.
2. **Route-based docs IA adopted in docs-site**
   - Added static routes: `/download`, `/docs/*`, `/project`, `/community`, `/status`.
3. **Release channel semantics formalized**
   - Added channel gate workflow and prerelease tagging behavior (`alpha`/`beta` prerelease).
4. **Policy/plugin schema groundwork added**
   - Added `policy-pack-schema-1.0.0.json` and `plugin-manifest-schema-1.0.0.json`.

## Risks and follow-ups

- Direct runtime parity across all deep probes remains environment-sensitive.
- Route-based docs pages should be followed by richer content and generation automation.
- Plugin signature verification runtime integration is still pending; schema is foundation only.

## Next-quarter priorities (Q2 → Q3 handoff)

1. Implement policy pack evaluation in CLI/report recommendation paths.
2. Add plugin manifest loading and signature verification gate.
3. Add route-aware docs generation pipeline and status-data auto-refresh.
4. Expand Rust/wasm contract tests once native modules land.
