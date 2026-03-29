# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Disk performance execution and parsing helpers.

Quick mode uses a short fio run and returns summarized read/write throughput.
"""

from __future__ import annotations

import json
import logging
import platform
import re
import subprocess
from typing import Any, Dict

logger = logging.getLogger("inspecta.disk_perf")


class DiskPerfError(Exception):
    """Raised when disk performance operations fail."""


_SAMPLE_FIO_JSON = {
    "jobs": [
        {
            "jobname": "inspecta_quick",
            "read": {"bw_bytes": 524_288_000, "iops": 500.0},
            "write": {"bw_bytes": 314_572_800, "iops": 300.0},
        }
    ]
}


def parse_fio_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse fio JSON output into normalized performance metrics."""
    jobs = data.get("jobs") or []
    if not jobs:
        raise DiskPerfError("fio output missing jobs section")

    job = jobs[0]
    read = job.get("read") or {}
    write = job.get("write") or {}

    read_mbps = float(read.get("bw_bytes", 0)) / (1024 * 1024)
    write_mbps = float(write.get("bw_bytes", 0)) / (1024 * 1024)

    return {
        "job": job.get("jobname", "inspecta_quick"),
        "read_mbps": round(read_mbps, 2),
        "write_mbps": round(write_mbps, 2),
        "read_iops": round(float(read.get("iops", 0)), 2),
        "write_iops": round(float(write.get("iops", 0)), 2),
    }


def execute_fio(use_sample: bool = False) -> Dict[str, Any]:
    """Execute fio quick benchmark and return parsed metrics plus raw data."""
    if use_sample:
        parsed = parse_fio_json(_SAMPLE_FIO_JSON)
        return {"status": "ok", "data": parsed, "raw_json": _SAMPLE_FIO_JSON}

    cmd = [
        "fio",
        "--name=inspecta_quick",
        "--filename=/tmp/inspecta_fio_test.dat",
        "--rw=readwrite",
        "--bs=1M",
        "--size=64M",
        "--numjobs=1",
        "--runtime=8",
        "--time_based=1",
        "--ioengine=sync",
        "--direct=0",
        "--unlink=1",
        "--group_reporting=1",
        "--output-format=json",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise DiskPerfError(
            "fio not found. Install with: sudo apt install fio"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise DiskPerfError("fio timed out after 30 seconds") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise DiskPerfError(f"fio failed with exit code {result.returncode}: {stderr}")

    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise DiskPerfError(f"Could not parse fio JSON output: {exc}") from exc

    parsed = parse_fio_json(raw)
    return {"status": "ok", "data": parsed, "raw_json": raw}


def execute_windows_winsat() -> Dict[str, Any]:
    """Execute Windows disk benchmark via winsat and return normalized metrics."""
    read_cmd = ["winsat", "disk", "-seq", "-read", "-drive", "c"]
    write_cmd = ["winsat", "disk", "-seq", "-write", "-drive", "c"]

    try:
        read_result = subprocess.run(
            read_cmd,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        write_result = subprocess.run(
            write_cmd,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except FileNotFoundError as exc:
        raise DiskPerfError("winsat not found on Windows") from exc
    except PermissionError as exc:
        if getattr(exc, "winerror", None) == 740:
            raise DiskPerfError(
                "winsat requires elevated privileges (run terminal as Administrator)"
            ) from exc
        raise DiskPerfError("winsat permission denied") from exc
    except OSError as exc:
        if getattr(exc, "winerror", None) == 740:
            raise DiskPerfError(
                "winsat requires elevated privileges (run terminal as Administrator)"
            ) from exc
        raise DiskPerfError(f"winsat launch failed: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise DiskPerfError("winsat timed out") from exc

    if read_result.returncode != 0 or write_result.returncode != 0:
        message = (
            (read_result.stderr or "").strip()
            or (write_result.stderr or "").strip()
            or "winsat returned non-zero exit code"
        )
        raise DiskPerfError(f"winsat failed: {message}")

    read_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s+MB/s", read_result.stdout)
    write_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s+MB/s", write_result.stdout)

    if not read_match or not write_match:
        raise DiskPerfError("winsat output missing MB/s metrics")

    read_mbps = float(read_match.group(1))
    write_mbps = float(write_match.group(1))

    return {
        "status": "ok",
        "data": {
            "job": "winsat_seq",
            "read_mbps": round(read_mbps, 2),
            "write_mbps": round(write_mbps, 2),
            "read_iops": None,
            "write_iops": None,
            "backend": "winsat",
        },
        "raw_text": {
            "read": read_result.stdout,
            "write": write_result.stdout,
        },
    }


def run_io_stress_cycles(cycles: int, use_sample: bool = False) -> Dict[str, Any]:
    """Run repeated IO benchmark cycles and aggregate summary metrics."""
    effective_cycles = max(1, int(cycles))
    cycle_results: list[dict[str, Any]] = []

    for idx in range(effective_cycles):
        cycle = scan_disk_performance(use_sample=use_sample)
        cycle_results.append({"cycle": idx + 1, **cycle})

    ok_cycles = [c for c in cycle_results if c.get("status") == "ok"]
    if not ok_cycles:
        return {
            "status": "error",
            "error": "All IO stress cycles failed",
            "cycles": cycle_results,
        }

    reads = [float(c["data"].get("read_mbps", 0) or 0) for c in ok_cycles]
    writes = [float(c["data"].get("write_mbps", 0) or 0) for c in ok_cycles]

    return {
        "status": "ok" if len(ok_cycles) == effective_cycles else "partial",
        "cycles": cycle_results,
        "summary": {
            "requested_cycles": effective_cycles,
            "successful_cycles": len(ok_cycles),
            "avg_read_mbps": round(sum(reads) / len(reads), 2),
            "avg_write_mbps": round(sum(writes) / len(writes), 2),
            "min_read_mbps": round(min(reads), 2),
            "max_read_mbps": round(max(reads), 2),
            "min_write_mbps": round(min(writes), 2),
            "max_write_mbps": round(max(writes), 2),
        },
    }


def scan_disk_performance(use_sample: bool = False) -> Dict[str, Any]:
    """Run quick disk benchmark and return structured result."""
    try:
        if not use_sample and platform.system().lower() == "windows":
            result = execute_windows_winsat()
        else:
            result = execute_fio(use_sample=use_sample)
        logger.info(
            "Disk benchmark collected (read=%s MB/s, write=%s MB/s)",
            result["data"].get("read_mbps"),
            result["data"].get("write_mbps"),
        )
        return result
    except DiskPerfError as exc:
        message = str(exc)
        logger.warning("Disk benchmark failed: %s", message)
        return {"status": "error", "error": message}
