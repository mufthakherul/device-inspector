from __future__ import annotations

import time
from typing import Any

from . import native_bridge
from .native_contract import build_rust_smart_contract


def _compute_throughput(item_count: int, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return 0.0
    return round(item_count / elapsed_seconds, 2)


def run_smart_contract_hot_path(
    parsed_items: list[dict[str, Any]],
    *,
    prefer_native: bool = True,
    binary: str = "inspecta-native",
) -> dict[str, Any]:
    """Run SMART contract-building hot path with native-first fallback.

    Returns deterministic execution metadata for report/test artifacts.
    """
    start = time.perf_counter()
    contracts = [build_rust_smart_contract(item) for item in parsed_items]
    python_elapsed = time.perf_counter() - start

    result: dict[str, Any] = {
        "engine": "python",
        "item_count": len(contracts),
        "python_elapsed_ms": round(python_elapsed * 1000, 3),
        "throughput_items_per_sec": _compute_throughput(len(contracts), python_elapsed),
        "schema_version": contracts[0]["schema_version"] if contracts else "1.0.0",
        "fallback_reason": None,
    }

    if not prefer_native or not contracts:
        return result

    native_start = time.perf_counter()
    try:
        native_output = native_bridge.run_native_smart_contract_batch(
            contracts,
            binary=binary,
        )
        native_elapsed = time.perf_counter() - native_start
        result.update(
            {
                "engine": "native",
                "native_elapsed_ms": round(native_elapsed * 1000, 3),
                "throughput_items_per_sec": _compute_throughput(
                    len(contracts), native_elapsed
                ),
                "native_output": native_output,
            }
        )
    except RuntimeError as exc:
        result["fallback_reason"] = str(exc)

    return result
