# Project Goal — device-inspector (inspecta)

Last updated: 2025-10-18

This document defines the mission, vision, scope, objectives, acceptance criteria, success metrics, constraints, non-goals, stakeholders, assumptions, risks, and high-level architecture for the device-inspector (inspecta) project. It is intended to be definitive guidance for contributors, maintainers, pilot partners, and early adopters during the design and implementation phases.

Table of contents
- Mission & vision
- Problem statement
- Target users & personas
- Primary objectives (SMART)
- Scope (in-scope / out-of-scope)
- Success criteria & acceptance criteria
- Key features (MVP and beyond)
- Non-goals & constraints
- High-level architecture
- Data model & artifacts
- Scoring model (summary)
- Auditability, privacy & security requirements
- Operational model & deployment considerations
- Quality, testing & validation plans
- Governance, contribution, and licensing
- Risks, mitigations & open issues
- Roadmap summary & milestones
- KPIs & metrics
- Deliverables (by phase)
- Appendix: links to related docs

---

Mission & vision
- Mission: Provide buyers, sellers, and technicians with a fast, trustworthy, privacy-first automated inspection tool that produces auditable evidence and clear recommendations for pre-purchase decisions on used laptops and PCs.
- Vision: Become the community-standard inspection toolkit ("inspecta") for pre-purchase device verification — an open, transparent, locally-executable diagnostic agent and evidence format trusted by individuals, refurbishers, and marketplaces.

Problem statement
Buying used laptops/PCs is risky: storage failure, battery wear, thermal issues, or hidden firmware/activation locks can cause buyers to pay for poor hardware. Existing open-source tools address individual tests (SMART, memtest, sensors) but there is no widely used, end-to-end, buyer-centric, auditable inspection tool that:
- orchestrates relevant automated checks,
- produces a canonical, machine-readable report and a clear human summary,
- provides tamper-evidence and privacy controls,
- is easy to run locally (quick checks) or as a full bootable diagnostic (deep checks).

This project closes that gap.

---

Target users & personas
- Individual buyer (Budget-conscious): needs a 5–10 minute check before buying from a listing.
- In-person buyer: wants to run quick checks in seller’s presence and get an evidence bundle.
- Remote buyer/verifier: requests seller-run test outputs and an auditable signed report.
- Technician / Refurbisher: runs full-mode diagnostics and repair estimates.
- Marketplace operator (pilot partner, opt-in): integrates verification badges (optional) and wants signed evidence for disputes.
- Small shop operator: uses the bootable mode for bulk evaluation and inventory.

---

Primary objectives (SMART)
1. Ship an MVP quick-mode agent (Linux-first) that:
   - runs inventory, SMART read, battery report, quick CPU/disk smoke, 30s memtester run, sensors snapshot,
   - produces report.json + report.pdf + artifacts,
   - completes reliably in ≤ 10 minutes on 90% of tested devices.
2. Provide a deterministic scoring engine (documented weights) and "who should buy" mapping for four buyer profiles.
3. Implement local-first behavior by default; optional authenticated upload is opt-in.
4. Offer a bootable live-USB builder script for full-mode memtest integration and extended stress tests in the next release cycle.
5. Ensure evidence integrity with SHA256 artifact bundles and optional client-side signing.

Objectives are measurable (test-run success rate, run-time targets, schema conformance, pilot satisfaction).

---

Scope

In-scope (first 2–4 releases)
- Quick-mode agent (Linux-first) CLI: inventory, SMART, battery, CPU/disk quick bench, memtester short run, sensors snapshot.
- Core report outputs: canonical JSON schema, PDF summary generator.
- Deterministic scoring engine and profile mapping for "Best for".
- Local artifact bundling with checksums and an option to sign.
- Documentation, README, CONTRIBUTING, SECURITY, LICENSE (non-commercial).
- Bootable ISO builder scripts (basic) to create a diagnostic live-USB image (Phase 2 deliverable).
- Pilot onboarding docs for testers/refurbishers.

Out-of-scope (initially)
- Full Windows/macOS native agent parity (best-effort later).
- Marketplace escrow, payment, or enforced reputation systems.
- Commercial SaaS hosting of reports by project (third-party services may implement).
- Automated image-based physical-damage detection (ML) in MVP (future enhancement).
- Legal guarantees of device condition or warranties (the product is diagnostic evidence only).

---

Success criteria & acceptance criteria

MVP acceptance criteria
- The quick-mode CLI runs on a supported Linux environment and produces:
  - report.json that validates against REPORT_SCHEMA.md.
  - report.pdf summarizing results and linking to artifacts.
  - artifacts/ folder with smartctl output, memtester log, sensor snapshot.
- The average execution time for Quick Mode is ≤ 10 minutes across a test matrix of 20 representative devices (various ages/models).
- The scoring engine produces an overall_score between 0–100 and a human-readable recommendation string for each buyer profile.
- All tests run in quick-mode are non-destructive (no forced disk writes that modify user data).
- Documentation includes install & run steps, privacy guidance, and limitation disclaimers.
- CI includes unit tests for parsers and scoring logic and runs on Linux.

Operational acceptance criteria
- Pilot with at least 10 devices testing the tool on different vendors/models with collected feedback and a triaged issue list.
- Security policy published and initial vulnerability-handling flow tested.

---

Key features (MVP and beyond)

MVP (core)
- Local CLI agent (inspecta) with `run --mode quick`.
- Inventory and system identification (vendor, model, serial, BIOS).
- SMART (smartctl) analyzer & health parsing.
- Battery health & cycle count parsing (for laptops).
- Quick CPU benchmark and short thermal sampling.
- Quick disk sample (fio/dd heuristics).
- Memory smoke test (memtester short run).
- Sensors snapshot (lm-sensors).
- Deterministic scoring engine and buyer-profile mapping.
- Report outputs: report.json, report.pdf, artifacts/ and checksums.

Phase 2 (enhancements)
- Bootable live-USB build script + integrated MemTest86 or open-source memtest.
- Longer stress tests, quick GPU smoke test, camera/audio sample capture for evidence.
- Optional signed reports (client keypair + verification tool).
- Web-based report viewer (static site) for local use and optional upload.
- Model DB for expected performance baselines (optional).

Phase 3 (advanced)
- Image analysis for screen/crack detection (ML assist).
- Manufacturer warranty check integration (via APIs).
- Marketplace integration & verified-badge program (opt-in).
- Commercial licensing product & repair-estimate integration (author-controlled).

---

Non-goals & constraints
- The agent will not attempt to repair devices.
- The agent will not attempt to bypass activation/firmware locks.
- The agent will not automatically collect or upload user personal data without clear consent.
- Project is initially licensed for non-commercial use per LICENSE.txt; this limits adoption and contributions from some organizations.

---

High-level architecture (planned)

1. Agent (local)
   - Language: Python (initial scaffold) — CLI executable `inspecta`.
   - Responsibilities: orchestration, calling native tools (smartctl, fio, memtester), collecting logs, packaging artifacts, computing scores, generating JSON+PDF.

2. Scoring engine
   - Deterministic, auditable rules (Python module).
   - Configurable weights and buyer profiles.
   - Unit-tested mapping of metrics → subscore → overall score.

3. Report generator
   - Produces canonical `report.json` (schema) and `report.pdf` (summarized visuals).
   - PDF generator using serverless-friendly tools (wkhtmltopdf / Puppeteer or Python PDF libs).

4. Bootable builder (optional)
   - Scripts to build a minimal live-USB image with included tools for full-mode tests.

5. Optional backend (opt-in)
   - Simple API to accept uploads (auth token), store artifacts (S3), and provide shareable links.
   - NOT part of the MVP; opt-in by deployments.

6. Evidence & signing
   - Local artifact bundling + SHA256 manifest.
   - Optional client-signed report package with public key embedded in JSON for verification.

---

Data model & artifacts (summary)
- Device: vendor, model, serial, bios_version, sku
- Tests: timestamped entries for each test (smartctl, memtest, cpu_bench, disk_bench, sensors)
- Scores: per-category (storage, battery, memory, cpu_thermal, gpu, network, security) + overall_score
- Artifacts: raw logs (smartctl.txt, memtest.log, sensors.csv), media (camera.jpg, audio.wav), PDF
- report.json: canonical machine-readable artifact; sample included in /samples

All raw artifacts MUST be treated as potentially containing PII. The default is to store them locally only.

---

Scoring model (summary)
- Weighted categories (example):
  - Storage health & performance: 22%
  - Battery & power: 15%
  - Memory: 12%
  - CPU performance & thermal: 15%
  - Screen & physical (automated checks limited): 10%
  - Ports & peripherals: 8%
  - Network: 6%
  - Security & firmware: 6%
- Score mapping: 0–100 aggregated score, grade bands:
  - 90–100: Excellent
  - 75–89: Good
  - 50–74: Fair (repairs recommended)
  - <50: Poor (avoid)
- All thresholds, heuristics, and mappings MUST be documented and auditable in code.

---

Auditability, privacy & security requirements

Auditability
- Each report must include:
  - test timestamps, tool versions, and raw logs
  - SHA256 manifest of artifacts
  - agent version and optional client public key signature (if signing used)

Privacy
- Local-first by default. Uploading reports is explicitly opt-in and must be authorized by the local user.
- Provide clear guidance to users to remove personal files and avoid uploading PII-containing artifacts.
- For any optional cloud storage, encrypt artifacts at rest and in transit (TLS+server-side encryption or client-side encryption).

Security
- Hardening: minimal privilege principle for agent operations; where root is required, warn users and document why.
- Secret scanning in CI and pre-commit to prevent accidental key leaks.
- Publish SECURITY.md and a vulnerability disclosure process (done).

Compliance considerations
- Include a data handling section for GDPR/CCPA guidance in docs.
- Make data retention settings configurable if the optional backend is implemented.

---

Operational model & deployment considerations
- Local CLI agent distribution via GitHub releases (source and optionally packaged binaries).
- Bootable ISOs produced by script and signed for reproducibility.
- Optional backend is self-hosted by organizations (we will provide sample deployment manifests).
- CI pipelines: unit tests, parsing tests, scoring tests, packaging. Use GitHub Actions for Linux-based tests and artifact builds.

---

Quality, testing & validation plans
- Unit tests for parsers (smartctl JSON), scoring functions, report schema validation.
- Integration tests that simulate tool outputs (mock smartctl, memtester logs) to validate end-to-end JSON generation.
- e2e tests on physical hardware (pilot) by maintainers/partners.
- Performance tests: measure average runtime across a device matrix.
- Acceptance tests: run the full quick-mode on at least 20 devices representing real-world variations.

---

Governance, contribution, and licensing
- Project owner: @mufthakherul — retains final decisions, commercial/licensing rights, and governance control.
- Contributions accepted following CONTRIBUTING.md and subject to LICENSE.txt (custom non-commercial terms).
- Maintain transparency in decision-making and document major governance changes in repo.

---

Risks, mitigations & open issues

Risk: False negatives/positives in automated checks
- Mitigation: include raw logs and human-readable guidance; emphasize limitations in README and PDF.

Risk: Platform fragmentation (Windows/macOS sensors)
- Mitigation: Linux-first, provide optional Windows/macOS wrappers later; strongly recommend live-USB for final verification.

Risk: Legal exposure from report claims (user relies on report and suffers loss)
- Mitigation: legal disclaimers in README and PDF; reports are evidence, not a warranty.

Risk: License choice limits adoption
- Mitigation: keep dual-licensing option for the author; provide clear path to request commercial license.

Open issues (to resolve during planning)
- Exact weightings for scoring and per-model baselines (need research and pilot tuning).
- Signing model for optional tamper-proof evidence (key management & verification UX).
- Acceptable default behavior for handling potential personal data in artifacts.

---

Roadmap summary & milestones
(Condensed — see ROADMAP.md for sprint-level details)
- Phase 0: Docs, schema, repo scaffold (complete)
- Phase 1 (MVP): Quick-mode Linux agent + scoring + report generation + sample report (target weeks 1–6)
- Phase 2: PDF improvements, viewer, optional backend upload API, and bootable live-USB scripts (weeks 7–12)
- Phase 3: Pilot program, hardening, Windows/macOS agent expansion, marketplace integrations (months 4–6)

---

KPIs & metrics (examples to track success)
- Tool run success rate across device matrix (target ≥ 90% for quick-mode)
- Average quick-mode runtime (target ≤ 10 minutes)
- Number of reports generated during pilot
- Pilot participant satisfaction (NPS)
- Number of reproducible bugs per 100 runs
- Number of unique contributions and PR turnaround time
- Security response time and patching time for critical issues

---

Deliverables (by phase)

Phase 0 — Documentation & scaffold
- README, LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, PROJECT_GOAL, ROADMAP (done)

Phase 1 — MVP quick-mode
- inspecta CLI (Linux)
- report.json schema & pdf template
- scoring engine & unit tests
- sample reports + artifact samples
- CI for unit tests & linters
- pilot onboarding guide

Phase 2 — enhancements
- Bootable ISO builder + MemTest integration
- PDF generator improvements and report viewer
- Optional upload API & storage integration (opt-in)
- Signed releases & reproducible builds

Phase 3 — production / expansion
- Windows/macOS agents (best-effort)
- Model performance DB & repair-cost heuristics
- Marketplace badge & verified program (opt-in, commercial collaboration)

---

Appendix: links to related docs
- ROADMAP.md
- FEATURES.md
- REPORT_SCHEMA.md
- README.md
- SECURITY.md
- CONTRIBUTING.md
- LICENSE.txt

---

Contact & stewarding
- Project owner / primary maintainer: @mufthakherul (GitHub)
- Security contact: see SECURITY.md

---

Change log
- 2025-10-18: Initial comprehensive PROJECT_GOAL.md created.
