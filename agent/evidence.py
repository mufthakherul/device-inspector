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


class EvidenceError(Exception):
    """Raised when evidence signing/verification operations fail."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_manifest_bytes(manifest: Dict[str, Any]) -> bytes:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _public_key_fingerprint(public_key_bytes: bytes) -> str:
    return _sha256_bytes(public_key_bytes)


def _sign_manifest_ed25519(
    manifest: Dict[str, Any],
    private_key_path: Path,
    signature_path: Path,
) -> Dict[str, Any]:
    """Create detached Ed25519 signature for a manifest.

    Uses cryptography package when available. Kept optional at runtime so
    unsigned pathways continue to work without extra dependency.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )
    except Exception as exc:
        raise EvidenceError("Ed25519 signing requires 'cryptography' package") from exc

    if not private_key_path.exists():
        raise EvidenceError(f"Signing key not found: {private_key_path}")

    key_bytes = private_key_path.read_bytes()
    try:
        private_key = serialization.load_pem_private_key(key_bytes, password=None)
    except Exception as exc:
        raise EvidenceError(f"Failed to load Ed25519 private key: {exc}") from exc

    if not isinstance(private_key, Ed25519PrivateKey):
        raise EvidenceError("Provided private key is not Ed25519")

    payload = _canonical_manifest_bytes(manifest)
    signature = private_key.sign(payload)
    signature_path.parent.mkdir(parents=True, exist_ok=True)
    signature_path.write_bytes(signature)

    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return {
        "algorithm": "ed25519",
        "signature_file": str(signature_path.name),
        "public_key_fingerprint_sha256": _public_key_fingerprint(public_bytes),
    }


def _verify_manifest_signature_ed25519(
    manifest: Dict[str, Any],
    signature_path: Path,
    public_key_path: Path,
) -> Tuple[bool, str]:
    """Verify detached Ed25519 manifest signature."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception:
        return False, "signature_verification_dependency_missing"

    if not public_key_path.exists():
        return False, f"public_key_missing:{public_key_path}"
    if not signature_path.exists():
        return False, f"signature_missing:{signature_path}"

    try:
        public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    except Exception as exc:
        return False, f"public_key_load_failed:{exc}"

    if not isinstance(public_key, Ed25519PublicKey):
        return False, "public_key_not_ed25519"

    signature = signature_path.read_bytes()
    payload = _canonical_manifest_bytes(manifest)

    try:
        public_key.verify(signature, payload)
    except Exception:
        return False, "signature_invalid"

    return True, "signature_valid"


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
    run_metadata: Dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> Tuple[Dict[str, Any], str]:
    """Build deterministic manifest and return (manifest_obj, manifest_sha256)."""
    generated_at = generated_at or (
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

    if run_metadata:
        manifest["run_metadata"] = run_metadata

    canonical = _canonical_manifest_bytes(manifest)
    manifest_sha = _sha256_bytes(canonical)
    return manifest, manifest_sha


def write_evidence_manifest(
    output_dir: Path,
    relative_paths: Iterable[str],
    agent_version: str,
    run_metadata: Dict[str, Any] | None = None,
    sign_key_path: Path | None = None,
    signature_filename: str = "manifest.sig",
    generated_at: str | None = None,
) -> Tuple[str, str]:
    """Write evidence manifest to artifacts and return (manifest_rel_path, sha256)."""
    manifest, manifest_sha = build_evidence_manifest(
        base_dir=output_dir,
        relative_paths=relative_paths,
        agent_version=agent_version,
        run_metadata=run_metadata,
        generated_at=generated_at,
    )

    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifacts_dir / "manifest.json"

    if sign_key_path is not None:
        sig_path = artifacts_dir / signature_filename
        signature_info = _sign_manifest_ed25519(
            manifest=manifest,
            private_key_path=sign_key_path,
            signature_path=sig_path,
        )
        manifest["signature"] = {
            "algorithm": signature_info["algorithm"],
            "detached": True,
            "signature_file": f"artifacts/{signature_info['signature_file']}",
            "public_key_fingerprint_sha256": signature_info[
                "public_key_fingerprint_sha256"
            ],
        }

        canonical = _canonical_manifest_bytes(manifest)
        manifest_sha = _sha256_bytes(canonical)

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return str(manifest_path.relative_to(output_dir)), manifest_sha


def verify_evidence_manifest(
    output_dir: Path,
    manifest_rel_path: str,
    public_key_path: Path | None = None,
) -> Dict[str, Any]:
    """Verify an existing evidence manifest file and return verification details."""
    manifest_path = output_dir / manifest_rel_path
    if not manifest_path.exists():
        return {
            "ok": False,
            "error": f"Manifest not found: {manifest_rel_path}",
            "checked": 0,
            "mismatches": [],
            "missing": [],
            "exit_code": 2,
            "exit_reason": "manifest_not_found",
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error": f"Invalid manifest JSON: {exc}",
            "checked": 0,
            "mismatches": [],
            "missing": [],
            "exit_code": 2,
            "exit_reason": "manifest_invalid_json",
        }

    entries = manifest.get("entries", [])
    mismatches: List[Dict[str, str]] = []
    missing: List[str] = []

    for entry in entries:
        rel = entry.get("path")
        expected = entry.get("sha256")
        if not rel or not expected:
            mismatches.append({"path": str(rel), "reason": "missing metadata"})
            continue

        full_path = output_dir / rel
        if not full_path.exists() or not full_path.is_file():
            mismatches.append({"path": rel, "reason": "missing file"})
            missing.append(rel)
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

    # Optional detached signature verification.
    signature = manifest.get("signature") if isinstance(manifest, dict) else None
    if isinstance(signature, dict):
        sig_rel = signature.get("signature_file")
        if not sig_rel:
            return {
                "ok": False,
                "checked": len(entries),
                "mismatches": mismatches,
                "missing": missing,
                "error": "Manifest signature metadata missing signature_file",
                "exit_code": 3,
                "exit_reason": "signature_metadata_invalid",
            }

        if public_key_path is None:
            return {
                "ok": False,
                "checked": len(entries),
                "mismatches": mismatches,
                "missing": missing,
                "error": "Signed manifest requires --public-key for verification",
                "exit_code": 3,
                "exit_reason": "public_key_required",
            }

        # Verify file hashes first; signature is meaningful only for intact bundle.
        if mismatches:
            return {
                "ok": False,
                "checked": len(entries),
                "mismatches": mismatches,
                "missing": missing,
                "exit_code": 1,
                "exit_reason": "integrity_mismatch",
            }

        sig_ok, sig_reason = _verify_manifest_signature_ed25519(
            manifest={k: v for k, v in manifest.items() if k != "signature"},
            signature_path=output_dir / sig_rel,
            public_key_path=public_key_path,
        )

        if not sig_ok:
            return {
                "ok": False,
                "checked": len(entries),
                "mismatches": mismatches,
                "missing": missing,
                "error": sig_reason,
                "exit_code": 3,
                "exit_reason": "signature_verification_failed",
            }

    if mismatches:
        return {
            "ok": False,
            "checked": len(entries),
            "mismatches": mismatches,
            "missing": missing,
            "exit_code": 1,
            "exit_reason": "integrity_mismatch",
        }

    return {
        "ok": True,
        "checked": len(entries),
        "mismatches": mismatches,
        "missing": missing,
        "exit_code": 0,
        "exit_reason": "verified",
    }


def audit_evidence_bundle(
    output_dir: Path,
    manifest_rel_path: str,
    public_key_path: Path | None = None,
) -> Dict[str, Any]:
    """Audit bundle reproducibility and determinism characteristics.

    The audit validates integrity first, then verifies deterministic-entry
    guarantees (sorted, unique paths and complete metadata) and checks that
    re-indexing live files yields the same entry metadata.
    """
    manifest_path = output_dir / manifest_rel_path
    if not manifest_path.exists():
        return {
            "ok": False,
            "integrity_ok": False,
            "deterministic_entries": False,
            "entry_metadata_complete": False,
            "reindexed_entries_match": False,
            "exit_code": 2,
            "exit_reason": "manifest_not_found",
            "error": f"Manifest not found: {manifest_rel_path}",
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "integrity_ok": False,
            "deterministic_entries": False,
            "entry_metadata_complete": False,
            "reindexed_entries_match": False,
            "exit_code": 2,
            "exit_reason": "manifest_invalid_json",
            "error": f"Invalid manifest JSON: {exc}",
        }

    integrity = verify_evidence_manifest(
        output_dir=output_dir,
        manifest_rel_path=manifest_rel_path,
        public_key_path=public_key_path,
    )

    entries = manifest.get("entries", []) if isinstance(manifest, dict) else []
    raw_paths = [e.get("path") for e in entries if isinstance(e, dict)]
    path_values = [p for p in raw_paths if isinstance(p, str)]

    deterministic_entries = path_values == sorted(path_values) and len(
        path_values
    ) == len(set(path_values))
    entry_metadata_complete = all(
        isinstance(e, dict)
        and isinstance(e.get("path"), str)
        and isinstance(e.get("size"), int)
        and isinstance(e.get("sha256"), str)
        and len(e.get("sha256", "")) == 64
        for e in entries
    )

    listed_paths = [e["path"] for e in entries if isinstance(e, dict) and "path" in e]
    reindexed_entries = generate_manifest_entries(output_dir, listed_paths)

    declared_by_path = {
        e.get("path"): {"size": e.get("size"), "sha256": e.get("sha256")}
        for e in entries
        if isinstance(e, dict) and isinstance(e.get("path"), str)
    }
    reindexed_by_path = {
        e["path"]: {"size": e["size"], "sha256": e["sha256"]} for e in reindexed_entries
    }
    reindexed_entries_match = declared_by_path == reindexed_by_path

    ok = (
        bool(integrity.get("ok"))
        and deterministic_entries
        and entry_metadata_complete
        and reindexed_entries_match
    )

    return {
        "ok": ok,
        "integrity_ok": bool(integrity.get("ok")),
        "deterministic_entries": deterministic_entries,
        "entry_metadata_complete": entry_metadata_complete,
        "reindexed_entries_match": reindexed_entries_match,
        "checked": int(integrity.get("checked", 0)),
        "mismatches": integrity.get("mismatches", []),
        "missing": integrity.get("missing", []),
        "manifest_sha256": _sha256_bytes(
            _canonical_manifest_bytes(manifest) if isinstance(manifest, dict) else b"{}"
        ),
        "exit_code": 0 if ok else 1,
        "exit_reason": "reproducible" if ok else "reproducibility_check_failed",
    }
