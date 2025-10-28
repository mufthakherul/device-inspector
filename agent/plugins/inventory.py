# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Inventory plugin for device-inspector agent.

Detects hardware information using dmidecode on Linux.
Parses vendor, model, serial number, BIOS version, and chassis type.
"""
from __future__ import annotations

import logging
import re
import subprocess
from typing import Any

logger = logging.getLogger("inspecta.inventory")


class InventoryError(Exception):
    """Raised when inventory detection fails."""


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
        output = execute_dmidecode()
        logger.info("Executed dmidecode successfully")

    return parse_dmidecode(output)
