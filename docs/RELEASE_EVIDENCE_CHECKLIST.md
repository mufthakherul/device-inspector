# Release Evidence Checklist

Use this checklist for every tagged release and keep links to run artifacts in the release notes.

## 1) Build and test evidence

- [ ] `ci-core.yml` passed on target commit
- [ ] `ci-integration-matrix.yml` passed on target commit
- [ ] Full test run succeeded with coverage gate pass
- [ ] Lint and format checks passed (`ruff`, `black --check`)

## 2) Security and integrity evidence

- [ ] `sbom-security.yml` completed with policy checks
- [ ] Release artifacts include `SHA256SUMS`
- [ ] Detached signatures are present when signing secrets are configured
- [ ] `inspecta verify` and `inspecta audit` validation paths confirmed

## 3) Distribution and channel evidence

- [ ] Release channel gates passed (`release-channel-gates.yml`)
- [ ] Promotion plan generated (`channel-promotion.yml` artifact)
- [ ] Distribution manifest refreshed (`docs-site/data/distribution-manifest.json`)
- [ ] Platform packaging lanes completed (desktop/mobile/iso as applicable)

## 4) Documentation and governance evidence

- [ ] `ROADMAP.md`, `PROJECT_GOAL.md`, and `PROJECT_READINESS.md` are synchronized
- [ ] Doc-claim validator report generated and clean
- [ ] KPI snapshot generated and passes quality gate
- [ ] Rollback notes included in release tracking

## 5) Release approval summary

- Release tag: `____________`
- Commit SHA: `____________`
- Approver(s): `____________`
- Evidence bundle link(s): `____________`
- Exceptions / risk notes: `____________`
