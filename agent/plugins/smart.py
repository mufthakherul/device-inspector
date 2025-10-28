# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""SMART parsing and execution helpers.

Functions here execute smartctl and parse the JSON output to produce
normalized dictionaries used in report composition and tests.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("inspecta.smart")


class SmartError(Exception):
    """Raised when SMART operations fail."""


def detect_storage_devices() -> List[str]:
    """Detect available storage devices on the system.

    Returns:
        List of device paths (e.g., ['/dev/sda', '/dev/nvme0n1'])

    Raises:
        SmartError: If device detection fails
    """
    devices = []

    # Check /sys/block for block devices
    sys_block = Path("/sys/block")
    if not sys_block.exists():
        logger.warning("/sys/block not found, cannot detect devices")
        return devices

    try:
        for entry in sys_block.iterdir():
            name = entry.name
            # Skip loop, ram, and virtual devices
            if name.startswith(("loop", "ram", "dm-", "sr")):
                continue

            # Include sd* (SATA/USB), nvme* (NVMe), hd* (older IDE)
            if name.startswith(("sd", "nvme", "hd", "vd")):
                # For NVMe, use the namespace (nvme0n1, not nvme0)
                if "nvme" in name and not re.match(r"nvme\d+n\d+", name):
                    continue

                device_path = f"/dev/{name}"
                devices.append(device_path)
                logger.debug("Detected storage device: %s", device_path)

    except Exception as e:
        raise SmartError(f"Failed to detect storage devices: {e}") from e

    return sorted(devices)


def execute_smartctl(device: str, use_sample: bool = False) -> Dict[str, Any]:
    """Execute smartctl on a device and return parsed JSON.

    Args:
        device: Device path (e.g., '/dev/sda', '/dev/nvme0n1')
        use_sample: If True, return sample data instead of executing

    Returns:
        Parsed smartctl JSON output

    Raises:
        SmartError: If smartctl execution fails
    """
    if use_sample:
        # Load sample data
        sample_path = (
            Path(__file__).parent.parent.parent
            / "samples"
            / "artifacts"
            / "smart_nvme0.json"
        )
        if not sample_path.exists():
            raise SmartError(f"Sample file not found: {sample_path}")

        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Using sample smartctl output for %s", device)
        return data

    # Determine if this is an NVMe device
    is_nvme = "nvme" in device

    # Build smartctl command
    cmd = ["smartctl", "--json", "-a"]
    if is_nvme:
        cmd.extend(["-d", "nvme"])
    cmd.append(device)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # smartctl exit codes:
        # 0 = success, no issues
        # 1 = command line parse error
        # 2 = device open failed
        # 4 = SMART command failed
        # 8 = error count increased (still get data)
        # Higher values indicate various failures

        if result.returncode == 1:
            raise SmartError(
                f"smartctl command line error for {device}: {result.stderr}"
            )
        elif result.returncode == 2:
            raise SmartError(
                f"Could not open device {device}. "
                f"Run with sudo or check device exists. Error: {result.stderr}"
            )
        elif result.returncode >= 128:
            raise SmartError(f"smartctl crashed for {device}: {result.stderr}")

        # Try to parse JSON even if exit code is non-zero
        # (smartctl can return data with non-zero exit codes)
        try:
            data = json.loads(result.stdout)
            logger.info(
                "Executed smartctl successfully for %s (exit code: %d)",
                device,
                result.returncode,
            )
            return data
        except json.JSONDecodeError as e:
            raise SmartError(
                f"Could not parse smartctl JSON output for {device}: {e}"
            ) from e

    except FileNotFoundError as exc:
        raise SmartError(
            "smartctl not found. Install with: sudo apt install smartmontools"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SmartError(f"smartctl timed out after 30 seconds for {device}") from exc


def parse_smart_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse smartctl JSON output into a simplified structure.

    This function intentionally remains small and deterministic for unit
    testing. It extracts vendor/model, device name, and a small set of
    relevant attributes if present.

    Args:
        data: Parsed JSON object from smartctl --json output.

    Returns:
        A dictionary containing normalized fields used in reports.
    """
    out: Dict[str, Any] = {}
    # device identification
    device = data.get("device") or {}
    out["name"] = device.get("name")
    out["model"] = device.get("model_name") or device.get("product")
    out["serial"] = device.get("serial_number")

    # try to extract attributes
    ata_smart = data.get("ata_smart_attributes") or {}
    table = ata_smart.get("table") if isinstance(ata_smart, dict) else None
    attrs = {}
    if isinstance(table, list):
        for entry in table:
            # attribute name can be in 'name' or 'id'
            name = entry.get("name")
            if entry.get("raw"):
                value = entry.get("raw", {}).get("value")
            else:
                value = entry.get("value")
            if name:
                attrs[name] = value

    nvme_smart = data.get("nvme_smart_health_information_log") or {}
    if isinstance(nvme_smart, dict):
        # map a few common nvme fields
        out["nvme_percentage_used"] = nvme_smart.get("percentage_used")
        out["nvme_critical_warning"] = nvme_smart.get("critical_warning")

    out["attributes"] = attrs
    return out


def scan_all_devices(use_sample: bool = False) -> List[Dict[str, Any]]:
    """Scan all storage devices and return SMART data for each.

    Args:
        use_sample: If True, use sample data instead of executing

    Returns:
        List of dictionaries with device info and SMART data
    """
    results = []

    if use_sample:
        # Return sample data for testing
        try:
            data = execute_smartctl("/dev/nvme0n1", use_sample=True)
            parsed = parse_smart_json(data)
            results.append(
                {
                    "device": "/dev/nvme0n1",
                    "type": "nvme",
                    "status": "ok",
                    "data": parsed,
                    "raw_json": data,
                }
            )
        except SmartError as e:
            logger.error("Failed to load sample SMART data: %s", e)
        return results

    # Detect devices
    try:
        devices = detect_storage_devices()
    except SmartError as e:
        logger.error("Failed to detect storage devices: %s", e)
        return results

    if not devices:
        logger.warning("No storage devices detected")
        return results

    # Scan each device
    for device in devices:
        try:
            data = execute_smartctl(device, use_sample=False)
            parsed = parse_smart_json(data)

            device_type = "nvme" if "nvme" in device else "sata"

            results.append(
                {
                    "device": device,
                    "type": device_type,
                    "status": "ok",
                    "data": parsed,
                    "raw_json": data,
                }
            )

        except SmartError as e:
            logger.warning("Failed to get SMART data for %s: %s", device, e)
            results.append(
                {
                    "device": device,
                    "type": "unknown",
                    "status": "error",
                    "error": str(e),
                }
            )

    return results
