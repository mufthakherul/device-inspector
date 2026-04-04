"""Validate desktop migration gate criteria for Electron/Tauri parity readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate_desktop_migration_gate(
    adapter_contract: dict[str, Any],
    criteria: dict[str, Any],
    desktop_package: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    req = criteria.get("requirements", {})
    required_commands = req.get("required_commands", [])
    required_scripts = req.get("required_desktop_scripts", [])
    required_windows_targets = req.get("required_windows_targets", [])

    if adapter_contract.get("offline_guarantee") != req.get("offline_guarantee"):
        errors.append("offline_guarantee requirement failed")

    cli_entrypoint = str(adapter_contract.get("cli_entrypoint", ""))
    expected_prefix = str(req.get("required_cli_entrypoint_prefix", ""))
    if not cli_entrypoint.startswith(expected_prefix):
        errors.append("cli_entrypoint prefix requirement failed")

    commands = adapter_contract.get("commands", {})
    for command_name in required_commands:
        if command_name not in commands:
            errors.append(f"missing command contract: {command_name}")

    scripts = (
        (desktop_package.get("scripts") or {})
        if isinstance(desktop_package, dict)
        else {}
    )
    for script_name in required_scripts:
        if script_name not in scripts:
            errors.append(f"missing desktop script: {script_name}")

    windows_targets = (
        ((desktop_package.get("build") or {}).get("win") or {}).get("target")
        if isinstance(desktop_package, dict)
        else []
    )
    if not isinstance(windows_targets, list):
        windows_targets = []

    for target in required_windows_targets:
        if target not in windows_targets:
            errors.append(f"missing windows target: {target}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate desktop migration gate")
    parser.add_argument(
        "--adapter-contract",
        default="apps/desktop/engine/adapter-contract.json",
    )
    parser.add_argument(
        "--criteria",
        default="apps/desktop/engine/migration-gate-criteria-1.0.0.json",
    )
    parser.add_argument("--desktop-package", default="apps/desktop/package.json")
    parser.add_argument(
        "--report",
        default="test-output/desktop-migration-gate-report.json",
    )
    args = parser.parse_args()

    adapter_path = Path(args.adapter_contract)
    criteria_path = Path(args.criteria)
    package_path = Path(args.desktop_package)

    adapter_contract = json.loads(adapter_path.read_text(encoding="utf-8"))
    criteria = json.loads(criteria_path.read_text(encoding="utf-8"))
    desktop_package = json.loads(package_path.read_text(encoding="utf-8"))

    errors = validate_desktop_migration_gate(
        adapter_contract=adapter_contract,
        criteria=criteria,
        desktop_package=desktop_package,
    )

    report = {
        "report_version": "1.0.0",
        "criteria_version": criteria.get("criteria_version"),
        "ok": len(errors) == 0,
        "errors": errors,
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("[desktop-migration-gate] validation")
    print(f"  criteria: {criteria_path}")
    print(f"  adapter: {adapter_path}")
    print(f"  ok: {report['ok']}")
    print(f"  report: {report_path}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
