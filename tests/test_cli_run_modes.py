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
    assert "failure_classification" in report["summary"]
