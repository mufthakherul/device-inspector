# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""SMART parsing and execution helpers.

Functions here execute smartctl and parse the JSON output to produce
normalized dictionaries used in report composition and tests.
"""

from __future__ import annotations

import json
import logging
import platform
import plistlib
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("inspecta.smart")


class SmartError(Exception):
    """Raised when SMART operations fail."""


def execute_macos_storage_health() -> List[Dict[str, Any]]:
    """Collect macOS storage health using diskutil plist outputs."""
    try:
        list_result = subprocess.run(
            ["diskutil", "list", "-plist"],
            capture_output=True,
            timeout=15,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SmartError("diskutil not found on macOS") from exc
    except subprocess.TimeoutExpired as exc:
        raise SmartError("macOS storage list probe timed out") from exc

    if list_result.returncode != 0:
        stderr = (list_result.stderr or b"").decode("utf-8", errors="ignore").strip()
        raise SmartError(f"macOS storage list probe failed: {stderr}")

    try:
        payload = plistlib.loads(list_result.stdout)
    except Exception as exc:
        raise SmartError(f"Could not parse macOS disk list output: {exc}") from exc

    entries = payload.get("AllDisksAndPartitions") or []
    device_ids = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        device_id = entry.get("DeviceIdentifier")
        if device_id and str(device_id).startswith("disk"):
            device_ids.append(str(device_id))

    normalized: List[Dict[str, Any]] = []
    for device_id in device_ids:
        try:
            info_result = subprocess.run(
                ["diskutil", "info", "-plist", f"/dev/{device_id}"],
                capture_output=True,
                timeout=12,
                check=False,
            )
        except subprocess.TimeoutExpired:
            continue

        if info_result.returncode != 0:
            continue

        try:
            info = plistlib.loads(info_result.stdout)
        except Exception:
            continue

        smart_status = str(info.get("SMARTStatus") or "Unknown")
        failed = smart_status.lower() not in {"verified", "passed", "ok", "unknown"}
        media_type = "ssd" if bool(info.get("SolidState")) else "hdd"

        normalized.append(
            {
                "device": f"/dev/{device_id}",
                "type": media_type,
                "status": "error" if failed else "ok",
                "data": {
                    "name": info.get("MediaName") or device_id,
                    "model": info.get("MediaName") or device_id,
                    "serial": info.get("SerialNumber"),
                    "attributes": {
                        "SMARTStatus": smart_status,
                        "SolidState": info.get("SolidState"),
                        "DiskSize": info.get("DiskSize"),
                    },
                    "macos_smart_status": smart_status,
                },
                "raw_json": info,
            }
        )

    return normalized


def list_windows_smartctl_devices() -> List[str]:
    """List Windows storage devices available to smartctl."""
    try:
        result = subprocess.run(
            ["smartctl", "--scan-open"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return []
    except subprocess.TimeoutExpired:
        return []

    if result.returncode != 0:
        return []

    devices: List[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Typical: "//./PhysicalDrive0 -d sat # ..."
        parts = line.split()
        if not parts:
            continue

        candidate = parts[0]
        if candidate.startswith("//./") or candidate.startswith("/dev/"):
            devices.append(candidate)

    return devices


def execute_windows_storage_health() -> List[Dict[str, Any]]:
    """Collect Windows storage health using PowerShell/CIM.

    Returns:
        List of disk records normalized to SMART-like structure.
    """
    # Preferred path: use smartctl if available on Windows.
    smartctl_devices = list_windows_smartctl_devices()
    if smartctl_devices:
        smartctl_results: List[Dict[str, Any]] = []
        for device in smartctl_devices:
            try:
                raw = execute_smartctl(device, use_sample=False)
                parsed = parse_smart_json(raw)
                smartctl_results.append(
                    {
                        "device": device,
                        "type": "unknown",
                        "status": "ok",
                        "data": parsed,
                        "raw_json": raw,
                    }
                )
            except SmartError as exc:
                smartctl_results.append(
                    {
                        "device": device,
                        "type": "unknown",
                        "status": "error",
                        "error": str(exc),
                    }
                )

        if any(r.get("status") == "ok" for r in smartctl_results):
            return smartctl_results

    ps_script = (
        "Get-PhysicalDisk | "
        "Select-Object FriendlyName,SerialNumber,MediaType,"
        "HealthStatus,OperationalStatus,Size | ConvertTo-Json -Compress"
    )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SmartError("PowerShell not found for Windows storage probe") from exc
    except subprocess.TimeoutExpired as exc:
        raise SmartError("Windows storage probe timed out") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise SmartError(f"Windows storage probe failed: {stderr}")

    try:
        payload = json.loads(result.stdout.strip() or "[]")
    except Exception as exc:
        raise SmartError(
            f"Could not parse Windows storage probe output: {exc}"
        ) from exc

    # PowerShell returns dict for single row, list for multiple rows.
    rows = payload if isinstance(payload, list) else [payload]
    normalized: List[Dict[str, Any]] = []

    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue

        health = str(row.get("HealthStatus", "Unknown")).lower()
        operational = str(row.get("OperationalStatus", "Unknown")).lower()
        failed = health not in {"healthy", "ok"} or "ok" not in operational

        normalized.append(
            {
                "device": f"physicaldisk{idx}",
                "type": str(row.get("MediaType", "unknown")).lower(),
                "status": "ok" if not failed else "error",
                "data": {
                    "name": row.get("FriendlyName"),
                    "model": row.get("FriendlyName"),
                    "serial": row.get("SerialNumber"),
                    "attributes": {
                        "HealthStatus": row.get("HealthStatus"),
                        "OperationalStatus": row.get("OperationalStatus"),
                        "Size": row.get("Size"),
                    },
                    "windows_health_status": row.get("HealthStatus"),
                },
                "raw_json": row,
            }
        )

    return normalized


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
        # Load realistic sample data from tool_outputs
        sample_path = (
            Path(__file__).parent.parent.parent
            / "samples"
            / "tool_outputs"
            / "smartctl_nvme_healthy.json"
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
    # Check both device-nested and root-level for model/serial
    # (different smartctl versions)
    out["model"] = (
        device.get("model_name")
        or device.get("product")
        or data.get("model_name")
        or data.get("model_family")
    )
    out["serial"] = device.get("serial_number") or data.get("serial_number")

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

    if platform.system().lower() == "windows":
        try:
            return execute_windows_storage_health()
        except SmartError as e:
            logger.warning("Windows storage health probe failed: %s", e)
            return [
                {
                    "device": "windows-storage",
                    "type": "unknown",
                    "status": "error",
                    "error": str(e),
                }
            ]

    if platform.system().lower() == "darwin":
        try:
            return execute_macos_storage_health()
        except SmartError as e:
            logger.warning("macOS storage health probe failed: %s", e)
            return [
                {
                    "device": "macos-storage",
                    "type": "unknown",
                    "status": "error",
                    "error": str(e),
                }
            ]

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


def collect_timeline_snapshots(
    devices: List[str],
    intervals_seconds: List[int],
    use_sample: bool = False,
) -> Dict[str, Any]:
    """Collect SMART snapshots for devices at multiple timeline points.

    Args:
        devices: List of device paths (e.g. ['/dev/sda', '/dev/nvme0n1'])
        intervals_seconds: Relative offsets to capture snapshots at
        use_sample: If True, use sample smartctl output without sleeping

    Returns:
        Timeline result with per-device snapshots and status metadata.
    """
    timeline: Dict[str, Any] = {
        "status": "ok",
        "intervals_seconds": intervals_seconds,
        "snapshots": [],
        "errors": [],
    }

    if not devices:
        timeline["status"] = "skip"
        timeline["errors"].append("No devices provided for SMART timeline")
        return timeline

    sorted_intervals = sorted([max(0, int(i)) for i in intervals_seconds])
    start = time.time()

    for idx, interval in enumerate(sorted_intervals):
        if not use_sample:
            target_elapsed = interval
            elapsed = time.time() - start
            sleep_for = target_elapsed - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

        point: Dict[str, Any] = {
            "offset_seconds": interval,
            "captured_at_epoch": time.time(),
            "devices": [],
        }

        for device in devices:
            try:
                raw = execute_smartctl(device, use_sample=use_sample)
                parsed = parse_smart_json(raw)
                point["devices"].append(
                    {
                        "device": device,
                        "status": "ok",
                        "data": parsed,
                    }
                )
            except SmartError as exc:
                timeline["status"] = "partial"
                message = str(exc)
                point["devices"].append(
                    {
                        "device": device,
                        "status": "error",
                        "error": message,
                    }
                )
                timeline["errors"].append(
                    f"offset={interval}s device={device}: {message}"
                )

        timeline["snapshots"].append(point)

        # In sample mode, avoid repeated waits but still capture all points.
        if use_sample and idx < len(sorted_intervals) - 1:
            continue

    return timeline
