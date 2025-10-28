# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for SMART plugin execution and parsing."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent.plugins import smart


def test_detect_storage_devices_mock():
    """Test storage device detection with mocked /sys/block."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            # Mock device entries
            mock_entries = [
                MagicMock(name="sda"),
                MagicMock(name="sdb"),
                MagicMock(name="nvme0n1"),
                MagicMock(name="loop0"),  # Should be filtered
                MagicMock(name="ram0"),   # Should be filtered
            ]
            for entry in mock_entries:
                entry.name = entry._mock_name

            mock_iterdir.return_value = mock_entries

            devices = smart.detect_storage_devices()

            assert "/dev/sda" in devices
            assert "/dev/sdb" in devices
            assert "/dev/nvme0n1" in devices
            assert "/dev/loop0" not in devices
            assert "/dev/ram0" not in devices


def test_execute_smartctl_with_sample():
    """Test smartctl execution with sample data."""
    result = smart.execute_smartctl("/dev/nvme0n1", use_sample=True)

    assert isinstance(result, dict)
    assert "device" in result
    assert result["device"]["name"] == "nvme0"


def test_parse_smart_json_sata_healthy():
    """Test parsing healthy SATA SMART data."""
    sample_path = (
        Path(__file__).parent.parent
        / "samples"
        / "tool_outputs"
        / "smartctl_sata_healthy.json"
    )

    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = smart.parse_smart_json(data)

    assert result["name"] == "/dev/sda"
    assert result["model"] == "Samsung SSD 860 EVO 500GB"
    assert result["serial"] == "S3Z9NB0K123456"
    assert "Reallocated_Sector_Ct" in result["attributes"]
    assert result["attributes"]["Reallocated_Sector_Ct"] == 0
    assert result["attributes"]["Power_On_Hours"] == 1234


def test_parse_smart_json_sata_failing():
    """Test parsing failing SATA SMART data."""
    sample_path = (
        Path(__file__).parent.parent
        / "samples"
        / "tool_outputs"
        / "smartctl_sata_failing.json"
    )

    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = smart.parse_smart_json(data)

    assert result["name"] == "/dev/sdb"
    assert result["model"] == "WDC WD10EZEX-08WN4A0"
    assert "Reallocated_Sector_Ct" in result["attributes"]
    assert result["attributes"]["Reallocated_Sector_Ct"] == 248  # Failing!
    assert result["attributes"]["Current_Pending_Sector"] == 64
    assert result["attributes"]["Offline_Uncorrectable"] == 32


def test_parse_smart_json_nvme():
    """Test parsing NVMe SMART data."""
    sample_path = (
        Path(__file__).parent.parent
        / "samples"
        / "artifacts"
        / "smart_nvme0.json"
    )

    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = smart.parse_smart_json(data)

    assert result["name"] == "nvme0"
    assert result["model"] == "Example NVMe SSD"
    assert result["serial"] == "SN123"
    assert result["nvme_percentage_used"] == 5
    assert result["nvme_critical_warning"] == 0


def test_scan_all_devices_with_sample():
    """Test scanning all devices with sample data."""
    results = smart.scan_all_devices(use_sample=True)

    assert len(results) >= 1
    assert results[0]["device"] == "/dev/nvme0n1"
    assert results[0]["type"] == "nvme"
    assert results[0]["status"] == "ok"
    assert "data" in results[0]


def test_smart_error_on_missing_sample():
    """Test that SmartError is raised when sample is missing."""
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(smart.SmartError, match="Sample file not found"):
            smart.execute_smartctl("/dev/sda", use_sample=True)


@patch("subprocess.run")
def test_execute_smartctl_permission_denied(mock_run):
    """Test smartctl execution with permission denied error."""
    mock_run.return_value = MagicMock(
        returncode=2,
        stdout="",
        stderr="Permission denied",
    )

    with pytest.raises(smart.SmartError, match="Could not open device"):
        smart.execute_smartctl("/dev/sda", use_sample=False)


@patch("subprocess.run")
def test_execute_smartctl_not_found(mock_run):
    """Test smartctl execution when command not found."""
    mock_run.side_effect = FileNotFoundError()

    with pytest.raises(smart.SmartError, match="smartctl not found"):
        smart.execute_smartctl("/dev/sda", use_sample=False)


@patch("subprocess.run")
def test_execute_smartctl_timeout(mock_run):
    """Test smartctl execution timeout."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired("smartctl", 30)

    with pytest.raises(smart.SmartError, match="timed out"):
        smart.execute_smartctl("/dev/sda", use_sample=False)


@patch("subprocess.run")
def test_execute_smartctl_success(mock_run):
    """Test successful smartctl execution."""
    sample_path = (
        Path(__file__).parent.parent
        / "samples"
        / "tool_outputs"
        / "smartctl_sata_healthy.json"
    )

    with open(sample_path, "r", encoding="utf-8") as f:
        sample_json = f.read()

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=sample_json,
        stderr="",
    )

    result = smart.execute_smartctl("/dev/sda", use_sample=False)

    assert isinstance(result, dict)
    assert result["device"]["name"] == "/dev/sda"
    mock_run.assert_called_once()
