# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for memtest plugin execution and parsing."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from agent.plugins import memtest


def test_extract_pass_fail_from_sample():
    """Test extracting pass/fail from sample memtester output."""
    output = """[main] All done. Pass count: 1/1, errors: 0"""

    result = memtest._extract_pass_fail(output)

    assert result["pass_count"] == 1
    assert result["error_count"] == 0
    assert result["status"] == "ok"


def test_extract_pass_fail_with_errors():
    """Test extracting results when errors occur."""
    output = """[main] All done. Pass count: 1/1, errors: 2"""

    result = memtest._extract_pass_fail(output)

    assert result["pass_count"] == 1
    assert result["error_count"] == 2
    assert result["status"] == "error"


def test_extract_test_results():
    """Test extracting individual test results."""
    output = """\
[main] Random Value (test 1/8): ok-
[main] Rotate Left (test 2/8): ok-
[main] Rotate Right (test 3/8): FAIL-
[main] All done. Pass count: 1/1, errors: 0"""

    result = memtest._extract_pass_fail(output)

    assert result["test_results"]["Random Value"] is True
    assert result["test_results"]["Rotate Left"] is True
    assert result["test_results"]["Rotate Right"] is False


def test_execute_memtest_with_sample():
    """Test execute_memtest returns sample data."""
    result = memtest.execute_memtest(use_sample=True)

    assert result["status"] == "ok"
    assert result["data"]["error_count"] == 0
    assert "raw_text" in result


@patch("subprocess.run")
def test_execute_memtest_success(mock_run):
    """Test successful memtester execution."""
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="[main] All done. Pass count: 1/1, errors: 0",
        stderr="",
    )

    result = memtest.execute_memtest(use_sample=False)

    assert result["status"] == "ok"
    assert result["data"]["pass_count"] == 1
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_execute_memtest_not_found(mock_run):
    """Test memtester not found raises error."""
    mock_run.side_effect = FileNotFoundError()

    try:
        memtest.execute_memtest(use_sample=False)
        assert False, "Expected MemtestError"
    except memtest.MemtestError as exc:
        assert "memtester not found" in str(exc)


@patch("subprocess.run")
def test_execute_memtest_timeout(mock_run):
    """Test memtester timeout raises error."""
    mock_run.side_effect = subprocess.TimeoutExpired("memtester", 40)

    try:
        memtest.execute_memtest(duration_seconds=30, use_sample=False)
        assert False, "Expected MemtestError"
    except memtest.MemtestError as exc:
        assert "timed out" in str(exc)


def test_scan_memory_with_sample():
    """Test scan_memory returns sample data."""
    result = memtest.scan_memory(use_sample=True)

    assert result["status"] == "ok"
    assert result["data"]["error_count"] == 0


@patch("agent.plugins.memtest.execute_memtest")
def test_scan_memory_skip_when_not_found(mock_execute):
    """Test scan_memory returns skip status when memtester not found."""
    mock_execute.side_effect = memtest.MemtestError(
        "memtester not found. Install with: sudo apt install memtester"
    )

    result = memtest.scan_memory(use_sample=False)

    assert result["status"] == "skip"
    assert "not found" in result["error"].lower()


@patch("agent.plugins.memtest.execute_memtest")
def test_scan_memory_error_handling(mock_execute):
    """Test scan_memory error handling for failures."""
    mock_execute.side_effect = memtest.MemtestError("Test execution failed")

    result = memtest.scan_memory(use_sample=False)

    assert result["status"] == "error"
    assert "failed" in result["error"].lower()


def test_import_memtest_log_memtester_source():
    """Importer should normalize memtester logs via existing parser."""
    raw = "[main] All done. Pass count: 2/2, errors: 0"
    imported = memtest.import_memtest_log(raw, source="memtester")

    assert imported["source"] == "memtester"
    assert imported["pass_count"] == 2
    assert imported["error_count"] == 0
    assert imported["status"] == "ok"


def test_import_memtest_log_memtest86_source():
    """Importer should parse simple memtest86 summary lines."""
    raw = "MemTest86 Summary\nPass: 3\nErrors: 0\n"
    imported = memtest.import_memtest_log(raw, source="memtest86")

    assert imported["source"] == "memtest86"
    assert imported["pass_count"] == 3
    assert imported["error_count"] == 0
    assert imported["status"] == "ok"


def test_import_memtest_log_unsupported_source_raises():
    """Unsupported source identifiers should raise MemtestError."""
    try:
        memtest.import_memtest_log("Pass: 1", source="unknown")
        assert False, "Expected MemtestError"
    except memtest.MemtestError as exc:
        assert "Unsupported memory log source" in str(exc)
