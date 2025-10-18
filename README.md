# device-inspector (inspecta)

Device Inspector — "inspecta" — is a local-first automated diagnostic tool for used laptops and PCs.  
This repository contains project documentation and initial artifacts. The code/agent will be added later. For now the repository is public and governed by a custom non-commercial license (see LICENSE.txt).

Short description
- Purpose: Let buyers, sellers, and technicians run automated diagnostics (SMART, quick CPU/disk benchmarks, battery health, memory smoke tests, sensor snapshot) and produce an auditable report (report.json + report.pdf).
- Mode: Local-first; quick-mode (2–10 min) and full-mode (opt-in, bootable memtest + long stress).
- Output: machine-readable JSON report + human-ready PDF summary + raw artifacts.

Repository status
- Stage: Documentation & project scaffolding only.
- Next: add an agent (Linux-first quick-mode), scoring engine, PDF generator, and bootable ISO scripts.

Quick links
- Project goal: PROJECT_GOAL.md
- Roadmap: ROADMAP.md
- Features (automated tests): FEATURES.md
- Report JSON schema: REPORT_SCHEMA.md
- License: LICENSE.txt

How to get started (local)
1. Create a repo named `device-inspector` (or import this repo's files).
2. Use the starter scaffold (to be added) or implement your agent according to FEATURES.md and REPORT_SCHEMA.md.

Contact
- Owner: mufthakherul
