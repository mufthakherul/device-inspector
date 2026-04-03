from __future__ import annotations

from pathlib import Path

from tools.benchmark_native_probe_runner import run_native_probe_benchmark


def test_run_native_probe_benchmark_smoke(monkeypatch):
    sample = Path("samples/artifacts/smart_nvme0.json")

    def fail_native(*args, **kwargs):
        raise RuntimeError("native helper not found")

    monkeypatch.setattr(
        "agent.native_probe_runner.native_bridge.run_native_smart_contract_batch",
        fail_native,
    )

    result = run_native_probe_benchmark(sample_path=sample, iterations=5)

    assert result["benchmark_version"] == "1.0.0"
    assert result["iterations"] == 5
    assert result["results"]["native_runner"]["engine"] == "python"
    assert "python_baseline" in result["results"]
