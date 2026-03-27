# AI & Developer Collaboration Guide

Use this guide when coding directly or through AI assistants (Copilot, GPT, Claude, VS Code agents, GitHub agents, etc.). It captures the project’s ground rules so human and AI contributors stay consistent, predictable, and reviewable.

## Core Principles
- Ship auditable diagnostics: every result should be backed by artifacts (logs/JSON) and transparent scoring.
- Respect the stack: Python 3.11+; Black/ruff/isort styling; pytest for tests; click CLI.
- Prefer reviewable changes; explain intent and risk in PR descriptions.
- Keep the repo clean: archive replaced/outdated files under `archives/` with a short README noting why they moved.

## Working Style
- Plan first: outline the change, risks, and test plan before coding. Keep scope as needed but complete.
- Read existing code before adding new patterns; reuse helpers in `agent/` and `agent/plugins/`.
- Make behavior obvious: fail fast with clear errors; log to `artifacts/agent.log` for CLI flows.
- Avoid speculative features; align with Roadmap and existing interfaces.

## Coding Standards
- Formatting: Black with target `py311`; import ordering via isort style; ruff for lint.
- Typing: prefer explicit types for public functions; keep signatures stable unless justified.
- Errors: raise domain errors from `agent.exceptions` or return structured error dicts used in reports/tests.
- Logging: use structured logging via `logging_utils.setup_logging`; avoid print except for CLI UX.
- CLI: keep click commands ergonomic; new flags require tests and documentation updates.

## Tests & Quality
- Baseline: run `python -m pytest` before and after changes; keep coverage ≥ existing threshold.
- Lint locally when touching logic: `ruff check .` and `black .` (these run in CI as `black --check .`).
- Add/adjust tests in `tests/` when changing behavior, parsing, or formats.
- Keep sample fixtures stable; add new fixtures under `samples/` and document their source.

## Documentation & Changelog
- Update relevant docs when behavior or UX changes (`docs/`, README, ROADMAP). Keep instructions concise and actionable.
- Note user-facing changes in PR descriptions; include migration/upgrade steps when needed.

## Archiving Rules
- Do not delete history. When replacing or removing docs/specs/scripts, move them to `archives/<category>/` and add a one-line reason plus date in a local README.
- Keep links alive: update references pointing to archived files.

## CI & Workflow Expectations
- CI runs formatting (Black) on Python 3.11; ensure the code parses under that target.
- Keep outputs deterministic; avoid time- or host-dependent behavior in tests.
- Secrets: never hardcode credentials; prefer environment variables and document them.

## How to Ask / Use AI
- Provide full context: goal, constraints, file paths, and expected inputs/outputs.
- Prefer targeted edits over large rewrites; review AI changes for style, safety, and licensing.
- When AI suggests new dependencies, justify them and update `pyproject.toml`/requirements only if essential.
