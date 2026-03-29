# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for CPU benchmark plugin execution and parsing."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from agent.plugins import cpu_bench


def test_parse_sysbench_output_basic_fields():
    sample = """
    CPU speed:
        events per second:  1200.50

    General statistics:
        total time:                          10.0012s
        total number of events:              12005
    """

    parsed = cpu_bench.parse_sysbench_output(sample)

    assert parsed["events_per_second"] == 1200.5
    assert parsed["total_events"] == 12005
    assert parsed["total_time_seconds"] == 10.0012


def test_execute_sysbench_with_sample():
    result = cpu_bench.execute_sysbench(use_sample=True)

    assert result["status"] == "ok"
    assert result["data"]["events_per_second"] > 0


@patch("subprocess.run")
@patch("agent.plugins.cpu_bench.platform.system", return_value="Linux")
def test_scan_cpu_benchmark_sysbench_not_found(_mock_platform, mock_run):
    mock_run.side_effect = FileNotFoundError()

    result = cpu_bench.scan_cpu_benchmark(use_sample=False)

    assert result["status"] == "error"
    assert "sysbench not found" in result["error"]


@patch("subprocess.run")
@patch("agent.plugins.cpu_bench.platform.system", return_value="Linux")
def test_scan_cpu_benchmark_timeout(_mock_platform, mock_run):
    mock_run.side_effect = subprocess.TimeoutExpired("sysbench", 20)

    result = cpu_bench.scan_cpu_benchmark(use_sample=False)

    assert result["status"] == "error"
    assert "timed out" in result["error"]


@patch("agent.plugins.cpu_bench.platform.system", return_value="Windows")
@patch("agent.plugins.cpu_bench.subprocess.run")
def test_scan_cpu_benchmark_windows_probe(mock_run, _mock_platform):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=(
            '{"events_per_second":2200.0,'
            '"backend":"windows_cim_estimate",'
            '"max_clock_mhz":4400,'
            '"logical_processors":8}'
        ),
        stderr="",
    )

    result = cpu_bench.scan_cpu_benchmark(use_sample=False)

    assert result["status"] == "ok"
    assert result["data"]["backend"] == "windows_cim_estimate"
    assert result["data"]["events_per_second"] == 2200.0
