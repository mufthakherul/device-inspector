# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Evidence manifest helpers.

Provides offline-first manifest generation and verification for inspecta output
bundles. This is a deterministic SHA256 manifest (unsigned) that can be used to
detect tampering and support reproducible inspections.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def generate_manifest_entries(
    base_dir: Path, relative_paths: Iterable[str]
) -> List[Dict[str, Any]]:
    """Generate manifest entries for existing files.

    Missing paths are ignored intentionally to allow caller flexibility.
    """
    entries: List[Dict[str, Any]] = []
    for rel in sorted(set(relative_paths)):
        path = base_dir / rel
        if not path.exists() or not path.is_file():
            continue

        entries.append(
            {
                "path": rel,
                "size": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )

    return entries


def build_evidence_manifest(
    base_dir: Path,
    relative_paths: Iterable[str],
    agent_version: str,
) -> Tuple[Dict[str, Any], str]:
    """Build deterministic manifest and return (manifest_obj, manifest_sha256)."""
    generated_at = (
        datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat()
    )
    entries = generate_manifest_entries(base_dir, relative_paths)

    manifest: Dict[str, Any] = {
        "manifest_version": "1.0.0",
        "generated_at": generated_at,
        "agent_version": agent_version,
        "algorithm": "sha256",
        "entries": entries,
    }

    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    manifest_sha = _sha256_bytes(canonical)
    return manifest, manifest_sha


def write_evidence_manifest(
    output_dir: Path,
    relative_paths: Iterable[str],
    agent_version: str,
) -> Tuple[str, str]:
    """Write evidence manifest to artifacts and return (manifest_rel_path, sha256)."""
    manifest, manifest_sha = build_evidence_manifest(
        base_dir=output_dir,
        relative_paths=relative_paths,
        agent_version=agent_version,
    )

    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifacts_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return str(manifest_path.relative_to(output_dir)), manifest_sha


def verify_evidence_manifest(
    output_dir: Path, manifest_rel_path: str
) -> Dict[str, Any]:
    """Verify an existing evidence manifest file and return verification details."""
    manifest_path = output_dir / manifest_rel_path
    if not manifest_path.exists():
        return {
            "ok": False,
            "error": f"Manifest not found: {manifest_rel_path}",
            "checked": 0,
            "mismatches": [],
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error": f"Invalid manifest JSON: {exc}",
            "checked": 0,
            "mismatches": [],
        }

    entries = manifest.get("entries", [])
    mismatches: List[Dict[str, str]] = []

    for entry in entries:
        rel = entry.get("path")
        expected = entry.get("sha256")
        if not rel or not expected:
            mismatches.append({"path": str(rel), "reason": "missing metadata"})
            continue

        full_path = output_dir / rel
        if not full_path.exists() or not full_path.is_file():
            mismatches.append({"path": rel, "reason": "missing file"})
            continue

        actual = _sha256_file(full_path)
        if actual != expected:
            mismatches.append(
                {
                    "path": rel,
                    "reason": "hash mismatch",
                    "expected": expected,
                    "actual": actual,
                }
            )

    return {
        "ok": len(mismatches) == 0,
        "checked": len(entries),
        "mismatches": mismatches,
    }
