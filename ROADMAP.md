# ROADMAP — device-inspector (inspecta) Next-Generation Master Plan

**Last updated:** 2026-03-30  
**Document type:** Strategic + execution roadmap (polyglot modernization)  
**Scope:** Product, architecture, diagnostics depth, distribution, security, governance, ecosystem scale

---

## 1) Vision and outcome

Build `inspecta` into a **professional, modern, cross-platform, offline-first, smart, portable, all-round diagnostics platform** that supports:

- Fast and reliable **Quick Mode** and robust **Full Mode**
- Verifiable, tamper-aware evidence bundles with strong trust signals
- Rich experiences for technicians, refurbishers, enterprises, field support, and power users
- Multi-channel distribution:
  - CLI packages and standalone binaries
  - Desktop apps (Windows/macOS/Linux)
  - Mobile apps (Android/iOS)
  - Bootable ISO for deep diagnostics
- Public docs + release portal with transparent operational status
- **Polyglot architecture** for performance, maintainability, and long-term scalability

---

## 2) Product principles

1. **Offline-first always:** zero-cloud required for core diagnostics and verification.
2. **Cross-platform parity:** no platform is second-class for core capabilities.
3. **Evidence integrity by default:** every run must be auditable and reproducible.
4. **Graceful degradation:** missing probes/tools produce actionable warnings, not crashes.
5. **Professional distribution:** checksums, signatures, release notes, and reproducible builds.
6. **Developer ergonomics:** clear architecture, contribution paths, CI visibility, testability.
7. **Performance-conscious engineering:** use the right language for each subsystem.
8. **Privacy-preserving by design:** local processing first, explicit opt-in for network actions.

---

## 3) Current baseline and modernization direction

### Current strengths (validated)
- Working CLI with quick/full execution paths.
- Evidence manifest generation + verification flows.
- Cross-platform workflows for build and smoke validation.
- Desktop/mobile/ISO scaffolding and pipelines in place.
- Docs-site deployment + release metadata synchronization.

### Strategic modernization direction (new)
- Move from mostly single-language orchestration to a **polyglot, capability-first stack**:
  - **Python**: orchestration, plugin API, report composition.
  - **Rust**: high-performance collectors, secure crypto/evidence operations, privileged probe modules.
  - **TypeScript**: web UX, docs portal, desktop UI surfaces.
  - **Dart (Flutter)**: mobile companion apps.
  - **Go**: lightweight background daemons/remote probe helpers where static binaries are ideal.
  - **Bash/PowerShell**: platform setup and operator automation scripts.

### Polyglot language-by-capability blueprint (expanded)

| Capability | Primary Language | Secondary Language(s) | Why this split |
|---|---|---|---|
| Core orchestration engine | Python | Rust (FFI), Go | Python keeps iteration speed high; Rust/Go accelerate critical paths. |
| High-risk native probe logic | Rust | C/C++ interop (where needed) | Memory safety + performance for low-level device interactions. |
| CLI UX and scripting surface | Python | Rust (optional compiled CLI core) | Fast delivery now, optional ultra-fast compiled path later. |
| Desktop UI | TypeScript | Rust (Tauri backend), Python bridge | Modern UI/UX + lighter binaries in Tauri mode. |
| Mobile apps | Dart (Flutter) | Kotlin/Swift bridges if needed | Strong cross-platform offline app delivery. |
| Web/docs portal | TypeScript | Astro/Next static generation | Fast static docs, strong DX, modern component workflow. |
| Offline AI/analytics | Rust + Python | ONNX Runtime / WebAssembly | Efficient local inference without mandatory cloud services. |
| Cryptography/evidence trust | Rust | Python bindings | Strong safety and deterministic signing/verification routines. |
| Build and release automation | YAML + Bash + PowerShell | Python task runners | Cross-platform CI and reproducible packaging control. |
| ISO runtime scripts | Bash | Rust utilities | Portable boot-time automation + high-performance helpers. |

---

## 4) Delivery phases (high-level)

- **Phase A — Core hardening & truth alignment** (Weeks 1–4)
- **Phase B — Polyglot architecture transition** (Weeks 5–10)
- **Phase C — Distribution and offline trust expansion** (Weeks 11–16)
- **Phase D — Enterprise reliability and observability** (Weeks 17–22)
- **Phase E — Ecosystem scale and SDK platform** (Weeks 23+)

---

## 5) Detailed execution plan (sprints)

> Sprint cadence: 2 weeks.  
> Definition of done: code + tests + docs + changelog + rollback notes + risk updates.

### Sprint 1 — Baseline integrity and compatibility freeze
- Lock report schema compatibility policy.
- Add versioned capability matrix consumed by CLI/desktop/mobile.
- Add migration guards for legacy artifacts.

### Sprint 2 — Offline evidence v2
- Add deterministic bundle mode with canonical ordering.
- Introduce signed attestations (detached + in-manifest metadata).
- Add forensic provenance metadata profile.

### Sprint 3 — Windows/macOS/Linux parity completion
- Close remaining native probe gaps with standardized adapter contracts.
- Add parity contract tests per OS family.
- Add reliability scoring for degraded probe sets.

### Sprint 4 — Rust acceleration layer
- Implement Rust probe runner for hot paths (SMART parse, sensor normalization, crypto ops).
- Expose FFI boundary to Python orchestration with strict schema types.
- Benchmark and target at least 30–50% speed-up on heavy parsing workloads.
- Add WebAssembly build option for selected Rust modules used in docs/desktop/mobile viewers.

### Sprint 5 — Desktop modernization (dual strategy)
- Keep Electron path stable.
- Add **Tauri/Rust+TS** experimental desktop track for lightweight distribution.
- Unified local engine adapter for both shells.
- Define migration gate for optional Electron -> Tauri default switch after parity + stability targets.

### Sprint 6 — Mobile offline specialist features
- Flutter report viewer + advanced validation UX.
- Offline pairing hardening (QR + file + LAN direct mode).
- Background verification job queue with integrity badges.
- Add optional native bridge modules (Kotlin/Swift) for platform-specific sensors or secure key storage.

### Sprint 7 — ISO deep diagnostics 2.0
- Add layered ISO profiles (quick tech bench / forensic / secure-lab).
- Add reproducibility attestations and dependency SBOM embedding.
- Add encrypted export bundle option.

### Sprint 8 — Packaging channels full automation
- Add channel promotion workflow (nightly -> beta -> stable).
- Add package notarization/signing automation where supported.
- Publish machine-readable distribution manifest per release.

### Sprint 9 — Smart analytics (offline)
- Add local anomaly detection for thermal/storage trends (on-device inference only).
- Add confidence score for each recommendation.
- Add explainability payload in report.
- Add ONNX-based local model runtime profile with CPU-only fallback for fully offline operation.

### Sprint 10 — Enterprise policy packs
- Add policy profiles (refurbish shop, enterprise IT, field service, resale audit).
- Add retention policy controls and evidence redaction presets.
- Add organization policy export/import.

### Sprint 11 — SDK and plugin platform
- Plugin SDK for Python + Rust adapters.
- Capability negotiation protocol.
- Signed plugin manifests and compatibility checks.

### Sprint 12 — Governance, docs IA v2, release readiness
- Align all top-level docs with actual implementation state.
- Expand docs-site to route-based IA (`/download`, `/docs/*`, `/project`, `/community`).
- Release readiness review gates for each platform lane.

---

## 6) Mandatory GitHub Actions workflow matrix (target state)

1. `ci-core.yml` — lint, tests, schema, security baseline.
2. `ci-integration-matrix.yml` — OS smoke + container matrix.
3. `build-cli-packages.yml` — wheel/sdist/native binaries/checksums.
4. `build-desktop-apps.yml` — desktop installers across OSes.
5. `build-mobile-android.yml` — Android APK/AAB.
6. `build-mobile-ios.yml` — iOS IPA lanes.
7. `build-harmonyos.yml` — HarmonyOS scaffold/production path.
8. `build-bootable-iso.yml` — reproducible ISO + checksums.
9. `release.yml` — orchestration + gating of release-critical workflows.
10. `deploy-pages.yml` — docs portal deployment.
11. `nightly-health.yml` — nightly health, drift, and stability checks.
12. `sbom-security.yml` — SBOM generation + vulnerability/license policy checks.
13. `performance-regression.yml` — benchmark guardrails for core probes.
14. `polyglot-build.yml` — validates Python/Rust/TypeScript/Flutter/Go build integrity.
15. `wasm-artifacts.yml` — builds and validates WebAssembly modules used by UI/analytics components.

---

## 7) Packaging and distribution targets

### CLI targets
- `pip`, `pipx`
- Homebrew (macOS/Linux)
- Winget/Chocolatey/Scoop (Windows)
- Linux package lanes (`.deb`, `.rpm`, `.AppImage`) + repository automation roadmap

### Desktop targets
- Windows: `.exe`, `.msix`
- macOS: `.dmg`, `.pkg`
- Linux: `.AppImage`, `.deb`, `.rpm`, optional Snap/Flatpak
- Experimental lightweight desktop builds via Tauri

### Mobile targets
- Android: `.apk`, `.aab`
- iOS: `.ipa`
- HarmonyOS: `.hap` (scaffold -> beta -> stable progression)

### Bootable target
- UEFI-capable `.iso` profiles with offline diagnostics and verified export workflows

---

## 8) Full mode completion definition (strict)

`full` mode is complete only when all are true:

1. Runs without scaffold errors on Windows/macOS/Linux.
2. Executes deep diagnostics pipeline with progress tracking.
3. Produces extended artifacts and full-mode report sections.
4. Supports retry plus interrupted-run recovery checkpoints.
5. Supports offline evidence generation and verification.
6. Has automated tests + CI integration runs.
7. Has user docs + troubleshooting flow.
8. Has deterministic output mode for reproducibility.

---

## 9) GitHub Pages information architecture (target)

- `/` Home
- `/download` platform installers, checksums, signatures, release notes
- `/docs/user` CLI usage, quick/full interpretation
- `/docs/technician` bootable and forensic workflows
- `/docs/developer` architecture, modules, plugin SDK, coding standards
- `/project` roadmap, changelog, governance, security policy, release policy
- `/community` discussions, issue templates, support and contribution map
- `/status` live build/release health summary

---

## 10) KPI dashboard and success metrics

- Quick-mode success rate by OS/device class
- Full-mode success rate by OS/device class
- False-warning and false-failure rates
- Mean runtime (quick/full)
- Installer success rate by platform
- Crash-free desktop/mobile sessions
- Report verification success rate
- Release workflow green rate + MTTR
- Docs time-to-first-success
- Probe parity index by platform
- Bundle reproducibility pass rate

---

## 11) Risk register (expanded)

1. Platform probe fragility  
   Mitigation: adapter contracts + fallback stacks + contract tests.
2. Signing/certificate complexity  
   Mitigation: staged signing policy + env-scoped secrets + dry-run checks.
3. Mobile/iOS CI constraints  
   Mitigation: signed/unsigned lane split + deterministic fallback artifacts.
4. ISO/legal dependency risks  
   Mitigation: SBOM + license gate + dependency inventory checks.
5. Trust and tamper resistance  
   Mitigation: signatures, timestamp policy, optional transparency records.
6. Polyglot integration complexity  
   Mitigation: strict schema contracts and compatibility test suites.

---

## 12) Governance and release policy

- Semantic versioning channels: `alpha`, `beta`, `stable`.
- Security response SLA and coordinated disclosure process.
- Mandatory release checklist:
  - test matrix green
  - build matrix green
  - checksums/signatures published
  - docs synchronized
  - rollback notes prepared
  - SBOM and policy checks passed

---

## 13) Repository structure (target evolution)

- `agent/` Python orchestration + plugin contracts
- `native/rust/` Rust probe and crypto acceleration modules
- `native/go/` Go-based lightweight probe daemons and remote helpers
- `native/wasm/` WebAssembly-ready modules for shared offline validation/inference
- `apps/desktop/` Desktop shells (Electron/Tauri tracks)
- `apps/mobile/` Flutter clients
- `apps/web/` TypeScript-based user/dev portal surfaces
- `bootable/iso/` ISO build profiles and runtime payloads
- `docs-site/` route-based docs portal
- `.github/workflows/` expanded CI/CD/security/perf matrix
- `packaging/` manifests, channel metadata, signing scripts
- `sdk/` plugin SDKs and examples
- `benchmarks/` performance baselines and regression harness

---

## 14) 90-day execution milestones

### Milestone M1 (Day 30)
- Baseline truth alignment complete (docs/claims/state).
- Core parity and reliability scoring validated.
- KPI collection framework initialized.

### Milestone M2 (Day 60)
- Rust acceleration path in production for selected probes.
- Desktop dual-shell strategy validated.
- Route-based docs portal deployed.

### Milestone M3 (Day 90)
- Channelized release automation (`alpha`/`beta`/`stable`) live.
- Offline smart analytics in full mode available.
- SDK + plugin signing baseline published.

---

## 15) Immediate next actions (first 16 issues to open)

1. Reconcile roadmap claims vs current implementation artifacts.
2. ✅ Implement interrupted-run recovery checkpoints for full mode (CLI checkpoint + resume path).
3. ✅ Add deterministic bundle mode test suite (`tests/test_evidence.py` fixed-timestamp + canonical ordering assertions).
4. Add `sbom-security.yml` workflow.
5. Add performance regression benchmark workflow.
6. Implement route-based docs-site IA (`/download`, `/docs/*`, etc.).
7. Add `.msix` packaging lane validation.
8. Add Linux repo publication workflow strategy (`deb/rpm index`).
9. Add policy pack schema for enterprise modes.
10. Add local anomaly detector module (offline inference).
11. Add Rust SMART parser integration contract tests.
12. Add plugin signing manifest schema.
13. Add release channel promotion gates.
14. ✅ Add reproducibility audit command for bundles (`inspecta audit` in `agent/cli.py`).
15. Refresh README/CHANGELOG/PROJECT_READINESS consistency.
16. Publish quarterly architecture review notes.

---

## Polyglot implementation guardrails (must-follow)

1. **No forced rewrite policy:** retain working Python logic; migrate only where performance/safety/portability gains are measurable.
2. **Contract-first integration:** all cross-language boundaries must use versioned schemas and compatibility tests.
3. **Offline guarantee:** every new feature must provide a cloud-free execution path.
4. **Deterministic outputs:** multi-language modules must preserve stable report/evidence semantics.
5. **Security-first native code:** Rust preferred for sensitive operations over unsafe C extensions.
6. **Cross-platform CI gate:** merge blocked unless affected language lanes pass on target platforms.
7. **Operator simplicity:** user-facing install/run experience must remain one-command/simple launcher.
8. **Performance accountability:** migrations require benchmark evidence before and after.

---

## 16) Status tracking template (required in every sprint)

- Planned
- In progress
- Done
- Deferred
- Blocked (with owner + unblock date)

Each sprint must update:
- delivery percentage
- test pass/fail
- release risk level
- cross-platform parity score
- KPI delta summary
- known regressions and rollback notes

---

## Section-by-section compliance matrix (1–16)

Use this matrix each sprint to ensure roadmap integrity and avoid over-claiming.

| Section | Compliance Criteria | Current Status | Evidence Source | Gap Owner | Target Sprint |
|---|---|---|---|---|---|
| 1 Vision | Core outcomes measurable and shipped | In progress | product + release outputs | PM | Rolling |
| 2 Principles | Offline, parity, integrity, degradation validated | In progress | tests + real-device runs | Eng Lead | Rolling |
| 3 Baseline | Claims match repository reality | Planned | docs audits | Maintainer | Sprint 1 |
| 4 Phases | Milestones mapped to delivery | In progress | planning board | PM | Rolling |
| 5 Sprints | DoD satisfied for each sprint | In progress | sprint reports | Team | Rolling |
| 6 Workflows | Required CI/CD/security workflows green | In progress | GitHub Actions | DevOps | Sprint 2 |
| 7 Packaging | Target channels produce usable artifacts | In progress | release artifacts | Release Eng | Sprint 8 |
| 8 Full mode | Strict completion criteria passed | In progress | `agent/cli.py` checkpoint state + `tests/test_cli_run_modes.py` resume test + deterministic evidence tests in `tests/test_evidence.py` | Core Eng | Sprint 2 |
| 9 Docs IA | Route-based portal complete | Planned | docs-site routes | DX | Sprint 12 |
| 10 KPIs | Dashboard and metrics pipeline active | Planned | status dashboards | PM+Data | Sprint 3 |
| 11 Risks | Mitigations enforced by policy/tests | In progress | risk + CI gates | Sec/QA | Rolling |
| 12 Governance | Channelized release policy enforced | Planned | release workflows | Release Eng | Sprint 8 |
| 13 Structure | Target repo layout adopted | In progress | repo tree | Maintainer | Sprint 4 |
| 14 Milestones | M1/M2/M3 objective evidence available | Planned | milestone reports | PM | Rolling |
| 15 Next actions | Action backlog actively executed | In progress | issue board | Team | Rolling |
| 16 Tracking | Sprint template fully maintained | Planned | sprint logs | PMO | Sprint 1 |

---

This roadmap intentionally balances ambition with verifiable delivery. The non-negotiable priorities remain: **offline trustworthiness, cross-platform reliability, and transparent evidence integrity**.