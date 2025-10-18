# REPORT_SCHEMA.md

Last updated: 2025-10-18

This document is the canonical, human-readable specification for the machine-readable report produced by device-inspector (inspecta). It defines the JSON schema, field semantics, validation rules, signing/manifest conventions, examples, and guidance for implementers, verifiers, and integrators.

Purpose
- Provide a stable, versioned JSON Schema that agents produce and consumers (viewers, backends, verifiers) validate.
- Ensure report portability, auditability, and machine-consumable semantics for scoring, artifacts, and evidence.
- Document expected fields, optional extensions, and rules for signing and verifying reports.

Important notes
- The top-level schema version is represented in `report_version`. Implementations MUST include a precise version string (semantic version format like `1.0.0`).
- This schema is normative: agents MUST produce JSON that validates against the schema for the declared `report_version`.
- The schema is intentionally strict about core fields but allows extensibility via the `extensions` object and `tests[].metadata` fields.

Compatibility & versioning
- Schema changes that add optional fields are backward compatible.
- Additive changes (new optional fields) do not require a schema version bump, but recommend bumping `report_version` for clarity.
- Breaking changes MUST increment major version (e.g., 2.x.x) and be documented in CHANGELOG.

Validation tooling
- Use a JSON Schema validator (e.g., `jsonschema` Python package, `ajv` for Node) to validate `report.json`.
- When validating signatures, verify canonicalization (see Signing section) and manifest checksums before schema validation where appropriate.

---

1) Canonical JSON Schema (draft-07)
Below is the canonical JSON Schema for report version 1.0.0. This is the authoritative machine-checkable schema; keep a machine copy as `report-schema.json` in the repo.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/mufthakherul/device-inspector/schemas/report-schema-1.0.0.json",
  "title": "device-inspector report",
  "description": "Canonical report schema for inspecta (device-inspector) reports (version 1.0.0).",
  "type": "object",
  "additionalProperties": false,
  "required": ["report_version", "generated_at", "agent_version", "device", "summary", "scores", "tests", "artifacts", "evidence"],
  "properties": {
    "report_version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
      "description": "Semantic version of the report schema (MAJOR.MINOR.PATCH)."
    },
    "generated_at": {
      "type": "string",
      "format": "date-time",
      "description": "UTC timestamp when the report was generated in ISO 8601 format."
    },
    "agent_version": {
      "type": "string",
      "description": "Version of the inspecta agent that produced the report."
    },
    "run_id": {
      "type": "string",
      "description": "Unique identifier for the run (UUID recommended).",
      "pattern": "^[a-f0-9-]{8,36}$"
    },
    "device": {
      "type": "object",
      "additionalProperties": false,
      "required": ["vendor", "model"],
      "properties": {
        "vendor": { "type": "string" },
        "model": { "type": "string" },
        "serial": { "type": "string" },
        "bios": { "type": "string" },
        "sku": { "type": "string" },
        "manufacture_date": { "type": "string", "format": "date" },
        "os": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "name": { "type": "string" },
            "version": { "type": "string" },
            "kernel": { "type": "string" },
            "arch": { "type": "string" }
          }
        },
        "notes": { "type": "string", "maxLength": 2000 }
      }
    },
    "summary": {
      "type": "object",
      "additionalProperties": false,
      "required": ["overall_score", "grade", "issues_count", "recommendation"],
      "properties": {
        "overall_score": { "type": "number", "minimum": 0, "maximum": 100 },
        "grade": { "type": "string", "enum": ["Excellent", "Good", "Fair", "Poor"] },
        "issues_count": { "type": "integer", "minimum": 0 },
        "recommendation": { "type": "string" }
      }
    },
    "scores": {
      "type": "object",
      "additionalProperties": false,
      "required": ["storage", "battery", "memory", "cpu_thermal", "gpu", "network", "security"],
      "properties": {
        "storage": { "type": "number", "minimum": 0, "maximum": 100 },
        "battery": { "type": "number", "minimum": 0, "maximum": 100 },
        "memory": { "type": "number", "minimum": 0, "maximum": 100 },
        "cpu_thermal": { "type": "number", "minimum": 0, "maximum": 100 },
        "gpu": { "type": "number", "minimum": 0, "maximum": 100 },
        "network": { "type": "number", "minimum": 0, "maximum": 100 },
        "security": { "type": "number", "minimum": 0, "maximum": 100 },
        "screen": { "type": "number", "minimum": 0, "maximum": 100 }
      }
    },
    "tests": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "smart": { "$ref": "#/definitions/testSmart" },
        "memtest": { "$ref": "#/definitions/testMemtest" },
        "cpu_benchmark": { "$ref": "#/definitions/testGeneric" },
        "disk_benchmark": { "$ref": "#/definitions/testGeneric" },
        "thermal_stress": { "$ref": "#/definitions/testThermal" },
        "battery": { "$ref": "#/definitions/testBattery" },
        "network": { "$ref": "#/definitions/testGeneric" },
        "custom": {
          "type": "array",
          "items": { "$ref": "#/definitions/testGeneric" }
        }
      }
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["type", "path", "sha256", "size_bytes"],
        "properties": {
          "type": { "type": "string", "description": "One of smart, memtest, cpu_bench, disk_bench, sensors, image, video, audio, other" },
          "path": { "type": "string", "description": "Relative path within the report bundle to the artifact file" },
          "sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
          "size_bytes": { "type": "integer", "minimum": 0 },
          "mime_type": { "type": "string" },
          "description": { "type": "string" }
        }
      }
    },
    "raw_logs": {
      "type": "object",
      "additionalProperties": true,
      "description": "Optional map of short names to log contents or relative paths. Implementations should prefer storing logs as artifacts and reference them here."
    },
    "evidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["manifest_sha256", "signed"],
      "properties": {
        "manifest_sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
        "signed": { "type": "boolean" },
        "signer_key_id": { "type": "string", "description": "Identifier of the public key used to sign (optional)" },
        "upload_consent": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "consented": { "type": "boolean" },
            "timestamp": { "type": "string", "format": "date-time" },
            "uploader": { "type": "string" }
          }
        }
      }
    },
    "extensions": {
      "type": "object",
      "description": "Optional extension map for vendor- or integrator-specific fields. Keys SHOULD be namespaced (e.g., com.vendor.feature).",
      "additionalProperties": true
    }
  },
  "definitions": {
    "testBase": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "start_ts", "end_ts"],
      "properties": {
        "id": { "type": "string" },
        "status": { "type": "string", "enum": ["PASS", "WARN", "FAIL", "SKIPPED"] },
        "score": { "type": "number", "minimum": 0, "maximum": 100, "description": "Optional per-test score 0..100" },
        "start_ts": { "type": "string", "format": "date-time" },
        "end_ts": { "type": "string", "format": "date-time" },
        "log": { "type": "string", "description": "Relative path to a log artifact or inline text" },
        "artifacts": {
          "type": "array",
          "items": { "type": "string" },
          "description": "List of artifact paths related to this test"
        },
        "metadata": { "type": "object", "additionalProperties": true, "description": "Plugin-specific metadata" }
      }
    },
    "testSmart": {
      "allOf": [
        { "$ref": "#/definitions/testBase" },
        {
          "type": "object",
          "required": ["parsed"],
          "properties": {
            "parsed": {
              "type": "object",
              "additionalProperties": true,
              "properties": {
                "device": { "type": "string" },
                "model": { "type": "string" },
                "serial": { "type": "string" },
                "health": { "type": "string" },
                "attributes": {
                  "type": "object",
                  "additionalProperties": true
                }
              }
            }
          }
        }
      ]
    },
    "testMemtest": {
      "allOf": [
        { "$ref": "#/definitions/testBase" },
        {
          "type": "object",
          "properties": {
            "errors": { "type": "integer", "minimum": 0 },
            "passes": { "type": "integer", "minimum": 0 },
            "details": { "type": "string" }
          }
        }
      ]
    },
    "testGeneric": {
      "allOf": [
        { "$ref": "#/definitions/testBase" },
        {
          "type": "object",
          "properties": {
            "tool": { "type": "string" },
            "result": { "type": "object", "additionalProperties": true }
          }
        }
      ]
    },
    "testThermal": {
      "allOf": [
        { "$ref": "#/definitions/testBase" },
        {
          "type": "object",
          "properties": {
            "max_cpu_c": { "type": "number" },
            "throttled": { "type": "boolean" },
            "samples_csv": { "type": "string" }
          }
        }
      ]
    },
    "testBattery": {
      "allOf": [
        { "$ref": "#/definitions/testBase" },
        {
          "type": "object",
          "properties": {
            "design_capacity_mwh": { "type": "number" },
            "full_capacity_mwh": { "type": "number" },
            "cycles": { "type": "integer" },
            "health_pct": { "type": "number", "minimum": 0, "maximum": 100 }
          }
        }
      ]
    }
  }
}
```

---

2) Field semantics & rules (detailed)
This section explains the meaning and recommended usage of each top-level field.

- report_version
  - Format: semver MAJOR.MINOR.PATCH (e.g., "1.0.0").
  - Agents MUST set this to the schema version they adhere to. Consumers SHOULD reject future major versions they don't support.

- generated_at
  - Use UTC ISO 8601 with timezone (e.g., "2025-10-18T18:00:00Z").
  - This timestamp is critical for evidence freshness and manifests.

- agent_version
  - Should reflect the agent package version (semantic version preferred).
  - Useful to reproduce behavior or parser compatibility.

- run_id
  - Unique per-run id (use UUIDv4). Useful for correlating artifacts and uploads.

- device
  - vendor, model are REQUIRED; prefer authoritative strings from dmidecode or system API.
  - serial recommended but may be redacted by the user prior to upload; the agent should include a `redaction` note in `extensions` if that occurs.

- summary
  - overall_score: 0..100. Calculated by weighted aggregation of `scores`. Round to integer or one decimal as desired.
  - grade: One of ["Excellent", "Good", "Fair", "Poor"] — derived from overall_score using documented thresholds.
  - issues_count: Number of items in the issues list (not part of the schema core but recommended in `extensions` if you implement a structured `issues` list).
  - recommendation: Short human-readable text for the buyer (recommendation MUST be conservative and include limitations).

- scores
  - Each category 0..100. If a category does not apply (e.g., battery on desktop), set to 100 and add `extensions` note. Alternatively, set to `null` (but the current schema requires numeric fields) — recommended practice: set to 100 and indicate "not_applicable" in extensions.

- tests
  - Each test object must include `status`, `start_ts`, `end_ts`.
  - Include `artifacts` array with relative artifact paths (these must correspond to items in `artifacts[]` at top-level).
  - For any test that produces large binary output (images, logs), store the file under `artifacts/` and reference by path.

- artifacts
  - Always include `sha256` (hex lowercase 64 chars) and `size_bytes`.
  - The `path` MUST be relative (no `..`) and indicate location inside the bundled report folder.
  - For uploaded reports, the server MUST verify these checksums before accepting and must compare the `manifest_sha256` to the report body.

- evidence.manifest_sha256 & signing
  - `manifest_sha256` is the SHA256 hex of the manifest.json file in the bundle (manifest lists artifacts and their checksums).
  - `signed` indicates whether a detached signature was produced and included; `signer_key_id` optionally records the signer's public key fingerprint or identifier.

---

3) Manifest and bundle format
A report bundle (what should be archived and optionally signed) must contain:
- report.json (the top-level report)
- artifacts/ (all artifact files)
- manifest.json (listing artifact paths and checksums, plus report.json checksum)
- manifest.sig (optional) — detached signature of `manifest.json` or of canonicalized manifest+report

manifest.json format (example):
```json
{
  "report_sha256": "6a3b...f1e",
  "artifacts": [
    { "path": "artifacts/smart_nvme0.json", "sha256": "abc123...", "size_bytes": 45678 },
    { "path": "artifacts/memtest.log", "sha256": "def456...", "size_bytes": 1234 }
  ],
  "generated_at": "2025-10-18T18:00:00Z"
}
```

Bundle verification steps:
1. Compute SHA256(report.json) and compare to `manifest.report_sha256`.
2. For each artifact, compute SHA256 and compare to list in manifest.
3. Verify `manifest.sig` (if present) using the signer's public key.
4. Validate report.json against schema.

Canonicalization
- Before signing manifest.json, use deterministic JSON canonicalization (e.g., JSON Canonicalization Scheme — JCS — RFC 8785) so signatures are reproducible across implementations.
- Document the canonicalization used in the repo and tool code.

---

4) Signing recommendations
- Algorithm: Ed25519 recommended (compact, fast). RSA-PSS acceptable for compatibility but larger keys.
- Key management:
  - User-generated keypair stored locally (private key protected by filesystem permissions). The agent must never upload private keys.
  - Optionally: hardware-backed keys (YubiKey) supported; document user instructions.
- Signature object:
  - Detached binary (recommended) named `manifest.sig` or `manifest.sig.base64`.
  - Include signer's public key fingerprint in `report.json.evidence.signer_key_id`.
- Verification tool:
  - Provide `inspecta verify --bundle signed_bundle.zip` to automate steps: manifest checksum, signature verification, schema validation.

---

5) Examples

Minimal example (excerpt):
```json
{
  "report_version": "1.0.0",
  "generated_at": "2025-10-18T18:00:00Z",
  "agent_version": "0.1.0",
  "run_id": "b3d4e9e2-2d9b-4aab-a1c4-3f12b9d0a1e6",
  "device": {
    "vendor": "Dell",
    "model": "XPS 9560",
    "serial": "ABC123",
    "bios": "1.23.4",
    "os": { "name": "Ubuntu", "version": "22.04", "kernel": "5.15.0-xx" }
  },
  "summary": {
    "overall_score": 78,
    "grade": "Good",
    "issues_count": 3,
    "recommendation": "Best for: Developers & Office. Replace battery soon; check fan."
  },
  "scores": {
    "storage": 92,
    "battery": 60,
    "memory": 100,
    "cpu_thermal": 70,
    "gpu": 55,
    "network": 80,
    "security": 100,
    "screen": 85
  },
  "tests": {
    "smart": {
      "id": "smart-nvme0",
      "status": "WARN",
      "start_ts": "2025-10-18T17:51:00Z",
      "end_ts": "2025-10-18T17:51:10Z",
      "parsed": {
        "device": "/dev/nvme0n1",
        "health": "PASSED",
        "attributes": { "reallocated_sectors": 0, "percentage_used": 6 }
      },
      "artifacts": ["artifacts/smart_nvme0.json"],
      "log": "artifacts/smart_nvme0.json"
    }
  },
  "artifacts": [
    { "type": "smart", "path": "artifacts/smart_nvme0.json", "sha256": "abc...", "size_bytes": 1234, "mime_type": "application/json" },
    { "type": "image", "path": "artifacts/camera_001.jpg", "sha256": "def...", "size_bytes": 23456, "mime_type": "image/jpeg" }
  ],
  "evidence": {
    "manifest_sha256": "6a3b...f1e",
    "signed": false
  }
}
```

---

6) Extensions & custom fields
- The `extensions` object allows additional structured or vendor-specific data. Keys SHOULD be namespaced (e.g., `com.example.repair_estimate`).
- Consumers MUST ignore unknown extension keys they don't understand.
- If an extension provides security-critical fields (e.g., alternate signatures), document their semantics and validation rules.

---

7) Implementation guidance & advice for authors
- Always write tests for parsers with real samples (include sample smartctl JSON in `/samples`).
- Keep the report schema stable; prefer additive changes and document breaking changes carefully.
- When adding optional fields, update `report_version` minor or patch number and add compatibility notes.
- Provide helper libraries for common languages (Python, Node) to produce/validate reports and sign/verify bundles. Keep canonicalization consistent across libraries.

---

8) Privacy & redaction rules
- If a user requests redaction (e.g., serial number), record this in `extensions.redaction` with:
  - field name(s) redacted,
  - redaction reason or user consent,
  - timestamp.
- Example:
```json
"extensions": {
  "com.inspecta.redaction": {
    "redacted_fields": ["device.serial"],
    "reason": "user-request",
    "timestamp": "2025-10-18T18:01:00Z"
  }
}
```
- When redaction occurs, signing still applies to the redacted bundle; verifyers must understand the redaction statement.

---

9) Common validation errors & remediations
- Missing required fields: Ensure `report_version`, `generated_at`, `agent_version`, `device`, `summary`, `scores`, `tests`, `artifacts`, and `evidence` are present.
- Artifact checksum mismatch: Recompute checksums, ensure paths are relative, and the manifest corresponds to actual files.
- Invalid timestamp format: Use full ISO 8601 with timezone (e.g., "2025-10-18T18:00:00Z").
- Non-numeric scores outside 0..100: Clamp or recalculate to the range before writing the report.

---

10) Signing & verification workflows (practical)
- Agent side:
  1. Finish tests and write `report.json`.
  2. Create `artifacts/` and compute per-artifact sha256; write `manifest.json`.
  3. Compute SHA256(report.json) and set `manifest.report_sha256`.
  4. Canonicalize `manifest.json` and sign producing `manifest.sig`.
  5. Set `evidence.manifest_sha256` to SHA256(manifest.json) and `evidence.signed = true`.
  6. Optionally pack into `inspecta-report-<run_id>.tar.gz` and provide to user.

- Verification side:
  1. Extract bundle.
  2. Verify SHA256 of manifest matches `report.evidence.manifest_sha256`.
  3. Verify artifact checksums from manifest.
  4. Verify manifest signature (if present) using `signer_key_id` public key.
  5. Validate `report.json` against schema.

---

11) Maintenance & change log
- Keep this markdown and the machine `report-schema.json` in sync.
- Any change to the schema MUST be accompanied by:
  - an updated `report_version`,
  - unit tests and example report(s),
  - migration guidance (how consumers should handle older versions).
- CHANGELOG entry example:
  - `2025-10-18 - 1.0.0 - initial schema and docs`

---

12) Appendix: validator quickstart (Python)
- Install:
  ```bash
  pip install jsonschema==3.2.0
  ```
- Example validation:
  ```python
  import json, jsonschema
  schema = json.load(open("report-schema-1.0.0.json"))
  report = json.load(open("report.json"))
  jsonschema.validate(report, schema)
  ```
- For canonical signing (JCS), use an established library for canonicalization before signing.

---

13) FAQ
Q: What if a field is unknown to the schema?
A: Consumers MUST ignore unknown fields unless they are critical for business logic. Use `extensions` for custom data.

Q: Can I omit battery scores on desktops?
A: Battery score should be set to 100 or a special sentinel in `extensions` indicating "not_applicable". The current schema requires numeric fields, so prefer 100 + extension note.

Q: How to represent partial runs?
A: Use test `status` = `"SKIPPED"` for tests not executed and include `metadata.skip_reason`.

---

14) Contact & contributions
- Report schema maintenance: PRs accepted via CONTRIBUTING.md.
- For schema evolution and proposals, open `rfc` labeled issues and reference `REPORT_SCHEMA.md` changes needed.

---

Thank you — this document is the authoritative description for the inspecta report JSON. Implementers: keep parsers, generators, and verifiers aligned with this schema and document any extension fields you introduce. If you want, I can now generate the machine `report-schema.json` file (exact JSON file) ready to commit to the repository, plus example `manifest.json` and a signed-bundle verification script (Python). Which would you like me to produce next?
