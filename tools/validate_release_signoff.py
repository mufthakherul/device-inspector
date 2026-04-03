"""Validate release signoff records against channel policy."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def classify_channel(tag: str) -> str:
    stable = re.compile(r"^v\d+\.\d+\.\d+$")
    alpha = re.compile(r"^v\d+\.\d+\.\d+-alpha\.\d+$")
    beta = re.compile(r"^v\d+\.\d+\.\d+-beta\.\d+$")

    if stable.match(tag):
        return "stable"
    if beta.match(tag):
        return "beta"
    if alpha.match(tag):
        return "alpha"
    raise ValueError(f"Unsupported release tag format: {tag}")


def required_approvals(channel: str) -> int:
    mapping = {"alpha": 1, "beta": 1, "stable": 2}
    return mapping.get(channel, 2)


def validate_signoff_payload(tag: str, payload: dict) -> list[str]:
    errors: list[str] = []

    channel = classify_channel(tag)
    required = required_approvals(channel)

    approved_by = payload.get("approved_by")
    if not isinstance(approved_by, list) or not all(
        isinstance(item, str) and item.strip() for item in approved_by
    ):
        errors.append("approved_by must be a non-empty list of approver names")
    elif len(approved_by) < required:
        errors.append(
            f"{channel} requires at least {required} approvals, got {len(approved_by)}"
        )

    checks = payload.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks must be an object")
    else:
        required_checks = [
            "release_channel_gates",
            "build_release",
            "sbom_security",
            "distribution_manifest",
        ]
        for key in required_checks:
            if checks.get(key) is not True:
                errors.append(f"checks.{key} must be true")

    note = payload.get("risk_acknowledgement")
    if not isinstance(note, str) or not note.strip():
        errors.append("risk_acknowledgement must be a non-empty string")

    return errors


def build_audit(tag: str, payload: dict, errors: list[str]) -> dict:
    channel = classify_channel(tag)
    return {
        "audit_version": "1.0.0",
        "generated_at": _now_iso(),
        "tag": tag,
        "channel": channel,
        "required_approvals": required_approvals(channel),
        "approved_by_count": (
            len(payload.get("approved_by", []))
            if isinstance(payload.get("approved_by"), list)
            else 0
        ),
        "status": "passed" if not errors else "failed",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release signoff record")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--signoff-json", required=True)
    parser.add_argument(
        "--audit-output", default="test-output/release-signoff-audit.json"
    )
    args = parser.parse_args()

    signoff_path = Path(args.signoff_json)
    payload = json.loads(signoff_path.read_text(encoding="utf-8"))

    errors = validate_signoff_payload(args.tag, payload)
    audit = build_audit(args.tag, payload, errors)

    audit_path = Path(args.audit_output)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    print("[release-signoff-validator] complete")
    print(f"  tag: {args.tag}")
    print(f"  status: {audit['status']}")
    print(f"  audit: {audit_path}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
