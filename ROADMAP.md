# ROADMAP — inspecta (Redesigned Execution Plan)

**Last updated:** 2026-04-04  
**Status model:** `Implemented` / `In Progress` / `Planned` / `Deferred`  
**Scope:** product execution plan aligned to current repository reality

---

## 1) Why this roadmap exists

This roadmap replaces the previous long-form strategic document with a delivery-focused plan:

- grounded in current code/workflow evidence,
- explicit about what is already implemented,
- clear about what is not yet implemented,
- structured by phases with measurable outcomes.

Legacy roadmap archived at: `archives/historical/ROADMAP_legacy_2026-04-04.md`.

---

## 2) Reality baseline (repo-verified)

## Implemented (high confidence)

- Core CLI execution paths and reporting:
  - `agent/cli.py`, `agent/report.py`, `agent/report_formatter.py`
- Evidence integrity and verification/audit flows:
  - `agent/evidence.py`, `tools/verify_bundle.py`, CLI verify/audit tests
- Schema compatibility + capability matrix:
  - `agent/schema_compat.py`, `agent/capability_matrix.py`, `schemas/capability-matrix-1.0.0.json`
- Reliability and analytics foundation:
  - `agent/reliability.py`, `agent/anomaly.py`, `agent/analytics_profile.py`
- Governance controls:
  - `agent/policy_pack.py`, `agent/plugin_manifest.py`, `agent/redaction.py`
- Rust boundary hardening:
  - `agent/native_contract.py`, `agent/native_bridge.py`, `tests/test_smart_rust_contract.py`
- Release/distribution automation:
  - `tools/generate_distribution_manifest.py`, `tools/channel_promotion.py`, `tools/release_signing.py`
- Strong workflow matrix in `.github/workflows/` including:
  - `ci-core.yml`, `ci-integration-matrix.yml`, `release.yml`, `build-release.yml`, `release-channel-gates.yml`, `channel-promotion.yml`, `sbom-security.yml`, `performance-regression.yml`, `polyglot-build.yml`
- Desktop/mobile scaffolds:
  - Desktop: `apps/desktop/*` + adapter contract
  - Mobile: `apps/mobile/lib/main.dart` with verification queue and integrity badges

## In Progress (partially implemented)

- Cross-platform deep-probe parity (beyond graceful degradation)
- Desktop dual-shell migration (Electron stable, Tauri migration gate scaffolded)
- Smart analytics expansion (foundations present; model maturity limited)
- Docs/site depth and automation maturity

## Planned / not fully implemented yet (key gaps)

1. Full Rust acceleration runner for hot paths with benchmarked 30–50% gains
2. OS-family parity contract tests across all supported host families
3. Tauri production-ready lane (currently scaffold/contract level)
4. Mobile advanced offline pairing modes (QR/file/LAN hardening completeness)
5. Native mobile bridges (Kotlin/Swift) for secure storage/sensor specialization
6. ISO reproducibility attestations + deeper SBOM embedding strategy
7. Plugin SDK (Python/Rust) and capability negotiation protocol
8. Strong release promotion governance (approval/signoff workflow depth)
9. Formalized milestone evidence packs (M1/M2/M3 objective scorecards)
10. Expanded device-class coverage for tablet/ARM/edge profiles

---

## 3) Platform and device strategy (professional cross-platform model)

## Host runtime (where `agent.cli` runs directly)

- **Tier A (primary):** Windows, Linux, macOS
- **Tier B (targeted variants):** Raspberry Pi OS / ARM Linux profiles
- **Tier C (specialized):** bootable ISO environments

## App surfaces and companion lanes

- Desktop: Windows/macOS/Linux
- Mobile: Android, iOS, HarmonyOS
- Additional mobile/tablet ecosystems (planned lanes):
  - Amazon Fire OS
  - KaiOS / Tizen class lanes (feasibility-driven)

> Note: mobile OS families are delivery/app lanes, not direct host runtime targets for the Python CLI core.

---

## 4) Target architecture (execution-oriented)

- **Python core:** orchestration, policy, scoring, report composition
- **Rust modules:** high-risk/high-throughput probe and trust operations
- **TypeScript desktop/web:** UX surfaces and integration shells
- **Flutter mobile:** offline companion and verification UX
- **Workflow-driven release engineering:** channel gates, signing, manifests, KPI pipelines

Non-negotiables:

1. Offline-first diagnostics
2. Deterministic evidence semantics
3. Cross-platform graceful degradation (no hard crashes for missing probes)
4. Security and integrity first (checksums, signatures, policy controls)

---

## 5) Redesigned phased implementation plan

## Phase P0 — Truth, quality, and governance lock (0–2 weeks)

**Goal:** keep docs/claims synced with repository facts every sprint.

### Deliverables
- Automated roadmap/readiness consistency check script
- Release evidence checklist template used in every release PR
- KPI snapshot quality gate baseline

### Exit criteria
- No top-level doc claim without direct file/workflow evidence
- CI quality gates stable across Python matrix

---

## Phase P1 — Core parity and reliability expansion (2–6 weeks)

**Goal:** reduce platform-probe parity gaps and improve deterministic behavior.

### Deliverables
- Expanded parity contract tests by OS family
- Reliability score calibration by probe-availability profile
- Structured degraded-mode recommendations in report output

### Exit criteria
- Probe parity index tracked per platform class
- Fewer degraded-but-unexplained outcomes in real-device runs

---

## Phase P2 — Native acceleration and performance proof (6–10 weeks)

**Goal:** move hot-path operations to production-grade native modules.

### Deliverables
- Rust probe runner for selected high-cost operations
- Benchmark harness + baseline/after comparison artifacts
- Optional WASM artifacts where practical for viewer/shared validation paths

### Exit criteria
- Measured speedup target achieved on selected workloads
- Compatibility tests passing for Python↔Rust schema contracts

---

## Phase P3 — Desktop and mobile product hardening (10–14 weeks)

**Goal:** mature companion surfaces beyond scaffold state.

### Deliverables
- Desktop migration gate criteria (Electron↔Tauri) with objective pass/fail rules
- Mobile offline pairing hardening (QR/file/LAN modes)
- Secure key/material handling plan for mobile-native bridges

### Exit criteria
- Desktop shell parity checklist published and validated
- Mobile verification UX reliability baseline met on Android/iOS

---

## Phase P4 — Release engineering and trust channel maturity (14–18 weeks)

**Goal:** production-grade release operations with strong trust signals.

### Deliverables
- Promotion governance extensions (approval rules + audit trail)
- Signing/notarization lane coverage matrix per platform
- Distribution manifest vNext with verification metadata enrichments

### Exit criteria
- Channel flow (nightly→alpha/beta→stable) fully governed
- Release artifacts consistently include checksums + signature/report metadata

---

## Phase P5 — Plugin ecosystem and enterprise extensibility (18–24 weeks)

**Goal:** deliver safe extensibility with compatibility and policy controls.

### Deliverables
- Plugin SDK (Python first, Rust adapter track)
- Capability negotiation protocol + compatibility matrix enforcement
- Policy profile packs for enterprise/operator archetypes

### Exit criteria
- Third-party plugin integration path documented and testable
- Compatibility failures produce deterministic, actionable diagnostics

---

## Phase P6 — Multi-device and ecosystem expansion (24+ weeks)

**Goal:** broaden practical support across mobile/tablet/edge classes.

### Deliverables
- Amazon Fire OS companion lane feasibility and MVP
- ARM/tablet/edge profile packs (including Raspberry Pi OS class)
- Hardware class certification matrix (laptop/desktop/tablet/mini-PC)

### Exit criteria
- Documented support tiers per OS and device class
- Repeatable validation packs for each supported lane

---

## 6) Prioritized improvement backlog (from current gap analysis)

Priority legend: `P0` highest → `P3` lower.

- `P0` Add automated docs-claim verifier for roadmap/readiness/goal consistency
- `P0` Expand OS parity test suite for probe contracts
- `P0` Publish measurable release signoff policy for channel promotions
- `P1` Implement Rust hot-path runner + benchmark reporting
- `P1` Add Tauri implementation spike with parity report against Electron shell
- `P1` Formalize mobile pairing security model and offline transport constraints
- `P1` Add distribution-manifest verification metadata (signature links/status)
- `P2` Implement plugin SDK package skeleton and examples
- `P2` Capability negotiation protocol spec + tests
- `P2` Extend KPI dashboard with trend windows and release regression markers
- `P3` Add Fire OS feasibility lane and compatibility matrix
- `P3` Add tablet-specific UX acceptance criteria and device-class profiles

---

## 7) KPI and quality gates

Required for each phase closeout:

- Test suite green (`pytest`) with coverage gate pass
- Lint/format pass (`ruff`, `black --check`)
- Release workflow health green for required matrix lanes
- Updated readiness summary with objective metrics
- Rollback and risk notes captured

---

## 8) Governance model for roadmap updates

- Update cadence: every sprint close
- Owner: maintainers + release engineering lead
- Change rule: every roadmap status change must reference concrete repo evidence
- Archive rule: replaced roadmap versions are stored under `archives/historical/`

---

## 9) Current phase focus (as of 2026-04-04)

Active emphasis:

1. P1 parity/reliability expansion
2. P2 native acceleration proof
3. P4 trust-channel governance hardening

This keeps the project advanced, professional, and scalable while preserving truthful delivery reporting.
