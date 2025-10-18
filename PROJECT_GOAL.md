# Project Goal

Device Inspector (inspecta) — a local-first, auditable automated inspection tool for pre-purchase diagnostics of used laptops and PCs.

Objectives
- Provide reliable automated checks (SMART, battery, memory smoke, quick CPU/disk benchmarks, sensors snapshot).
- Produce an auditable report (JSON + PDF) with a concise buy/no-buy verdict, per-category scores, and an evidence bundle (logs, artifacts).
- Prioritize privacy (local-first) and verifiability (timestamped, checksums, optional signing).
- Offer a bootable live-USB mode for full, OS-independent diagnostics.

Primary users
- Individual buyers and sellers
- Refurbishers and repair technicians
- Marketplaces wishing to provide inspection evidence (via opt-in integrations)

Constraints
- Initial implementation will be Linux-first (quick-mode), with cross-platform (Windows/macOS) support added later where practical.
