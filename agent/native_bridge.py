# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Native helper bridge.

Detects the optional `inspecta-native` Rust helper and returns a structured
capability payload so the Python agent can use native code when available
while remaining fully functional without it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, Optional


def detect_native_capabilities(
    binary: str = "inspecta-native", timeout: int = 5
) -> Dict[str, Any]:
    """Probe the optional native helper.

    Returns a small dictionary describing whether the helper exists,
    where it lives, and the parsed handshake payload (if available).
    The agent remains functional even when the helper is missing.
    """
    binary_path = shutil.which(binary)
    if not binary_path:
        return {"available": False, "binary": None, "reason": "not_found"}

    try:
        result = subprocess.run(
            [binary_path, "--handshake"],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "binary": binary_path, "reason": str(exc)}

    payload: Optional[Dict[str, Any]] = None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {
            "available": False,
            "binary": binary_path,
            "reason": f"invalid_json: {exc}",
        }

    return {
        "available": True,
        "binary": binary_path,
        "payload": payload,
        "status": (
            payload.get("status", "unknown") if isinstance(payload, dict) else "unknown"
        ),
    }


def run_native_smart_contract_batch(
    contracts: list[dict[str, Any]],
    binary: str = "inspecta-native",
    timeout: int = 15,
) -> dict[str, Any]:
    """Execute optional native SMART contract hot-path runner.

    Expected protocol:
    - Command: `inspecta-native --smart-batch-contract`
    - stdin: JSON object containing `contracts`
    - stdout: JSON object with native execution metadata
    """
    binary_path = shutil.which(binary)
    if not binary_path:
        raise RuntimeError("native helper not found")

    payload = json.dumps({"contracts": contracts}, separators=(",", ":"))

    try:
        result = subprocess.run(
            [binary_path, "--smart-batch-contract"],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=payload,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"native batch execution failed: {exc}") from exc

    try:
        native_output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"native batch returned invalid json: {exc}") from exc

    if not isinstance(native_output, dict):
        raise RuntimeError("native batch returned invalid payload shape")

    return native_output
