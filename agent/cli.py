# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Command-line interface for inspecta agent.

Provides a minimal Click-based CLI with `run --mode quick` to produce a
report.json and placeholder artifacts. Designed for tests and developer runs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import click

from . import __version__, native_bridge
from .logging_utils import setup_logging
from .plugins import battery, cpu_bench, disk_perf, inventory, memtest, sensors, smart
from .report import compose_report
from .report_formatter import generate_pdf_report, generate_txt_report, open_file

# Simple console logger for CLI (detailed logging set up in run command)
logger = logging.getLogger("inspecta")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """inspecta — local-first device inspection toolkit.

    Automated diagnostics for used laptops and PCs.
    Generates auditable JSON reports with hardware health scores.

    \b
    Common Usage:
      inspecta run --mode quick --output ./output
      inspecta inventory

    \b
    Documentation:
      GitHub: https://github.com/mufthakherul/device-inspector
      Docs: See README.md for complete guide

    \b
    Note: Most commands require root/sudo privileges to access
    hardware information (dmidecode, smartctl). Use --use-sample
    flag for testing without root access.
    """


@cli.command("inventory")
@click.option(
    "--use-sample", is_flag=True, help="Use sample data instead of executing dmidecode"
)
def inventory_cmd(use_sample: bool) -> None:
    """Detect and display device hardware information.

    Detects system vendor, model, serial number, BIOS version, and
    other hardware identifiers using dmidecode.

    \b
    Examples:
      sudo inspecta inventory              # Real hardware detection
      inspecta inventory --use-sample      # Test with sample data

    \b
    Requirements:
      - dmidecode (install: apt-get install dmidecode)
      - root/sudo privileges (unless --use-sample)

    Output: JSON with vendor, model, serial, BIOS, SKU, and other fields
    """
    try:
        device_info = inventory.get_inventory(use_sample=use_sample)
        print(json.dumps(device_info, indent=2))
    except inventory.InventoryError as e:
        logger.error("Inventory detection failed: %s", e)
        raise SystemExit(1)


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["quick", "full"]),
    default="quick",
    help="Inspection mode: 'quick' for fast check, 'full' for comprehensive (future)",
)
@click.option(
    "--output",
    required=True,
    type=click.Path(path_type=Path),
    help="Output directory for report.json and artifacts/",
)
@click.option(
    "--profile",
    default="default",
    help="Target usage profile: default, office, developer, gamer, server",
)
@click.option(
    "--no-prompt",
    is_flag=True,
    help="Skip interactive prompts (useful for CI/automated runs)",
)
@click.option(
    "--use-sample",
    is_flag=True,
    help="Use sample data for testing (no root/hardware access required)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose debug logging to console and agent.log",
)
@click.option(
    "--auto-open",
    is_flag=True,
    default=True,
    help="Automatically open the report after inspection (default: enabled)",
)
@click.option(
    "--no-auto-open",
    is_flag=True,
    help="Disable automatic opening of the report after inspection",
)
@click.option(
    "--format",
    type=click.Choice(["txt", "pdf", "both"]),
    default="txt",
    help=(
        "Report format: 'txt' for text, 'pdf' for PDF (requires reportlab), "
        "'both' for both formats"
    ),
)
def run(
    mode: str,
    output: Path,
    profile: str,
    no_prompt: bool,
    use_sample: bool,
    verbose: bool,
    auto_open: bool,
    no_auto_open: bool,
    format: str,
) -> None:
    """Run a complete device inspection and generate report.

    Performs automated hardware health checks including:
    - Device inventory (vendor, model, serial, BIOS)
    - Storage SMART health (all drives: SATA, NVMe, USB)
    - Battery health (cycle count, capacity)
    - Disk performance benchmark (fio)
    - CPU benchmarking (sysbench)
    - Memory testing [future]

    Generates report.json with scores, recommendations, and raw artifacts.
    Also generates human-readable report (TXT or PDF) that automatically opens.

    \b
    Examples:
      sudo inspecta run --mode quick --output ./output
      inspecta run --mode quick --output ./test --use-sample
      sudo inspecta run --mode quick --output ./out --profile gamer --verbose
      inspecta run --mode quick --output ./out --use-sample --format pdf
      inspecta run --mode quick --output ./out --use-sample --no-auto-open

    \b
    Requirements (for real hardware inspection):
      - smartctl (install: apt-get install smartmontools)
      - dmidecode (install: apt-get install dmidecode)
            - fio (install: apt-get install fio)
            - sysbench (install: apt-get install sysbench)
      - root/sudo privileges
      - reportlab (optional, for PDF reports: pip install reportlab)

    \b
    Output Structure:
      <output>/
        report.json          # Main inspection report with scores
        report.txt           # Human-readable text report (auto-opens by default)
        report.pdf           # Human-readable PDF report (if --format pdf)
        artifacts/
          agent.log          # Detailed execution log
          smart_*.json       # Raw SMART data per device
          battery.json       # Battery health details (when available)
          disk_perf.json     # fio benchmark summary
          cpu_bench.json     # sysbench benchmark summary
          memtest.log        # Memory test results [future]
          sensors.csv        # Temperature/fan data [future]

    \b
    Exit Codes:
      0   - Success (full hardware inspection)
      10  - Partial success (sample data used or warnings)
      20  - Failure (unsupported mode or critical errors)

    \b
    Note: Currently only 'quick' mode is implemented. 'full' mode
    (bootable diagnostics) is planned for future releases.
    """
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Set up structured logging to file
    log_file = artifacts_dir / "agent.log"
    log_level = logging.DEBUG if verbose else logging.INFO
    inspector_logger = setup_logging(
        log_file, console_level=log_level, file_level=logging.DEBUG
    )

    inspector_logger.info("=" * 60)
    inspector_logger.info("INSPECTA AGENT v%s", __version__)
    inspector_logger.info(
        "Mode: %s | Profile: %s | Sample: %s", mode, profile, use_sample
    )
    inspector_logger.info("=" * 60)

    native_capabilities = native_bridge.detect_native_capabilities()
    if native_capabilities.get("available"):
        inspector_logger.info(
            "Native helper detected at %s (status=%s)",
            native_capabilities.get("binary"),
            native_capabilities.get("status"),
        )
    else:
        inspector_logger.info(
            "Native helper not available: %s",
            native_capabilities.get("reason", "unknown"),
        )

    logger.info("Starting inspecta run (mode=%s, profile=%s)", mode, profile)

    if mode != "quick":
        logger.error("Only quick mode is supported in this scaffold. Exiting.")
        inspector_logger.error("Unsupported mode: %s", mode)
        raise SystemExit(20)

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Get device inventory
    inspector_logger.info("Step 1: Detecting device inventory...")
    try:
        device_info = inventory.get_inventory(use_sample=use_sample)
        logger.info(
            "Detected device: %s %s",
            device_info.get("vendor"),
            device_info.get("model"),
        )
        inspector_logger.info(
            "Device detected: %s %s (Serial: %s, BIOS: %s)",
            device_info.get("vendor"),
            device_info.get("model"),
            device_info.get("serial", "N/A"),
            device_info.get("bios_version", "N/A"),
        )
    except inventory.InventoryError as e:
        logger.warning("Inventory detection failed: %s. Using placeholder.", e)
        inspector_logger.warning("Inventory detection failed: %s", e, exc_info=verbose)
        device_info = {"vendor": "unknown", "model": "unknown", "serial": None}

    # Scan storage devices with SMART
    inspector_logger.info("Step 2: Scanning storage devices...")
    logger.info("Scanning storage devices...")
    smart_results = smart.scan_all_devices(use_sample=use_sample)

    if not smart_results:
        logger.warning("No storage devices found or SMART data unavailable")
        inspector_logger.warning("No storage devices detected")
        smart_status = "missing"
        tests_list = []
    else:
        smart_status = "ok"
        tests_list = []
        inspector_logger.info("Found %d storage device(s)", len(smart_results))

        # Write SMART artifacts and build tests list
        for idx, result in enumerate(smart_results):
            device_name = result["device"].replace("/dev/", "")

            if result["status"] == "ok":
                # Write raw JSON artifact
                artifact_name = f"smart_{device_name}.json"
                (artifacts_dir / artifact_name).write_text(
                    json.dumps(result["raw_json"], indent=2), encoding="utf-8"
                )

                # Add to tests list
                tests_list.append(
                    {
                        "name": f"smartctl_{device_name}",
                        "status": "ok",
                        "data": result["data"],
                        "status_detail": "sample" if use_sample else "executed",
                    }
                )

                logger.info(
                    "Collected SMART data for %s: %s",
                    result["device"],
                    result["data"].get("model", "unknown"),
                )
                inspector_logger.info(
                    "SMART OK: %s - %s (Serial: %s)",
                    result["device"],
                    result["data"].get("model", "unknown"),
                    result["data"].get("serial", "N/A"),
                )
            else:
                # Add error to tests list
                tests_list.append(
                    {
                        "name": f"smartctl_{device_name}",
                        "status": "error",
                        "error": result.get("error", "Unknown error"),
                    }
                )
                logger.error(
                    "Failed to get SMART data for %s: %s",
                    result["device"],
                    result.get("error", "Unknown"),
                )
                inspector_logger.error(
                    "SMART FAILED: %s - %s",
                    result["device"],
                    result.get("error", "Unknown error"),
                )

        if use_sample:
            smart_status = "sample"
            inspector_logger.info("Using sample SMART data (no real execution)")

    # Scan battery health
    inspector_logger.info("Step 3: Scanning battery health...")
    battery_result = battery.scan_battery(use_sample=use_sample)
    if battery_result["status"] == "ok":
        battery_artifact = artifacts_dir / "battery.json"
        battery_artifact.write_text(
            json.dumps(battery_result["data"], indent=2), encoding="utf-8"
        )
        tests_list.append(
            {
                "name": "battery_health",
                "status": "ok",
                "data": battery_result["data"],
                "status_detail": "sample" if use_sample else "executed",
            }
        )
        inspector_logger.info(
            "Battery OK: health=%s%% cycles=%s",
            battery_result["data"].get("health_pct", "N/A"),
            battery_result["data"].get("cycle_count", "N/A"),
        )
    elif battery_result["status"] == "missing":
        tests_list.append(
            {
                "name": "battery_health",
                "status": "missing",
                "error": battery_result.get("error", "Battery not detected"),
            }
        )
        inspector_logger.info("Battery not detected (desktop or unavailable)")
    else:
        tests_list.append(
            {
                "name": "battery_health",
                "status": "error",
                "error": battery_result.get("error", "Battery scan failed"),
            }
        )
        inspector_logger.warning(
            "Battery scan failed: %s", battery_result.get("error", "unknown")
        )

    # Run disk performance benchmark
    inspector_logger.info("Step 4: Running disk performance benchmark...")
    disk_result = disk_perf.scan_disk_performance(use_sample=use_sample)
    if disk_result["status"] == "ok":
        disk_artifact = artifacts_dir / "disk_perf.json"
        disk_artifact.write_text(
            json.dumps(disk_result["data"], indent=2), encoding="utf-8"
        )
        tests_list.append(
            {
                "name": "disk_performance",
                "status": "ok",
                "data": disk_result["data"],
                "status_detail": "sample" if use_sample else "executed",
            }
        )
        inspector_logger.info(
            "Disk benchmark OK: read=%s MB/s write=%s MB/s",
            disk_result["data"].get("read_mbps", "N/A"),
            disk_result["data"].get("write_mbps", "N/A"),
        )
    else:
        tests_list.append(
            {
                "name": "disk_performance",
                "status": "error",
                "error": disk_result.get("error", "Disk benchmark failed"),
            }
        )
        inspector_logger.warning(
            "Disk benchmark failed: %s", disk_result.get("error", "unknown")
        )

    # Run CPU benchmark
    inspector_logger.info("Step 5: Running CPU benchmark...")
    cpu_result = cpu_bench.scan_cpu_benchmark(use_sample=use_sample)
    if cpu_result["status"] == "ok":
        cpu_artifact = artifacts_dir / "cpu_bench.json"
        cpu_artifact.write_text(
            json.dumps(cpu_result["data"], indent=2), encoding="utf-8"
        )
        tests_list.append(
            {
                "name": "cpu_benchmark",
                "status": "ok",
                "data": cpu_result["data"],
                "status_detail": "sample" if use_sample else "executed",
            }
        )
        inspector_logger.info(
            "CPU benchmark OK: events/s=%s",
            cpu_result["data"].get("events_per_second", "N/A"),
        )
    else:
        tests_list.append(
            {
                "name": "cpu_benchmark",
                "status": "error",
                "error": cpu_result.get("error", "CPU benchmark failed"),
            }
        )
        inspector_logger.warning(
            "CPU benchmark failed: %s", cpu_result.get("error", "unknown")
        )

    inspector_logger.info("Step 6: Running memory test...")
    memtest_result = memtest.scan_memory(use_sample=use_sample)
    if memtest_result["status"] == "ok":
        # Write memtest log artifact
        memtest_artifact = artifacts_dir / "memtest.log"
        memtest_artifact.write_text(
            memtest_result.get("raw_text", "OK\n"), encoding="utf-8"
        )
        tests_list.append(
            {
                "name": "memory_test",
                "status": "ok",
                "data": memtest_result["data"],
                "status_detail": "sample" if use_sample else "executed",
            }
        )
        inspector_logger.info(
            "Memory test OK: result=%s", memtest_result["data"].get("result", "PASS")
        )
    elif memtest_result["status"] == "skip":
        # Write placeholder when memtester not available
        (artifacts_dir / "memtest.log").write_text(
            "Memtester not available\n", encoding="utf-8"
        )
        tests_list.append(
            {
                "name": "memory_test",
                "status": "skip",
                "reason": memtest_result.get("reason", "memtester not available"),
            }
        )
        inspector_logger.info("Memory test skipped: %s", memtest_result.get("reason"))
    else:
        (artifacts_dir / "memtest.log").write_text(
            f"Error: {memtest_result.get('error', 'unknown')}\n", encoding="utf-8"
        )
        tests_list.append(
            {
                "name": "memory_test",
                "status": "error",
                "error": memtest_result.get("error", "Memory test failed"),
            }
        )
        inspector_logger.warning(
            "Memory test failed: %s", memtest_result.get("error", "unknown")
        )

    inspector_logger.info("Step 7: Collecting thermal sensors snapshot...")
    try:
        sensors_result = (
            sensors.get_sensors_snapshot()
            if not use_sample
            else {
                "status": "ok",
                "platform": "linux",
                "tool": "lm-sensors",
                "sensors": [
                    {
                        "adapter": "coretemp-isa-0000",
                        "type": "CPU",
                        "readings": [
                            {
                                "label": "Package id 0",
                                "temp": 45.0,
                                "high": 100.0,
                                "crit": 100.0,
                            },
                            {
                                "label": "Core 0",
                                "temp": 42.0,
                                "high": 100.0,
                                "crit": 100.0,
                            },
                            {
                                "label": "Core 1",
                                "temp": 44.0,
                                "high": 100.0,
                                "crit": 100.0,
                            },
                        ],
                    }
                ],
                "max_temp": 45.0,
                "avg_temp": 43.7,
                "critical_temps": [],
            }
        )
    except sensors.SensorError as e:
        # Sensors not available - create empty result
        sensors_result = {"sensors": []}
        inspector_logger.info("Thermal sensors not available: %s", str(e))

    try:
        # Write sensors CSV artifact
        sensors_csv = artifacts_dir / "sensors.csv"
        csv_lines = ["timestamp,sensor,temp_c"]

        if use_sample or sensors_result.get("sensors"):
            import time

            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for sensor in sensors_result.get("sensors", []):
                for reading in sensor.get("readings", []):
                    csv_lines.append(
                        f"{timestamp},{reading['label']},{reading['temp']}"
                    )

        sensors_csv.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

        if sensors_result.get("max_temp"):
            tests_list.append(
                {
                    "name": "thermal_snapshot",
                    "status": "ok",
                    "data": {
                        "max_temp": sensors_result["max_temp"],
                        "avg_temp": sensors_result.get("avg_temp"),
                        "critical": len(sensors_result.get("critical_temps", [])) > 0,
                    },
                    "status_detail": "sample" if use_sample else "executed",
                }
            )
            inspector_logger.info(
                "Thermal snapshot OK: max=%.1f°C, avg=%.1f°C",
                sensors_result["max_temp"],
                sensors_result.get("avg_temp", 0),
            )
        else:
            tests_list.append(
                {
                    "name": "thermal_snapshot",
                    "status": "skip",
                    "reason": "No thermal sensors available",
                }
            )
            inspector_logger.info("Thermal snapshot: No sensors available")
    except Exception as e:
        (artifacts_dir / "sensors.csv").write_text(
            "timestamp,sensor,temp_c\n", encoding="utf-8"
        )
        tests_list.append(
            {
                "name": "thermal_snapshot",
                "status": "error",
                "error": str(e),
            }
        )
        inspector_logger.warning("Thermal snapshot failed: %s", str(e))

    inspector_logger.info("Step 8: Generating report...")
    report = compose_report(
        agent_version=__version__,
        device=device_info,
        artifacts=[str(p.relative_to(out_dir)) for p in artifacts_dir.iterdir()],
        tests=tests_list,
        mode=mode,
        profile=profile,
        smart_status=smart_status,
        native=native_capabilities,
    )

    report_path = out_dir / "report.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    logger.info("Report written to %s", report_path)
    inspector_logger.info("Report generated: %s", report_path)
    inspector_logger.info(
        "Overall Score: %d/%d (%s)",
        report["summary"]["overall_score"],
        100,
        report["summary"]["grade"],
    )

    # Generate human-readable report(s)
    inspector_logger.info("Step 9: Generating human-readable report(s)...")
    report_to_open = None

    # Determine if auto-open should be enabled
    should_auto_open = auto_open and not no_auto_open

    if format in ["txt", "both"]:
        try:
            txt_report_path = generate_txt_report(report, out_dir)
            logger.info("Text report written to %s", txt_report_path)
            inspector_logger.info("Text report generated: %s", txt_report_path)
            if report_to_open is None:
                report_to_open = txt_report_path
        except Exception as e:
            logger.warning("Failed to generate text report: %s", e)
            inspector_logger.warning("Text report generation failed: %s", e)

    if format in ["pdf", "both"]:
        try:
            pdf_report_path = generate_pdf_report(report, out_dir)
            if pdf_report_path:
                logger.info("PDF report written to %s", pdf_report_path)
                inspector_logger.info("PDF report generated: %s", pdf_report_path)
                # Prefer PDF over TXT if both are generated
                report_to_open = pdf_report_path
            else:
                logger.warning(
                    "PDF generation skipped: reportlab not installed. "
                    "Install with: pip install reportlab"
                )
                inspector_logger.warning(
                    "PDF report generation skipped: reportlab not available"
                )
        except Exception as e:
            logger.warning("Failed to generate PDF report: %s", e)
            inspector_logger.warning("PDF report generation failed: %s", e)

    # Auto-open the report if requested
    if should_auto_open and report_to_open:
        inspector_logger.info("Opening report: %s", report_to_open)
        if open_file(report_to_open):
            logger.info("Report opened successfully: %s", report_to_open)
            inspector_logger.info("Report opened in default application")
        else:
            logger.warning(
                "Failed to open report automatically. Please open manually: %s",
                report_to_open,
            )
            inspector_logger.warning("Failed to auto-open report")

    inspector_logger.info("=" * 60)
    inspector_logger.info("Inspection complete. Log file: %s", log_file)
    inspector_logger.info("=" * 60)

    # Exit codes: 0 success, 10 partial/warn, 20 failure
    # For scaffold, treat sample smart as WARN (10)
    if smart_status == "sample":
        logger.warning(
            "Quick run used sample artifacts; reporting partial success (WARN)"
        )
        raise SystemExit(10)


if __name__ == "__main__":
    cli()
