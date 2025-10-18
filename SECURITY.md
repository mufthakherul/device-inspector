# Security Policy — device-inspector (inspecta)

Last updated: 2025-10-18

This document describes how to report security vulnerabilities, how reports will be handled, timelines and expectations, and best practices for responsible security research related to Device Inspector (inspecta). The project maintainers take security seriously and will treat reports confidentially and professionally.

If you discover a security issue, please follow the Responsible Disclosure procedure described below. Do NOT create a public issue for security-sensitive reports.

---

## Quick summary / TL;DR

- Prefer encrypted email for reports: security@device-inspector.org (PGP key fingerprint below). If you can't use PGP, open a direct contact through the maintainer's GitHub profile: @mufthakherul.
- Include a clear proof-of-concept (PoC), steps to reproduce, affected version(s), and any logs or artifacts (redacted of PII) when reporting.
- We will acknowledge receipt within 72 hours and give status updates until resolved.
- We aim to release a coordinated fix within 30 days for critical issues, sooner where feasible. Timelines may vary for complex or third-party issues.
- We will coordinate public disclosure with the reporter. We prefer to fix before public disclosure.

---

## Scope

This policy applies to:
- Code and files in this repository (https://github.com/mufthakherul/device-inspector).
- Official release artifacts published by the project (binaries, ISO images, installers) that originate from this repo.

Out of scope:
- Third-party projects and libraries. If the issue stems from a dependency (e.g., smartmontools, fio, sysbench, MemTest), we will coordinate with the upstream maintainer if necessary.
- User environments or deployment-specific infrastructure that is external to the project (e.g., a user's own cloud or CI setup). Report such issues to the relevant provider and notify us if the issue affects the project.
- Physical attacks or hardware-only issues that are unrelated to the project's software. If hardware behavior causes insecure results in the project (e.g., sensor spoofing that the agent cannot detect), include the hardware model and evidence — we will advise but cannot fix third-party hardware.

---

## How to report a vulnerability

Preferred (secure) method:
1. Encrypt your report with the project's PGP public key and email it to security@device-inspector.org.
2. If encryption is not possible, send a message to the project owner via GitHub (see "Contact" below) asking for a secure channel.

Alternative:
- If you cannot use email, open a GitHub issue with the title prefixed `SECURITY REPORT:` but first contact the maintainer to request the issue be made private (only do this if instructed; otherwise do not post sensitive details publicly).

What to include in your report:
- A short summary of the issue (one paragraph).
- The product and version(s) affected (e.g., `agent v0.3.0`, `commit SHA: abc123...`).
- Detailed steps to reproduce the issue, including commands, configuration, and test data (minimal PoC preferred).
- Expected vs. actual behavior.
- Screenshots, logs, and sample `report.json` or artifacts that demonstrate the problem (redact any personal data).
- Network setup or topology where relevant.
- Any mitigation ideas or suggested fixes (optional).
- Your contact details and whether you prefer to remain anonymous.

Report template (example)
```
Subject: [SECURITY] Device Inspector - arbitrary code execution in agent vX.Y.Z

Summary:
- Brief description: The agent executes unsanitized shell commands from a device label that can be controlled by an attacker.

Affected versions:
- inspecta agent v0.1.0 through v0.2.3 (commit X..Y)

Steps to reproduce:
1. Start agent with `inspecta run --device /dev/sdX --label "$(malicious payload)"`
2. Observe execution of `$(malicious payload)` in /tmp/exec.log

PoC:
- Minimal script or curl commands here (attach encrypted file)

Impact:
- Arbitrary command execution as agent user; high severity on devices run by non-privileged users.

Contact:
- name / email / PGP fingerprint
```

---

## PGP key / encryption instructions

We strongly encourage reporters to encrypt sensitive reports. Use PGP/GPG and encrypt the message to the project's public key.

Project PGP key (public key fingerprint placeholder)
- PGP key fingerprint: 0123 4567 89AB CDEF 0123 4567 89AB CDEF 0123 45AB

How to encrypt (example)
1. Import the public key (if you have it as a file):
   ```bash
   gpg --import inspecta-pubkey.asc
   ```
2. Encrypt a report file:
   ```bash
   gpg --encrypt --recipient "device-inspector (inspecta) <security@device-inspector.org>" -o report.gpg report.txt
   ```
3. Send the encrypted file via email to security@device-inspector.org.

If you cannot use PGP:
- Use the GitHub contact for the owner (@mufthakherul) to request an alternative secure channel (e.g., Signal, Keybase, or secure paste). Do not post sensitive details publicly.

> NOTE: The fingerprint above is a placeholder. The authoritative PGP public key will be published in this repository and on the maintainer's GitHub profile. Always verify the fingerprint by contacting the maintainer.

---

## Response process and timelines

We follow a responsible disclosure process with these general SLAs:

- Acknowledgement: within 72 hours of receiving a report (we will reply confirming receipt and next steps).
- Initial triage: within 5 business days to determine severity and initial mitigation or workaround steps.
- Fix ETA: we will provide an estimated time to a patch; for critical issues we aim for mitigation or a fix within 30 days when feasible.
- Coordinated disclosure: we will coordinate a disclosure timeline with the reporter. Public disclosure is mutually agreed where possible.
- Patch release: patches will be published to the main repo and tagged releases. Users will be notified via release notes and, where applicable, security advisories.

Severity classification (example)
- Critical — Remote code execution, privilege escalation, or data exposure allowing access to private user data without user interaction. Requires immediate mitigation.
- High — Vulnerabilities that allow local privilege escalation, persistent data exposure, or circumvention of major security controls. Should be fixed quickly.
- Medium — Vulnerabilities requiring local access or user interaction, or those that reduce defense-in-depth but require other conditions to exploit.
- Low — Minor information leaks, UI issues with low security impact, or issues that are hard to exploit.

Triage is performed by maintainers. Severity determinations are influenced by exploitability, impact, and user exposure.

---

## Handling of sensitive data & PoC

- Do not send unencrypted PII, passwords, or private keys in public channels.
- If you must send sample data that contains PII, redact or encrypt it.
- We will sanitize logs or artifacts before publishing them publicly and will consult the reporter before releasing PoCs or exploit details.
- If a PoC reveals sensitive user data, we will treat the report as high-severity until proven otherwise.

---

## Coordination & disclosure

- We will attempt to coordinate a disclosure timeline with the reporter and upstream projects where applicable.
- We prefer to withhold public disclosure until a patch is available, but we will consider publisher/maintainer requests and coordinated disclosure windows.
- If the reporter prefers immediate public disclosure (after a reasonable grace period), we will negotiate a mutually acceptable date. The maintainer may request a short embargo for patching.
- We may request that CERT, a bug-bounty platform, or other coordination body be included for high-impact issues.

---

## CVE / advisory publication

- For confirmed security vulnerabilities, maintainers will:
  - Create a GitHub Security Advisory and publish patches, or
  - Publish a CVE request (if severity and ecosystem warrant it).
- The advisory will include:
  - Affected versions
  - Severity rating
  - Mitigation and upgrade instructions
  - Acknowledgements and credits (if the reporter agrees)

---

## Remediation & patching policy

- Patch availability depends on the complexity:
  - Simple fixes: push patch and release within days.
  - Complex or third-party fixes: work with upstream; provide mitigations and temporary guidance to users.
- When a fix is released:
  - We will publish release notes with clear upgrade instructions.
  - Provide a CVE/advisory if applicable.
  - Publish post-mortem if the issue caused a security incident.

Backports:
- Security patches will be backported to maintained release branches at the maintainer's discretion.

---

## Security testing / acceptable testing practices

We encourage security research, but please follow these rules:

Do:
- Test against local instances or test systems you own.
- Use simulated / sandboxed devices and test data.
- Report findings via the responsible disclosure channel.

Do NOT:
- Test against production systems you do not own or manage.
- Attempt to access, modify, or exfiltrate data from third parties or other users.
- Perform denial-of-service attacks against public infrastructure or user systems.
- Publicly post exploit details or PoCs before a fix is available and disclosure coordinated.

Safe harbor:
- If you follow this policy in good faith (report vulnerabilities privately, avoid data exfiltration, and comply with instructions from maintainers), we will not pursue legal action. However, this safe harbor does not protect against reckless, illegal, or damaging activities.

---

## Handling of reports that appear to be attacks, illegal, or malicious

- If a report suggests ongoing malicious activity or an active exploit:
  - The maintainers may share relevant information with trusted parties or law enforcement where necessary.
  - We will notify the reporter if disclosure to third parties is required (except where prohibited by law).

---

## Evidence and logging for maintainers

When triaging reports maintainers will:
- Record the report receipt and triage steps in a private issue or internal tracker.
- Preserve relevant logs and artifacts in a secure store with restricted access.
- Track timeline, communications, and fixes for auditing and post-mortem.

---

## Disclosure credit & acknowledgements

- We will credit researchers who report issues in advisories and release notes unless they request anonymity.
- If the researcher requests a bug bounty or formal recognition, we will evaluate and respond (note: the project currently does not run a public bug bounty program).

---

## Security tooling & CI

Planned/maintained security tooling:
- Dependency scanning (e.g., Dependabot or equivalent) will run on enabled language manifests to identify known vulnerable dependencies.
- CI pipelines will run static analysis and linter checks.
- We will add automated security checks (SAST/secret scanning) as the codebase grows.

If you notice a dangerous dependency or secret in the repo, report it privately per this policy immediately.

---

## Legal & export control considerations

- Researchers must comply with local laws and export control restrictions. Do not transmit controlled technical data across jurisdictions where prohibited.
- This policy does not grant legal immunity. If in doubt about the lawfulness of a test, seek legal advice before proceeding.

---

## Contact / reporting channels

Primary contact (preferred):
- Encrypted email: security@device-inspector.org (PGP encryption encouraged)

Secondary contact:
- GitHub owner: @mufthakherul — use the GitHub profile contact to request a secure channel if PGP/email not possible.

If you do not receive an acknowledgement within 72 hours, re-send or contact the maintainer via GitHub with "SECURITY" in the title.

---

## Maintainer responsibilities

Maintainers will:
- Acknowledge reports within 72 hours.
- Triage and assign severity within 5 business days when possible.
- Keep reporters updated periodically (status updates frequency depends on severity).
- Coordinate fixes and disclosure responsibly.
- Maintain confidential records of the communication and remediation actions.
- When a security advisory is published, include mitigation and upgrade steps.

---

## Post-incident: disclosure, post-mortems, and lessons learned

For significant incidents, we will publish a post-incident report that includes:
- Root cause analysis (technical, not identifying individuals)
- Timeline of detection and remediation
- Mitigations applied
- Steps to avoid recurrence

Personal data released in error will be redacted from public reports.

---

## Acknowledgements and credits

We appreciate security researchers and responsible disclosure. Past and future contributors reporting vulnerabilities in good faith will be acknowledged per their wishes in advisories and release notes.

---

## Change log for this policy

- 2025-10-18 — v1.0 — Initial comprehensive SECURITY.md created.

---

## Appendix — example GPG usage

1. Export public key to a file:
   ```bash
   gpg --export --armor "device-inspector (inspecta) <security@device-inspector.org>" > inspecta-pubkey.asc
   ```
2. Verify fingerprint:
   ```bash
   gpg --fingerprint "device-inspector (inspecta) <security@device-inspector.org>"
   ```
3. Encrypt a report:
   ```bash
   gpg --encrypt --recipient "device-inspector (inspecta) <security@device-inspector.org>" -o report.gpg report.txt
   ```

---

If you want, I can:
- Add the actual PGP public key block to this file (provide the key or ask me to generate one in the repo instructions).
- Produce an automated ISSUE_TEMPLATE for confidential security reports that reminds reporters to encrypt before sending.
- Draft a GitHub Actions workflow skeleton to run dependency scanning and secret-detection on PRs.

Choose which follow-up you want and I will generate it next.
