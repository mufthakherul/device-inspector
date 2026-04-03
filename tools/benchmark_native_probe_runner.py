from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.native_contract import build_rust_smart_contract  # noqa: E402
from agent.native_probe_runner import run_smart_contract_hot_path  # noqa: E402
from agent.plugins.smart import parse_smart_json  # noqa: E402


def run_native_probe_benchmark(
    sample_path: Path,
    iterations: int,
) -> dict[str, Any]:
    raw_payload = json.loads(sample_path.read_text(encoding="utf-8"))
    parsed = parse_smart_json(raw_payload)
    dataset = [parsed for _ in range(max(1, iterations))]

    py_start = time.perf_counter()
    python_contracts = [build_rust_smart_contract(item) for item in dataset]
    py_elapsed = time.perf_counter() - py_start

    native_result = run_smart_contract_hot_path(dataset, prefer_native=True)

    python_throughput = round(len(dataset) / py_elapsed, 2) if py_elapsed > 0 else 0.0
    runner_throughput = float(native_result.get("throughput_items_per_sec", 0.0))
    speedup = (
        round(runner_throughput / python_throughput, 4) if python_throughput else 0.0
    )

    return {
        "benchmark_version": "1.0.0",
        "sample": str(sample_path),
        "iterations": len(dataset),
        "results": {
            "python_baseline": {
                "elapsed_ms": round(py_elapsed * 1000, 3),
                "throughput_items_per_sec": python_throughput,
                "schema_version": (
                    python_contracts[0].get("schema_version")
                    if python_contracts
                    else "1.0.0"
                ),
            },
            "native_runner": native_result,
        },
        "speedup_vs_python": speedup,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark inspecta native SMART hot-path probe runner."
    )
    parser.add_argument(
        "--sample",
        type=Path,
        default=Path("samples/artifacts/smart_nvme0.json"),
        help="Path to sample SMART JSON payload.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=500,
        help="Number of repeated parsed items for throughput measurement.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("test-output/native-probe-benchmark.json"),
        help="Where to write benchmark JSON output.",
    )
    args = parser.parse_args()

    benchmark = run_native_probe_benchmark(
        sample_path=args.sample,
        iterations=max(1, args.iterations),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    print(f"Benchmark written: {args.output}")
    print(
        "Runner engine="
        f"{benchmark['results']['native_runner'].get('engine')} "
        "speedup="
        f"{benchmark.get('speedup_vs_python')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
