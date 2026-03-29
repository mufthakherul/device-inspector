# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for battery plugin execution and parsing."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, mock_open, patch

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
@patch("platform.system")
def test_scan_battery_missing_device(mock_platform, mock_run):
    mock_platform.return_value = "Linux"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="/org/freedesktop/UPower/devices/DisplayDevice\n",
        stderr="",
    )

    result = battery.scan_battery(use_sample=False)

    assert result["status"] == "missing"
    assert "No battery device detected" in result["error"]


@patch("subprocess.run")
@patch("platform.system")
def test_scan_battery_upower_not_found(mock_platform, mock_run):
    mock_platform.return_value = "Linux"
    mock_run.side_effect = FileNotFoundError()

    result = battery.scan_battery(use_sample=False)

    assert result["status"] == "error"
    assert "upower not found" in result["error"]


@patch("subprocess.run")
@patch("platform.system")
def test_scan_battery_timeout(mock_platform, mock_run):
    mock_platform.return_value = "Linux"
    mock_run.side_effect = subprocess.TimeoutExpired("upower", 10)

    result = battery.scan_battery(use_sample=False)

    assert result["status"] == "error"
    assert "timed out" in result["error"]


def test_parse_powercfg_report_valid_xml():
    """Test parsing valid Windows powercfg XML output."""
    xml = """<?xml version="1.0" encoding="utf-8"?>
<BatteryReport>
  <BatteryInformation>
    <BatteryName>Internal Battery</BatteryName>
    <ManufacturerName>Dell</ManufacturerName>
    <CycleCount>120</CycleCount>
    <StatusDescription>Charging</StatusDescription>
  </BatteryInformation>
  <DesignCapacity>60000</DesignCapacity>
  <FullChargeCapacity>48000</FullChargeCapacity>
</BatteryReport>"""

    parsed = battery.parse_powercfg_report(xml)

    assert parsed["present"] is True
    assert parsed["state"] == "Charging"
    assert parsed["health_pct"] == 80  # 48000/60000 * 100
    assert parsed["cycle_count"] == 120
    assert parsed["vendor"] == "Dell"
    assert parsed["model"] == "Internal Battery"


def test_parse_powercfg_report_invalid_xml():
    """Test parsing invalid XML raises BatteryError."""
    invalid_xml = "<BatteryReport><invalid>"

    try:
        battery.parse_powercfg_report(invalid_xml)
        assert False, "Expected BatteryError"
    except battery.BatteryError as exc:
        assert "parse" in str(exc).lower()


def test_parse_powercfg_report_missing_battery_info():
    """Test parsing XML without BatteryInformation raises error."""
    xml = """<?xml version="1.0" encoding="utf-8"?>
<BatteryReport>
  <DesignCapacity>60000</DesignCapacity>
</BatteryReport>"""

    try:
        battery.parse_powercfg_report(xml)
        assert False, "Expected BatteryError"
    except battery.BatteryError as exc:
        assert "BatteryInformation" in str(exc)


def test_execute_powercfg_with_sample():
    """Test execute_powercfg returns sample data."""
    result = battery.execute_powercfg(use_sample=True)

    assert result["status"] == "ok"
    assert result["data"]["present"] is True
    assert result["data"]["health_pct"] is not None
    assert result["data"]["cycle_count"] == 251
    assert "raw_text" in result


@patch("subprocess.run")
@patch("tempfile.NamedTemporaryFile")
def test_execute_powercfg_success(mock_tmpfile, mock_run):
    """Test successful powercfg execution on Windows."""
    # Setup temp file
    mock_file = MagicMock()
    mock_file.__enter__.return_value.name = "/tmp/battery.xml"
    mock_tmpfile.return_value = mock_file

    # Setup powercfg success response
    mock_run.return_value = MagicMock(returncode=0, stderr="")

    # Mock file read
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
<BatteryReport>
  <BatteryInformation>
    <BatteryName>Test Battery</BatteryName>
    <ManufacturerName>TestMfg</ManufacturerName>
    <CycleCount>50</CycleCount>
    <StatusDescription>Discharging</StatusDescription>
  </BatteryInformation>
  <DesignCapacity>50000</DesignCapacity>
  <FullChargeCapacity>45000</FullChargeCapacity>
</BatteryReport>"""

    with patch("builtins.open", mock_open(read_data=xml_content)):
        result = battery.execute_powercfg(use_sample=False)

    assert result["status"] == "ok"
    assert result["data"]["health_pct"] == 90
    assert result["data"]["cycle_count"] == 50


@patch("subprocess.run")
def test_execute_powercfg_not_found(mock_run):
    """Test powercfg not found raises error."""
    mock_run.side_effect = FileNotFoundError()

    try:
        battery.execute_powercfg(use_sample=False)
        assert False, "Expected BatteryError"
    except battery.BatteryError as exc:
        assert "powercfg" in str(exc).lower()


@patch("platform.system")
@patch("agent.plugins.battery.execute_powercfg")
def test_scan_battery_on_windows(mock_execute_powercfg, mock_platform):
    """Test scan_battery uses powercfg on Windows."""
    mock_platform.return_value = "Windows"
    mock_execute_powercfg.return_value = {
        "status": "ok",
        "data": {"health_pct": 85, "device": "battery_ACPI"},
    }

    result = battery.scan_battery(use_sample=True)

    mock_execute_powercfg.assert_called_once_with(use_sample=True)
    assert result["status"] == "ok"


@patch("platform.system")
@patch("agent.plugins.battery.execute_powercfg")
def test_scan_battery_windows_missing_battery(mock_execute_powercfg, mock_platform):
    """Test scan_battery handles missing Windows battery."""
    mock_platform.return_value = "Windows"
    mock_execute_powercfg.side_effect = battery.BatteryError("No battery detected")

    result = battery.scan_battery(use_sample=False)

    assert result["status"] == "missing"
    assert "no battery" in result["error"].lower()
