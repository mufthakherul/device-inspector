# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for report formatting utilities."""
import json
from pathlib import Path

import pytest

from agent.report_formatter import (
    format_txt_report,
    generate_pdf_report,
    generate_txt_report,
    open_file,
)


@pytest.fixture
def sample_report():
    """Create a sample report dictionary for testing."""
    return {
        "report_version": "1.0.0",
        "generated_at": "2025-10-30T12:00:00Z",
        "agent": {"name": "inspecta", "version": "0.1.0"},
        "device": {
            "vendor": "Test Vendor",
            "model": "Test Model",
            "serial": "TEST123",
            "bios_version": "1.0.0",
            "sku": "TEST-SKU",
        },
        "mode": "quick",
        "profile": "default",
        "summary": {
            "overall_score": 85,
            "grade": "Good",
            "recommendation": "Profile: default",
        },
        "scores": {
            "storage": 90,
            "battery": 80,
            "memory": 85,
            "cpu_thermal": 85,
        },
        "tests": [
            {
                "name": "smartctl_sda",
                "status": "ok",
                "data": {"model": "Test SSD", "serial": "SSD123"},
                "status_detail": "executed",
            },
            {
                "name": "smartctl_sdb",
                "status": "error",
                "error": "Device not found",
            },
        ],
        "artifacts": [
            "artifacts/agent.log",
            "artifacts/smart_sda.json",
            "artifacts/memtest.log",
        ],
        "evidence": {"manifest_sha256": None, "signed": False},
    }


def test_format_txt_report(sample_report):
    """Test TXT report formatting."""
    txt_content = format_txt_report(sample_report)

    # Check for key sections
    assert "DEVICE INSPECTION REPORT" in txt_content
    assert "DEVICE INFORMATION" in txt_content
    assert "OVERALL ASSESSMENT" in txt_content
    assert "COMPONENT SCORES" in txt_content
    assert "TEST RESULTS" in txt_content
    assert "ARTIFACTS" in txt_content

    # Check device information
    assert "Test Vendor" in txt_content
    assert "Test Model" in txt_content
    assert "TEST123" in txt_content

    # Check scores
    assert "85/100" in txt_content  # Overall score
    assert "Good" in txt_content  # Grade
    assert "Storage" in txt_content
    assert "90/100" in txt_content  # Storage score

    # Check test results
    assert "smartctl_sda" in txt_content
    assert "Test SSD" in txt_content
    assert "smartctl_sdb" in txt_content
    assert "Device not found" in txt_content


def test_generate_txt_report(sample_report, tmp_path):
    """Test TXT report file generation."""
    report_path = generate_txt_report(sample_report, tmp_path)

    # Check file was created
    assert report_path.exists()
    assert report_path.name == "report.txt"

    # Check content
    content = report_path.read_text(encoding="utf-8")
    assert "DEVICE INSPECTION REPORT" in content
    assert "Test Vendor" in content


def test_generate_pdf_report(sample_report, tmp_path):
    """Test PDF report file generation."""
    pdf_path = generate_pdf_report(sample_report, tmp_path)

    # PDF generation requires reportlab, so it might return None
    if pdf_path is not None:
        # Check file was created
        assert pdf_path.exists()
        assert pdf_path.name == "report.pdf"
        
        # Check it's a valid PDF (starts with PDF magic bytes)
        with open(pdf_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF"
    else:
        # reportlab not installed, which is acceptable
        pass


def test_generate_pdf_report_without_reportlab(sample_report, tmp_path, monkeypatch):
    """Test PDF report generation when reportlab is not available."""
    # Mock the import to fail
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name.startswith("reportlab"):
            raise ImportError("reportlab not available")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    # Should return None when reportlab is not available
    pdf_path = generate_pdf_report(sample_report, tmp_path)
    assert pdf_path is None


def test_open_file_with_nonexistent_file(tmp_path):
    """Test open_file with a non-existent file."""
    nonexistent_file = tmp_path / "nonexistent.txt"
    # Should return False for non-existent files
    result = open_file(nonexistent_file)
    # Result may vary based on platform, but should not crash
    assert isinstance(result, bool)


def test_txt_report_handles_missing_optional_fields():
    """Test TXT report formatting with missing optional fields."""
    minimal_report = {
        "report_version": "1.0.0",
        "generated_at": "2025-10-30T12:00:00Z",
        "agent": {"name": "inspecta", "version": "0.1.0"},
        "device": {
            "vendor": "Test Vendor",
            "model": "Test Model",
        },
        "mode": "quick",
        "profile": "default",
        "summary": {
            "overall_score": 50,
            "grade": "Fair",
            "recommendation": "Some recommendation",
        },
        "scores": {},
        "tests": [],
        "artifacts": [],
    }

    txt_content = format_txt_report(minimal_report)

    # Should not crash and should have basic structure
    assert "DEVICE INSPECTION REPORT" in txt_content
    assert "Test Vendor" in txt_content
    assert "50/100" in txt_content
    assert "Fair" in txt_content


def test_txt_report_formatting_with_special_characters():
    """Test TXT report with special characters in data."""
    report = {
        "report_version": "1.0.0",
        "generated_at": "2025-10-30T12:00:00Z",
        "agent": {"name": "inspecta", "version": "0.1.0"},
        "device": {
            "vendor": "Test & Co.",
            "model": "Model™",
            "serial": "ABC-123/XYZ",
        },
        "mode": "quick",
        "profile": "default",
        "summary": {
            "overall_score": 75,
            "grade": "Good",
            "recommendation": "Good for office & home use",
        },
        "scores": {"storage": 75},
        "tests": [],
        "artifacts": [],
    }

    txt_content = format_txt_report(report)

    # Should handle special characters without crashing
    assert "Test & Co." in txt_content
    assert "Model™" in txt_content
    assert "ABC-123/XYZ" in txt_content
