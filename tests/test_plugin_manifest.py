from __future__ import annotations

import base64
import json

import pytest
from click.testing import CliRunner

from agent.cli import cli
from agent.plugin_manifest import verify_plugin_manifest


def _build_signed_manifest():
    cryptography = pytest.importorskip("cryptography")
    _ = cryptography
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    payload = {
        "schema_version": "1.0.0",
        "plugin_id": "diagnostics.sample-plugin",
        "name": "Sample Diagnostics Plugin",
        "version": "1.2.3",
        "entrypoint": "sample_plugin:main",
        "runtime": "python",
        "capabilities": ["smart.parse", "battery.parse"],
    }

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    signature = private_key.sign(canonical)

    manifest = {
        **payload,
        "signing": {
            "algorithm": "ed25519",
            "signature": base64.b64encode(signature).decode("utf-8"),
            "public_key_id": "sample-key-1",
        },
    }

    keyring = {
        "sample-key-1": base64.b64encode(public_key).decode("utf-8"),
    }
    return manifest, keyring


def test_verify_plugin_manifest_happy_path(tmp_path):
    manifest, keyring = _build_signed_manifest()

    manifest_path = tmp_path / "plugin-manifest.json"
    keyring_path = tmp_path / "keyring.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    keyring_path.write_text(json.dumps(keyring, indent=2), encoding="utf-8")

    result = verify_plugin_manifest(manifest_path, keyring_path)
    assert result["ok"] is True
    assert result["plugin_id"] == "diagnostics.sample-plugin"
    assert result["public_key_id"] == "sample-key-1"


def test_plugin_verify_command_success(tmp_path):
    manifest, keyring = _build_signed_manifest()

    manifest_path = tmp_path / "plugin-manifest.json"
    keyring_path = tmp_path / "keyring.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    keyring_path.write_text(json.dumps(keyring, indent=2), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "plugin-verify",
            str(manifest_path),
            "--keyring",
            str(keyring_path),
        ],
    )

    assert result.exit_code == 0
    assert "Plugin manifest verified" in result.output


def test_run_requires_keyring_when_plugin_manifest_set(tmp_path):
    manifest, _ = _build_signed_manifest()
    manifest_path = tmp_path / "plugin-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--mode",
            "quick",
            "--output",
            str(tmp_path / "out"),
            "--use-sample",
            "--plugin-manifest",
            str(manifest_path),
            "--no-auto-open",
        ],
    )

    assert result.exit_code == 20
