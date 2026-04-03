from __future__ import annotations

import json

from click.testing import CliRunner

from agent.cli import cli


def test_run_full_mode_executes_pipeline(tmp_path):
    out_dir = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--mode",
            "full",
            "--output",
            str(out_dir),
            "--use-sample",
            "--no-auto-open",
            "--format",
            "txt",
        ],
    )

    # sample mode returns partial-success code in current design
    assert result.exit_code == 10
    report_path = out_dir / "report.json"
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["mode"] == "full"
    assert "run_metadata" in report
    assert report["evidence"]["manifest_path"] == "artifacts/manifest.json"
    assert "report.json" in {
        e.get("path")
        for e in json.loads(
            (out_dir / "artifacts" / "manifest.json").read_text(encoding="utf-8")
        ).get("entries", [])
    }

    test_names = {t.get("name") for t in report.get("tests", [])}
    assert "thermal_stress" in test_names
    assert "smart_timeline" in test_names
    assert "disk_stress_cycles" in test_names
    assert "native_probe_runner" in test_names
    assert "failure_classification" in report["summary"]


def test_run_full_mode_resumes_from_checkpoint_without_inventory_call(
    tmp_path, monkeypatch
):
    out_dir = tmp_path / "out"
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_payload = {
        "version": 1,
        "mode": "full",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "completed_steps": ["inventory"],
        "state": {
            "device_info": {
                "vendor": "CheckpointVendor",
                "model": "CheckpointModel",
                "serial": "CP-123",
            },
            "tests_list": [],
            "smart_results": [],
            "smart_status": "missing",
        },
    }
    (artifacts_dir / "full_mode_checkpoint.json").write_text(
        json.dumps(checkpoint_payload, indent=2),
        encoding="utf-8",
    )

    def fail_if_inventory_called(*args, **kwargs):
        raise AssertionError("inventory.get_inventory should not be called on resume")

    monkeypatch.setattr("agent.cli.inventory.get_inventory", fail_if_inventory_called)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--mode",
            "full",
            "--output",
            str(out_dir),
            "--use-sample",
            "--no-auto-open",
            "--format",
            "txt",
        ],
    )

    assert result.exit_code == 10
    report_path = out_dir / "report.json"
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["device"]["vendor"] == "CheckpointVendor"
    assert not (artifacts_dir / "full_mode_checkpoint.json").exists()


def test_run_require_hardware_rejects_sample_mode(tmp_path):
    out_dir = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--mode",
            "quick",
            "--output",
            str(out_dir),
            "--use-sample",
            "--require-hardware",
            "--no-auto-open",
            "--format",
            "txt",
        ],
    )

    assert result.exit_code == 20
    assert "cannot be combined" in result.output


def test_run_applies_basic_redaction_and_retention_policy(tmp_path):
    out_dir = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--mode",
            "quick",
            "--output",
            str(out_dir),
            "--use-sample",
            "--redaction-preset",
            "basic",
            "--retention-days",
            "30",
            "--no-auto-open",
            "--format",
            "txt",
        ],
    )

    assert result.exit_code == 10
    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert report["evidence"]["redaction"]["preset"] == "basic"
    assert report["evidence"]["retention_policy"]["retention_days"] == 30
    assert "*" in str(report["device"].get("serial", ""))


def test_run_rejects_non_positive_retention_days(tmp_path):
    out_dir = tmp_path / "out"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--mode",
            "quick",
            "--output",
            str(out_dir),
            "--use-sample",
            "--retention-days",
            "0",
            "--no-auto-open",
        ],
    )

    assert result.exit_code == 20
