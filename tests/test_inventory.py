# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for inventory plugin."""
from __future__ import annotations

from pathlib import Path

import pytest

from agent.plugins import inventory


def test_parse_dmidecode_sample():
    """Test parsing of sample dmidecode output."""
    sample_path = (
        Path(__file__).parent.parent
        / "samples"
        / "tool_outputs"
        / "dmidecode_sample.txt"
    )

    with open(sample_path, "r", encoding="utf-8") as f:
        output = f.read()

    result = inventory.parse_dmidecode(output)

    assert result["vendor"] == "Dell Inc."
    assert result["model"] == "XPS 15 9560"
    assert result["serial"] == "ABC12345"
    assert result["bios_version"] == "1.21.0"
    assert result["bios_date"] == "05/15/2023"
    assert result["chassis_type"] == "Notebook"
    assert result["sku"] == "078B"
    assert result["uuid"] == "4c4c4544-0042-4310-8034-b2c04f323142"
    assert result["family"] == "XPS"


def test_get_inventory_with_sample():
    """Test get_inventory with sample data."""
    result = inventory.get_inventory(use_sample=True)

    assert result["vendor"] == "Dell Inc."
    assert result["model"] == "XPS 15 9560"
    assert result["serial"] is not None
    assert result["bios_version"] is not None


def test_parse_dmidecode_missing_fields():
    """Test parsing dmidecode output with missing fields."""
    minimal_output = """
Handle 0x0001, DMI type 1, 27 bytes
System Information
\tManufacturer: Test Vendor
\tProduct Name: Test Model
\tSerial Number: Not Specified
"""

    result = inventory.parse_dmidecode(minimal_output)

    assert result["vendor"] == "Test Vendor"
    assert result["model"] == "Test Model"
    assert result["serial"] is None  # "Not Specified" should be filtered
    assert result["bios_version"] is None


def test_inventory_error_on_missing_sample(monkeypatch):
    """Test that InventoryError is raised when sample is missing."""

    # Mock Path.exists to return False for the sample file
    def mock_exists(self):
        return False

    monkeypatch.setattr(Path, "exists", mock_exists)

    with pytest.raises(inventory.InventoryError, match="Sample file not found"):
        inventory.get_inventory(use_sample=True)


def test_parse_dmidecode_empty_output():
    """Test parsing empty dmidecode output."""
    result = inventory.parse_dmidecode("")

    # All fields should be None
    assert result["vendor"] is None
    assert result["model"] is None
    assert result["serial"] is None
    assert result["bios_version"] is None
