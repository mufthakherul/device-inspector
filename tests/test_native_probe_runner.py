from __future__ import annotations

from agent.native_probe_runner import run_smart_contract_hot_path


def _sample_parsed() -> dict:
    return {
        "name": "nvme0",
        "model": "Example NVMe SSD",
        "serial": "SN123",
        "attributes": {"Power_On_Hours": 10},
        "nvme_percentage_used": 5,
        "nvme_critical_warning": 0,
    }


def test_native_probe_runner_python_fallback_when_native_unavailable(monkeypatch):
    def fail_native(*args, **kwargs):
        raise RuntimeError("native helper not found")

    monkeypatch.setattr(
        "agent.native_probe_runner.native_bridge.run_native_smart_contract_batch",
        fail_native,
    )

    result = run_smart_contract_hot_path([_sample_parsed()], prefer_native=True)

    assert result["engine"] == "python"
    assert result["item_count"] == 1
    assert "native helper not found" in str(result.get("fallback_reason"))


def test_native_probe_runner_uses_native_when_available(monkeypatch):
    def ok_native(contracts, binary="inspecta-native", timeout=15):
        _ = (binary, timeout)
        return {"status": "ok", "processed": len(contracts)}

    monkeypatch.setattr(
        "agent.native_probe_runner.native_bridge.run_native_smart_contract_batch",
        ok_native,
    )

    result = run_smart_contract_hot_path([_sample_parsed(), _sample_parsed()])

    assert result["engine"] == "native"
    assert result["item_count"] == 2
    assert result["native_output"]["processed"] == 2
    assert result.get("fallback_reason") is None
