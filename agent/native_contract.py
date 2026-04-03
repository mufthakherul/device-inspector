from __future__ import annotations

from typing import Any, Mapping


class NativeContractError(ValueError):
    """Raised when native contract payload validation fails."""


def build_rust_smart_contract(parsed: Mapping[str, Any]) -> dict[str, Any]:
    """Build a versioned Rust SMART boundary payload from parsed SMART data."""
    attributes = parsed.get("attributes", {})
    if not isinstance(attributes, dict):
        attributes = {}

    payload = {
        "schema_version": "1.0.0",
        "device": {
            "name": parsed.get("name"),
            "model": parsed.get("model"),
            "serial": parsed.get("serial"),
        },
        "metrics": {
            "nvme_percentage_used": parsed.get("nvme_percentage_used"),
            "nvme_critical_warning": parsed.get("nvme_critical_warning"),
            "attributes": attributes,
        },
    }
    validate_rust_smart_contract(payload)
    return payload


def validate_rust_smart_contract(
    payload: Mapping[str, Any], expected_schema_version: str = "1.0.0"
) -> None:
    """Validate Rust SMART boundary payload shape and value types."""
    if payload.get("schema_version") != expected_schema_version:
        raise NativeContractError(
            "Invalid schema_version for Rust SMART contract payload"
        )

    device = payload.get("device")
    metrics = payload.get("metrics")
    if not isinstance(device, dict):
        raise NativeContractError("Rust SMART contract missing device object")
    if not isinstance(metrics, dict):
        raise NativeContractError("Rust SMART contract missing metrics object")

    for key in ("name", "model", "serial"):
        value = device.get(key)
        if value is not None and not isinstance(value, str):
            raise NativeContractError(f"device.{key} must be str or null")

    for key in ("nvme_percentage_used", "nvme_critical_warning"):
        value = metrics.get(key)
        if value is not None and not isinstance(value, int):
            raise NativeContractError(f"metrics.{key} must be int or null")

    attributes = metrics.get("attributes")
    if not isinstance(attributes, dict):
        raise NativeContractError("metrics.attributes must be an object")
