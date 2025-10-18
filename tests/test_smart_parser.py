from __future__ import annotations

import json
from pathlib import Path

from agent.plugins import smart


def test_parse_sample_smart():
    root = Path(__file__).resolve().parents[1]
    sample = root / "samples" / "artifacts" / "smart_nvme0.json"
    data = json.loads(sample.read_text(encoding="utf-8"))
    parsed = smart.parse_smart_json(data)
    assert parsed["name"] == "nvme0"
    assert parsed["model"] == "Example NVMe SSD"
    assert parsed["nvme_percentage_used"] == 5
