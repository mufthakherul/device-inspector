# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Battery detection and health parsing helpers.

Linux implementation uses upower to detect batteries and read health metrics.
Windows implementation uses powercfg to generate and parse battery reports.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from . import linux_env

logger = logging.getLogger("inspecta.battery")


class BatteryError(Exception):
    """Raised when battery operations fail."""


def parse_pmset_batt_output(output: str) -> Dict[str, Any]:
    """Parse `pmset -g batt` output for state and percentage."""
    if "No batteries" in output:
        raise BatteryError("No battery detected")

    pct_match = re.search(r"(\d+)%", output)
    state_match = re.search(r";\s*([a-zA-Z\s]+?);", output)

    state = state_match.group(1).strip() if state_match else "unknown"
    percentage = float(pct_match.group(1)) if pct_match else None

    return {
        "present": percentage is not None,
        "state": state,
        "percentage": percentage,
    }


def parse_macos_power_json(output: str) -> Dict[str, Any]:
    """Parse `system_profiler SPPowerDataType -json` output."""
    try:
        payload = json.loads(output)
    except Exception as exc:
        raise BatteryError(f"Could not parse macOS power JSON: {exc}") from exc

    sections = payload.get("SPPowerDataType") or []
    section = sections[0] if isinstance(sections, list) and sections else {}
    batteries = section.get("sppower_battery_health_info") or []
    batt = batteries[0] if isinstance(batteries, list) and batteries else {}

    cycle_count = batt.get("sppower_cycle_count")
    full_capacity = batt.get("sppower_battery_max_capacity")
    design_capacity = batt.get("sppower_battery_design_capacity")

    health_pct = None
    if full_capacity is not None and design_capacity:
        try:
            full_val = float(full_capacity)
            design_val = float(design_capacity)
            if design_val > 0:
                health_pct = int(round((full_val / design_val) * 100))
                health_pct = max(0, min(100, health_pct))
        except (TypeError, ValueError):
            health_pct = None

    return {
        "cycle_count": (
            int(cycle_count) if isinstance(cycle_count, (int, float)) else None
        ),
        "health_pct": health_pct,
        "design_capacity_mwh": design_capacity,
        "full_capacity_mwh": full_capacity,
        "vendor": section.get("sppower_manufacturer") or "Apple",
        "model": section.get("sppower_battery_model") or "Internal Battery",
    }


def execute_macos_battery(use_sample: bool = False) -> Dict[str, Any]:
    """Execute macOS battery probes (`pmset` + `system_profiler`)."""
    if use_sample:
        pmset_data = parse_pmset_batt_output(
            "Now drawing from 'Battery Power'\n"
            " -InternalBattery-0\t95%; discharging; "
            "3:12 remaining present: true"
        )
        profiler_data = {
            "cycle_count": 251,
            "health_pct": 83,
            "design_capacity_mwh": 57000,
            "full_capacity_mwh": 47100,
            "vendor": "Apple",
            "model": "Internal Battery",
        }
        parsed = {**pmset_data, **profiler_data, "device": "battery_apple_internal"}
        return {"status": "ok", "data": parsed, "raw_text": "sample-macos"}

    try:
        pmset_result = subprocess.run(
            ["pmset", "-g", "batt"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BatteryError("pmset not found on macOS") from exc
    except subprocess.TimeoutExpired as exc:
        raise BatteryError("pmset timed out after 10 seconds") from exc

    if pmset_result.returncode != 0:
        stderr = pmset_result.stderr.strip() or pmset_result.stdout.strip()
        raise BatteryError(f"pmset failed: {stderr}")

    pmset_data = parse_pmset_batt_output(pmset_result.stdout)

    profiler_data: Dict[str, Any] = {}
    try:
        profiler_result = subprocess.run(
            ["system_profiler", "SPPowerDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if profiler_result.returncode == 0 and profiler_result.stdout.strip():
            profiler_data = parse_macos_power_json(profiler_result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, BatteryError):
        profiler_data = {}

    parsed = {**pmset_data, **profiler_data, "device": "battery_apple_internal"}
    return {
        "status": "ok",
        "data": parsed,
        "raw_text": (
            f"{pmset_result.stdout}\n" f"{(profiler_data and 'system_profiler') or ''}"
        ),
    }


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

_SAMPLE_POWERCFG = """\
<?xml version="1.0" encoding="utf-8"?>
<BatteryReport>
  <ReportGeneratorVersion>2.3</ReportGeneratorVersion>
  <BatteryInformation>
    <BatteryName>Microsoft AC Adapter</BatteryName>
    <ManufacturerName>Microsoft</ManufacturerName>
    <SerialNumber>123456789</SerialNumber>
    <ChemistryFull>LION</ChemistryFull>
    <Voltage>12000</Voltage>
    <CycleCount>251</CycleCount>
    <StatusDescription>Charging</StatusDescription>
  </BatteryInformation>
  <RecentUsage>
    <Usage>
      <Time>2026-03-27T10:30:00</Time>
      <ChargePercent>97</ChargePercent>
    </Usage>
  </RecentUsage>
  <DesignCapacity>57000</DesignCapacity>
  <FullChargeCapacity>47100</FullChargeCapacity>
</BatteryReport>
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


def parse_powercfg_report(xml_text: str) -> Dict[str, Any]:
    """Parse Windows powercfg /batteryreport XML into normalized fields.

    Args:
        xml_text: Raw XML output from powercfg /batteryreport

    Returns:
        Dictionary with battery metrics normalized to match upower format.

    Raises:
        BatteryError: If XML parsing fails or required elements are missing.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise BatteryError(f"Failed to parse powercfg XML: {exc}") from exc

    # Helper to extract text from XML element by path
    def get_text(path: str) -> Optional[str]:
        elem = root.find(path)
        return elem.text if elem is not None else None

    def get_int(path: str) -> Optional[int]:
        text = get_text(path)
        if text is None:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    battery_info = root.find(".//BatteryInformation")
    if battery_info is None:
        raise BatteryError("No BatteryInformation element in powercfg report")

    design_capacity = get_int(".//DesignCapacity")
    full_capacity = get_int(".//FullChargeCapacity")

    # Calculate health percentage from capacities (mWh in powercfg)
    health_pct = None
    if full_capacity is not None and design_capacity and design_capacity > 0:
        health_pct = int(round((full_capacity / design_capacity) * 100))
        # Clamp to 0-100 range
        health_pct = max(0, min(100, health_pct))

    return {
        "present": True,
        "state": get_text(".//StatusDescription") or "unknown",
        "percentage": None,  # Not readily available in simplified powercfg
        "health_pct": health_pct,
        "cycle_count": get_int(".//CycleCount"),
        "design_capacity_mwh": design_capacity,
        "full_capacity_mwh": full_capacity,
        "vendor": get_text(".//ManufacturerName"),
        "model": get_text(".//BatteryName"),
    }


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
            f"upower not found. {linux_env.tool_install_hint('upower')}"
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


def execute_powercfg(use_sample: bool = False) -> Dict[str, Any]:
    """Execute powercfg on Windows and return parsed battery data.

    Args:
        use_sample: If True, return sample battery data without calling powercfg.

    Returns:
        Dictionary with status, data, and raw XML text.

    Raises:
        BatteryError: If powercfg fails or XML parsing fails.
    """
    if use_sample:
        parsed = parse_powercfg_report(_SAMPLE_POWERCFG)
        parsed["device"] = "battery_ACPI"
        return {"status": "ok", "data": parsed, "raw_text": _SAMPLE_POWERCFG}

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        report_path = tmp.name

    try:
        # Preferred invocation on Windows PowerCfg.
        result = subprocess.run(
            ["powercfg", "/batteryreport", "/output", report_path],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        # Fallback for environments that require the legacy colon syntax.
        if result.returncode != 0:
            result = subprocess.run(
                ["powercfg", "/batteryreport", f"/output:{report_path}"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )

        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
            if "no battery" in stderr.lower():
                raise BatteryError(f"No battery detected: {stderr}")
            raise BatteryError(f"powercfg failed: {stderr}")

        with open(report_path, "r", encoding="utf-8") as f:
            xml_text = f.read()

        parsed = parse_powercfg_report(xml_text)
        parsed["device"] = "battery_ACPI"
        return {"status": "ok", "data": parsed, "raw_text": xml_text}

    except subprocess.TimeoutExpired as exc:
        raise BatteryError("powercfg timed out after 15 seconds") from exc
    except FileNotFoundError as exc:
        raise BatteryError("powercfg not available (Windows only)") from exc
    except OSError as exc:
        raise BatteryError(f"Failed to read powercfg report: {exc}") from exc
    finally:
        try:
            os.remove(report_path)
        except OSError:
            pass


def scan_battery(use_sample: bool = False) -> Dict[str, Any]:
    """Scan battery health and return a structured result.

    Detects OS and uses upower (Linux/Unix) or powercfg (Windows).

    Args:
        use_sample: If True, use sample data instead of executing tools.

    Returns:
        Dictionary with keys:
        - status: 'ok', 'missing', or 'error'
        - data: Battery metrics dict (when status == 'ok')
        - error: Error message string (when status != 'ok')
    """
    system = platform.system()

    if system == "Windows":
        try:
            result = execute_powercfg(use_sample=use_sample)
            logger.info(
                "Battery data collected from powercfg (device=%s)",
                result["data"].get("device"),
            )
            return result
        except BatteryError as exc:
            message = str(exc)
            if "no battery" in message.lower():
                logger.info("Battery scan not applicable: %s", message)
                return {"status": "missing", "error": message}
            logger.warning("Battery scan failed: %s", message)
            return {"status": "error", "error": message}
    elif system == "Darwin":
        try:
            result = execute_macos_battery(use_sample=use_sample)
            logger.info(
                "Battery data collected from macOS probes (device=%s)",
                result["data"].get("device"),
            )
            return result
        except BatteryError as exc:
            message = str(exc)
            if "no battery" in message.lower():
                logger.info("Battery scan not applicable: %s", message)
                return {"status": "missing", "error": message}
            logger.warning("Battery scan failed: %s", message)
            return {"status": "error", "error": message}
    else:
        # Linux and other Unix-like systems (macOS, etc.) use upower
        try:
            result = execute_upower(use_sample=use_sample)
            logger.info(
                "Battery data collected from upower (device=%s)",
                result["data"].get("device"),
            )
            return result
        except BatteryError as exc:
            message = str(exc)
            if "No battery device detected" in message:
                logger.info("Battery scan not applicable: %s", message)
                return {"status": "missing", "error": message}
            logger.warning("Battery scan failed: %s", message)
            return {"status": "error", "error": message}
