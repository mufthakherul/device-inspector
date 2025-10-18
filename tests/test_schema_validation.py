"""Tests that validate sample report and generated report against schema."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sample_report_validates_schema():
    report = ROOT / "samples" / "sample_report.json"
    schema = ROOT / "schemas" / "report-schema-1.0.0.json"
    # Use the provided script to validate
    ret = subprocess.run(
        [
            "python",
            str(ROOT / "scripts" / "validate_report.py"),
            str(report),
            str(schema),
        ]
    )
    assert ret.returncode == 0


def test_cli_quick_generates_valid_report(tmp_path: Path):
    # Run the CLI module as a script to generate a report
    out = tmp_path / "out"
    out.mkdir()
    ret = subprocess.run(
        [
            "python",
            "-m",
            "agent.cli",
            "run",
            "--mode",
            "quick",
            "--output",
            str(out),
            "--no-prompt",
        ]
    )
    # CLI uses exit code 10 for partial success when sample smart used
    assert ret.returncode in (0, 10)
    report = out / "report.json"
    assert report.exists()
    schema = ROOT / "schemas" / "report-schema-1.0.0.json"
    ret2 = subprocess.run(
        [
            "python",
            str(ROOT / "scripts" / "validate_report.py"),
            str(report),
            str(schema),
        ]
    )
    assert ret2.returncode == 0
