from __future__ import annotations

import json
from pathlib import Path

from tools.validate_desktop_migration_gate import validate_desktop_migration_gate


def test_validate_desktop_migration_gate_happy_path():
    adapter = json.loads(
        Path("apps/desktop/engine/adapter-contract.json").read_text(encoding="utf-8")
    )
    criteria = json.loads(
        Path("apps/desktop/engine/migration-gate-criteria-1.0.0.json").read_text(
            encoding="utf-8"
        )
    )
    desktop_package = json.loads(
        Path("apps/desktop/package.json").read_text(encoding="utf-8")
    )

    errors = validate_desktop_migration_gate(adapter, criteria, desktop_package)

    assert errors == []


def test_validate_desktop_migration_gate_detects_missing_command():
    adapter = {
        "offline_guarantee": True,
        "cli_entrypoint": "python -m agent.cli",
        "commands": {"runInspection": {}},
    }
    criteria = {
        "requirements": {
            "offline_guarantee": True,
            "required_commands": ["runInspection", "verifyBundle"],
            "required_cli_entrypoint_prefix": "python -m agent.cli",
            "required_desktop_scripts": ["start"],
            "required_windows_targets": ["nsis"],
        }
    }
    package = {
        "scripts": {"start": "electron ."},
        "build": {"win": {"target": ["nsis"]}},
    }

    errors = validate_desktop_migration_gate(adapter, criteria, package)

    assert any("missing command contract: verifyBundle" in err for err in errors)
