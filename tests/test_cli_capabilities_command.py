from __future__ import annotations

import json

from click.testing import CliRunner

from agent.cli import cli


def test_capabilities_command_json_surface_cli():
    runner = CliRunner()
    result = runner.invoke(cli, ["capabilities", "--surface", "cli", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["matrix_version"] == "1.0.0"
    assert payload["surface"] == "cli"
    assert "run_full" in payload["capabilities"]


def test_capabilities_command_text_surface_mobile():
    runner = CliRunner()
    result = runner.invoke(cli, ["capabilities", "--surface", "mobile"])

    assert result.exit_code == 0
    assert "Capability Matrix Version: 1.0.0" in result.output
    assert "Surface: mobile" in result.output
    assert "verify_bundle" in result.output
