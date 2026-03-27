# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Disk performance execution and parsing helpers.

Quick mode uses a short fio run and returns summarized read/write throughput.
"""

from __future__ import annotations

import json
import logging
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


def scan_disk_performance(use_sample: bool = False) -> Dict[str, Any]:
    """Run quick disk benchmark and return structured result."""
    try:
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
