from __future__ import annotations

import json

from click.testing import CliRunner

from agent.cli import cli


def _sample_report() -> dict:
    return {
        "report_version": "1.0.0",
        "generated_at": "2026-03-29T00:00:00Z",
        "agent": {"name": "inspecta", "version": "0.1.0"},
        "device": {
            "vendor": "Vendor",
            "model": "Model",
            "serial": "SER123",
            "bios_version": "1.0",
        },
        "mode": "quick",
        "profile": "default",
        "summary": {
            "overall_score": 80,
            "grade": "Good",
            "recommendation": "Suitable for office",
        },
        "scores": {"storage": 90, "battery": 70},
        "tests": [],
        "artifacts": ["artifacts/agent.log"],
    }


def test_report_command_generates_html(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_sample_report()), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["report", str(report_path), "--format", "html"])

    assert result.exit_code == 0
    assert (tmp_path / "report.html").exists()


def test_report_command_generates_txt(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_sample_report()), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["report", str(report_path), "--format", "txt"])

    assert result.exit_code == 0
    assert (tmp_path / "report.txt").exists()


def test_report_command_migrates_legacy_report_shape(tmp_path):
    legacy = {
        "agent_version": "0.0.9",
        "generated_at": "2026-03-29T00:00:00Z",
        "summary": {"overall_score": 77},
        "scores": {},
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(legacy), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["report", str(report_path), "--format", "txt"])

    assert result.exit_code == 0
    assert (tmp_path / "report.txt").exists()


def test_report_command_rejects_unsupported_schema_major(tmp_path):
    report = _sample_report()
    report["report_version"] = "2.0.0"
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["report", str(report_path), "--format", "txt"])

    assert result.exit_code != 0
    assert "Unsupported report schema major version" in str(result.exception)
