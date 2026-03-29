# ROADMAP — device-inspector (inspecta) Master Plan

**Last updated:** 2026-03-29  
**Document type:** Forward roadmap (execution-grade)  
**Scope:** Product + engineering + delivery + docs + release + platform expansion  

---

## 1) Vision and outcome

Build `inspecta` into a **professional, modern, cross-platform, offline-first, multi-purpose diagnostics platform** with:

- Reliable **Quick Mode** and fully implemented **Full Mode**
- Verifiable, tamper-aware evidence bundles
- Strong UX for technicians, refurbishers, enterprises, and end users
- Multi-channel distribution:
  - CLI packages
  - Desktop apps (Windows/macOS/Linux)
  - Mobile apps (Android APK / iOS package pipeline)
  - Bootable ISO for deep diagnostics
- Public GitHub Pages portal for users and developers

---

## 2) Product principles

1. **Offline-first by default**: core diagnostics work with zero cloud requirement.
2. **Cross-platform comfort**: Windows/macOS/Linux should have first-class paths (not Linux-only assumptions).
3. **Evidence integrity**: every run should be auditable and reproducible.
4. **Graceful degradation**: missing probes degrade quality but do not crash workflows.
5. **Professional distribution**: signed binaries, installers, checksums, and release notes.
6. **Developer friendliness**: documented architecture, contributor guides, CI transparency.

---

## 3) Current baseline (as of 2026-03-29)

### Completed foundation
- Quick mode CLI flow
- ✅ **Full mode fully implemented** (no longer scaffold placeholder):
  - Three runtime profiles: balanced (10min), deep (30min), forensic (60min)
  - Timeout controls with per-profile defaults (overridable via --timeout)
  - Retry policy and safe-stop behavior per profile
  - Dry-run mode for execution planning without actual diagnostics
  - Structured progress logging and state machine foundation
- JSON/TXT/PDF/HTML reporting
- Evidence manifest generation + verify command
- Optional upload API (core endpoints)
- React-based local viewer scaffold
- 117+ tests (including 17 new profile tests) with 47.29% coverage
- Windows battery invocation hardening (powercfg argument fallback + cleanup)
- ✅ Sprint 1 fully complete (full-mode architecture finalized)
- ✅ Sprint 2 diagnostics expansion (advanced completion):
   - SMART timeline snapshots (`smart_timeline.json`) for full mode
   - Memory deep-log importer pipeline (`memtester` + `memtest86` parser support)
   - Thermal severity tiers (`low`, `moderate`, `high`, `critical`)
   - Failure classification in report summary (`hardware_risk`, `tooling_missing`, `environment_limited`)
   - Profile-driven full-mode stress duration wiring
   - IO stress cycle execution + artifact (`disk_stress.json`) and summary metrics
- ✅ Sprint 3 Windows parity (advanced completion):
   - Windows inventory backend via PowerShell/CIM (`Win32_ComputerSystem`, `Win32_BIOS`, enclosure data)
   - Windows inventory registry fallback (`HKLM:\HARDWARE\DESCRIPTION\System\BIOS`)
   - Windows benchmark fallback backends when Linux tools unavailable:
      - Disk: `winsat` sequential read/write backend
      - CPU: PowerShell/CIM derived CPU performance estimate backend
   - Windows storage health backend via PowerShell `Get-PhysicalDisk` (health/operational status mapping)
   - smartctl-first Windows storage probing (`smartctl --scan-open`) with native fallback
   - Windows CPU throttling detection backend via CIM sampling (frequency-drop based)
   - OpenHardwareMonitor-first thermal adapter strategy with WMI fallback

### Gaps to close
- True Windows/macOS native probe parity for inventory/perf/thermal
- Mobile/desktop app packaging pipelines
- Bootable ISO reproducible production build
- GitHub Pages product + developer portal
- Enterprise hardening (retention, malware scan, signed release policy)

---

## 4) Delivery phases (high-level)

- **Phase A — Stabilize Core & Full Mode** (Weeks 1–6)
- **Phase B — Cross-Platform Parity** (Weeks 7–12)
- **Phase C — Distribution Expansion** (Weeks 13–18)
- **Phase D — Bootable + Enterprise Readiness** (Weeks 19–24)
- **Phase E — Ecosystem & Scale** (Weeks 25+)

---

## 5) Detailed execution plan (sprints)

> Sprint cadence: 2 weeks each.  
> Definition of done (all sprints): tests, docs, changelog, release notes draft, rollback notes.

### Sprint 1 — Full Mode Architecture Finalization

**Status:** ✅ **COMPLETED** (2026-03-29)

**Goal:** Finalize `--mode full` design and execution engine.

**Tasks:**
- Define full-mode state machine (`prepare -> probe -> stress -> memtest -> evidence -> finalize`).
  - ✅ Implemented state machine concepts in profiles module with phase-based execution
- ✅ Implement full-mode command path in `agent/cli.py` (removed scaffold exit; phase-1 baseline)
- ✅ Add runtime profiles for full mode: `balanced`, `deep`, `forensic`
  - `balanced`: 10-minute timeout, 2-minute stress, 2 thermal cycles, 2 retries (default)
  - `deep`: 30-minute timeout, 10-minute stress, 5 thermal cycles, 3 retries
  - `forensic`: 60-minute timeout, 20-minute stress, 10 thermal cycles, 5 retries (never interrupt)
- ✅ Add timeout controls, retry policy, safe-stop behavior
  - Per-profile timeout configuration (overridable via --timeout CLI option)
  - Retry strategies with max-attempts per profile
  - Safe-stop enabled for balanced/deep; disabled for forensic mode
- ✅ Add dry-run planner output for technicians
  - `--dry-run` flag shows execution plan without running diagnostics
  - Plan includes probe list, timeout, thermal cycles, artifacts structure

**Acceptance criteria:**
- ✅ `inspecta run --mode full --output <dir>` executes non-scaffold baseline flow
- ✅ Structured progress events emitted to log and optional JSONL stream (via inspector_logger)
- ✅ Tests for full mode baseline flow added (test_cli_run_modes.py)
- ✅ Profile tests for all three profiles (balanced, deep, forensic) added (test_profiles.py)
- ✅ Dry-run mode generates and displays execution plan
- ✅ Code passes Black formatting and Ruff linting
- ✅ All 18 profile+CLI tests passing with 47.29% coverage

---

### Sprint 2 — Full Mode Diagnostics Completion

**Status:** ✅ **COMPLETED** (2026-03-29)

**Goal:** Complete deep diagnostics stack.

**Tasks:**
- 🟡 Integrate long-duration stress plans (CPU, IO, thermal cycles).
   - ✅ CPU/thermal duration now profile-driven for full mode.
   - ✅ IO stress-cycling plan implemented with aggregated cycle summaries.
- ✅ Integrate memory deep tests with importers (MemTest logs + native memtest outputs).
- ✅ Add extended SMART timeline snapshots.
- ✅ Add thermal throttling severity scoring tiers.
- ✅ Add failure classification (`hardware_risk`, `tooling_missing`, `environment_limited`).

**Acceptance criteria:**
- ✅ Full mode produces extended artifacts and richer scoring (timeline + severity + importer-backed memory data + IO cycle summaries).
- ✅ Report includes full-mode timeline/risk context via `smart_timeline` test output and `summary.failure_classification`.
- ✅ No hard crash when one deep probe fails (graceful partial classification pathways retained).

---

### Sprint 3 — Windows Native Parity

**Status:** ✅ **COMPLETED** (2026-03-29)

**Goal:** Remove Linux-only assumptions for core probes on Windows.

**Tasks:**
- ✅ Inventory backend: WMI/CIM + registry fallback.
- ✅ Storage health backend: smartctl-compatible path + Windows native APIs where possible.
- ✅ CPU/thermal: robust PowerShell/WMI/OpenHardwareMonitor adapter strategy.
- ✅ Battery: fix `powercfg` invocation and path quoting edge cases (primary + fallback argument strategy).
- ✅ Inventory backend: PowerShell/CIM implementation added in `agent/plugins/inventory.py`.
- ✅ Benchmarks: Windows-compatible backends when `fio/sysbench` absent.
   - Disk fallback via `winsat` backend in `agent/plugins/disk_perf.py`
   - CPU fallback via CIM estimate backend in `agent/plugins/cpu_bench.py`
- ✅ Storage health backend: smartctl-compatible path + Windows native APIs where possible.
   - Added smartctl-first Windows probing via `smartctl --scan-open`
   - Added native Windows storage-health probe via `Get-PhysicalDisk` fallback in `agent/plugins/smart.py`
- ✅ CPU/thermal: robust PowerShell/WMI/OpenHardwareMonitor adapter strategy.
   - Added Windows throttling detection pipeline using CIM sampling in `agent/plugins/sensors.py`
   - Added OpenHardwareMonitor-first snapshot path with WMI fallback

**Acceptance criteria:**
- ✅ Real Windows run has valid inventory fields (not unknown placeholders) on supported devices.
- ✅ Battery report succeeds when OS command succeeds directly.
- ✅ Degradation warnings are clear and actionable.
- ✅ Fresh real-device **no-sample** run completes end-to-end with graceful degradation (non-admin `winsat` elevation surfaced as warning, no CLI crash).

---

### Sprint 4 — macOS Native Parity

**Status:** 🟡 **IN PROGRESS** (2026-03-29)

**Goal:** First-class macOS support.

**Tasks:**
- ✅ Inventory via `system_profiler` hardware JSON adapter (normalized model/serial/firmware fields).
- ✅ Battery via `pmset` + `system_profiler SPPowerDataType` normalization pipeline.
- ✅ Thermal and CPU metrics with safe fallback policy (`osx-cpu-temp`/`powermetrics`, `sysctl` throttling indicators).
- ✅ Storage health mapping for NVMe/SATA where available via `diskutil` plist + SMART status normalization.
- ✅ CI job for macOS functional smoke tests added (`macos-smoke` in `.github/workflows/ci.yml`).

**Acceptance criteria:**
- ✅ macOS quick mode path now has native probe backends and graceful degradation logic.
- ✅ Platform-specific tests run in CI (workflow includes `macos-smoke`; unit tests cover macOS probe code paths).

---

### Sprint 5 — Linux Robustness and Distro Matrix

**Goal:** Improve Linux consistency across distros.

**Tasks:**
- Distro capability detector (Debian/Ubuntu/Fedora/Arch families).
- Tool resolver with install hints per distro.
- Permission model checks (sudo/capabilities).
- Containerized integration smoke matrix.

**Acceptance criteria:**
- Reduced false failures due to distro differences.
- Probe behavior documented per distro class.

---

### Sprint 6 — Offline Professional Bundle

**Goal:** Turn output into enterprise-grade offline bundle.

**Tasks:**
- Include report JSON in manifest coverage policy.
- Detached signature mode (`ed25519`) for report bundles.
- Bundle validator command improvements with machine-readable exit taxonomy.
- Tamper simulation test suite.
- Add immutable run metadata (tool versions, OS fingerprint hash, timestamps).

**Acceptance criteria:**
- `inspecta verify` detects intentional tampering across tracked files.
- Signed and unsigned verification pathways documented.

---

### Sprint 7 — CLI Packaging & Installer Distribution

**Goal:** Professional CLI distribution channels.

**Tasks:**
- Publish Python package (`pip`, `pipx`) with release automation.
- Build standalone artifacts per OS (PyInstaller/Nuitka strategy review).
- Add package channels:
  - Windows: `winget` / Chocolatey / Scoop metadata
  - macOS: Homebrew tap
  - Linux: `.deb`, `.rpm`, AppImage (minimum)
- Add checksums and signature verification docs.

**Acceptance criteria:**
- Users can install CLI from at least one native channel per platform.
- Release assets generated automatically on tag.

---

### Sprint 8 — Desktop App Suite (Windows/macOS/Linux)

**Goal:** GUI applications for non-CLI users.

**Tasks:**
- Build desktop shell (Tauri or Electron) around local engine.
- Add run manager, artifact explorer, report viewer, verification UI.
- Installer outputs:
  - Windows: `.msix` / `.exe`
  - macOS: `.dmg` / `.pkg`
  - Linux: `.AppImage`, `.deb`, `.rpm`, optional Snap/Flatpak
- Local-only mode toggle with strict network deny policy.

**Acceptance criteria:**
- GUI app runs offline and launches diagnostics locally.
- Platform installers built via CI release jobs.

---

### Sprint 9 — Android & iOS Mobile Pipeline

**Goal:** Mobile companion app pipelines and release readiness.

**Tasks:**
- Mobile app architecture (Flutter or React Native) for report viewing, bundle verification, optional upload management.
- Android build workflow to produce **APK/AAB**.
- iOS workflow to produce **IPA** (and optional archive artifacts as requested packaging alias `apkx` in docs matrix if needed for organization-specific naming).
- Secure signing via GitHub Environments + encrypted secrets.
- Device pairing via QR/local transfer (offline friendly).

**Acceptance criteria:**
- Android CI produces signed/unsigned APK artifacts.
- iOS CI on macOS runners produces IPA build artifacts (where signing secrets available).
- Mobile app can open and validate report bundles.

---

### Sprint 10 — HarmonyOS and Extended Platforms

**Goal:** Expand to additional ecosystems.

**Tasks:**
- Define HarmonyOS target strategy (HAP package pipeline + compatibility scope).
- Build adapter layer for platform-specific packaging outputs.
- Publish platform capability matrix and support policy.

**Acceptance criteria:**
- HarmonyOS packaging workflow documented and scaffolded.
- Release matrix includes Windows/macOS/Linux/Android/iOS/HarmonyOS status.

---

### Sprint 11 — Bootable ISO Production

**Goal:** Complete reproducible bootable diagnostics image.

**Tasks:**
- Replace scaffold with real ISO build backend.
- Include full-mode probe tools and dependencies in image.
- Add secure boot/UEFI guidance.
- Add forensic write-minimization mode.
- CI pipeline to build ISO nightly and on tag.

**Acceptance criteria:**
- Bootable ISO builds reproducibly from CI.
- Technician can run full diagnostics from USB and export signed bundles.

---

### Sprint 12 — GitHub Pages Product + Developer Portal

**Goal:** Public website for users, developers, and downloads.

**Tasks:**
- Build `docs-site` with sections:
  - Project purpose and value proposition
  - User quickstart (CLI/Desktop/Mobile/ISO)
  - Download center (latest releases by platform)
  - Developer docs (architecture, plugin API, contributing, security)
  - Roadmap, changelog, support, FAQ
- Add `pages` deployment workflow.
- Add release metadata sync job to auto-update download cards.

**Acceptance criteria:**
- GitHub Pages site auto-deploys on main/docs changes.
- Download page reflects latest release assets automatically.

---

## 6) Mandatory GitHub Actions workflow matrix

Create/maintain the following workflows in `.github/workflows/`:

1. `ci-core.yml`
   - Lint, unit tests, schema validation, security checks.
2. `ci-integration-matrix.yml`
   - OS matrix smoke tests (windows-latest, ubuntu-latest, macos-latest).
3. `build-cli-packages.yml`
   - Python wheels/sdist + standalone binaries + checksums.
4. `build-desktop-apps.yml`
   - Windows/macOS/Linux GUI app installers.
5. `build-mobile-android.yml`
   - Android APK/AAB artifacts.
6. `build-mobile-ios.yml`
   - iOS IPA build on macOS runner with signing environment support.
7. `build-harmonyos.yml`
   - HarmonyOS packaging scaffold/production (as feasible per toolchain).
8. `build-bootable-iso.yml`
   - Reproducible ISO builds + artifact upload.
9. `release.yml`
   - Tag-triggered release orchestration across all build outputs.
10. `deploy-pages.yml`
   - GitHub Pages deployment for docs/product portal.
11. `nightly-health.yml`
   - Nightly full pipeline health check and drift reporting.

---

## 7) Packaging and distribution targets

### CLI targets
- `pip`, `pipx`
- Homebrew (macOS/Linux)
- Winget/Chocolatey/Scoop (Windows)
- apt/deb and rpm repos (Linux)

### Desktop targets
- Windows: `.msix`, `.exe`
- macOS: `.dmg`, `.pkg`
- Linux: `.AppImage`, `.deb`, `.rpm`, optional Snap/Flatpak

### Mobile targets
- Android: `.apk`, `.aab`
- iOS: `.ipa` (and organizational alias packaging docs if `apkx` naming is required in external distribution workflows)

### Bootable target
- UEFI-capable `.iso` with offline diagnostics and export support

---

## 8) Full mode completion definition (strict)

`full` mode is complete only when all are true:

1. Runs without scaffold error on Windows/macOS/Linux.
2. Executes deep diagnostics pipeline with progress tracking.
3. Produces extended artifact set and full-mode section in report.
4. Supports resume/retry and interrupted-run recovery.
5. Supports offline evidence generation + verification.
6. Has automated tests + integration runs in CI.
7. Has user docs and troubleshooting flow.

---

## 9) GitHub Pages information architecture

`/` Home
- What inspecta is, who it is for, key features.

`/download`
- Platform-specific installers, checksums, signatures, release notes.

`/docs/user`
- CLI usage, quick/full mode, report interpretation.

`/docs/technician`
- Bootable USB workflow, forensic mode, evidence verification.

`/docs/developer`
- Architecture, modules, plugin SDK, testing, contribution, coding standards.

`/project`
- Purpose, roadmap, changelog, governance, security policy.

`/community`
- Discussions, issue templates, support channels, contribution map.

---

## 10) KPI dashboard and success metrics

- Real-device quick mode success rate by OS/device class
- Real-device full mode success rate by OS/device class
- False-warning rate and false-failure rate
- Mean runtime (quick/full)
- Installer success rate by platform
- Crash-free sessions (desktop/mobile)
- Report verification success rate
- Release pipeline reliability (green rate)
- Docs quality: time-to-first-success for new users

---

## 11) Risk register (expanded)

1. **Platform probe fragility**  
   Mitigation: adapter abstraction + contract tests + fallback hierarchy.

2. **Signing and certificate complexity**  
   Mitigation: staged signing strategy, environment-scoped secrets, dry-run signing checks.

3. **Mobile/iOS CI constraints**  
   Mitigation: macOS runner strategy, separate signed/unsigned lanes, reproducible fallback artifacts.

4. **Bootable image legal/tool licensing concerns**  
   Mitigation: explicit dependency inventory and license compliance gate.

5. **Security trust of reports**  
   Mitigation: signed evidence, timestamp policy, optional transparency log.

---

## 12) Governance and release policy

- Semantic versioning with channels: `alpha`, `beta`, `stable`.
- Security response SLA and disclosure policy.
- Mandatory release checklist:
  - test matrix green
  - build matrix green
  - signatures/checksums published
  - docs updated
  - rollback notes prepared

---

## 13) Suggested repository structure additions

- `apps/desktop/`
- `apps/mobile/`
- `bootable/iso/`
- `docs-site/` (for GitHub Pages)
- `.github/workflows/` expanded with matrix workflows
- `packaging/` (installer manifests, metadata, signing scripts)

---

## 14) 90-day execution milestones

### Milestone M1 (Day 30)
- Full mode core engine implemented.
- Windows battery and inventory parity improved.
- CI integration matrix active.

### Milestone M2 (Day 60)
- Desktop app MVP installers built.
- CLI packaging channels active.
- GitHub Pages v1 live.

### Milestone M3 (Day 90)
- Android + iOS build pipelines operational.
- Bootable ISO production build available.
- Cross-platform release orchestration fully automated.

---

## 15) Immediate next actions (first 10 issues to open)

1. Implement full-mode flow controller and progress state machine.
2. Replace Windows inventory placeholder with WMI backend.
3. Fix Windows `powercfg` invocation edge cases and parser hardening.
4. Add benchmark backend abstraction for platform compatibility.
5. Add full-mode report schema extensions.
6. Create `build-cli-packages.yml` workflow.
7. Create `build-desktop-apps.yml` workflow.
8. Create `build-mobile-android.yml` + `build-mobile-ios.yml` workflows.
9. Create `build-bootable-iso.yml` workflow.
10. Launch `docs-site` + `deploy-pages.yml` workflow.

---

## 16) Status tracking template (use in each sprint)

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

---

This roadmap is intentionally ambitious and comprehensive. Execute in increments, keep each workflow green, and prioritize **real-device reliability** plus **offline trustworthiness** as the non-negotiable core.
