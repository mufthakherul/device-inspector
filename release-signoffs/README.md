# Release Signoffs

Store per-tag signoff records here using the format:

- `release-signoffs/<tag>.json`

Example file content:

```json
{
  "approved_by": ["release-manager", "security-lead"],
  "checks": {
    "release_channel_gates": true,
    "build_release": true,
    "sbom_security": true,
    "distribution_manifest": true
  },
  "risk_acknowledgement": "No blocking release risks."
}
```

These records are validated by:

- `.github/workflows/release-signoff-gate.yml`
- `tools/validate_release_signoff.py`
