# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for battery plugin execution and parsing."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from agent.plugins import battery


def test_parse_upower_output_basic_fields():
    sample = """
    battery
      present:             yes
      state:               charging
      energy-full:         40.0 Wh
      energy-full-design:  50.0 Wh
      charge-cycles:       123
      percentage:          80%
    """

    parsed = battery.parse_upower_output(sample)

    assert parsed["present"] is True
    assert parsed["state"] == "charging"
    assert parsed["health_pct"] == 80
    assert parsed["cycle_count"] == 123
    assert parsed["percentage"] == 80.0


def test_execute_upower_with_sample():
    result = battery.execute_upower(use_sample=True)

    assert result["status"] == "ok"
    assert result["data"]["present"] is True
    assert result["data"]["health_pct"] is not None
    assert "raw_text" in result


@patch("subprocess.run")
def test_scan_battery_missing_device(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="/org/freedesktop/UPower/devices/DisplayDevice\n",
        stderr="",
    )

    result = battery.scan_battery(use_sample=False)

    assert result["status"] == "missing"
    assert "No battery device detected" in result["error"]


@patch("subprocess.run")
def test_scan_battery_upower_not_found(mock_run):
    mock_run.side_effect = FileNotFoundError()

    result = battery.scan_battery(use_sample=False)

    assert result["status"] == "error"
    assert "upower not found" in result["error"]


@patch("subprocess.run")
def test_scan_battery_timeout(mock_run):
    mock_run.side_effect = subprocess.TimeoutExpired("upower", 10)

    result = battery.scan_battery(use_sample=False)

    assert result["status"] == "error"
    assert "timed out" in result["error"]
