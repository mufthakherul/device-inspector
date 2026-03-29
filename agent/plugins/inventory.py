# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Inventory plugin for device-inspector agent.

Detects hardware information using dmidecode on Linux.
Parses vendor, model, serial number, BIOS version, and chassis type.
"""

from __future__ import annotations

import json
import logging
import platform
import re
import subprocess
from typing import Any

logger = logging.getLogger("inspecta.inventory")


class InventoryError(Exception):
    """Raised when inventory detection fails."""


def execute_macos_inventory() -> str:
    """Execute macOS system_profiler query and return JSON payload."""
    try:
        result = subprocess.run(
            ["system_profiler", "SPHardwareDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        raise InventoryError("system_profiler not found on macOS") from exc
    except subprocess.TimeoutExpired as exc:
        raise InventoryError("macOS inventory query timed out") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise InventoryError(f"macOS inventory query failed: {stderr}")

    return result.stdout.strip()


def parse_macos_inventory(output: str) -> dict[str, Any]:
    """Parse JSON output from `system_profiler SPHardwareDataType -json`."""
    try:
        payload = json.loads(output)
    except Exception as exc:
        raise InventoryError(f"Could not parse macOS inventory output: {exc}") from exc

    rows = payload.get("SPHardwareDataType") or []
    row = rows[0] if isinstance(rows, list) and rows else {}

    def clean(value: Any) -> Any:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    model = clean(row.get("machine_model") or row.get("model_name"))
    model_identifier = clean(row.get("machine_model_identifier"))
    if model and model_identifier and model_identifier not in model:
        normalized_model = f"{model} ({model_identifier})"
    else:
        normalized_model = model or model_identifier

    return {
        "vendor": clean(row.get("machine_name")) or "Apple",
        "model": normalized_model,
        "serial": clean(row.get("serial_number")),
        "bios_version": clean(row.get("boot_rom_version")),
        "bios_date": None,
        "chassis_type": clean(row.get("chassis_type")) or "Notebook",
        "sku": clean(row.get("provisioning_UDID")),
        "uuid": clean(row.get("platform_UUID")),
        "family": clean(row.get("chip_type")) or clean(row.get("cpu_type")),
    }


def execute_windows_inventory_registry() -> str:
    """Execute Windows registry fallback query and return JSON payload."""
    ps_script = (
        "$r=Get-ItemProperty 'HKLM:\\HARDWARE\\DESCRIPTION\\System\\BIOS';"
        "$obj=[ordered]@{"
        "vendor=$r.SystemManufacturer;"
        "model=$r.SystemProductName;"
        "serial=$r.BaseBoardSerialNumber;"
        "bios_version=$r.BIOSVersion;"
        "bios_date=$r.BIOSReleaseDate;"
        "chassis_type=$null;"
        "sku=$r.SystemSKU;"
        "uuid=$null;"
        "family=$r.SystemFamily"
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
        raise InventoryError("PowerShell not found on Windows") from exc
    except subprocess.TimeoutExpired as exc:
        raise InventoryError("Windows registry inventory query timed out") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise InventoryError(f"Windows registry inventory query failed: {stderr}")

    return result.stdout.strip()


def execute_windows_inventory() -> str:
    """Execute Windows CIM queries and return JSON payload.

    Returns:
        JSON string produced by PowerShell ConvertTo-Json.
    """
    ps_script = (
        "$cs=Get-CimInstance Win32_ComputerSystem; "
        "$bios=Get-CimInstance Win32_BIOS; "
        "$enc=Get-CimInstance Win32_SystemEnclosure | Select-Object -First 1; "
        "$obj=[ordered]@{"
        "vendor=$cs.Manufacturer;"
        "model=$cs.Model;"
        "serial=$bios.SerialNumber;"
        "bios_version=($bios.SMBIOSBIOSVersion -join ', ');"
        "bios_date=$bios.ReleaseDate;"
        "chassis_type=($enc.ChassisTypes -join ', ');"
        "sku=$cs.SystemSKUNumber;"
        "uuid=$cs.SystemFamily;"
        "family=$cs.SystemFamily"
        "}; "
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
        raise InventoryError("PowerShell not found on Windows") from exc
    except subprocess.TimeoutExpired as exc:
        raise InventoryError("Windows inventory query timed out") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise InventoryError(f"Windows inventory query failed: {stderr}")

    return result.stdout.strip()


def parse_windows_inventory(output: str) -> dict[str, Any]:
    """Parse JSON output from execute_windows_inventory."""
    try:
        data = json.loads(output)
    except Exception as exc:
        raise InventoryError(
            f"Could not parse Windows inventory output: {exc}"
        ) from exc

    def clean(value: Any) -> Any:
        if value is None:
            return None
        text = str(value).strip()
        if text in ("", "To Be Filled By O.E.M.", "Not Specified"):
            return None
        return text

    return {
        "vendor": clean(data.get("vendor")),
        "model": clean(data.get("model")),
        "serial": clean(data.get("serial")),
        "bios_version": clean(data.get("bios_version")),
        "bios_date": clean(data.get("bios_date")),
        "chassis_type": clean(data.get("chassis_type")),
        "sku": clean(data.get("sku")),
        "uuid": clean(data.get("uuid")),
        "family": clean(data.get("family")),
    }


def _has_minimum_inventory(data: dict[str, Any]) -> bool:
    """Check if parsed inventory has minimum useful identity fields."""
    return bool(data.get("vendor") and data.get("model"))


def execute_dmidecode() -> str:
    """Execute dmidecode and return output.

    Returns:
        Raw dmidecode output as string.

    Raises:
        InventoryError: If dmidecode is not found or requires elevated permissions.
    """
    try:
        result = subprocess.run(
            ["dmidecode", "-t", "system", "-t", "bios", "-t", "chassis"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0:
            if "Permission denied" in result.stderr or result.returncode == 1:
                raise InventoryError(
                    "dmidecode requires root/sudo privileges. "
                    "Run with: sudo inspecta inventory"
                )
            raise InventoryError(f"dmidecode failed: {result.stderr}")

        return result.stdout

    except FileNotFoundError as exc:
        raise InventoryError(
            "dmidecode not found. Install with: sudo apt install dmidecode"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise InventoryError("dmidecode timed out after 10 seconds") from exc


def parse_dmidecode(output: str) -> dict[str, Any]:
    """Parse dmidecode output into structured device info.

    Args:
        output: Raw dmidecode output text.

    Returns:
        Dictionary with keys: vendor, model, serial, bios_version, bios_date,
        chassis_type, sku, uuid, family
    """
    result: dict[str, Any] = {
        "vendor": None,
        "model": None,
        "serial": None,
        "bios_version": None,
        "bios_date": None,
        "chassis_type": None,
        "sku": None,
        "uuid": None,
        "family": None,
    }

    # Parse System Information section
    system_match = re.search(
        r"System Information\s+(.*?)(?=\n\nHandle|\Z)", output, re.DOTALL
    )
    if system_match:
        system_section = system_match.group(1)

        # Extract manufacturer
        if match := re.search(r"Manufacturer:\s*(.+)", system_section):
            result["vendor"] = match.group(1).strip()

        # Extract product name
        if match := re.search(r"Product Name:\s*(.+)", system_section):
            result["model"] = match.group(1).strip()

        # Extract serial number
        if match := re.search(r"Serial Number:\s*(.+)", system_section):
            serial = match.group(1).strip()
            # Skip placeholder values
            if serial not in ("Not Specified", "To Be Filled By O.E.M.", ""):
                result["serial"] = serial

        # Extract SKU
        if match := re.search(r"SKU Number:\s*(.+)", system_section):
            sku = match.group(1).strip()
            if sku not in ("Not Specified", "To Be Filled By O.E.M.", ""):
                result["sku"] = sku

        # Extract UUID
        if match := re.search(r"UUID:\s*(.+)", system_section):
            result["uuid"] = match.group(1).strip()

        # Extract Family
        if match := re.search(r"Family:\s*(.+)", system_section):
            family = match.group(1).strip()
            if family not in ("Not Specified", "To Be Filled By O.E.M.", ""):
                result["family"] = family

    # Parse BIOS Information section
    bios_match = re.search(
        r"BIOS Information\s+(.*?)(?=\n\nHandle|\Z)", output, re.DOTALL
    )
    if bios_match:
        bios_section = bios_match.group(1)

        # Extract BIOS version
        if match := re.search(r"Version:\s*(.+)", bios_section):
            result["bios_version"] = match.group(1).strip()

        # Extract BIOS release date
        if match := re.search(r"Release Date:\s*(.+)", bios_section):
            result["bios_date"] = match.group(1).strip()

    # Parse Chassis Information section
    chassis_match = re.search(
        r"Chassis Information\s+(.*?)(?=\n\nHandle|\Z)", output, re.DOTALL
    )
    if chassis_match:
        chassis_section = chassis_match.group(1)

        # Extract chassis type
        if match := re.search(r"Type:\s*(.+)", chassis_section):
            result["chassis_type"] = match.group(1).strip()

    return result


def get_inventory(use_sample: bool = False) -> dict[str, Any]:
    """Get device inventory information.

    Args:
        use_sample: If True, use sample dmidecode output instead of executing.

    Returns:
        Parsed inventory dictionary.

    Raises:
        InventoryError: If inventory detection fails.
    """
    if use_sample:
        # Load sample data
        from pathlib import Path

        sample_path = (
            Path(__file__).parent.parent.parent
            / "samples"
            / "tool_outputs"
            / "dmidecode_sample.txt"
        )
        if not sample_path.exists():
            raise InventoryError(f"Sample file not found: {sample_path}")

        with open(sample_path, "r", encoding="utf-8") as f:
            output = f.read()
        logger.info("Using sample dmidecode output")
    else:
        if platform.system().lower() == "windows":
            try:
                output = execute_windows_inventory()
                parsed = parse_windows_inventory(output)
                if _has_minimum_inventory(parsed):
                    logger.info("Executed Windows inventory query successfully")
                    return parsed
                logger.warning(
                    "Windows inventory missing core fields; using registry fallback"
                )
            except InventoryError as exc:
                logger.warning("Windows CIM inventory failed: %s", exc)

            reg_output = execute_windows_inventory_registry()
            logger.info("Executed Windows registry fallback inventory successfully")
            return parse_windows_inventory(reg_output)

        if platform.system().lower() == "darwin":
            output = execute_macos_inventory()
            logger.info("Executed macOS inventory query successfully")
            return parse_macos_inventory(output)

        output = execute_dmidecode()
        logger.info("Executed dmidecode successfully")

    return parse_dmidecode(output)
