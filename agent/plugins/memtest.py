# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Memory testing and quick smoke test helpers.

Uses memtester to perform quick memory tests on available RAM.
On systems without memtester, provides sample data for testing.
"""

from __future__ import annotations

import logging
import re
import subprocess
from typing import Any, Dict

from . import linux_env

logger = logging.getLogger("inspecta.memtest")


class MemtestError(Exception):
    """Raised when memtest operations fail."""


_SAMPLE_MEMTEST = """\
[main] Allocating 512MB of memory for testing
[main] Allocating memory... done
[main] Locking pages in memory... done
[main] Calculating number of loops... This will take a moment...
[main] Tests to run (per loop): 8
[main] Iterations: 38
[main] 0% done
[main] Random Value (test 1/8): ok-

[main] Rotate Left (test 2/8): ok-
[main] Rotate Right (test 3/8): ok-
[main] XOR comparison (test 4/8): ok-
[main] SUB comparison (test 5/8): ok-
[main] MUL comparison (test 6/8): ok-
[main] DIV comparison (test 7/8): ok-
[main] OR comparison (test 8/8): ok-
[main] 100% done
[main] Test complete.
[main] Pass complete, %d errors, continuing...
[main] All done. Pass count: 1/1, errors: 0
"""


def _extract_pass_fail(output: str) -> Dict[str, Any]:
    """Extract pass/fail summary from memtester output.

    Args:
        output: Raw memtester output

    Returns:
        Dictionary with pass_count, error_count, and details.
    """
    result: Dict[str, Any] = {
        "pass_count": 0,
        "error_count": 0,
        "test_results": {},
        "status": "unknown",
    }

    # Look for final summary line: "All done. Pass count: X/Y, errors: Z"
    for line in output.splitlines():
        if "All done" in line and "Pass count" in line:
            # Extract pass count and error count
            pass_match = re.search(r"Pass count:\s+(\d+)/(\d+)", line)
            error_match = re.search(r"errors:\s+(\d+)", line)

            if pass_match:
                result["pass_count"] = int(pass_match.group(1))
            if error_match:
                result["error_count"] = int(error_match.group(1))

            # Determine overall status
            if result["error_count"] == 0 and result["pass_count"] > 0:
                result["status"] = "ok"
            elif result["error_count"] > 0:
                result["status"] = "error"

    # Count individual test results
    test_pattern = r"\[main\]\s+(\w+(?:\s+\w+)*)\s+\(test \d+/\d+\):\s+(ok|FAIL)"
    for match in re.finditer(test_pattern, output):
        test_name = match.group(1).strip()
        test_status = match.group(2).strip()
        result["test_results"][test_name] = test_status == "ok"

    return result


def import_memtest_log(raw_text: str, source: str = "memtester") -> Dict[str, Any]:
    """Import and normalize memory test logs from supported sources.

    Supported source values:
    - memtester: Native memtester text output
    - memtest86: Text export containing `Pass` / `Error` summary lines

    Args:
        raw_text: Log content to parse
        source: Source format identifier

    Returns:
        Parsed dictionary with pass_count/error_count/status and source metadata.
    """
    source_key = (source or "").strip().lower()

    if source_key == "memtester":
        parsed = _extract_pass_fail(raw_text)
        parsed["source"] = "memtester"
        return parsed

    if source_key == "memtest86":
        result: Dict[str, Any] = {
            "pass_count": 0,
            "error_count": 0,
            "test_results": {},
            "status": "unknown",
            "source": "memtest86",
        }

        pass_match = re.search(r"pass(?:es)?\s*[:=]\s*(\d+)", raw_text, re.IGNORECASE)
        err_match = re.search(r"error(?:s)?\s*[:=]\s*(\d+)", raw_text, re.IGNORECASE)

        if pass_match:
            result["pass_count"] = int(pass_match.group(1))
        if err_match:
            result["error_count"] = int(err_match.group(1))

        if result["error_count"] > 0:
            result["status"] = "error"
        elif result["pass_count"] > 0:
            result["status"] = "ok"

        return result

    raise MemtestError(
        f"Unsupported memory log source '{source}'. Use 'memtester' or 'memtest86'."
    )


def execute_memtest(
    duration_seconds: int = 30, use_sample: bool = False
) -> Dict[str, Any]:
    """Execute memtester for quick memory smoke test.

    Args:
        duration_seconds: Approximate runtime for memtester (30-60 recommended)
        use_sample: If True, return sample data without executing memtester.

    Returns:
        Dictionary with status, data, and raw output.

    Raises:
        MemtestError: If memtester fails or is not available.
    """
    if use_sample:
        parsed = _extract_pass_fail(_SAMPLE_MEMTEST)
        return {"status": "ok", "data": parsed, "raw_text": _SAMPLE_MEMTEST}

    try:
        # Run memtester for ~512MB (adjust based on available RAM)
        # Use -q flag for quiet mode to reduce output verbosity
        result = subprocess.run(
            ["memtester", "512M", "1", "-q"],
            capture_output=True,
            text=True,
            timeout=duration_seconds + 10,  # Add buffer for startup/shutdown
            check=False,
        )

        if result.returncode != 0 and "memtester: not found" not in result.stderr:
            stderr = result.stderr.strip() or result.stdout.strip()
            raise MemtestError(f"memtester failed: {stderr}")

        parsed = _extract_pass_fail(result.stdout)
        return {
            "status": "ok" if parsed["status"] != "unknown" else "error",
            "data": parsed,
            "raw_text": result.stdout,
        }

    except FileNotFoundError as exc:
        linux_hint = linux_env.tool_install_hint("memtester").replace(
            "Install with: ", ""
        )
        raise MemtestError(
            (
                "memtester not found. Install with: "
                f"{linux_hint} (Linux) or "
                "download from memtest.org (other systems)"
            )
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise MemtestError(
            f"memtester timed out after {duration_seconds + 10} seconds"
        ) from exc


def scan_memory(duration_seconds: int = 30, use_sample: bool = False) -> Dict[str, Any]:
    """Scan memory health with quick smoke test.

    Args:
        duration_seconds: Duration of memory test in seconds.
        use_sample: If True, use sample data instead of executing memtester.

    Returns:
        Dictionary with status ('ok', 'skip', 'error') and optional data.
    """
    try:
        result = execute_memtest(
            duration_seconds=duration_seconds, use_sample=use_sample
        )
        logger.info(
            "Memory test completed (errors: %d)",
            result["data"].get("error_count", 0),
        )
        return result
    except MemtestError as exc:
        message = str(exc)
        if "not found" in message.lower():
            logger.info("Memory test skipped: %s", message)
            return {"status": "skip", "error": message}

        logger.warning("Memory test failed: %s", message)
        return {"status": "error", "error": message}
