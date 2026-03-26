# device-inspector (inspecta)

[![CI](https://github.com/mufthakherul/device-inspector/workflows/CI/badge.svg)](https://github.com/mufthakherul/device-inspector/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: Custom](https://img.shields.io/badge/License-Custom%20Non--Commercial-orange.svg)](LICENSE.txt)

Local-first automated diagnostics for used laptops & PCs — quick-mode audits, auditable JSON+PDF reports, and optional bootable full diagnostics. Public, non-commercial use; © 2025 mufthakherul

**Status:** 🟢 **Active Development** — Phase 1 MVP Sprint 1 Complete (~60% complete)  
**Current Version:** 0.1.0  
**Last Updated:** 2025-10-30

> **📊 Project Status:** Sprint 1 COMPLETE! Inventory detection, real SMART execution, and structured logging fully implemented. 22 tests passing with CI/CD. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed progress and [NEXT_STEPS.md](NEXT_STEPS.md) for Sprint 2 priorities.

---

## Table of Contents

- 🎯 [Current Implementation Status](#current-implementation-status)
- [Overview](#overview)
- [Key Features](#key-features-mvp-focus)
- [Quick Facts](#quick-facts)
- [Installation](#installation-prep)
- [Quickstart](#quickstart-run-a-quick-mode-check)
- [CLI Usage](#cli-usage-examples)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license--legal-notes)

## Documentation

### For End Users
- 📦 **[Distribution Guide](docs/DISTRIBUTION.md)** - Download and use standalone executables (v1)
- 🚀 **Quick Start** - See download links in [Releases](https://github.com/mufthakherul/device-inspector/releases)

### For Developers
- 📖 **[Developer Setup Guide](docs/DEV_SETUP.md)** - Complete setup instructions for contributors
- 🏗️ **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical architecture and design decisions
- 🔨 **[Building Guide](docs/BUILDING.md)** - How to build standalone executables
- 🤖 **[AI & Developer Guide](docs/AI_AGENT_GUIDE.md)** - Guardrails for human and AI collaborators
- 📋 **[Project Status](PROJECT_STATUS.md)** - Detailed implementation progress
- 🚀 **[Next Steps](NEXT_STEPS.md)** - Prioritized action items for Sprint 2
- 🗺️ **[Roadmap](ROADMAP.md)** - Sprint-by-sprint implementation plan
- 🎯 **[Features](FEATURES.md)** - Complete feature specifications
- 🤝 **[Contributing](CONTRIBUTING.md)** - Contribution guidelines and workflow
- 🔒 **[Security](SECURITY.md)** - Security policy and vulnerability reporting

---

## 🎯 Current Implementation Status

**Phase:** Phase 1 — MVP Quick-mode Agent (Sprint 1 COMPLETE ✅)  
**Completion:** ~60% of MVP functionality implemented  

### ✅ What's Working Now (Sprint 1 Complete)

- **Agent CLI** — Full `inspecta run --mode quick` with real hardware detection
- **Inventory Detection** — ✅ dmidecode integration (vendor, model, serial, BIOS)
- **SMART Execution** — ✅ Real smartctl execution on SATA/NVMe drives
- **Device Detection** — ✅ Automatic storage device scanning (/sys/block)
- **Multi-Drive Support** — ✅ Handles multiple storage devices (SATA, NVMe, USB)
- **Error Handling** — ✅ Comprehensive error messages with installation hints
- **Structured Logging** — ✅ Detailed logs to artifacts/agent.log
- **Report Generation** — ✅ Creates report.json with real device data
- **Human-Readable Reports** — ✅ TXT and PDF reports with auto-open functionality
- **Testing** — ✅ 29 unit tests passing (was 22), CI pipeline active
- **Documentation** — ✅ Comprehensive specs, roadmap, and contributing guides
- **Sample Data** — ✅ dmidecode, smartctl (healthy/failing SATA, NVMe)

### 🚧 In Development (Sprint 2 - Next)

- **Complete Schema** — Full REPORT_SCHEMA.md implementation with validation
- **Coverage Reporting** — pytest-cov integration for 60%+ coverage
- **Disk Performance** — fio integration for read/write benchmarks
- **Battery Health** — upower/powercfg integration
- **CPU Benchmarking** — sysbench integration

### 📋 Coming Later (Sprint 2-3)

- Memory testing (memtester)
- Thermal monitoring (lm-sensors)
- Profile-based scoring (Office, Developer, Gamer, etc.)

**See [PROJECT_STATUS.md](PROJECT_STATUS.md) for complete progress tracking and [NEXT_STEPS.md](NEXT_STEPS.md) for upcoming priorities.**

---

Overview
Device Inspector (inspecta) is a local-first inspection toolkit to help buyers, sellers, and technicians evaluate the condition of used laptops and desktops. The final product will run automated hardware and system checks, collect verifiable artifacts (logs, SMART dumps, memtest outputs, sensors), compute transparent scores, and produce a human-friendly PDF plus a canonical machine-readable JSON report suitable for sharing as inspection evidence.

Key features (MVP focus)
- Inventory: vendor, model, serial, BIOS/UEFI
- Storage: SMART health parsing and quick read/write samples
- Battery: design vs current capacity, cycle count (laptops)
- Memory: quick in-OS smoke test (memtester) and bootable MemTest option (Full mode)
- CPU: quick benchmark and short thermal smoke test
- Sensors: snapshot of CPU/GPU temps and fan speeds
- Peripherals: basic enumeration (USB, GPU, network)
- Outputs: canonical report.json, human-friendly report.pdf, artifacts/ bundle
- Scoring engine: deterministic, auditable weighting and category scores
- Local-first by default — uploads are optional and require explicit consent
- Anti-tamper evidence (planned): SHA256 bundles, timestamps, optional signed reports

Quick facts
- Repo name: device-inspector
- Product alias: inspecta
- Priority platform: Linux-first (live-USB option for full tests)
- License: Custom non-commercial (see LICENSE.txt). Author retains right to relicense.

Project goals
- Give buyers fast, reliable, and auditable diagnostics before purchase
- Produce evidence-backed reports that support negotiation and dispute resolution
- Be transparent and reproducible (include raw logs for every numeric result)
- Start with a compact quick-mode that runs in minutes and an opt-in full-mode for technicians

Prerequisites (what your machine needs to run quick tests)
- Linux (recommended for full reliability). Quick-mode aims to be cross-platform later.
- Root / sudo for some checks (SMART, sensors, memtester)
- Tools (installable via package manager):
  - smartctl (smartmontools)
  - fio (or dd heuristic fallback)
  - sysbench (or a small CPU microbenchmark)
  - memtester (for in-OS memory quick test)
  - lm-sensors (for sensors snapshot)
  - ffmpeg (optional — for webcam evidence)
  - python3 (for agent CLI and report generation)
- NOTE: full MemTest requires booting from USB (MemTest86 or MemTest86+)

## Installation Options

### Option 1: Standalone Executables (Recommended for End Users) 🎯

**No Python or dependencies required!** Download pre-built executables for Windows or macOS:

1. **Download** the latest release for your platform:
   - Windows: `inspecta-0.1.0-windows.zip`
   - macOS: `inspecta-0.1.0-macos.zip`
   - Linux: `inspecta-0.1.0-linux.zip`
   
   Get them from [Releases](https://github.com/mufthakherul/device-inspector/releases)

2. **Extract** the zip file to any folder

3. **Run** with a single click:
   - Windows: Double-click `Run_Inspecta.bat`
   - macOS/Linux: Run `./run_inspecta.sh`

**That's it!** No installation, no dependencies, no Python needed.

📖 **Full instructions:** See [Distribution Guide](docs/DISTRIBUTION.md)

---

### Option 2: From Source (For Developers)

This repository contains the full Python source code. To run from source:

1. Clone the repo:
   ```bash
   git clone https://github.com/mufthakherul/device-inspector.git
   cd device-inspector
   ```
2. Create a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```
3. (Optional) Install PDF report support:
   ```bash
   pip install -r requirements-optional.txt  # Adds reportlab for PDF reports
   ```
4. (Optional) Install native tools for hardware access (example for Debian/Ubuntu):
   ```bash
   sudo apt update
   sudo apt install smartmontools dmidecode fio sysbench memtester lm-sensors
   ```

📖 **Full instructions:** See [Developer Setup Guide](docs/DEV_SETUP.md)

Quickstart — what works now (v0.1.0)

> **✅ Sprint 1 Complete:** Inventory detection, SMART execution, and logging fully working. Try it with sample data (no root needed) or real hardware (requires sudo).

**Test with sample data (no root privileges required):**
```bash
# Clone and install
git clone https://github.com/mufthakherul/device-inspector.git
cd device-inspector
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run with sample data
inspecta run --mode quick --output ./reports/test-run --use-sample

# Check device inventory
inspecta inventory --use-sample

# View the generated report
cat ./reports/test-run/report.json
cat ./reports/test-run/artifacts/agent.log
```

**Run on real hardware (requires root for dmidecode/smartctl):**
```bash
# Install system tools first
sudo apt install smartmontools dmidecode

# Run inspection
sudo inspecta run --mode quick --output ./reports/my-laptop --verbose

# Or check inventory separately
sudo inspecta inventory
```

**What you get:**
- `report.json` — Device info, SMART data, scores
- `artifacts/agent.log` — Detailed execution log
- `artifacts/smart_*.json` — SMART data per storage device
- Exit code 10 (sample data) or 0 (real hardware)

- Full mode (longer, technician/better confidence, planned):
  ```bash
  inspecta run --mode full --output ./reports/device123
  # or build + boot a live-USB for MemTest86 full run
  ```

CLI usage examples (working now)
- Generate quick report with sample data (auto-opens TXT report by default):
  inspecta run --mode quick --output ./reports/serial-ABC123 --use-sample
- Generate PDF report and open automatically:
  inspecta run --mode quick --output ./reports/serial-ABC123 --use-sample --format pdf
- Generate both TXT and PDF reports (opens PDF):
  inspecta run --mode quick --output ./reports/serial-ABC123 --use-sample --format both
- Disable auto-open feature:
  inspecta run --mode quick --output ./reports/serial-ABC123 --use-sample --no-auto-open

Report output (what you receive)
The agent produces:
- report.json — canonical, machine-readable report (see REPORT_SCHEMA.md)
- report.txt — human-friendly text summary with scoring and recommendations (auto-opens by default)
- report.pdf — human-friendly PDF summary (optional, requires reportlab: pip install -r requirements-optional.txt)
- artifacts/ — directory with raw logs: agent.log, smartctl.txt, memtest.log, sensors.csv

Sample top-level JSON fields (excerpt)
```json
{
  "report_version": "1.0",
  "generated_at": "2025-10-18T18:00:00Z",
  "device": { "vendor": "Dell", "model": "XPS 9560", "serial": "ABC123" },
  "summary": { "overall_score": 78, "grade": "Good", "recommendation": "Office/Developer" },
  "scores": { "storage": 92, "battery": 60, "memory": 100 }
}
```
(Full schema lives in REPORT_SCHEMA.md and will be published as JSON Schema during implementation.)

Scoring & recommendations (concept)
- Categories (example weights):
  - Storage health & performance: 22%
  - Battery: 15%
  - Memory stability: 12%
  - CPU perf & thermal: 15%
  - Screen/physical (auto detection limited): 10%
  - Ports & peripherals: 8%
  - Network: 6%
  - Security & firmware: 6%
- Mapping to human recommendation:
  - 90–100: Excellent — ready to use
  - 75–89: Good — minor issues
  - 50–74: Fair — repairs recommended
  - <50: Poor — avoid unless for parts
- Recommendations will be profile-aware (Office, Developer, Content Creator, Gamer, Server) with minimum thresholds per profile.

Operational modes
- Quick mode:
  - Fast, in-OS, minimal intrusive checks.
  - Target time: 2–10 minutes.
  - Good for buyers who need a quick sanity check.
- Full mode:
  - Longer, includes bootable MemTest and extended stress tests (fio long runs, longer CPU stress).
  - Time: 30 minutes to multiple hours depending on depth.
  - Recommended for technicians and refurbishers.

Bootable live-USB (overview)
- Deliver trusted OS image (minimal Linux) with included tooling (smartctl, memtester, stress-ng, fio, ffmpeg, camera utilities).
- Booting from USB avoids OS interference and allows MemTest86 or MemTest runs.
- Build scripts and instructions will be provided under /bootable when implemented.

Architecture overview (planned)
- Agent (Python/Go): orchestrates tests, collects artifacts, signs and bundles results.
- Scoring engine (deterministic, auditable rules in Python)
- Report generator: produces report.json and report.pdf (Puppeteer/wkhtmltopdf or Python PDF generator)
- Optional backend (opt-in): upload endpoint to store reports and share trusted links
- Bootable ISO builder: minimal Linux + test suite for offline full-mode

Privacy, security & evidence
- Local-first: default behavior saves reports locally; uploads are opt-in and authenticated.
- Evidence: every report includes raw logs. Plans for SHA256 checksums and optional signing to prevent tampering.
- Sensitive data: agent will advise users to remove personal data and will redact obvious personal files from artifacts before upload (configurable).
- Security disclosures: see SECURITY.md for reporting vulnerabilities.

License & legal notes
- This repository is public for non-commercial use per LICENSE.txt (custom non-commercial license).
- The author (© 2025 mufthakherul) retains rights to relicense or commercialize the project later.
- The license may limit corporate adoption; if you need a commercial license, contact the author.

Contributing
- See CONTRIBUTING.md for contribution flow.
- Short summary:
  - Open issues for bugs or features.
  - Fork, create a branch, open a PR with tests and documentation.
  - Follow the Contributor Covenant (CODE_OF_CONDUCT.md).

Roadmap & milestones
- Documentation & scaffold (complete)
- MVP agent (quick-mode, Linux-first) — inventory, SMART, battery, memtest short, sensors, scoring, PDF
- Report viewer and optional upload API (opt-in)
- Bootable live-USB and full MemTest integration
- Cross-platform agents (Windows/macOS best-effort)
- Pilot with community refurbishers and marketplaces
(See ROADMAP.md for sprint-level breakdown.)

Troubleshooting & FAQ (short)
- Q: smartctl errors or "no such device"
  - A: Ensure smartmontools installed and run as root. Some NVMe devices require `smartctl -d nvme`.
- Q: memtester cannot allocate memory
  - A: Reduce memtester size or run memtester in an environment with less memory pressure.
- Q: Device locked by firmware / activation lock
  - A: Agent will report locks and recommend seller remove them; some locks cannot be bypassed by the agent.

Acknowledgements & references
- smartmontools (smartctl) for disk health
- memtester / MemTest86 for memory testing
- fio & sysbench for IO/CPU benchmarking
- LibreHardwareMonitor / OpenHardwareMonitor for sensor access ideas
- The open-source community and pilot testers (future)

Contact
- Owner / maintainer: @mufthakherul on GitHub
- For commercial licensing inquiries: contact via GitHub

---

Thanks for reading — this README is a living document and will evolve as the project moves from documentation into code. For now it's the canonical project landing page: clear goals, usage expectations, and how we treat privacy and evidence.
```
