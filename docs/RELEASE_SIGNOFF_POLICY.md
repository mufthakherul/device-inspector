# Release Signoff Policy

This policy defines measurable approval and evidence requirements for release channel promotion.

## Channel requirements

| Channel | Tag pattern | Required approvals | Mandatory checks |
|---|---|---:|---|
| alpha | `vX.Y.Z-alpha.N` | 1 | release-channel-gates, build-release, sbom-security, distribution-manifest |
| beta | `vX.Y.Z-beta.N` | 1 | release-channel-gates, build-release, sbom-security, distribution-manifest |
| stable | `vX.Y.Z` | 2 | release-channel-gates, build-release, sbom-security, distribution-manifest |

## Signoff record format

For each tagged release, include a signoff file at:

- `release-signoffs/<tag>.json`

Required JSON fields:

- `approved_by`: array of approver names
- `checks`: object containing boolean values for:
  - `release_channel_gates`
  - `build_release`
  - `sbom_security`
  - `distribution_manifest`
- `risk_acknowledgement`: non-empty release risk summary

## Validation and audit trail

- Validation runs via `.github/workflows/release-signoff-gate.yml`.
- Policy checks enforced by `tools/validate_release_signoff.py`.
- Audit trail artifact: `test-output/release-signoff-audit.json`.

## Promotion governance intent

This policy provides a measurable release promotion baseline and prevents channel progression without explicit approvals and evidence-backed checks.
