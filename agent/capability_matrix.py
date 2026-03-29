from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CAPABILITY_MATRIX_VERSION = "1.0.0"


def _matrix_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "schemas"
        / f"capability-matrix-{CAPABILITY_MATRIX_VERSION}.json"
    )


def load_capability_matrix() -> dict[str, Any]:
    path = _matrix_path()
    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload.get("matrix_version") != CAPABILITY_MATRIX_VERSION:
        raise ValueError(
            "Capability matrix version mismatch: "
            f"expected {CAPABILITY_MATRIX_VERSION}, "
            f"got {payload.get('matrix_version')}"
        )

    return payload


def get_surface_capabilities(surface: str) -> dict[str, Any]:
    matrix = load_capability_matrix()
    surfaces = matrix.get("surfaces", {})
    if surface not in surfaces:
        raise ValueError(f"Unknown capability surface: {surface}")

    return {
        "matrix_version": matrix.get("matrix_version"),
        "surface": surface,
        "description": surfaces[surface].get("description", ""),
        "capabilities": list(surfaces[surface].get("capabilities", [])),
    }
