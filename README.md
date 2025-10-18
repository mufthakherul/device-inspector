```markdown
# device-inspector (inspecta)

Local-first automated diagnostics for used laptops & PCs — quick-mode audits, auditable JSON+PDF reports, and optional bootable full diagnostics. Public, non-commercial use; © 2025 mufthakherul

Status: Documentation & project scaffold — agent & implementation coming next.

---

Table of contents
- Overview
- Key features
- Quick facts
- Project goals
- Installation (prep)
- Quickstart (run a quick-mode check)
- CLI usage examples
- Report output (what you get)
- Scoring & recommendations
- Operational modes: Quick vs Full
- Bootable live-USB (high-level)
- Architecture overview
- Privacy, security & evidence
- License & legal notes
- Contributing
- Roadmap & milestones
- Troubleshooting & FAQ
- Acknowledgements & resources
- Contact

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

Installation (developer / local)
This repository currently contains documentation and sample artifacts. Implementation will include a Python CLI agent. Expected installation steps for the agent (future):
1. Clone the repo:
   ```bash
   git clone https://github.com/mufthakherul/device-inspector.git
   cd device-inspector
   ```
2. (Optional) Create a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Install native tools (example for Debian/Ubuntu):
   ```bash
   sudo apt update
   sudo apt install smartmontools fio sysbench memtester lm-sensors ffmpeg
   sudo sensors-detect  # follow prompts
   ```

Quickstart — conceptual (what the user will run)
- Quick mode (2–10 minutes): runs inventory, SMART health, quick CPU/disk smoke, memtester short run, sensors snapshot, and writes artifacts/report:
  ```bash
  inspecta run --mode quick --output ./reports/device123
  ```
- Full mode (longer, technician/better confidence):
  ```bash
  inspecta run --mode full --output ./reports/device123
  # or build + boot a live-USB for MemTest86 full run
  ```

CLI usage examples (planned)
- Generate quick report locally:
  inspecta run --mode quick --output ./reports/serial-ABC123
- Generate and print JSON summary:
  inspecta run --mode quick --output ./reports/serial-ABC123 --print-summary
- Create bootable diagnostic USB image (linux host):
  inspecta build-iso --include-memtest --output diagnostic.iso

Report output (what you receive)
The agent produces:
- report.json — canonical, machine-readable report (see REPORT_SCHEMA.md)
- report.pdf — human-friendly summary with scoring, recommendations, and included evidence thumbnails
- artifacts/ — directory with raw logs: smartctl.txt, memtest.log, cpu_bench.txt, sensors.csv, camera.jpg (if applicable)

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
