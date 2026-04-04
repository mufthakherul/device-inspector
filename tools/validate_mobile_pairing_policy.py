"""Validate mobile offline pairing policy and hardening requirements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_MODES = {"qr", "file", "lan"}


def validate_mobile_pairing_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    pairing = policy.get("pairing")
    if not isinstance(pairing, dict):
        return ["pairing object missing"]

    token_prefix = pairing.get("token_prefix")
    if token_prefix != "inspecta:pairing:offline":
        errors.append("pairing.token_prefix must be 'inspecta:pairing:offline'")

    modes = pairing.get("modes", [])
    if not isinstance(modes, list):
        errors.append("pairing.modes must be a list")
    else:
        mode_set = {str(item) for item in modes}
        missing_modes = sorted(REQUIRED_MODES - mode_set)
        if missing_modes:
            errors.append(f"pairing.modes missing required entries: {missing_modes}")

    ttl = pairing.get("max_ttl_minutes")
    if not isinstance(ttl, int) or ttl <= 0 or ttl > 15:
        errors.append("pairing.max_ttl_minutes must be int between 1 and 15")

    security = pairing.get("security")
    if not isinstance(security, dict):
        errors.append("pairing.security must be an object")
    else:
        if security.get("require_integrity_hash") is not True:
            errors.append("security.require_integrity_hash must be true")
        if security.get("disallow_cloud_dependency") is not True:
            errors.append("security.disallow_cloud_dependency must be true")
        if security.get("rotation_required") is not True:
            errors.append("security.rotation_required must be true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate mobile pairing policy")
    parser.add_argument(
        "--policy",
        default="apps/mobile/pairing-policy-1.0.0.json",
    )
    parser.add_argument(
        "--report",
        default="test-output/mobile-pairing-policy-report.json",
    )
    args = parser.parse_args()

    policy_path = Path(args.policy)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))

    errors = validate_mobile_pairing_policy(policy)
    report = {
        "report_version": "1.0.0",
        "policy_version": policy.get("policy_version"),
        "ok": len(errors) == 0,
        "errors": errors,
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("[mobile-pairing-policy] validation")
    print(f"  policy: {policy_path}")
    print(f"  ok: {report['ok']}")
    print(f"  report: {report_path}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
