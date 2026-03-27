# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Battery detection and health parsing helpers.

Linux implementation uses upower to detect batteries and read health metrics.
"""

from __future__ import annotations

import logging
import re
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger("inspecta.battery")


class BatteryError(Exception):
    """Raised when battery operations fail."""


_SAMPLE_UPOWER = """\
  native-path:          BAT0
  vendor:               SMP
  model:                L22M4PC2
  serial:               1234
  power supply:         yes
  updated:              Fri 27 Mar 2026 01:23:45 PM UTC (12 seconds ago)
  has history:          yes
  has statistics:       yes
  battery
    present:             yes
    rechargeable:        yes
    state:               discharging
    warning-level:       none
    energy:              45.9 Wh
    energy-empty:        0 Wh
    energy-full:         47.1 Wh
    energy-full-design:  57.0 Wh
    energy-rate:         8.1 W
    voltage:             16.7 V
    charge-cycles:       251
    percentage:          97%
    capacity:            82.63%
"""


def _extract_number(value: Optional[str]) -> Optional[float]:
    """Extract first floating point number from a string."""
    if not value:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    if not match:
        return None
    return float(match.group(0))


def parse_upower_output(output: str) -> Dict[str, Any]:
    """Parse `upower -i` output into normalized battery fields."""
    fields: Dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip()

    present = fields.get("present", "no").lower() == "yes"
    state = fields.get("state", "unknown")

    # Prefer explicit capacity percentage if available, otherwise derive it.
    health_pct_value = _extract_number(fields.get("capacity"))
    if health_pct_value is None:
        full = _extract_number(fields.get("energy-full"))
        design = _extract_number(fields.get("energy-full-design"))
        if full is not None and design and design > 0:
            health_pct_value = (full / design) * 100.0

    cycle_count = _extract_number(
        fields.get("charge-cycles") or fields.get("cycle count")
    )

    result: Dict[str, Any] = {
        "present": present,
        "state": state,
        "percentage": _extract_number(fields.get("percentage")),
        "health_pct": (
            int(round(health_pct_value)) if health_pct_value is not None else None
        ),
        "cycle_count": int(cycle_count) if cycle_count is not None else None,
        "design_capacity_wh": _extract_number(fields.get("energy-full-design")),
        "full_capacity_wh": _extract_number(fields.get("energy-full")),
    }

    # Optional metadata fields when present.
    if fields.get("vendor"):
        result["vendor"] = fields["vendor"]
    if fields.get("model"):
        result["model"] = fields["model"]

    return result


def _detect_battery_path() -> str:
    """Detect the first battery device path using `upower -e`."""
    try:
        result = subprocess.run(
            ["upower", "-e"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BatteryError(
            "upower not found. Install with: sudo apt install upower"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise BatteryError("upower -e timed out after 10 seconds") from exc

    if result.returncode != 0:
        raise BatteryError(f"upower -e failed: {result.stderr.strip()}")

    for line in result.stdout.splitlines():
        line = line.strip()
        if "/battery_" in line:
            return line

    raise BatteryError("No battery device detected by upower")


def execute_upower(use_sample: bool = False) -> Dict[str, Any]:
    """Execute upower and return parsed battery data plus raw output."""
    if use_sample:
        parsed = parse_upower_output(_SAMPLE_UPOWER)
        parsed["device"] = "battery_BAT0"
        return {"status": "ok", "data": parsed, "raw_text": _SAMPLE_UPOWER}

    device_path = _detect_battery_path()

    try:
        result = subprocess.run(
            ["upower", "-i", device_path],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise BatteryError("upower -i timed out after 10 seconds") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise BatteryError(f"upower -i failed for {device_path}: {stderr}")

    parsed = parse_upower_output(result.stdout)
    parsed["device"] = device_path.split("/")[-1]
    return {"status": "ok", "data": parsed, "raw_text": result.stdout}


def scan_battery(use_sample: bool = False) -> Dict[str, Any]:
    """Scan battery health and return a structured result.

    Returns:
        Dictionary with status ('ok', 'missing', 'error') and optional data.
    """
    try:
        result = execute_upower(use_sample=use_sample)
        logger.info("Battery data collected (device=%s)", result["data"].get("device"))
        return result
    except BatteryError as exc:
        message = str(exc)
        if "No battery device detected" in message:
            logger.info("Battery scan not applicable: %s", message)
            return {"status": "missing", "error": message}

        logger.warning("Battery scan failed: %s", message)
        return {"status": "error", "error": message}
