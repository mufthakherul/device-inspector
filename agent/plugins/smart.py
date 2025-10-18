# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""SMART parsing helpers.

Functions here parse the JSON output produced by `smartctl --json` and
produce a normalized dictionary used in report composition and tests.
"""
from __future__ import annotations

from typing import Any, Dict


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
