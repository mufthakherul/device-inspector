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
