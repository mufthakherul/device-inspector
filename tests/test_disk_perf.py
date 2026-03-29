# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for disk performance plugin execution and parsing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.plugins import disk_perf


def test_parse_fio_json_basic_fields():
    fio_json = {
        "jobs": [
            {
                "jobname": "inspecta_quick",
                "read": {"bw_bytes": 419430400, "iops": 400.0},
                "write": {"bw_bytes": 209715200, "iops": 200.0},
            }
        ]
    }

    parsed = disk_perf.parse_fio_json(fio_json)

    assert parsed["job"] == "inspecta_quick"
    assert parsed["read_mbps"] == 400.0
    assert parsed["write_mbps"] == 200.0
    assert parsed["read_iops"] == 400.0
    assert parsed["write_iops"] == 200.0


def test_execute_fio_with_sample():
    result = disk_perf.execute_fio(use_sample=True)

    assert result["status"] == "ok"
    assert result["data"]["read_mbps"] > 0
    assert result["data"]["write_mbps"] > 0


@patch("subprocess.run")
@patch("agent.plugins.disk_perf.platform.system", return_value="Linux")
def test_scan_disk_performance_fio_not_found(_mock_platform, mock_run):
    mock_run.side_effect = FileNotFoundError()

    result = disk_perf.scan_disk_performance(use_sample=False)

    assert result["status"] == "error"
    assert "fio not found" in result["error"]


@patch("subprocess.run")
@patch("agent.plugins.disk_perf.platform.system", return_value="Linux")
def test_scan_disk_performance_fio_failure(mock_platform, mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="bad args")

    result = disk_perf.scan_disk_performance(use_sample=False)

    assert result["status"] == "error"
    assert "fio failed" in result["error"]


@patch("agent.plugins.disk_perf.platform.system", return_value="Windows")
@patch("agent.plugins.disk_perf.subprocess.run")
def test_scan_disk_performance_windows_winsat(mock_run, _mock_platform):
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="Disk  300.25 MB/s", stderr=""),
        MagicMock(returncode=0, stdout="Disk  250.75 MB/s", stderr=""),
    ]

    result = disk_perf.scan_disk_performance(use_sample=False)

    assert result["status"] == "ok"
    assert result["data"]["backend"] == "winsat"
    assert result["data"]["read_mbps"] == 300.25
    assert result["data"]["write_mbps"] == 250.75


def test_run_io_stress_cycles_with_sample():
    result = disk_perf.run_io_stress_cycles(cycles=2, use_sample=True)

    assert result["status"] == "ok"
    assert result["summary"]["requested_cycles"] == 2
    assert result["summary"]["successful_cycles"] == 2
    assert result["summary"]["avg_read_mbps"] > 0
