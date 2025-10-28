# ROADMAP — device-inspector (inspecta)

**Last updated:** 2025-10-28  
**Status:** Phase 1 in progress — Sprint 1 started  

> **📊 Progress Update (2025-10-28):** Sprint 0 complete (100%). Sprint 1 at ~30% completion with basic agent skeleton and SMART parsing implemented. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed current state.

This roadmap is the authoritative, actionable plan for building the device-inspector (inspecta) project. It converts the Project Goal and high-level strategy into a time-boxed implementation plan: phases, sprints, milestones, deliverables, acceptance criteria, owners, risks and mitigations, metrics, and operational playbooks for pilot and launch.

Use this document to:
- Guide implementation and prioritization.
- Create issues and PRs linked to specific sprint work.
- Coordinate contributors, pilot partners, and stakeholders.
- Track progress toward MVP and beyond.

Summary timeline (recommended)
- Kickoff: Week 0 (planning) starting 2025-10-20
- MVP (Quick-mode agent + scoring + report outputs): Weeks 1–6 (2 sprints)
- Core infra (report PDF, schema, viewer, basic backend opt-in): Weeks 7–12 (2 sprints)
- Full-mode & bootable image, QA, pilot: Weeks 13–18 (2 sprints)
- Pilot iteration, stabilization, release v1.0: Weeks 19–22 (1–2 sprints)
- Post-launch improvements & v2 planning: ongoing

If you prefer 2-week sprints, the 16-week detailed plan below covers ~8 sprints plus pilot/launch tasks. Dates below assume an immediate start on Monday 2025-10-20; adjust to your calendar.

---

Contents
1. Phases & schedule (high-level)
2. Sprint-by-sprint plan (detailed tasks & acceptance criteria)
3. Milestones & deliverables
4. Roles & staffing recommendations
5. CI/CD, QA, and testing strategy
6. Reporting, monitoring & KPIs
7. Pilot program & launch playbook
8. Risk register & mitigations
9. Governance, legal & compliance tasks
10. Backlog & issue hygiene guidance
11. Post-launch roadmap ideas & prioritization
12. How to use this roadmap (operational checklist)

---

1) PHASES & SCHEDULE (high-level)
- Phase 0 — Discovery & scaffold (DONE/Week 0)
  - Repo scaffold, docs (README, LICENSE, CONTRIBUTING, SECURITY), JSON schema stub, samples.
- Phase 1 — MVP Quick-mode Agent (Weeks 1–6)
  - Linux-first CLI agent delivering inventory, SMART parse, battery, CPU/disk quick bench, memtester short, sensors snapshot, report.json and report.pdf, scoring engine.
- Phase 2 — Report/Viewer/Optional Backend (Weeks 7–12)
  - PDF generator, static web viewer for local report.json, optional upload API & storage (opt-in), authentication for uploads.
- Phase 3 — Full-mode & Bootable Image (Weeks 13–18)
  - Bootable live-USB build scripts, MemTest86 integration guidance or open memtester boot flow, long stress tests orchestration, signed evidence bundle.
- Phase 4 — Pilot & Release (Weeks 19–22)
  - Pilot testing with shops/repairers, bugfixes, docs polish, v1.0 release.
- Phase 5 — v2+ (ongoing)
  - Windows/macOS agents, ML image analysis, warranty APIs, marketplace integrations, commercialization options.

---

2) SPRINT-BY-SPRINT PLAN (2-week sprints; dates approximate)

Sprint 0 — Discovery & infra (2025-10-20 → 2025-11-02) ✅ **COMPLETE**
Goal: repo scaffolding, governance, and choice of tech stack so devs can start coding.

**Status:** ✅ 100% Complete (2025-10-28)

Tasks
- ✅ Finalize language/runtime (Python 3.11 for agent)
- ✅ Create repo skeleton: /agent, /bootable, /server, /web, /docs, /samples, .github workflows
- ✅ Publish key docs: README, LICENSE.txt, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, PROJECT_GOAL.md, ROADMAP.md
- ✅ Set up GitHub Project board, issue templates, PR templates
- ✅ Define minimal CI matrix (Linux runner) and basic linting rules

Acceptance criteria
- ✅ Repo exists with required docs and templates.
- ✅ CI skeleton exists (lint job) and passes on main branch.
- ✅ Project board has prioritized epic cards for Phase 1.

Sprint 1 — Agent skeleton + Inventory & SMART (2025-11-03 → 2025-11-16) 🟡 **IN PROGRESS**
Goal: Basic agent CLI that detects system and runs smartctl to produce structured SMART JSON entry in report.json.

**Status:** 🟡 ~30% Complete (2025-10-28)  
**What's Done:** CLI skeleton, basic SMART parser, report.json generation, 6 tests passing  
**In Progress:** Real smartctl execution, inventory plugin  
**Blockers:** Need focused development time

Tasks
- ✅ Implement CLI skeleton: `inspecta` with `run --mode quick` and `inventory` subcommand
- 🟡 Implement inventory plugin (dmidecode/system_profiler/PowerShell placeholder) — **IN PROGRESS**
- 🟡 Add smartctl wrapper integration (use smartctl --json format) and parser module — **Partial: Parser done, execution needed**
- ✅ Create basic report.json composer & sample output
- 🟡 Unit tests for parsing logic — **Partial: 6 tests, need more**
- ✅ CI: run unit tests on Linux; package smartctl presence check

Acceptance criteria
- 🟡 `inspecta inventory` outputs device JSON (vendor, model, serial, bios) — **Needs implementation**
- 🟡 `inspecta run --mode quick` invokes smartctl (if available) and writes artifacts/smartctl.json and minimal report.json — **Works with sample data, needs real execution**
- ✅ Unit tests pass in CI — **6 tests passing**

**Next Actions:** See [NEXT_STEPS.md](NEXT_STEPS.md) Priority 1-3 for detailed implementation tasks.

Sprint 2 — Disk perf, battery, CPU quick bench, scoring (2025-11-17 → 2025-11-30) 🔴 **NOT STARTED**
Goal: Basic agent CLI that detects system and runs smartctl to produce structured SMART JSON entry in report.json.

Tasks
- Implement CLI skeleton: `inspecta` with `run --mode quick` and `inventory` subcommand
- Implement inventory plugin (dmidecode/system_profiler/PowerShell placeholder)
- Add smartctl wrapper integration (use smartctl --json format) and parser module
- Create basic report.json composer & sample output
- Unit tests for parsing logic
- CI: run unit tests on Linux; package smartctl presence check

Acceptance criteria
- `inspecta inventory` outputs device JSON (vendor, model, serial, bios)
- `inspecta run --mode quick` invokes smartctl (if available) and writes artifacts/smartctl.json and minimal report.json
- Unit tests pass in CI

Sprint 2 — Disk perf, battery, CPU quick bench, scoring (2025-11-17 → 2025-11-30)
Goal: Add quick disk performance sample, battery parsing, CPU quick benchmark, and implement scoring engine for core categories.

Tasks
- Add disk sample wrapper (fio quick job or dd fallback)
- Add battery health parser (powercfg report parsing & upower/system_profiler support)
- Integrate CPU quick benchmark (sysbench or microbenchmark)
- Implement scoring functions and weight config; add profile presets (Office, Developer, Creator, Gamer, Server)
- Implement JSON scores in report.json and simple human summary line
- Tests for scoring mapping and metric normalization

Acceptance criteria
- `inspecta run --mode quick` returns report.json with scores and a recommendation string
- Score reproducible and unit-tested against mocked inputs
- Benchmarks sample included in artifacts and referenced in JSON

Sprint 3 — Memtester quick-mode, sensors snapshot, thermal smoke (2025-12-01 → 2025-12-14)
Goal: Memory quick smoke test, sensors snapshot, short thermal stress and throttle detection.

Tasks
- Add memtester wrapper for in-OS short runs (30s–60s) and memtest bootable plan doc
- Integrate lm-sensors parsing / OpenHardwareMonitor integration (Windows plan) for temps & fans
- Implement short stress test (stress-ng or sysbench CPU load) with sampling of CPU frequency and temps
- Update scoring with thermal results and memtest flags
- Add artifact logs to artifacts/ and include in report.json

Acceptance criteria
- Memtester short run completes and produces memtest log recorded in artifacts
- Thermal sampling shows baseline & stress peak in sensors CSV and included in JSON
- Throttling detection logic triggers WARN/FAIL appropriately and recorded

Sprint 4 — Report PDF generation & schema, static viewer (2025-12-15 → 2026-01-04)
Goal: Produce a human-friendly PDF, finalize JSON schema and implement a simple static web viewer for local report display.

Tasks
- Finalize JSON Schema (report-schema.json) and tests for schema validation
- Implement PDF report generator (Puppeteer/wkhtmltopdf or Python WeasyPrint) with templating
- Create a minimal React static viewer that reads local report.json and displays summary and raw logs
- Add `inspecta report --open` to launch viewer against local report
- Add sample report artifacts and screenshots for viewer demo

Acceptance criteria
- report.json validates against schema
- report.pdf generated from sample report.json matches template and includes evidence thumbnails
- Local viewer opens and renders report.json correctly

Sprint 5 — Backend API (opt-in) & upload flow (2026-01-05 → 2026-01-18)
Goal: Build minimal secure upload API with opt-in behavior; artifact storage to S3-compatible store.

Tasks
- Implement server skeleton (Node/Express or Python/Flask/FastAPI) with POST /reports for authenticated upload
- Implement token-based auth for upload (short-lived tokens)
- Store artifacts in S3 (or local file store for dev)
- Implement basic report retrieval endpoint GET /reports/{id} and GET /reports/{id}/pdf
- Implement server-side virus/malware scan policy for uploaded content (optional step)
- Update agent with `--upload` flow that only proceeds with explicit user consent

Acceptance criteria
- Agent can `inspecta run --mode quick --upload https://... --token <token>` and server accepts and stores artifacts, returns report ID and link
- Server has basic ACL and retention policy config
- Security: uploads accepted only via token; HTTPS required

Sprint 6 — Bootable image builder + memtest integration (2026-01-19 → 2026-02-01)
Goal: Provide reproducible scripts to build a bootable diagnostic image that includes memtest and core tools.

Tasks
- Choose base distro (Alpine minimal or Ubuntu minimal) and create builder scripts (Packer or simple bash/guestfish)
- Include smartmontools, fio, stress-ng, memtest86 or memtest86+ (or document licensing steps)
- Provide USB write instructions and quick boot checklist for technicians
- Add mechanism to generate signed artifact manifest from live-USB runs (timestamp, sha256, agent version)
- Document memtest full-run workflow and how to attach memtest logs to report.json

Acceptance criteria
- `tools/build-live-iso.sh` produces a bootable ISO that boots to a shell with tools present
- Bootable image integrates MemTest or provides clear steps to run MemTest86 and collect logs
- Documented process to collect and import memtest logs into report.json

Sprint 7 — QA & pilot recruitment (2026-02-02 → 2026-02-15)
Goal: Prepare pilot program, automated tests, and CI e2e for quick-mode; recruit pilot partners.

Tasks
- Implement CI e2e for quick-mode on Ubuntu runner (mock tools where necessary)
- Create test matrix and run smoke tests across simulated configs (mock smartctl output)
- Draft pilot onboarding doc and test kit checklist for pilot participants
- Identify 10 pilot devices or partners (local repair shops, friends, community) and agree on runs, data sharing, and NDAs if needed

Acceptance criteria
- CI passes unit and integration tests
- Pilot guide complete and pilot partners recruited or listed
- Pilot consent form + data handling agreements drafted

Sprint 8 — Pilot execution, feedback & v1 stabilization (2026-02-16 → 2026-03-01)
Goal: Run pilot, collect feedback, close critical bugs, prepare for v1.0 release.

Tasks
- Run quick-mode on pilot devices, collect report.json and artifacts
- Triage feedback, fix high/critical bugs and scoring anomalies
- Update docs based on pilot results
- Finalize release candidate and prepare release notes and changelog

Acceptance criteria
- Pilot run success rate metric captured and >= threshold (target 80–90% for first pilot)
- Identified critical problems fixed and regression tests added
- Release candidate prepared and tagged

Release v1.0 — Publish & announce (2026-03-02 → 2026-03-08)
Goal: Release v1.0 with source, signed artifacts, sample reports, and pilot case studies.

Tasks
- Tag v1.0, publish release assets (source tarball, ISO builder scripts)
- Publish signed checksums and instructions to verify
- Blog post and release notes describing limitations & next steps
- Outreach: invite community testers and document how to contribute

Acceptance criteria
- v1.0 published with signed artifacts and release notes
- At least one public pilot case study or sample report published
- Roadmap for v1.1 outlined (post-launch improvements)

---

3) MILESTONES & DELIVERABLES (concise)
- M0: Repo scaffold and docs (README, LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT) — DONE
- M1: Agent skeleton + SMART + inventory + sample report — Sprint 1 completion
- M2: Quick-mode features + scoring + sample PDF — Sprint 2–4 completion
- M3: Viewer + optional server upload — Sprint 4–5 completion
- M4: Bootable ISO builder + memtest integration — Sprint 6 completion
- M5: Pilot complete and v1.0 release — Sprint 8 & Release

---

4) ROLES & STAFFING (recommended)
- Product Lead / PM (1): prioritization, pilot coordination, docs editorial
- Tech Lead / Architect (1): system design, CI, security sign-off
- Agent Developers (2): Python + packaging + native tool integrations
- Backend/API Developer (1): upload API, storage, basic auth
- Frontend/Viewer (1): React static viewer, UX
- QA / Test Engineer (1): CI, tests, pilot coordination
- DevOps / Build (1): ISO builder, CI/CD, release packaging
- Designer (part-time): PDF template and UX for viewer
- Legal / Privacy Advisor (consultant): license and data policy review
- Community Manager (part-time): pilot onboarding & communications

Small teams can multi-role; if contributors are limited, prioritize Agent + QA + PM.

---

5) CI / CD, QA, and TESTING STRATEGY
CI (GitHub Actions)
- Lint & static analysis on PRs
- Unit tests (fast) — run on each PR
- Integration tests (slow) — scheduled nightly or run on-demand
- Build artifacts job — package source dist, build ISO (on schedule)
- Release pipeline — sign artifacts, publish GitHub Release

Security & SCA
- Dependabot or equivalent for dependency alerts
- Secret scanning in repo & pre-commit detect-secrets
- SAST tools (bandit / ruff / mypy) included in CI

QA
- Unit coverage target: >= 65% at v1 but aim for higher
- End-to-end manual test checklist for pilot (shared as runbook)
- Regression tests for parsers and scoring engine

Pre-merge gates
- At least one approving review
- Passing unit tests & linters
- No secrets in PR

---

6) REPORTING, MONITORING & KPIs
Track the following metrics in backlog and dashboards:
- Quick-mode run success rate (per model and overall)
- Median quick-mode runtime (target ≤ 10 min)
- Pilot satisfaction (NPS)
- Number of signed reports generated
- CI pass rate & PR review time (median)
- Security triage time and patch lead time for critical issues

Reporting cadence
- Weekly sprint status updates: completed items, blocked items, pilot metrics
- Monthly metrics report: KPIs + community contributions + issues closed

---

7) PILOT PROGRAM & LAUNCH PLAYBOOK
Pilot objectives
- Validate agent on real devices
- Validate scoring thresholds and buyer mapping
- Validate PDF format & evidence usability for buyers
- Collect usability feedback and edge-case failures

Pilot recruitment
- Invite 5–10 refurbishers/shops and 10–20 individual volunteers
- Prepare pilot kit: checklists, expected outputs, consent and PII handling forms, contact for security

Pilot runbook
- Distribute agent & checklist
- Have participants run a predefined quick-mode command and upload report only if they consent
- Collect reports and annotate device metadata
- Run follow-up interviews and log issues

Launch playbook
- Finalize release notes, blog, social media post
- Provide quickstart guide and recorded demo
- Outreach to communities (r/hardware, refurbishers, local electronics markets)

---

8) RISK REGISTER & MITIGATIONS
Risk: Hardware heterogeneity causes test failures
- Mitigation: Quick-mode with graceful degradation; robust error handling & clear messaging; collect error telemetry (opt-in)

Risk: Sensitive data in artifacts
- Mitigation: Default to local storage; redact guidance & warnings; pre-upload redaction step; encrypted uploads

Risk: License choice reduces adoption
- Mitigation: Keep option to offer commercial licensing; clearly document process to request permissions

Risk: Tampering and seller fraud (faked logs)
- Mitigation: Evidence signing, video capture during stress tests, timestamped logs, bootable image option

Risk: Legal claims from report misinterpretation
- Mitigation: Strong disclaimers, "not a warranty" language, pilot terms & liability limits in LICENSE

---

9) GOVERNANCE, LEGAL & COMPLIANCE TASKS
- Maintain LICENSE.txt (custom non-commercial) and explain in README and CONTRIBUTING
- Provide a commercial licensing contact method and template for commercial requests
- Prepare data processing guidance for pilot partners (GDPR notes)
- Implement a CLA or contributor terms if required by maintainers (decide early)

---

10) BACKLOG & ISSUE HYGIENE GUIDANCE
Backlog prioritization
- P0: MVP features required for quick-mode & report.json
- P1: PDF generator, viewer, upload API
- P2: Bootable ISO scripts & memtest full flow
- P3: Windows/macOS agents, advanced features

Issue labels & templates
- Use `good first issue`, `help wanted`, `bug`, `enhancement`, `rfc`, `security`, `priority:high/medium/low`
- Maintain grooming cadence: triage weekly and assign owners
- Link issues to sprint cards on project board

Example initial issues to create now
- Agent: CLI skeleton and run command
- SMART: parse JSON and map key attributes
- Scoring: implement storage/battery/memory scoring functions with unit tests
- PDF: initial template and generator skeleton
- Bootable: write ISO builder script skeleton

---

11) POST-LAUNCH & v2 PRIORITIES (high-value ideas)
- Signed report verification tool and public key registry for marketplaces
- Windows native sensor integrations (HWiNFO / OpenHardwareMonitor)
- Model DB for expected perf baselines and auto-tuning of thresholds
- Repair cost estimator and integration with repair shops
- Image-based surface analysis (ML-assisted detection of screen cracks/scratches)
- Marketplace badges & SDK for third-party integrations (commercial option)

Prioritization criteria for v2
- Impact on buyer confidence
- Implementation complexity and risk
- Legal and privacy implications
- Potential revenue/partnership paths (for future commercialization)

---

12) HOW TO USE THIS ROADMAP (operational checklist)
- Create Sprint cards for each sprint task and assign owners + estimates.
- Create issues using the example list; break features into small PR-sized tasks.
- Enforce PR review rules and CI gates.
- Run pilot with tracked metrics and log results into an artifacts folder for retrospective.
- Review risks at each sprint retro and adjust priorities.

---

Appendix: Sprint checklist (per sprint)
- [ ] Create issues for sprint tasks, estimate story points
- [ ] Assign owners and reviewers
- [ ] Implement feature with tests & docs
- [ ] Open PR(s) with description, test steps, and CI passing
- [ ] Reviewer approves and merges
- [ ] Update project board and release notes draft
- [ ] Run smoke e2e and capture evidence

---

This roadmap is a living document. As we run sprints and receive pilot feedback, update this file with new dates, scope changes, and decisions. Use the GitHub Project board to reflect sprint status and link issues/PRs to the milestones and cards defined above.
