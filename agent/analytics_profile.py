from __future__ import annotations

import importlib.util
import os
from typing import Any


def get_offline_analytics_profile(prefer_onnx: bool = True) -> dict[str, Any]:
    """Return deterministic offline analytics runtime profile metadata.

    Runtime selection order:
    1) Explicit INSPECTA_ANALYTICS_RUNTIME override
    2) ONNX Runtime CPU profile (if available and preferred)
    3) Built-in rules-only engine
    """

    override = os.getenv("INSPECTA_ANALYTICS_RUNTIME", "").strip().lower()
    if override:
        if override in {"onnx-cpu", "rules-only"}:
            return {
                "engine": override,
                "source": "env-override",
                "offline": True,
            }
        return {
            "engine": "rules-only",
            "source": "env-override-invalid",
            "offline": True,
            "warning": "invalid_runtime_override",
        }

    if prefer_onnx and importlib.util.find_spec("onnxruntime") is not None:
        return {
            "engine": "onnx-cpu",
            "source": "auto-detect",
            "offline": True,
        }

    return {
        "engine": "rules-only",
        "source": "auto-fallback",
        "offline": True,
    }
