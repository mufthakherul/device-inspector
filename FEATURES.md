# FEATURES — device-inspector (inspecta)

Last updated: 2025-10-18

This document is a comprehensive, detailed feature specification for device-inspector (inspecta). It describes every automated capability the agent will provide (MVP and planned), exact outputs and artifacts, configuration and CLI options, thresholds and scoring heuristics, plugin interfaces, data formats, testability requirements, security/privacy controls, and implementation guidance for contributors.

Use this as the canonical feature reference while implementing the agent, scoring engine, report generator, live-USB, and optional backend.

---

Contents
- 0. Overview & goals
- 1. Feature surface (by category)
  - 1.1 Inventory & provenance
  - 1.2 Storage & SMART
  - 1.3 Memory checks
  - 1.4 CPU & performance
  - 1.5 GPU & basic graphics
  - 1.6 Thermals & fans
  - 1.7 Battery & power (laptops)
  - 1.8 Network (wired & wireless)
  - 1.9 Peripherals & I/O (camera, audio, SD, USB)
  - 1.10 Security & firmware (TPM, Secure Boot)
  - 1.11 Software-level checks
- 2. Reporting & artifacts
  - 2.1 Canonical report.json
  - 2.2 report.pdf (human summary)
  - 2.3 Artifact bundle & manifest
  - 2.4 Signed report package (optional)
- 3. Scoring engine & buyer profiles
  - 3.1 Category weights & mapping
  - 3.2 Heuristics & thresholds (detailed)
  - 3.3 Profile-specific minimums and recommendations
- 4. Operational modes & UX
  - 4.1 Quick mode (MVP)
  - 4.2 Full mode (bootable / technician)
  - 4.3 Interactive guided mode
- 5. CLI, config file, environment variables, exit codes
  - 5.1 CLI commands & flags
  - 5.2 config.yml (schema)
  - 5.3 Environment variables
  - 5.4 Exit codes & machine signals
- 6. Plugin architecture & extensibility
  - 6.1 Plugin contract (interfaces)
  - 6.2 Plugin discovery & ordering
  - 6.3 Safeguards & sandboxing
- 7. Server integration & upload API (opt-in)
  - 7.1 Upload flow and authentication
  - 7.2 API contract (endpoints / required fields)
  - 7.3 Retention, encryption, and access controls
- 8. Evidence integrity, signing, and verification
  - 8.1 Manifest and checksums
  - 8.2 Signing format & key management (recommended)
  - 8.3 Verification workflow
- 9. Artifacts, PII, and privacy controls
  - 9.1 Default local-first policy
  - 9.2 Redaction & consent UI model
  - 9.3 Data retention and deletion
- 10. Tests, QA, and acceptance criteria per feature
- 11. Performance & runtime expectations
- 12. Supported hardware / platform matrix & fallbacks
- 13. Troubleshooting guidance and common error messages
- 14. Security considerations & hardening
- 15. Implementation guidance & recommended libraries
- 16. Future features & extension ideas
- Appendix A: Example config YAML
- Appendix B: Example manifest & signed-package JSON
- Appendix C: Change log

---

0. Overview & goals
The project provides an orchestrated set of automated checks that run on the target device and produce:
- a canonical machine-readable report (report.json),
- a human-friendly PDF summary (report.pdf),
- an artifacts bundle (raw logs, images, sensor CSVs),
- an optional signed bundle to enable third-party verification.

Primary design constraints:
- Local-first by default (no cloud upload without explicit consent).
- Non-destructive tests in quick mode.
- Transparent, auditable scoring rules and raw logs.
- Linux-first for full reliability; cross-platform best-effort for quick mode.

---

1. Feature surface (by category)

Implementation note: each feature listed below must include:
- tool(s) used,
- data captured,
- artifact filename(s),
- pass/warn/fail criteria,
- score mapping stub,
- unit/integration tests required.

1.1 Inventory & provenance
- Description: gather vendor, model, product name, serial number, BIOS/UEFI version, SKU, chassis type, manufacture date (when available), OS info, kernel, agent version.
- Tools:
  - Linux: dmidecode, lshw, /sys, hostnamectl
  - Windows: Get-CimInstance Win32_BIOS / Get-ComputerInfo (PowerShell) — MVP placeholder
  - macOS: system_profiler
- Artifacts:
  - artifacts/inventory.json (canonical)
- Pass/WARN/Fail: always informational; FAIL only if inventory cannot be read.
- Tests:
  - Unit: parse sample dmidecode outputs into inventory.json
  - Integration: run inventory on CI runner (mocked)

1.2 Storage & SMART
- Description: detect drives (SATA/NVMe/USB), read SMART attributes, map critical attributes to health, run short read benchmark sample.
- Tools:
  - smartctl (smartmontools) with --json for parsing
  - nvme-cli for NVMe if available (nvme smart-log)
  - fio (quick sample) or dd fallback
- Artifacts:
  - artifacts/smart_{dev}.json (raw smartctl JSON)
  - artifacts/disk_perf_{dev}.json (fio or summary)
- Key attributes collected:
  - Reallocated_Sector_Ct, Current_Pending_Sector, Offline_Uncorrectable, Wear_Leveling_Count/Wear_Leveling, Percentage Used (SSD), Power_On_Hours, Power_Cycle_Count
- Pass/WARN/Fail rules (examples):
  - FAIL if Reallocated_Sector_Ct > 0 OR Current_Pending_Sector > 0 for HDD.
  - FAIL for SSD: if Critical SMART health status is FAILED or PercentageUsed >= 90.
  - WARN if PercentageUsed >= 70 or Power_On_Hours >> typical age.
- Score mapping:
  - map SMART overall save to 0–100 subscore; combine with perf percentile into storage score.
- Tests:
  - Parser unit tests with diverse smartctl JSON outputs.
  - Perf harness mocks to test scoring mapping.

1.3 Memory checks
- Description: detect total RAM, module details (size, speed, ecc), run in-OS memtester short job (quick) and log errors; document bootable MemTest86 integration for full-mode.
- Tools:
  - Linux: dmidecode/GetMemory, memtester for quick check
  - Bootable: MemTest86 / MemTest86+
- Artifacts:
  - artifacts/memtester.log
  - artifacts/meminfo.json
- Pass/WARN/Fail:
  - FAIL if any memtester errors are observed.
  - WARN if memtester cannot allocate target size or test incomplete.
- Tests:
  - Simulated memtester log parse unit tests.
  - Add integration test that simulates memtester error output.

1.4 CPU & performance
- Description: identify CPU model and capabilities, run quick single-core and multi-core micro-benchmarks, short thermal stress to detect throttling.
- Tools:
  - lscpu / /proc/cpuinfo, sysbench (or hyperfine microbench), stress-ng for short stress
- Artifacts:
  - artifacts/cpu_info.json
  - artifacts/cpu_bench.json
  - artifacts/thermal_timeseries.csv
- Pass/WARN/Fail:
  - WARN if observed sustained throttle or frequency drop > X% under short stress (configurable).
  - Compare benchmark score to baseline table (if present) else use absolute heuristics.
- Tests:
  - Unit tests for parsing sysbench output and frequency/time sampling logic.

1.5 GPU & basic graphics
- Description: detect GPUs (integrated/discrete), driver versions, perform a lightweight GPU smoke test (render/time limited) to detect artifacts.
- Tools:
  - Linux: lspci, glxinfo, vulkaninfo, `vkcube`/glmark2 smoke test
  - Windows: dxdiag/NVIDIA nvidia-smi (best-effort later)
- Artifacts:
  - artifacts/gpu_info.json
  - artifacts/gpu_bench.json
  - artifacts/gpu_screenshot_0.png (if offscreen capture used)
- Pass/WARN/Fail:
  - FAIL if smoke test produces artifacts (if artifact detection is implemented).
  - WARN for driver mismatch or absent GPU for expected profile (e.g., "Gamer" profile).
- Tests:
  - Mocked glmark2 output parse tests.

1.6 Thermals & fans
- Description: read idle temperatures and fan RPMs, run short stress and sample delta, detect thermal throttling events.
- Tools:
  - lm-sensors (Linux), hddtemp (if needed), ipmitool (on servers), HWiNFO / OpenHardwareMonitor on Windows (future)
- Artifacts:
  - artifacts/sensors_{timestamp}.csv
  - artifacts/fans_{timestamp}.json
- Pass/WARN/Fail:
  - FAIL if peak CPU temp > 95°C sustained or if repeated throttling detected.
  - WARN if peak > 85°C or fans not spinning when load present.
- Tests:
  - Simulate sensor timeseries and assert throttling detection.

1.7 Battery & power (laptops)
- Description: design capacity vs current full charge, cycle count, AC adapter detection, estimated health percentage.
- Tools:
  - Linux: upower, ACPI sysfs
  - Windows: powercfg /batteryreport
  - macOS: system_profiler SPPowerDataType
- Artifacts:
  - artifacts/battery_report.html (Windows) or battery.json
- Pass/WARN/Fail:
  - FAIL if health_pct < 40% and battery is primary for mobility buyers.
  - WARN if health_pct < 70% or cycle_count > vendor_recommendation*0.7.
- Tests:
  - Parser tests for `powercfg /batteryreport` HTML and upower JSON.

1.8 Network (wired & wireless)
- Description: enumerate adapters, link speeds for Ethernet, Wi‑Fi scan & RSSI, optional throughput test (iperf3 or speedtest CLI).
- Tools:
  - ethtool / nmcli / iw / iperf3 / speedtest-cli
- Artifacts:
  - artifacts/network.json
  - artifacts/iperf_{run}.json
- Pass/WARN/Fail:
  - WARN if negotiated link speed is significantly below expected capability.
  - Network tests are optional (may require remote server).
- Tests:
  - Unit tests for parsing ethtool and iw outputs.

1.9 Peripherals & I/O
- Description: enumerate USB devices, SD readers; test camera capture, microphone and speaker loopback (optional).
- Tools:
  - ffmpeg / v4l2capture / arecord/aplay
- Artifacts:
  - artifacts/camera_sample.jpg
  - artifacts/audio_sample.wav
  - artifacts/usb_list.json
- Pass/WARN/Fail:
  - PASS if camera frame captured at expected resolution; WARN otherwise.
  - Be conservative: do not record audio without explicit consent.
- Tests:
  - Mocked ffmpeg capture outputs; file existence assertions in integration tests.

1.10 Security & firmware
- Description: detect TPM presence and version, Secure Boot status, UEFI vs legacy, BIOS version and date; detect OS activation and basic malware scanning (optional, non-invasive).
- Tools:
  - Linux: tpm2-tools, mokutil, efibootmgr
  - Windows: Get-TPM, slmgr (activation)
  - Optional: ClamAV quick scan (user opt-in)
- Artifacts:
  - artifacts/security.json
- Pass/WARN/Fail:
  - WARN if TPM absent for buyer profile (e.g., enterprise use).
  - WARN if Secure Boot disabled for profiles requiring it.
- Tests:
  - Unit tests for parsing tpm2-tools output.

1.11 Software-level checks
- Description: OS details, activation state (Windows), presence of suspicious large numbers of user accounts or strange startup services (light heuristics only).
- Tools:
  - system-provided APIs or psutil-like scans
- Artifacts:
  - artifacts/os_software.json
- Pass/WARN/Fail:
  - Informational; flag suspicious findings as WARN only after conservative heuristics.
- Tests:
  - Mocked environments with expected outputs.

---

2. Reporting & artifacts

2.1 Canonical report.json
- Purpose: single source of truth consumed by viewers, server, and downstream tooling.
- Top-level fields (required):
  - report_version (string)
  - generated_at (ISO8601)
  - agent_version
  - device { vendor, model, serial, bios, sku, os }
  - summary { overall_score, grade, issues_count, recommendation }
  - scores { storage, battery, memory, cpu_thermal, gpu, network, security, peripherals }
  - tests { smart, memtest, cpu_benchmark, disk_benchmark, thermal_stress, battery, network }
  - artifacts [ { type, path, checksum, size_bytes } ]
  - raw_logs { filename: base64/text or pointer }
  - evidence { manifest_sha256, signed: boolean, signer_key_id (if signed) }
- Schema: a json-schema (report-schema.json) must be created and validated by agent before finalizing report.json.

2.2 report.pdf (human summary)
- Contents:
  - Header: device, serial (optionally redacted), agent version, generated_at
  - One-line buy/no-buy verdict
  - Overall score big visual (0–100)
  - Per-category scores with colored badges and brief explanation
  - Top issues list (max 6) linking to artifacts paths
  - Evidence thumbnails (smartctl summary, sensors graph, camera snapshot if present)
  - Short seller negotiation suggestions (non-binding) and "what to check in-person" checklist
  - Footer: legal disclaimer and contact for commercial license
- Generation:
  - Template in HTML/CSS then convert to PDF (Puppeteer or WeasyPrint) OR Python PDF generator.
  - Must embed report.json digest and artifact manifest checksum.

2.3 Artifact bundle & manifest
- Structure:
  - /artifacts/
    - smart_{dev}.json
    - memtest.log
    - cpu_bench.json
    - sensors.csv
    - camera_001.jpg
    - battery_report.html
  - manifest.json:
    - list of artifacts and SHA256 checksums
  - signed_manifest.sig (optional)
- Naming conventions and timestamping must be consistent.

2.4 Signed report package (optional)
- Purpose: allow receiver to verify report authenticity and that artifacts belonged to the device at test time.
- Recommended format:
  - A ZIP or tar.gz containing report.json, artifacts/, manifest.json and a signature file `manifest.sig`.
- Signature:
  - Ed25519 recommended for compactness and modern usage.
  - Signature covers manifest.json and report.json (canonicalized).
  - Key storage: user local keypair (private key never uploaded); public key can be embedded in report JSON or published separately for marketplaces.

---

3. Scoring engine & buyer profiles

3.1 Category weights (recommended default)
- Storage: 22%
- Battery: 15% (only for laptops)
- Memory: 12%
- CPU & thermal: 15%
- Screen & physical (auto-limited): 10%
- Ports & peripherals: 8%
- Network: 6%
- Security & firmware: 6%
Total = 100%

3.2 Heuristics & thresholds (detailed)
- Storage:
  - Hard Fail: Reallocated_Sector_Ct > 0 OR Current_Pending_Sector > 0 => storage_subscore = 0
  - SSD wear_percentage >= 90% => storage_subscore = 10
  - Else: map (performance percentile 0–100 and wear inverse) -> weighted subscore
- Battery:
  - health_pct = current_full / design_capacity * 100
  - FAIL if health_pct < 40% (for mobile buyers)
  - WARN if health_pct < 70%
  - Cycle thresholds: vendor_cycle_max * 0.8 -> warn, > vendor_cycle_max -> fail
- Memory:
  - Any memtester errors -> 0
  - No errors -> 100
- Thermal:
  - FAIL if sustained CPU > 95°C or repeated throttling events
  - WARN if peak > 85°C or single throttle event
- CPU performance:
  - Map sysbench score to percentile for CPU model if DB exists; otherwise use absolute heuristics (single-core > X points = good)
- GPU:
  - For gaming profile, require discrete GPU and GPU_bench >= threshold
- Network:
  - If iperf run available, map Mbps to subscore relative to expected link
- Security:
  - TPM absent: WARN for enterprise profile
  - Secure Boot disabled: WARN for security-conscious buyers

3.3 Profile-specific minimums & mapping
- Office / Student:
  - Overall >= 60, RAM >= 8GB, battery_health >= 50%
- Developer / Remote Worker:
  - Overall >= 70, CPU cores >=4, RAM >=16GB, storage_subscore >= 60
- Content Creator:
  - GPU_subscore >= 70 OR CPU_subscore >= 80, RAM >= 32GB suggested, storage NVMe recommended
- Gamer:
  - GPU_subscore >= 70 and thermal_subscore >= 70
- Server / NAS:
  - Storage_subscore >= 90, ECC RAM recommended

Recommendation strings generated from mapping:
- "Recommended for: Office & Student. Battery health moderate; replace if needing long mobile use."
- "Not recommended for gaming or content creation due to GPU and thermal limits."

---

4. Operational modes & UX

4.1 Quick mode (MVP)
- Purpose: provide a 2–10 minute, safe, in-OS check for buyers.
- Tests run:
  - Inventory
  - SMART health (quick)
  - Disk perf sample (short fio job)
  - CPU quick bench (few seconds)
  - Memtester quick run (e.g., 30s)
  - Sensors snapshot (idle)
  - Battery report (if laptop)
- Defaults:
  - Non-destructive I/O, read-only filesystem checks except temp files with unique name.
  - No automatic uploads; report saved locally.
- CLI:
  - `inspecta run --mode quick --output ./reports/serial-ABC123`

4.2 Full mode (technician)
- Purpose: provide deep tests for refurbishers and technicians; may require bootable USB and elevated privileges.
- Tests run:
  - Full MemTest86 (bootable)
  - Extended fio/IOPS tests
  - GPU benchmark (optional)
  - Extended thermal/stress runs (e.g., 15–60 minutes)
  - Filesystem integrity checks (fsck/chkdsk) — interactive and only with explicit consent
- Warnings:
  - Full mode may stress hardware and can take hours; the agent will warn and require explicit confirmation.

4.3 Interactive guided mode
- Purpose: ask user about buyer profile and intended use to adapt thresholds and tests.
- Example:
  - `inspecta run --mode quick --profile developer --interactive`

---

5. CLI, config file, environment variables, exit codes

5.1 CLI commands & flags (planned)
- `inspecta --version`
- `inspecta run --mode [quick|full|guided] --profile [office|developer|gamer|creator|server] --output <dir> [--upload url --token token] [--sign-key <path>] [--no-prompt] [--verbose]`
- `inspecta inventory --output inventory.json`
- `inspecta build-iso --include-memtest --output diagnostic.iso` (on Linux host)
- `inspecta verify --bundle <signed_bundle.zip>` (verify signatures & manifest)
- `inspecta report --open <report.json>` (open local viewer)

5.2 config.yml (schema)
- Location order: CLI flag overrides environment variable overrides config file at `$XDG_CONFIG_HOME/inspecta/config.yml` or `~/.config/inspecta/config.yml`.
- Keys:
  - agent:
    - version: string
    - run_as: [auto|root|user]  # recommended default auto (elevate for privileged tests)
  - tests:
    - quick:
      - memtester_seconds: 30
      - cpu_bench_runs: 3
      - fio_sample_size_mb: 256
  - scoring:
    - weights:
      storage: 0.22
      battery: 0.15
      memory: 0.12
      cpu_thermal: 0.15
      screen: 0.10
      peripherals: 0.08
      network: 0.06
      security: 0.06
  - signing:
    - enabled: false
    - private_key_path: "~/.inspecta/keys/ed25519_key"
    - public_key_id: "user@example.com"
  - upload:
    - url: ""
    - token: ""
    - allow_upload: false
  - privacy:
    - redact_personal_data: true
    - exclude_paths: ["/home/*/Documents/*"]
- Example config provided in Appendix A.

5.3 Environment variables
- INSPECTA_CONFIG=/path/to/config.yml
- INSPECTA_NO_PROMPT=1 (non-interactive)
- INSPECTA_SIGN_KEY=/path/to/key
- INSPECTA_UPLOAD_URL=https://reports.example.com

5.4 Exit codes & machine signals
- 0: Success (report produced)
- 1: Generic error (inspecta encountered an unhandled problem)
- 2: Usage / CLI parse error
- 10: Partial success — tests completed with WARNs, report produced
- 20: Failure — tests failed (no report), critical missing tools or permissions
- 30: Aborted by user
- SIGINT (Ctrl-C): graceful shutdown; partial artifacts saved with timestamped suffix

---

6. Plugin architecture & extensibility

6.1 Plugin contract (interfaces)
- Plugins are Python modules (for MVP) that implement a simple class or functions:
  - `discover(context) -> dict` (optional)
  - `run(context) -> TestResult`
  - `describe() -> dict` (name, version, required_privileges, artifacts)
- `TestResult` fields:
  - id (string), status (PASS/WARN/FAIL/SKIPPED), score (0–100), metrics (dict), artifacts (list of artifact descriptors), logs (text or path), start_ts, end_ts
- Each plugin must declare:
  - `requires_root: bool`
  - `timeout_seconds: int`
  - `depends_on: [plugin_id]` (optional)

6.2 Plugin discovery & ordering
- Plugins live under `/agent/plugins/` or installed via entry points (Python pkg).
- At runtime, agent resolves DAG based on `depends_on`, runs in topological order; parallelize independent plugins with a worker pool.
- Plugin metadata registered in `plugins.json` in agent package.

6.3 Safeguards & sandboxing
- Plugins should not write to arbitrary filesystem locations; artifacts must be under `--output/artifacts/`.
- Dangerous operations (fsck, chkdsk) only executed when `--confirm-destructive` flag present and agent warns.
- Plugins run with resource limits (ulimit) and timeouts to avoid runaway tests.

---

7. Server integration & upload API (opt-in)

7.1 Upload flow (agent)
- Agent asks explicit consent before upload.
- Client performs `POST /api/v1/reports` with multipart/form-data:
  - fields: metadata (JSON), report.json, manifest.json
  - files: artifacts (streamed)
- Authentication: Bearer token or short-lived upload token (`Authorization: Bearer <token>`).
- TLS mandatory.

7.2 API contract (summary)
- POST /api/v1/reports
  - Request: multipart upload; metadata json includes agent_version and signer_key_id
  - Response: { id: "<uuid>", url: "https://..." }
- GET /api/v1/reports/{id}
  - Response: JSON metadata + links to artifacts (if user consented)
- GET /api/v1/reports/{id}/pdf
  - Response: PDF download
- DELETE /api/v1/reports/{id} (requires token with deletion scope)

7.3 Server storage & retention
- Server must store artifacts encrypted at rest (SSE or application-side encryption).
- Retention configurable (default 90 days).
- Access control configurable per-upload (public link token, private owner token).

---

8. Evidence integrity, signing, and verification

8.1 Manifest & checksums
- manifest.json example structure:
  - {
      "report_sha256": "<hex>",
      "artifacts": [
        { "path": "artifacts/smart_nvme0.json", "sha256": "<hex>", "size": 12345 },
        ...
      ],
      "generated_at": "2025-10-18T18:00:00Z"
    }

8.2 Signing format & key management
- Recommended: Ed25519 signatures over canonical manifest (UTF-8, sorted keys).
- File `manifest.sig` contains ascii-armored base64 signature or raw detached signature.
- Public key fingerprint and optionally key URL included in `report.json` as `evidence.signer_pubkey_fingerprint`.
- Key options:
  - user-generated keypair: `inspecta key generate --type ed25519`
  - hardware-backed keys (Yubikey) supported if available

8.3 Verification
- `inspecta verify --bundle signed_bundle.zip` will:
  - validate manifest checksums against artifacts
  - verify signature(s) against provided public key(s)
  - output `verification_report.json` with verdict and details

---

9. Artifacts, PII, and privacy controls

9.1 Default local-first policy
- Agent writes all artifacts to local `--output` dir.
- Upload is disabled by default.

9.2 Redaction & consent
- Default `config.yml` has `redact_personal_data: true`.
- Redaction flow before upload:
  - Agent lists files that may contain PII (screenshots, home directory files) and asks user to confirm explicit upload or redaction.
  - Automated redactions: blur identifiable images (optional), remove absolute user paths in logs (optional).
- Explicit consent recorded in `report.json` under `evidence.upload_consent: { yes: true, timestamp: ... }`.

9.3 Deletion & user rights
- Local deletion: user can remove report bundle via `inspecta prune --older-than 30d`.
- Server: provide per-upload owner token and deletion endpoint; comply with GDPR/CCPA requests per pilot contract.

---

10. Tests, QA, and acceptance criteria per feature

For each plugin/feature produce:
- Unit tests for parser and scoring logic
- Mocked integration tests for tool absence and fallback behavior
- e2e smoke test that runs agent quick-mode with mocked tool outputs (CI)
- Manual e2e tests on physical hardware for pilot (logged runs)

Examples:
- SMART parser: tests with healthy SMART JSON, failing SMART JSON, SMART missing fields.
- Memtester: tests for no-error output and simulated error output; scoring mapping test.
- PDF generation: snapshot test asserting presence of key sections and embedded checksum.

CI matrix:
- Linting + unit tests on PRs (Linux)
- Nightly integration runs for full quick-mode using mocked tool outputs
- Optional scheduled ISO builder test on run schedule

---

11. Performance & runtime expectations

Quick-mode target:
- Typical device runtime: 2–10 minutes
- Goals:
  - Inventory & SMART: 30–90s
  - CPU bench & memtester short run: 30–90s
  - Disk quick sample: 30–90s
- Full-mode:
  - Bootable MemTest full run: variable (30m–several hours)
  - Long fio tests: user-configurable (recommend 5–30 minutes per run)

Resource constraints:
- Quick-mode should limit CPU stress to short bursts and respect power limits on laptops.
- Agent should detect thermal runaway and abort long tests if safety thresholds exceeded.

---

12. Supported hardware / platform matrix & fallbacks

Initial support priority:
- Primary: Linux (Ubuntu LTS flavors) — full coverage
- Secondary: Windows 10/11 (limited via PowerShell; some tests best-effort)
- Tertiary: macOS (inventory and some tests only)
- Platform fallbacks:
  - If smartctl absent: report SMART unavailable and suggest install instructions
  - If fio absent: fallback to dd sequential read (caveat noted)
  - If memtester absent: recommend memtester install or offer bootable memtest path

Hardware detectors:
- NVMe devices: use `smartctl -d nvme`
- RAID: detect via controllers; SMART may be behind RAID controller; log as limitation
- TPM: tpm2-tools or Get-TPM on Windows

---

13. Troubleshooting guidance & common error messages

Common issues:
- "smartctl: command not found" -> user-friendly message: "Install smartmontools: sudo apt install smartmontools"
- "permission denied reading device" -> warn user to run as root or use sudo for privileged tests
- "memtester failed to allocate memory" -> reduce memtester size or close other apps
- "fio aborted due to read errors" -> STOP test; mark storage subscore FAIL; include raw logs

Agent will:
- provide clear remediation steps,
- include link to docs and how-to,
- persist exit logs at `output/artifacts/agent.log`.

---

14. Security considerations & hardening

- Principle of least privilege: warn when requiring root and limit elevated operations to necessary commands.
- Secret handling: never log tokens or private keys in plaintext in artifacts.
- Validate all external inputs (server upload responses, config files).
- Use secure defaults: HTTPS-only uploads, verify server certificates.
- Pre-commit and CI secret scanning to prevent leaks.
- Supply-chain: sign release artifacts and publish checksums.

---

15. Implementation guidance & recommended libraries

Agent language: Python 3.11 recommended for rapid development and cross-platform libraries.

Suggested libraries:
- CLI: Click or argparse (Click for nicer UX)
- JSON Schema validation: jsonschema
- PDF generation: WeasyPrint or Puppeteer (Node) if HTML templating preferred (WeasyPrint preferred pure-Python)
- Logging: structlog or Python logging with JSON handler for artifacts
- Concurrency: asyncio or threads for plugin parallelism
- Testing: pytest
- Pre-commit: pre-commit with black, ruff, isort
- Signing: PyNaCl (Ed25519) or cryptography library

Containerized dev & reproducible builds:
- Use GitHub Actions to run lint/test/build on Linux runners.
- Use Packer or Docker for ISO build environment.

---

16. Future features & extension ideas (priority-ranked)
- 1: Signed public key registry for marketplaces to verify seller-signed reports.
- 2: Windows native sensor integration using LibreHardwareMonitor agent or HWiNFO exporter.
- 3: Model baseline DB with performance expectations per CPU/GPU model (crowdsourced).
- 4: Repair-cost heuristics tied to local repair shop price lists.
- 5: ML-based image analysis for screen cracks and surface damage detection.
- 6: Marketplace SDK for badge issuance and dispute resolution.

---

Appendix A: Example config YAML
```yaml
agent:
  version: "0.1.0"
  run_as: auto

tests:
  quick:
    memtester_seconds: 30
    cpu_bench_runs: 3
    fio_sample_size_mb: 256

scoring:
  weights:
    storage: 0.22
    battery: 0.15
    memory: 0.12
    cpu_thermal: 0.15
    screen: 0.10
    peripherals: 0.08
    network: 0.06
    security: 0.06

signing:
  enabled: false
  private_key_path: "~/.inspecta/ed25519.key"
  public_key_id: "user@example.com"

upload:
  allow_upload: false
  url: ""
  token: ""

privacy:
  redact_personal_data: true
  exclude_paths:
    - "/home/*/Downloads/*"
```

Appendix B: Example manifest & signed-package JSON
```json
{
  "report_sha256": "6a3b...f1e",
  "artifacts": [
    { "path": "artifacts/smart_nvme0.json", "sha256": "abc123...", "size": 45678 },
    { "path": "artifacts/memtest.log", "sha256": "def456...", "size": 1234 }
  ],
  "generated_at": "2025-10-18T18:00:00Z"
}
```
If signed with Ed25519, `manifest.sig` contains the detached signature bytes base64-encoded.

Appendix C: Change log
- 2025-10-18: Initial comprehensive FEATURES.md (this file)

---

Implementation note for contributors
- For each feature, create a corresponding issue with:
  - Implementation tasks (plugin, parser, tests, docs)
  - Acceptance tests (unit and integration)
  - Estimated story points
- Attach sample tool outputs in `/samples` for reliable parser tests.

---

This FEATURES.md is intentionally exhaustive to guide implementation and to reduce ambiguity. It should be updated as pilots provide feedback and thresholds are tuned.
