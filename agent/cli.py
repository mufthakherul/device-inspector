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

from . import __version__
from .logging_utils import setup_logging
from .plugins import inventory, smart
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
    help="Report format: 'txt' for text, 'pdf' for PDF (requires reportlab), 'both' for both formats",
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
    - Battery health (cycle count, capacity) [future]
    - Memory testing [future]
    - CPU benchmarking [future]

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

    inspector_logger.info("Step 3: Writing placeholder artifacts...")

    # Write placeholder memtester log and sensors CSV
    (artifacts_dir / "memtest.log").write_text(
        "Memtester placeholder\nOK\n", encoding="utf-8"
    )
    (artifacts_dir / "sensors.csv").write_text(
        "timestamp,cpu_temp,fan_rpm\n", encoding="utf-8"
    )

    inspector_logger.info("Step 4: Generating report...")
    report = compose_report(
        agent_version=__version__,
        device=device_info,
        artifacts=[str(p.relative_to(out_dir)) for p in artifacts_dir.iterdir()],
        tests=tests_list,
        mode=mode,
        profile=profile,
        smart_status=smart_status,
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
    inspector_logger.info("Step 5: Generating human-readable report(s)...")
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
            logger.warning("Failed to open report automatically. Please open manually: %s", report_to_open)
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
