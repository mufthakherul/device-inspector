from __future__ import annotations

import json
from pathlib import Path

from tools.validate_mobile_pairing_policy import validate_mobile_pairing_policy


def test_validate_mobile_pairing_policy_happy_path():
    policy = json.loads(
        Path("apps/mobile/pairing-policy-1.0.0.json").read_text(encoding="utf-8")
    )

    errors = validate_mobile_pairing_policy(policy)

    assert errors == []


def test_validate_mobile_pairing_policy_rejects_missing_mode():
    policy = {
        "policy_version": "1.0.0",
        "pairing": {
            "token_prefix": "inspecta:pairing:offline",
            "modes": ["qr", "lan"],
            "max_ttl_minutes": 10,
            "security": {
                "require_integrity_hash": True,
                "disallow_cloud_dependency": True,
                "rotation_required": True,
            },
        },
    }

    errors = validate_mobile_pairing_policy(policy)

    assert any("missing required entries" in err for err in errors)
