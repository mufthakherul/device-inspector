# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Plugin manifest verification helpers.

Provides schema + signature verification for plugin manifests to support
signed plugin rollout foundations (Sprint 11 roadmap track).
"""

from __future__ import annotations

import base64
import binascii
import json
from pathlib import Path
from typing import Any

import jsonschema


class PluginManifestError(Exception):
    """Raised when plugin manifest validation or verification fails."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _schema_path() -> Path:
    return _project_root() / "schemas" / "plugin-manifest-schema-1.0.0.json"


def load_plugin_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and JSON-schema validate a plugin manifest."""
    if not manifest_path.exists() or not manifest_path.is_file():
        raise PluginManifestError(f"Plugin manifest not found: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginManifestError(f"Invalid plugin manifest JSON: {exc}") from exc

    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    try:
        jsonschema.validate(manifest, schema)
    except jsonschema.ValidationError as exc:
        raise PluginManifestError(
            f"Plugin manifest schema validation failed: {exc.message}"
        )

    return manifest


def load_public_keyring(keyring_path: Path) -> dict[str, str]:
    """Load public keys for plugin signature verification.

    Supported JSON formats:
    1) {"keys": [{"id": "key-id", "public_key": "..."}, ...]}
    2) {"key-id": "...", "another-id": "..."}
    """
    if not keyring_path.exists() or not keyring_path.is_file():
        raise PluginManifestError(f"Plugin keyring not found: {keyring_path}")

    try:
        payload = json.loads(keyring_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginManifestError(f"Invalid keyring JSON: {exc}") from exc

    if isinstance(payload, dict) and isinstance(payload.get("keys"), list):
        result: dict[str, str] = {}
        for item in payload["keys"]:
            if not isinstance(item, dict):
                continue
            key_id = item.get("id")
            pub = item.get("public_key")
            if isinstance(key_id, str) and isinstance(pub, str):
                result[key_id] = pub
        if not result:
            raise PluginManifestError("Plugin keyring contains no valid keys")
        return result

    if isinstance(payload, dict):
        result = {
            key_id: pub
            for key_id, pub in payload.items()
            if isinstance(key_id, str) and isinstance(pub, str)
        }
        if not result:
            raise PluginManifestError("Plugin keyring contains no valid keys")
        return result

    raise PluginManifestError("Unsupported plugin keyring format")


def _decode_public_key(raw: str) -> bytes:
    # Accept 32-byte raw key encoded as base64 or hex.
    try:
        decoded = base64.b64decode(raw, validate=True)
        if len(decoded) == 32:
            return decoded
    except binascii.Error:
        pass

    try:
        decoded = bytes.fromhex(raw)
        if len(decoded) == 32:
            return decoded
    except ValueError:
        pass

    raise PluginManifestError("Public key must be 32-byte base64 or hex")


def verify_plugin_manifest_signature(
    manifest: dict[str, Any],
    keyring: dict[str, str],
) -> dict[str, Any]:
    """Verify in-manifest Ed25519 signature against a keyring."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception as exc:
        raise PluginManifestError(
            "Plugin signature verification requires 'cryptography' package"
        ) from exc

    signing = manifest.get("signing")
    if not isinstance(signing, dict):
        raise PluginManifestError("Plugin manifest missing signing metadata")

    key_id = signing.get("public_key_id")
    signature_b64 = signing.get("signature")
    algorithm = signing.get("algorithm")

    if algorithm != "ed25519":
        raise PluginManifestError("Unsupported plugin signing algorithm")
    if not isinstance(key_id, str) or not key_id:
        raise PluginManifestError("Plugin manifest missing public_key_id")
    if not isinstance(signature_b64, str) or not signature_b64:
        raise PluginManifestError("Plugin manifest missing signature")

    if key_id not in keyring:
        raise PluginManifestError(
            f"No public key found for plugin public_key_id: {key_id}"
        )

    public_key_bytes = _decode_public_key(keyring[key_id])
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

    try:
        signature_bytes = base64.b64decode(signature_b64, validate=True)
    except binascii.Error as exc:
        raise PluginManifestError("Plugin signature is not valid base64") from exc

    payload = {k: v for k, v in manifest.items() if k != "signing"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )

    try:
        public_key.verify(signature_bytes, canonical)
    except Exception as exc:
        raise PluginManifestError("Plugin signature verification failed") from exc

    return {
        "ok": True,
        "plugin_id": manifest.get("plugin_id"),
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "public_key_id": key_id,
        "capabilities": manifest.get("capabilities", []),
    }


def verify_plugin_manifest(
    manifest_path: Path,
    keyring_path: Path,
) -> dict[str, Any]:
    """Load, validate, and verify a plugin manifest in one call."""
    manifest = load_plugin_manifest(manifest_path)
    keyring = load_public_keyring(keyring_path)
    result = verify_plugin_manifest_signature(manifest, keyring)
    result["manifest_path"] = str(manifest_path)
    return result
