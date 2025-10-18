# Contributing to device-inspector (inspecta)

Thank you for your interest in contributing to device-inspector (inspecta). This document explains the project's contribution workflow, code and documentation standards, testing & CI expectations, governance for issues and pull requests, security reporting, and onboarding steps for new contributors. Please read this file carefully before opening issues or PRs.

TL;DR
- Read the Code of Conduct (CODE_OF_CONDUCT.md) — be respectful.
- This project is public and licensed for non-commercial use (LICENSE.txt). Contributions are accepted under the contribution terms described in the license; see section "Contributions & Copyright" below.
- Fork → branch → commit → open Pull Request (PR) to `main`.
- Follow the commit, branch, and PR naming conventions below.
- Run tests and linters locally before submitting; CI runs automatically on PRs.

Table of contents
- Getting started
- Reporting issues (bugs) and filing feature requests
- Design discussions & RFCs
- Branching model and naming conventions
- Commit message guidelines
- Coding standards & linters
- Tests: unit, integration, e2e
- Pre-commit hooks and developer tooling
- Pull request process & review checklist
- Labels, milestones & project board usage
- Security & responsible disclosure
- Contributor rights & license
- Release, versioning and changelog
- Documentation, localization & examples
- Onboarding and mentorship for first-time contributors
- Frequently asked questions
- Contact & maintainers

----------------------------------------------------------------
Getting started (first-time contributor)
----------------------------------------------------------------

1. Fork the repository on GitHub.
2. Clone your fork:
   ```bash
   git clone git@github.com:<your-username>/device-inspector.git
   cd device-inspector
   git remote add upstream git@github.com:mufthakherul/device-inspector.git
   ```
3. Create a branch for your work (see Branching model below):
   ```bash
   git checkout -b feat/my-feature-short-description
   ```
4. Set up the development environment (Linux recommended). Minimal example steps (subject to change when code is available):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt   # when available
   ```
5. Run linters and tests locally (see Tests & Linters sections).
6. Commit changes, push your branch to your fork and open a Pull Request (PR) targeting `main`.

If you want a small task to start with, check the "good first issue" label on issues — we tag those for newcomers.

----------------------------------------------------------------
Reporting Issues (bug reports) and Feature Requests
----------------------------------------------------------------

Issue quality guidelines:
- Search existing issues and PRs before opening a new one.
- Choose the appropriate template (bug report vs feature request).
- Provide reproducible steps, exact command lines, OS and version, agent version (when available), and attach minimal logs (redacted for personal data) or `report.json` if relevant.
- Keep titles short and descriptive: `BUG: smartctl errors on NVMe with sample output` or `FEATURE: add sysbench-based CPU microbenchmark`.

Bug report template (short):
- Title: clear short description
- Environment: OS, kernel, agent version, tools (smartctl version, etc.)
- Steps to reproduce
- Expected behavior
- Actual behavior
- Attachments: small logs, `report.json`, truncated outputs

Feature request template (short):
- Problem statement
- Proposed design / API (if known)
- User story(s)
- Risks & alternatives
- Backwards compatibility considerations

----------------------------------------------------------------
Design discussions & RFCs
----------------------------------------------------------------

For significant design or architecture changes (new subsystems, scoring changes, evidence signing, backend APIs), open a design discussion or an RFC issue and label it `design` or `rfc`. The RFC should include:
- Motivation and goals
- Proposed design and alternatives
- Impact on users and backward compatibility
- Security, privacy, and legal considerations
- Migration path and rollout plan

We encourage community feedback on RFCs. Major changes require consensus from maintainers.

----------------------------------------------------------------
Branching model & naming conventions
----------------------------------------------------------------

Branching model:
- `main` — stable development branch; PRs should target `main`.
- Feature branches: `feat/<short-desc>` OR `feature/<short-desc>`
- Bugfix branches: `fix/<short-desc>` or `bug/<short-desc>`
- Hotfix branches (if needed for emergency fixes after release): `hotfix/<short-desc>`
- Docs: `docs/<short-desc>`
- Experiments: `exp/<short-desc>` (not for long-lived code)

Branch naming examples:
- `feat/quick-mode-report-json`
- `fix/smartctl-nvme-detection`
- `docs/README-improvements`

----------------------------------------------------------------
Commit message conventions
----------------------------------------------------------------

We use Conventional Commits style as a guideline. Keep commits focused and atomic.

Recommended format:
```
<type>(<scope>): <short summary>

Optional longer description and reasoning. Wrap at ~72 characters.
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only changes
- `style` — formatting, missing semi-colons, etc (no code logic changes)
- `refactor` — code change that neither fixes a bug nor adds a feature
- `perf` — performance improvements
- `test` — adding or updating tests
- `chore` — build scripts, tooling, dependency updates

Examples:
- `feat(agent): add smartctl JSON parsing wrapper`
- `fix(cli): handle nvme devices when smartctl -d nvme is needed`

Sign commits (optional but recommended for maintainers):
```bash
git config user.signingkey <GPG_KEY_ID>
git commit -S -m "..."
```

----------------------------------------------------------------
Coding standards & linters
----------------------------------------------------------------

Please follow these style rules (subject to additions based on chosen language stack). When code exists, we'll publish specific linters/configs.

Python:
- Use Black for formatting: `black .`
- Use Flake8 / Ruff for linting: `ruff .` or `flake8 .`
- Type hints encouraged; use mypy for static typing.

Shell scripts:
- Follow `shellcheck` suggestions; use `shellcheck` in CI.

Go / Rust / Node / other languages:
- Use standard formatting tools (gofmt, cargo fmt, prettier/eslint, rustfmt).

Testing:
- Add tests for new features or behavior changes.
- Keep tests deterministic and fast where possible.
- Integration tests that require devices may be tagged and run separately.

----------------------------------------------------------------
Tests: unit, integration, e2e
----------------------------------------------------------------

- Unit tests: fast, isolated, no hardware dependency.
- Integration tests: may use docker or simulated devices; keep them optional in CI or gated into a slow-test job.
- Hardware/e2e tests: require real devices or bootable ISOs (Full mode). We will provide ways to run those locally; these are not required for PRs, but maintainers may run them before merging certain PRs.

Test commands (examples — implemented later):
```bash
pytest -q
pytest -q tests/unit
pytest -q tests/integration  # may require docker or specific tools
```

When adding tests:
- Include minimal fixtures.
- Avoid flakiness; use retry only when justified and documented.
- CI must pass all unit tests before PR merge.

----------------------------------------------------------------
Pre-commit hooks & developer tooling
----------------------------------------------------------------

We recommend using `pre-commit` to run linters and basic checks before commits. Example (to be added in repo):
- `pre-commit` config that runs:
  - black / ruff / isort (Python)
  - shellcheck (shell)
  - markdownlint (docs)
  - detect-secrets / git-secrets (to prevent committing secrets)

Install locally:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

We may provide a `devcontainer` and/or Docker-based development environment for reproducible builds.

----------------------------------------------------------------
Pull Request (PR) process & review checklist
----------------------------------------------------------------

Open a PR from your feature branch to `main`.

PR title format:
```
[type(scope)]: short summary
```
Example: `feat(agent): add quick-mode smartctl wrapper`

PR description should include:
- Summary of changes
- Related issues (link to `#123` or `Fixes #123` when closing)
- How to test locally (commands)
- CI status and known limitations
- If applicable: migration notes or breaking changes

Review checklist (maintainers or reviewers will verify):
- [ ] PR targets `main` and uses an appropriate branch naming
- [ ] The description explains the "why", not only the "what"
- [ ] All unit tests pass and new tests are provided where applicable
- [ ] Code follows style guides and passes linters
- [ ] No secrets or sensitive data included
- [ ] Documentation updated (README, docs, or inline comments) as needed
- [ ] Changes are modular and scoped
- [ ] Any design or security impact is documented
- [ ] Contributors have signed CLA if requested (see Contributions section)

Merging:
- PRs require at least one approving review from a maintainer (or two for major changes).
- CI must pass before merge.
- Maintain a fast turnaround for reviews but ensure quality.

----------------------------------------------------------------
Labels, milestones & project board usage
----------------------------------------------------------------

Labels (examples):
- `good first issue` — recommended for new contributors
- `bug` — confirmed bug
- `enhancement` — new feature
- `documentation` — docs improvement
- `design` / `rfc` — architecture proposals
- `help wanted` — maintainers request help
- `security` — security-related issues (handled privately)
- `priority:high/medium/low` — priority level

Milestones:
- Use milestones for releases or major sprints (MVP, v1.0, v1.1).
- When opening issues, assign to the appropriate milestone if known.

Project board:
- We use a project board (kanban) to track active work, in-review, blocked, and done items.

----------------------------------------------------------------
Security & Responsible Disclosure
----------------------------------------------------------------

If you discover a security vulnerability, DO NOT open a public issue. Follow the guidance in SECURITY.md:
- Contact the maintainers privately via the designated channel.
- Provide a detailed report: steps to reproduce, proof-of-concept, impacted versions, and suggested mitigation.
- We will acknowledge within 72 hours and coordinate a fix and disclosure.

We will respond respectfully and treat reports as confidential during investigation.

----------------------------------------------------------------
Contributions & Copyright
----------------------------------------------------------------

By contributing (submitting PRs, issues, or other content) you agree to the contributions terms in LICENSE.txt:
- You represent that you have the rights to submit the contribution.
- You grant the project a perpetual, worldwide, royalty-free license to use and redistribute your contributions under the project's license (see LICENSE.txt).
- The maintainers may ask you to sign a Contributor License Agreement (CLA) or a simple statement in a contribution 'sign-off' if needed for governance; we will only request this when necessary.

Please do not submit third-party code unless you are authorized to contribute it and you include license attribution.

----------------------------------------------------------------
Release process, versioning, and changelog
----------------------------------------------------------------

We follow Semantic Versioning (SemVer) for releases:
- MAJOR version when you make incompatible API changes,
- MINOR version when you add functionality in a backwards-compatible manner,
- PATCH version when you make backwards-compatible bug fixes.

Release steps (maintainers):
1. Prepare changelog entries (keep `CHANGELOG.md` or use GitHub Releases with release notes generated from PRs).
2. Bump version in code/artifacts (as applicable).
3. Tag release `vX.Y.Z` and push tags.
4. Create GitHub Release with notes and attach artifacts (tarball, ISO images, installers).

Backporting:
- Security patches may be backported to supported release branches as needed.

----------------------------------------------------------------
Documentation, examples & localization
----------------------------------------------------------------

Documentation is part of the project and should be kept up-to-date. When adding features:
- Update README.md, REPORT_SCHEMA.md, and any relevant docs in /docs.
- Add examples and sample outputs (`samples/`).
- Use clear, plain language to explain limitations (especially for hardware-dependent checks).
- For non-English translations, create a `/i18n/` folder with language-specific docs and indicate translation status.

----------------------------------------------------------------
Onboarding & mentorship for first-time contributors
----------------------------------------------------------------

We welcome new contributors. If you want to contribute but are uncertain where to start:
- Look for issues labeled `good first issue` or `help wanted`.
- Ask on the issue or discussion and a maintainer or volunteer will help you get oriented.
- We are willing to pair-review your first PR and provide coaching on tests and style.

----------------------------------------------------------------
Frequently asked questions (FAQ)
----------------------------------------------------------------

Q: I found personal data in artifacts — can I share it?
A: No. Do not post or upload artifacts with personal data to public issues. Redact or remove personal files before sharing. Use private disclosure channels per SECURITY.md if needed.

Q: Can I use code from this repo for commercial purposes?
A: Not without a separate commercial license from the Author. See LICENSE.txt. If you need commercial use, contact the Author for licensing.

Q: How long will maintainers take to review?
A: Target response time is 7–14 days for issues and PRs, depending on complexity and maintainer availability. Critical security or blocking issues may be escalated.

----------------------------------------------------------------
Contact & maintainers
----------------------------------------------------------------

Project owner / primary maintainer:
- GitHub: @mufthakherul

Maintainers, reviewers, and community volunteers will be listed in MAINTAINERS.md (to be added).

----------------------------------------------------------------
Help us keep the project healthy
----------------------------------------------------------------

- File well-formed issues and PRs.
- Add tests for bugs and new features.
- Keep your PRs small and focused.
- Be patient and kind in reviews—maintainers are volunteers.

----------------------------------------------------------------
Acknowledgements
----------------------------------------------------------------

We adapt best practices from many open-source projects. This CONTRIBUTING.md is intended to make contribution simple and predictable for everyone.

----------------------------------------------------------------
Version history of this document
----------------------------------------------------------------

- v1.0 — Initial comprehensive contributing guide (2025-10-18)

----------------------------------------------------------------
If you want, I can:
- produce ready-to-use issue templates and PR templates aligned to this contributing guide,
- generate a `pre-commit` configuration and `pyproject.toml` skeleton,
- produce a CI (GitHub Actions) workflow skeleton for linting and tests.
