# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""CPU benchmark execution and parsing helpers.

Quick mode uses a short sysbench CPU run and extracts summary metrics.
"""

from __future__ import annotations

import logging
import platform
import re
import subprocess
from typing import Any, Dict, Optional

from . import linux_env

logger = logging.getLogger("inspecta.cpu_bench")


class CpuBenchError(Exception):
    """Raised when CPU benchmark operations fail."""


_SAMPLE_SYSBENCH = """\
sysbench 1.0.20 (using system LuaJIT 2.1.0-beta3)

Running the test with following options:
Number of threads: 2

CPU speed:
    events per second:  1789.35

General statistics:
    total time:                          10.0028s
    total number of events:              17900
"""


def _extract_float(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1))


def _extract_int(pattern: str, text: str) -> Optional[int]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def parse_sysbench_output(output: str) -> Dict[str, Any]:
    """Parse sysbench output into normalized CPU benchmark metrics."""
    events_per_second = _extract_float(r"events per second:\s*([0-9.]+)", output)
    total_events = _extract_int(r"total number of events:\s*([0-9]+)", output)
    total_time_seconds = _extract_float(r"total time:\s*([0-9.]+)s", output)

    if events_per_second is None:
        raise CpuBenchError("sysbench output missing events per second")

    return {
        "events_per_second": round(events_per_second, 2),
        "total_events": total_events,
        "total_time_seconds": total_time_seconds,
    }


def execute_sysbench(use_sample: bool = False) -> Dict[str, Any]:
    """Execute sysbench CPU quick test and return parsed metrics."""
    if use_sample:
        parsed = parse_sysbench_output(_SAMPLE_SYSBENCH)
        return {"status": "ok", "data": parsed, "raw_text": _SAMPLE_SYSBENCH}

    cmd = ["sysbench", "cpu", "--threads=2", "--time=10", "run"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CpuBenchError(
            f"sysbench not found. {linux_env.tool_install_hint('sysbench')}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CpuBenchError("sysbench timed out after 20 seconds") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise CpuBenchError(
            f"sysbench failed with exit code {result.returncode}: {stderr}"
        )

    parsed = parse_sysbench_output(result.stdout)
    return {"status": "ok", "data": parsed, "raw_text": result.stdout}


def execute_windows_cpu_probe() -> Dict[str, Any]:
    """Execute Windows CPU probe using CIM and derive a benchmark proxy metric."""
    ps_script = (
        "$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1;"
        "$eps=[math]::Round("
        "($cpu.MaxClockSpeed * $cpu.NumberOfLogicalProcessors) / 4.0,2);"
        "$obj=[ordered]@{"
        "events_per_second=$eps;"
        "total_events=$null;"
        "total_time_seconds=$null;"
        "backend='windows_cim_estimate';"
        "max_clock_mhz=$cpu.MaxClockSpeed;"
        "logical_processors=$cpu.NumberOfLogicalProcessors"
        "};"
        "$obj | ConvertTo-Json -Compress"
    )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CpuBenchError("PowerShell not found on Windows") from exc
    except subprocess.TimeoutExpired as exc:
        raise CpuBenchError("Windows CPU probe timed out") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise CpuBenchError(f"Windows CPU probe failed: {stderr}")

    import json

    try:
        data = json.loads(result.stdout)
    except Exception as exc:
        raise CpuBenchError(f"Could not parse Windows CPU probe output: {exc}") from exc

    return {"status": "ok", "data": data, "raw_text": result.stdout}


def execute_macos_cpu_probe() -> Dict[str, Any]:
    """Execute macOS CPU probe via sysctl and derive a benchmark proxy metric."""
    cmd = ["sysctl", "-n", "hw.ncpu", "hw.cpufrequency"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CpuBenchError("sysctl not found on macOS") from exc
    except subprocess.TimeoutExpired as exc:
        raise CpuBenchError("macOS CPU probe timed out") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise CpuBenchError(f"macOS CPU probe failed: {stderr}")

    values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(values) < 2:
        raise CpuBenchError("macOS CPU probe output incomplete")

    try:
        logical_processors = int(values[0])
        freq_hz = float(values[1])
    except ValueError as exc:
        raise CpuBenchError(f"Could not parse macOS CPU probe output: {exc}") from exc

    freq_mhz = round(freq_hz / 1_000_000.0, 2)
    eps = round((freq_mhz * logical_processors) / 5.0, 2)

    return {
        "status": "ok",
        "data": {
            "events_per_second": eps,
            "total_events": None,
            "total_time_seconds": None,
            "backend": "macos_sysctl_estimate",
            "max_clock_mhz": freq_mhz,
            "logical_processors": logical_processors,
        },
        "raw_text": result.stdout,
    }


def scan_cpu_benchmark(use_sample: bool = False) -> Dict[str, Any]:
    """Run quick CPU benchmark and return structured result."""
    try:
        if not use_sample and platform.system().lower() == "windows":
            result = execute_windows_cpu_probe()
        elif not use_sample and platform.system().lower() == "darwin":
            result = execute_macos_cpu_probe()
        else:
            result = execute_sysbench(use_sample=use_sample)
        logger.info(
            "CPU benchmark collected (events_per_second=%s)",
            result["data"].get("events_per_second"),
        )
        return result
    except CpuBenchError as exc:
        message = str(exc)
        logger.warning("CPU benchmark failed: %s", message)
        return {"status": "error", "error": message}
