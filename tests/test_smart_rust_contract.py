from __future__ import annotations

import json
from pathlib import Path

from agent.plugins import smart


def test_rust_contract_payload_from_sample_is_stable_shape():
    root = Path(__file__).resolve().parents[1]
    sample = root / "samples" / "artifacts" / "smart_nvme0.json"

    data = json.loads(sample.read_text(encoding="utf-8"))
    parsed = smart.parse_smart_json(data)
    payload = smart.to_rust_contract_payload(parsed)

    assert payload["schema_version"] == "1.0.0"
    assert set(payload.keys()) == {"schema_version", "device", "metrics"}
    assert set(payload["device"].keys()) == {"name", "model", "serial"}
    assert "attributes" in payload["metrics"]
    assert isinstance(payload["metrics"]["attributes"], dict)


def test_rust_contract_payload_handles_missing_optional_keys():
    payload = smart.to_rust_contract_payload({"name": "sda", "attributes": {}})

    assert payload["device"]["name"] == "sda"
    assert payload["device"]["model"] is None
    assert payload["metrics"]["nvme_percentage_used"] is None
