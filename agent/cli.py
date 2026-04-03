# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Command-line interface for inspecta agent.

Provides a minimal Click-based CLI with `run --mode quick` to produce a
report.json and placeholder artifacts. Designed for tests and developer runs.
"""

from __future__ import annotations

import hashlib
import json
import logging
import platform as os_platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from . import __version__, native_bridge
from .capability_matrix import get_surface_capabilities, load_capability_matrix
from .evidence import (
    EvidenceError,
    audit_evidence_bundle,
    verify_evidence_manifest,
    write_evidence_manifest,
)
from .logging_utils import setup_logging
from .plugin_manifest import PluginManifestError, verify_plugin_manifest
from .plugins import battery, cpu_bench, disk_perf, inventory, memtest, sensors, smart
from .policy_pack import PolicyPackError, load_policy_pack
from .profiles import get_profile, is_valid_profile
from .redaction import apply_redaction, apply_retention_policy
from .report import compose_report
from .report_formatter import (
    generate_html_report,
    generate_pdf_report,
    generate_txt_report,
    open_file,
)
from .schema_compat import ensure_supported_report_version, migrate_legacy_report
from .upload_client import UploadError, upload_report_bundle

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
    GitHub: https://github.com/mufthakherul/inspecta-nexus
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
    help=(
        "Inspection mode: 'quick' for fast check, 'full' for enhanced comprehensive run"
    ),
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
    "--require-hardware",
    is_flag=True,
    help=(
        "Enforce real-device execution. Fails fast if sample mode is requested. "
        "Useful for production/field runs."
    ),
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
    type=click.Choice(["txt", "pdf", "html", "both"]),
    default="txt",
    help=(
        "Report format: 'txt' for text, 'pdf' for PDF (requires reportlab), "
        "'html' for browser-friendly HTML, 'both' for txt+pdf"
    ),
)
@click.option(
    "--with-stress",
    is_flag=True,
    help="Include thermal stress test with CPU throttling detection (adds ~30s)",
)
@click.option(
    "--upload",
    default=None,
    help=("Optional upload base URL (or /reports endpoint). Requires --token."),
)
@click.option(
    "--token",
    default=None,
    help="Upload token for authenticated report upload (used with --upload)",
)
@click.option(
    "--modes-profile",
    type=click.Choice(["balanced", "deep", "forensic"]),
    default="balanced",
    help=(
        "Full-mode runtime profile: balanced (10min), deep (30min), "
        "forensic (60min, max instrumentation)"
    ),
)
@click.option(
    "--timeout",
    type=int,
    default=None,
    help=(
        "Override timeout in seconds (default: profile-dependent). "
        "Use for custom hardware scenarios."
    ),
)
@click.option(
    "--dry-run",
    is_flag=True,
    help=(
        "Plan-only mode: display execution plan and probe configurations "
        "without actually running diagnostics"
    ),
)
@click.option(
    "--sign-key",
    default=None,
    help=("Optional path to Ed25519 private key (PEM) for detached manifest signing."),
)
@click.option(
    "--policy-pack",
    default=None,
    type=click.Path(path_type=Path),
    help=(
        "Optional policy-pack JSON path. Applies enterprise policy evaluation "
        "to report summary and recommendation."
    ),
)
@click.option(
    "--plugin-manifest",
    default=None,
    type=click.Path(path_type=Path),
    help=(
        "Optional signed plugin manifest JSON path to verify before run "
        "and include in evidence metadata."
    ),
)
@click.option(
    "--plugin-keyring",
    default=None,
    type=click.Path(path_type=Path),
    help=("Plugin keyring JSON file used to verify --plugin-manifest signatures."),
)
@click.option(
    "--redaction-preset",
    type=click.Choice(["none", "basic", "strict"]),
    default="none",
    help=(
        "Evidence redaction preset for generated report output. "
        "Use 'basic' or 'strict' for enterprise-safe sharing."
    ),
)
@click.option(
    "--retention-days",
    type=int,
    default=None,
    help=("Optional retention policy metadata (days) embedded in report evidence."),
)
@click.option(
    "--resume/--no-resume",
    default=True,
    help=(
        "Resume interrupted full-mode runs from checkpoint state "
        "stored in artifacts/full_mode_checkpoint.json (default: enabled)."
    ),
)
def run(
    mode: str,
    output: Path,
    profile: str,
    no_prompt: bool,
    use_sample: bool,
    require_hardware: bool,
    verbose: bool,
    auto_open: bool,
    no_auto_open: bool,
    format: str,
    with_stress: bool,
    upload: str | None,
    token: str | None,
    modes_profile: str,
    timeout: int | None,
    dry_run: bool,
    sign_key: str | None,
    policy_pack: Path | None,
    plugin_manifest: Path | None,
    plugin_keyring: Path | None,
    redaction_preset: str,
    retention_days: int | None,
    resume: bool,
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
            inspecta run --mode quick --output ./prod --require-hardware
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
    Note: 'full' mode currently runs an enhanced comprehensive pipeline
    that builds on quick mode with thermal stress enabled by default.
    """
    run_started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if require_hardware and use_sample:
        message = (
            "--require-hardware cannot be combined with --use-sample. "
            "Run without --use-sample for real-device diagnostics."
        )
        logger.error(message)
        click.echo(message, err=True)
        raise SystemExit(20)

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if upload and not token:
        logger.error("--upload requires --token")
        raise SystemExit(20)

    if retention_days is not None and retention_days <= 0:
        logger.error("--retention-days must be a positive integer")
        raise SystemExit(20)

    loaded_policy_pack: dict[str, Any] | None = None
    if policy_pack is not None:
        try:
            loaded_policy_pack = load_policy_pack(policy_pack)
            logger.info("Loaded policy pack: %s", loaded_policy_pack.get("pack_id"))
        except PolicyPackError as exc:
            logger.error("Policy pack validation failed: %s", exc)
            raise SystemExit(20)

    plugin_verification: dict[str, Any] | None = None
    if plugin_manifest is not None:
        if plugin_keyring is None:
            logger.error("--plugin-manifest requires --plugin-keyring")
            raise SystemExit(20)
        try:
            plugin_verification = verify_plugin_manifest(
                manifest_path=plugin_manifest,
                keyring_path=plugin_keyring,
            )
            logger.info(
                "Plugin manifest verified: %s@%s",
                plugin_verification.get("plugin_id"),
                plugin_verification.get("version"),
            )
        except PluginManifestError as exc:
            logger.error("Plugin manifest verification failed: %s", exc)
            raise SystemExit(20)

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

    # ========================================================================
    # Full-mode Profile and Timeout Configuration
    # ========================================================================
    if mode == "full":
        # Load and validate full-mode profile
        if not is_valid_profile(modes_profile):
            logger.error(
                "Invalid full-mode profile: %s. Available: balanced, deep, forensic",
                modes_profile,
            )
            raise SystemExit(1)

        runtime_profile = get_profile(modes_profile)
        inspector_logger.info(
            "Full mode enabled: profile=%s (timeout=%ds, "
            "stress_duration=%ds, thermal_cycles=%d)",
            runtime_profile.name,
            runtime_profile.timeout_seconds,
            runtime_profile.stress_duration_seconds,
            runtime_profile.enable_thermal_cycles,
        )

        # Override timeout if specified
        effective_timeout = (
            timeout if timeout is not None else runtime_profile.timeout_seconds
        )
        inspector_logger.info("Effective timeout: %d seconds", effective_timeout)

        # Phase-1 full mode baseline: enforce thermal stress unless explicitly set.
        if not with_stress:
            with_stress = True
            inspector_logger.info(
                "Full mode auto-enabled thermal stress test (--with-stress)."
            )

        # ====================================================================
        # Dry-run Mode: Display Plan Without Execution
        # ====================================================================
        if dry_run:
            inspector_logger.info("DRY-RUN MODE: No actual probes will be executed")
            plan_output = _generate_dry_run_plan(
                mode=mode,
                profile_name=modes_profile,
                runtime_profile=runtime_profile,
                timeout=effective_timeout,
                use_sample=use_sample,
            )
            inspector_logger.info("Execution Plan:")
            inspector_logger.info(plan_output)
            print(plan_output)  # Also print to console
            raise SystemExit(0)  # Exit after plan display
    else:
        # Quick mode: use default timeout of 300s
        effective_timeout = timeout if timeout is not None else 300
        inspector_logger.info("Quick mode: timeout=%d seconds", effective_timeout)

    # Runtime profile defaults when quick mode is used
    if mode != "full":
        runtime_profile = None

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = artifacts_dir / "full_mode_checkpoint.json"
    checkpoint_enabled = mode == "full"
    checkpoint_data: dict[str, Any] = {
        "version": 1,
        "mode": mode,
        "updated_at": run_started_at,
        "completed_steps": [],
        "state": {},
    }

    if checkpoint_enabled and resume and checkpoint_path.exists():
        loaded_checkpoint = _load_full_mode_checkpoint(checkpoint_path)
        if loaded_checkpoint:
            checkpoint_data = loaded_checkpoint
            inspector_logger.info(
                "Resuming full-mode run from checkpoint: %s",
                checkpoint_path,
            )

    checkpoint_state: dict[str, Any] = checkpoint_data.get("state", {})
    completed_steps: set[str] = set(checkpoint_data.get("completed_steps", []))

    tests_list: list[dict[str, Any]] = checkpoint_state.get("tests_list", [])
    device_info = checkpoint_state.get("device_info")
    smart_results = checkpoint_state.get("smart_results", [])
    smart_status = checkpoint_state.get("smart_status", "missing")

    # Get device inventory
    if (
        checkpoint_enabled
        and "inventory" in completed_steps
        and device_info is not None
    ):
        inspector_logger.info("Step 1: Inventory restored from checkpoint")
    else:
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
            inspector_logger.warning(
                "Inventory detection failed: %s", e, exc_info=verbose
            )
            device_info = {"vendor": "unknown", "model": "unknown", "serial": None}

        if checkpoint_enabled:
            _save_full_mode_checkpoint(
                checkpoint_path=checkpoint_path,
                checkpoint_data=checkpoint_data,
                completed_step="inventory",
                state_updates={
                    "device_info": device_info,
                    "tests_list": tests_list,
                    "smart_results": smart_results,
                    "smart_status": smart_status,
                },
            )
            completed_steps.add("inventory")

    # Scan storage devices with SMART
    if checkpoint_enabled and "smart_scan" in completed_steps and smart_results:
        inspector_logger.info("Step 2: SMART scan restored from checkpoint")
    else:
        inspector_logger.info("Step 2: Scanning storage devices...")
        logger.info("Scanning storage devices...")
        smart_results = smart.scan_all_devices(use_sample=use_sample)

        if not smart_results:
            logger.warning("No storage devices found or SMART data unavailable")
            inspector_logger.warning("No storage devices detected")
            smart_status = "missing"
        else:
            smart_status = "ok"
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

        if checkpoint_enabled:
            _save_full_mode_checkpoint(
                checkpoint_path=checkpoint_path,
                checkpoint_data=checkpoint_data,
                completed_step="smart_scan",
                state_updates={
                    "device_info": device_info,
                    "tests_list": tests_list,
                    "smart_results": smart_results,
                    "smart_status": smart_status,
                },
            )
            completed_steps.add("smart_scan")

    # Sprint 2: SMART timeline snapshots for full mode.
    if mode == "full" and runtime_profile and runtime_profile.enable_smart_timeline:
        if checkpoint_enabled and "smart_timeline" in completed_steps:
            inspector_logger.info("SMART timeline restored from checkpoint")
        else:
            timeline_devices = [
                r.get("device") for r in smart_results if r.get("device")
            ]
            timeline_result = smart.collect_timeline_snapshots(
                devices=timeline_devices,
                intervals_seconds=[
                    0,
                    max(1, runtime_profile.stress_duration_seconds // 2),
                ],
                use_sample=use_sample,
            )

            timeline_artifact = artifacts_dir / "smart_timeline.json"
            timeline_artifact.write_text(
                json.dumps(timeline_result, indent=2),
                encoding="utf-8",
            )
            tests_list.append(
                {
                    "name": "smart_timeline",
                    "status": (
                        "ok"
                        if timeline_result.get("status") in {"ok", "partial"}
                        else "skip"
                    ),
                    "data": {
                        "timeline_status": timeline_result.get("status"),
                        "snapshot_count": len(timeline_result.get("snapshots", [])),
                        "error_count": len(timeline_result.get("errors", [])),
                    },
                    "status_detail": "sample" if use_sample else "executed",
                }
            )
            inspector_logger.info(
                "SMART timeline collected: snapshots=%d errors=%d",
                len(timeline_result.get("snapshots", [])),
                len(timeline_result.get("errors", [])),
            )

            if checkpoint_enabled:
                _save_full_mode_checkpoint(
                    checkpoint_path=checkpoint_path,
                    checkpoint_data=checkpoint_data,
                    completed_step="smart_timeline",
                    state_updates={
                        "device_info": device_info,
                        "tests_list": tests_list,
                        "smart_results": smart_results,
                        "smart_status": smart_status,
                    },
                )
                completed_steps.add("smart_timeline")

    # Scan battery health
    if checkpoint_enabled and "battery" in completed_steps:
        inspector_logger.info("Step 3: Battery scan restored from checkpoint")
    else:
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

        if checkpoint_enabled:
            _save_full_mode_checkpoint(
                checkpoint_path=checkpoint_path,
                checkpoint_data=checkpoint_data,
                completed_step="battery",
                state_updates={
                    "device_info": device_info,
                    "tests_list": tests_list,
                    "smart_results": smart_results,
                    "smart_status": smart_status,
                },
            )
            completed_steps.add("battery")

    # Run disk performance benchmark
    if checkpoint_enabled and "disk_perf" in completed_steps:
        inspector_logger.info("Step 4: Disk benchmark restored from checkpoint")
    else:
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

        if checkpoint_enabled:
            _save_full_mode_checkpoint(
                checkpoint_path=checkpoint_path,
                checkpoint_data=checkpoint_data,
                completed_step="disk_perf",
                state_updates={
                    "device_info": device_info,
                    "tests_list": tests_list,
                    "smart_results": smart_results,
                    "smart_status": smart_status,
                },
            )
            completed_steps.add("disk_perf")

    # Sprint 2 advanced: IO stress cycles for full mode profiles.
    if mode == "full" and runtime_profile:
        if checkpoint_enabled and "disk_stress" in completed_steps:
            inspector_logger.info("Step 4b: Disk stress restored from checkpoint")
        else:
            io_cycles = max(1, int(runtime_profile.enable_thermal_cycles))
            inspector_logger.info(
                "Step 4b: Running IO stress cycles (%d cycle(s))...",
                io_cycles,
            )
            io_stress = disk_perf.run_io_stress_cycles(
                cycles=io_cycles,
                use_sample=use_sample,
            )

            io_artifact = artifacts_dir / "disk_stress.json"
            io_artifact.write_text(json.dumps(io_stress, indent=2), encoding="utf-8")

            tests_list.append(
                {
                    "name": "disk_stress_cycles",
                    "status": (
                        "ok"
                        if io_stress.get("status") in {"ok", "partial"}
                        else "error"
                    ),
                    "data": io_stress.get("summary", {}),
                    "status_detail": "sample" if use_sample else "executed",
                }
            )
            inspector_logger.info(
                "IO stress cycles complete: status=%s",
                io_stress.get("status"),
            )

            if checkpoint_enabled:
                _save_full_mode_checkpoint(
                    checkpoint_path=checkpoint_path,
                    checkpoint_data=checkpoint_data,
                    completed_step="disk_stress",
                    state_updates={
                        "device_info": device_info,
                        "tests_list": tests_list,
                        "smart_results": smart_results,
                        "smart_status": smart_status,
                    },
                )
                completed_steps.add("disk_stress")

    # Run CPU benchmark
    if checkpoint_enabled and "cpu_bench" in completed_steps:
        inspector_logger.info("Step 5: CPU benchmark restored from checkpoint")
    else:
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

        if checkpoint_enabled:
            _save_full_mode_checkpoint(
                checkpoint_path=checkpoint_path,
                checkpoint_data=checkpoint_data,
                completed_step="cpu_bench",
                state_updates={
                    "device_info": device_info,
                    "tests_list": tests_list,
                    "smart_results": smart_results,
                    "smart_status": smart_status,
                },
            )
            completed_steps.add("cpu_bench")

    if checkpoint_enabled and "memory_test" in completed_steps:
        inspector_logger.info("Step 6: Memory test restored from checkpoint")
    else:
        inspector_logger.info("Step 6: Running memory test...")
        memtest_duration = 30
        if mode == "full" and runtime_profile:
            memtest_duration = max(30, runtime_profile.stress_duration_seconds // 2)

        memtest_result = memtest.scan_memory(
            duration_seconds=memtest_duration,
            use_sample=use_sample,
        )
        if memtest_result["status"] == "ok":
            # Write memtest log artifact
            memtest_artifact = artifacts_dir / "memtest.log"
            memtest_raw_text = memtest_result.get("raw_text", "OK\n")
            memtest_artifact.write_text(memtest_raw_text, encoding="utf-8")

            # Sprint 2: importer-based deep parsing (memtester source for now).
            imported_memtest = memtest.import_memtest_log(
                memtest_raw_text, source="memtester"
            )
            tests_list.append(
                {
                    "name": "memory_test",
                    "status": "ok",
                    "data": imported_memtest,
                    "status_detail": "sample" if use_sample else "executed",
                }
            )
            inspector_logger.info(
                "Memory test OK: pass_count=%s error_count=%s",
                imported_memtest.get("pass_count", "N/A"),
                imported_memtest.get("error_count", "N/A"),
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
            inspector_logger.info(
                "Memory test skipped: %s", memtest_result.get("reason")
            )
        else:
            (artifacts_dir / "memtest.log").write_text(
                f"Error: {memtest_result.get('error', 'unknown')}\n",
                encoding="utf-8",
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

        if checkpoint_enabled:
            _save_full_mode_checkpoint(
                checkpoint_path=checkpoint_path,
                checkpoint_data=checkpoint_data,
                completed_step="memory_test",
                state_updates={
                    "device_info": device_info,
                    "tests_list": tests_list,
                    "smart_results": smart_results,
                    "smart_status": smart_status,
                },
            )
            completed_steps.add("memory_test")

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

    # Step 8: Thermal stress test (optional, enabled with --with-stress)
    stress_duration = 30
    if mode == "full" and runtime_profile:
        stress_duration = runtime_profile.stress_duration_seconds

    if with_stress:
        inspector_logger.info(
            "Step 8: Running thermal stress test (%ss)...",
            stress_duration,
        )
        try:
            if use_sample:
                # Sample thermal stress data
                thermal_stress_result = {
                    "baseline_max_temp": 45.0,
                    "baseline_freq_mhz": 3600.0,
                    "peak_temp": 78.5,
                    "avg_stress_temp": 72.3,
                    "min_freq_mhz": 3400.0,
                    "avg_freq_mhz": 3500.0,
                    "throttling_detected": False,
                    "throttle_reason": None,
                    "duration_seconds": stress_duration,
                    "num_samples": 15,
                    "samples": [
                        {
                            "timestamp": "2026-03-27T13:00:00Z",
                            "temp_c": 45.0,
                            "freq_mhz": 3600.0,
                            "throttled": False,
                        },
                        {
                            "timestamp": "2026-03-27T13:00:02Z",
                            "temp_c": 58.2,
                            "freq_mhz": 3590.0,
                            "throttled": False,
                        },
                        {
                            "timestamp": "2026-03-27T13:00:04Z",
                            "temp_c": 72.5,
                            "freq_mhz": 3580.0,
                            "throttled": False,
                        },
                    ],
                }
            else:
                thermal_stress_result = sensors.detect_cpu_throttling(
                    duration_seconds=stress_duration
                )

            thermal_severity = sensors.classify_thermal_severity(
                peak_temp=thermal_stress_result.get("peak_temp"),
                throttling_detected=thermal_stress_result.get("throttling_detected"),
                throttle_reason=thermal_stress_result.get("throttle_reason"),
            )

            # Write thermal stress CSV artifact
            if thermal_stress_result.get("samples"):
                thermal_csv = artifacts_dir / "thermal_stress.csv"
                csv_content = sensors.generate_thermal_stress_csv(
                    thermal_stress_result["samples"]
                )
                thermal_csv.write_text(csv_content, encoding="utf-8")

            # Add test result
            tests_list.append(
                {
                    "name": "thermal_stress",
                    "status": "ok",
                    "data": {
                        "baseline_temp": thermal_stress_result.get("baseline_max_temp"),
                        "peak_temp": thermal_stress_result.get("peak_temp"),
                        "avg_temp": thermal_stress_result.get("avg_stress_temp"),
                        "throttled": thermal_stress_result.get("throttling_detected"),
                        "throttle_reason": thermal_stress_result.get("throttle_reason"),
                        "baseline_freq_mhz": thermal_stress_result.get(
                            "baseline_freq_mhz"
                        ),
                        "min_freq_mhz": thermal_stress_result.get("min_freq_mhz"),
                        "thermal_severity": thermal_severity.get("severity"),
                        "thermal_penalty": thermal_severity.get("score_penalty"),
                    },
                    "status_detail": "sample" if use_sample else "executed",
                }
            )

            if thermal_stress_result.get("throttling_detected"):
                peak_temp = thermal_stress_result.get("peak_temp")
                peak_temp_display = (
                    f"{peak_temp:.1f}°C"
                    if isinstance(peak_temp, (int, float))
                    else "N/A"
                )
                inspector_logger.warning(
                    "⚠️  Throttling detected! Peak: %s, Reason: %s",
                    peak_temp_display,
                    thermal_stress_result.get("throttle_reason", "Unknown"),
                )
            else:
                peak_temp = thermal_stress_result.get("peak_temp")
                peak_temp_display = (
                    f"{peak_temp:.1f}°C"
                    if isinstance(peak_temp, (int, float))
                    else "N/A"
                )
                inspector_logger.info(
                    "Thermal stress OK: Peak=%s, no throttling detected",
                    peak_temp_display,
                )

        except sensors.SensorError as e:
            inspector_logger.warning("Thermal stress test skipped: %s", str(e))
            tests_list.append(
                {
                    "name": "thermal_stress",
                    "status": "skip",
                    "reason": str(e),
                }
            )
        except Exception as e:
            inspector_logger.error("Thermal stress test failed: %s", str(e))
            tests_list.append(
                {
                    "name": "thermal_stress",
                    "status": "error",
                    "error": str(e),
                }
            )
    else:
        inspector_logger.info(
            "Step 8: Thermal stress test skipped (use --with-stress to enable)"
        )

    inspector_logger.info("Step 9: Generating report...")
    report = compose_report(
        agent_version=__version__,
        device=device_info,
        artifacts=[str(p.relative_to(out_dir)) for p in artifacts_dir.iterdir()],
        tests=tests_list,
        mode=mode,
        profile=profile,
        smart_status=smart_status,
        native=native_capabilities,
        policy_pack_payload=loaded_policy_pack,
        plugin_manifest_verification=plugin_verification,
    )

    apply_retention_policy(report, retention_days)
    report = apply_redaction(report, redaction_preset)

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
    inspector_logger.info("Step 10: Generating human-readable report(s)...")
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

    if format == "html":
        try:
            html_report_path = generate_html_report(report, out_dir)
            logger.info("HTML report written to %s", html_report_path)
            inspector_logger.info("HTML report generated: %s", html_report_path)
            report_to_open = html_report_path
        except Exception as e:
            logger.warning("Failed to generate HTML report: %s", e)
            inspector_logger.warning("HTML report generation failed: %s", e)

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

    if upload and token:
        inspector_logger.info("Step 11: Uploading report bundle (opt-in)...")
        try:
            upload_result = upload_report_bundle(
                upload_url=upload,
                token=token,
                output_dir=out_dir,
                metadata={
                    "mode": mode,
                    "profile": profile,
                    "use_sample": use_sample,
                    "agent_version": __version__,
                },
            )
            inspector_logger.info("Upload successful: %s", upload_result)
            logger.info("Upload successful (status=%s)", upload_result.get("status"))
        except UploadError as e:
            inspector_logger.warning("Upload failed: %s", str(e))
            logger.warning("Upload failed: %s", str(e))

    inspector_logger.info("Step 12: Generating evidence manifest...")
    evidence_candidates: list[str] = []
    # Exclude agent.log since it's still being written to by the logger
    evidence_candidates.extend(
        [
            str(p.relative_to(out_dir))
            for p in artifacts_dir.iterdir()
            if not p.name.endswith(".log")
        ]
    )

    txt_report = out_dir / "report.txt"
    pdf_report = out_dir / "report.pdf"
    html_report = out_dir / "report.html"
    for extra in (txt_report, pdf_report, html_report):
        if extra.exists() and extra.is_file():
            evidence_candidates.append(str(extra.relative_to(out_dir)))

    # Sprint 6 policy: always include report.json in manifest coverage.
    evidence_candidates.append("report.json")

    # Immutable run metadata for forensic reproducibility.
    def _tool_version(tool: str, args: list[str] | None = None) -> str | None:
        command = [tool] + (args or ["--version"])
        try:
            res = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return None

        text = (res.stdout or "").strip() or (res.stderr or "").strip()
        if not text:
            return None
        return text.splitlines()[0][:200]

    os_fingerprint_source = "|".join(
        [
            os_platform.system(),
            os_platform.release(),
            os_platform.version(),
            os_platform.machine(),
            os_platform.processor() or "",
        ]
    )

    run_finished_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    run_metadata = {
        "started_at": run_started_at,
        "completed_at": run_finished_at,
        "python_version": os_platform.python_version(),
        "platform": os_platform.platform(),
        "os_fingerprint_sha256": hashlib.sha256(
            os_fingerprint_source.encode("utf-8")
        ).hexdigest(),
        "tool_versions": {
            "smartctl": _tool_version("smartctl"),
            "fio": _tool_version("fio"),
            "sysbench": _tool_version("sysbench"),
            "memtester": _tool_version("memtester"),
            "sensors": _tool_version("sensors"),
            "powercfg": _tool_version("powercfg", ["/?"]),
            "winsat": _tool_version("winsat", ["/?"]),
        },
    }

    sign_key_path = Path(sign_key) if sign_key else None

    # Finalize report metadata before manifest creation so report.json hash is stable.
    if "artifacts/manifest.json" not in report.get("artifacts", []):
        report.setdefault("artifacts", []).append("artifacts/manifest.json")

    report.setdefault("evidence", {})
    report["evidence"]["manifest_sha256"] = None
    report["evidence"]["manifest_path"] = "artifacts/manifest.json"
    report["evidence"]["signed"] = bool(sign_key_path)
    report["run_metadata"] = run_metadata

    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    try:
        manifest_rel_path, manifest_sha256 = write_evidence_manifest(
            output_dir=out_dir,
            relative_paths=evidence_candidates,
            agent_version=__version__,
            run_metadata=run_metadata,
            sign_key_path=sign_key_path,
        )
    except EvidenceError as exc:
        inspector_logger.error("Evidence manifest signing failed: %s", exc)
        raise SystemExit(20)

    if manifest_rel_path not in report["artifacts"]:
        report["artifacts"].append(manifest_rel_path)

    # Do not rewrite report after manifest generation to preserve report.json hash
    # when report.json is included in manifest coverage policy.

    inspector_logger.info(
        "Evidence manifest written: %s (sha256=%s)",
        manifest_rel_path,
        manifest_sha256,
    )

    inspector_logger.info("=" * 60)
    inspector_logger.info("Inspection complete. Log file: %s", log_file)
    inspector_logger.info("=" * 60)

    if checkpoint_enabled and checkpoint_path.exists():
        checkpoint_path.unlink(missing_ok=True)

    # Exit codes: 0 success, 10 partial/warn, 20 failure
    # For scaffold, treat sample smart as WARN (10)
    if smart_status == "sample":
        logger.warning(
            "Quick run used sample artifacts; reporting partial success (WARN)"
        )
        raise SystemExit(10)


@cli.command("report")
@click.argument("report_file", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--open",
    "open_report",
    is_flag=True,
    help="Open report in default app/browser after generating requested format.",
)
@click.option(
    "--format",
    "report_format",
    type=click.Choice(["txt", "pdf", "html"]),
    default="html",
    help="Format to generate from report.json.",
)
def report_cmd(report_file: Path, open_report: bool, report_format: str) -> None:
    """Generate/open human-readable outputs from an existing report.json."""
    if report_file.suffix.lower() != ".json":
        raise click.BadParameter("report_file must be a JSON file")

    with open(report_file, encoding="utf-8") as fh:
        report = migrate_legacy_report(json.load(fh))

    ensure_supported_report_version(str(report.get("report_version", "0.0.0")))

    output_dir = report_file.parent
    generated_path: Path | None = None

    if report_format == "txt":
        generated_path = generate_txt_report(report, output_dir)
    elif report_format == "pdf":
        generated_path = generate_pdf_report(report, output_dir)
        if generated_path is None:
            raise click.ClickException(
                "PDF generation unavailable. Install optional deps: reportlab"
            )
    elif report_format == "html":
        generated_path = generate_html_report(report, output_dir)

    click.echo(f"Generated: {generated_path}")

    if open_report and generated_path is not None:
        if not open_file(generated_path):
            raise click.ClickException(
                f"Failed to open report automatically: {generated_path}"
            )
        click.echo(f"Opened: {generated_path}")


@cli.command("capabilities")
@click.option(
    "--surface",
    type=click.Choice(["cli", "desktop", "mobile"]),
    default="cli",
    help="Target surface to view capability declarations for.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output capability payload as JSON.",
)
def capabilities_cmd(surface: str, as_json: bool) -> None:
    """Show versioned capability matrix data for CLI/Desktop/Mobile surfaces."""
    matrix = load_capability_matrix()
    payload = get_surface_capabilities(surface)

    if as_json:
        click.echo(json.dumps(payload, indent=2))
        return

    click.echo(f"Capability Matrix Version: {matrix.get('matrix_version')}")
    click.echo(f"Surface: {payload.get('surface')}")
    click.echo(f"Description: {payload.get('description')}")
    click.echo("Capabilities:")
    for item in payload.get("capabilities", []):
        click.echo(f"  - {item}")


@cli.command("verify")
@click.argument("bundle_dir", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--manifest",
    default="artifacts/manifest.json",
    help="Path to manifest file (relative to bundle directory).",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output results as JSON instead of human-readable format.",
)
@click.option(
    "--public-key",
    default=None,
    help="Optional Ed25519 public key (PEM) for signed manifest verification.",
)
def verify_cmd(
    bundle_dir: Path,
    manifest: str,
    as_json: bool,
    public_key: str | None,
) -> None:
    """Verify evidence integrity of a report bundle.

    Validates SHA256 hashes stored in the manifest against actual files.
    Detects tampering, data corruption, or missing artifacts.

    \b
    Examples:
      inspecta verify ./output
      inspecta verify ./output --manifest artifacts/manifest.json
      inspecta verify ./output --json

    Exit codes:
      0 - All files intact, no tampering detected
      1 - Hash mismatch or integrity failure
      2 - Bundle or manifest not found
    """
    if not bundle_dir.is_dir():
        raise click.BadParameter(f"Bundle directory not found: {bundle_dir}")

    result = verify_evidence_manifest(
        bundle_dir,
        manifest,
        public_key_path=Path(public_key) if public_key else None,
    )

    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(f"Bundle:            {bundle_dir}")
        click.echo(f"Manifest:          {manifest}")
        click.echo(f"Files checked:     {result.get('checked', 0)}")
        click.echo(f"Integrity status:  {'✓ OK' if result.get('ok') else '✗ FAILED'}")
        click.echo(
            "Result code:       "
            f"{result.get('exit_code')} ({result.get('exit_reason')})"
        )

        if result.get("mismatches"):
            click.echo("\n⚠ Integrity Issues:")
            for mismatch in result["mismatches"]:
                path = mismatch.get("path", "unknown")
                reason = mismatch.get("reason", "unknown")
                click.echo(f"  - {path}: {reason}")
                if "expected" in mismatch and "actual" in mismatch:
                    click.echo(f"    Expected: {mismatch['expected'][:16]}...")
                    click.echo(f"    Found:    {mismatch['actual'][:16]}...")

        if result.get("missing"):
            click.echo("\n⚠ Missing Files:")
            for missing in result["missing"]:
                click.echo(f"  - {missing}")

    # Exit code based on integrity status
    raise SystemExit(int(result.get("exit_code", 1)))


@cli.command("audit")
@click.argument("bundle_dir", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--manifest",
    default="artifacts/manifest.json",
    help="Path to manifest file (relative to bundle directory).",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output results as JSON instead of human-readable format.",
)
@click.option(
    "--public-key",
    default=None,
    help="Optional Ed25519 public key (PEM) when auditing signed manifests.",
)
def audit_cmd(
    bundle_dir: Path,
    manifest: str,
    as_json: bool,
    public_key: str | None,
) -> None:
    """Audit bundle reproducibility and deterministic evidence properties.

    Combines integrity verification with deterministic-entry checks and
    re-index comparison to ensure a bundle can be reproduced consistently.

    Exit codes:
      0 - Reproducible and integrity verified
      1 - Integrity or reproducibility checks failed
      2 - Bundle or manifest not found / invalid manifest JSON
    """
    if not bundle_dir.is_dir():
        raise click.BadParameter(f"Bundle directory not found: {bundle_dir}")

    result = audit_evidence_bundle(
        output_dir=bundle_dir,
        manifest_rel_path=manifest,
        public_key_path=Path(public_key) if public_key else None,
    )

    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(f"Bundle:                 {bundle_dir}")
        click.echo(f"Manifest:               {manifest}")
        integrity_status = "✓ OK" if result.get("integrity_ok") else "✗ FAILED"
        click.echo(f"Integrity:              {integrity_status}")
        click.echo(
            "Deterministic entries:   "
            f"{'✓ OK' if result.get('deterministic_entries') else '✗ FAILED'}"
        )
        click.echo(
            "Metadata completeness:   "
            f"{'✓ OK' if result.get('entry_metadata_complete') else '✗ FAILED'}"
        )
        click.echo(
            "Re-indexed parity:       "
            f"{'✓ OK' if result.get('reindexed_entries_match') else '✗ FAILED'}"
        )
        click.echo(
            "Result code:             "
            f"{result.get('exit_code')} ({result.get('exit_reason')})"
        )

    raise SystemExit(int(result.get("exit_code", 1)))


@cli.command("plugin-verify")
@click.argument("manifest_file", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--keyring",
    required=True,
    type=click.Path(path_type=Path, exists=True),
    help="Path to plugin keyring JSON used for signature verification.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output verification result as JSON.",
)
def plugin_verify_cmd(manifest_file: Path, keyring: Path, as_json: bool) -> None:
    """Verify signed plugin manifest against schema + keyring."""
    try:
        result = verify_plugin_manifest(
            manifest_path=manifest_file,
            keyring_path=keyring,
        )
    except PluginManifestError as exc:
        if as_json:
            click.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            click.echo(f"Plugin manifest verification failed: {exc}")
        raise SystemExit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(
            "Plugin manifest verified: "
            f"{result.get('plugin_id')}@{result.get('version')} "
            f"(key_id={result.get('public_key_id')})"
        )

    raise SystemExit(0)


@cli.command("policy-export")
@click.argument("policy_file", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--output",
    required=True,
    type=click.Path(path_type=Path),
    help="Destination path for normalized policy-pack JSON.",
)
def policy_export_cmd(policy_file: Path, output: Path) -> None:
    """Validate and export normalized policy-pack JSON."""
    try:
        payload = load_policy_pack(policy_file)
    except PolicyPackError as exc:
        raise click.ClickException(str(exc))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    click.echo(f"Exported policy pack: {output}")


@cli.command("policy-import")
@click.argument("policy_file", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(path_type=Path),
    help="Directory where imported policy-pack file will be written.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing target file if it already exists.",
)
def policy_import_cmd(policy_file: Path, output_dir: Path, force: bool) -> None:
    """Import a validated policy-pack into a target directory."""
    try:
        payload = load_policy_pack(policy_file)
    except PolicyPackError as exc:
        raise click.ClickException(str(exc))

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{payload.get('pack_id', 'policy-pack')}.json"
    if target.exists() and not force:
        raise click.ClickException(
            f"Target policy file already exists: {target}. Use --force to overwrite."
        )

    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    click.echo(f"Imported policy pack: {target}")


# ============================================================================
# Helper Functions for Full-Mode Planning and Configuration
# ============================================================================


def _generate_dry_run_plan(
    mode: str,
    profile_name: str,
    runtime_profile,
    timeout: int,
    use_sample: bool,
) -> str:
    """Generate a human-readable execution plan for dry-run mode.

    Args:
        mode: Inspection mode (quick or full)
        profile_name: Full-mode profile name (balanced, deep, forensic)
        runtime_profile: RuntimeProfile instance with configuration
        timeout: Effective timeout in seconds
        use_sample: Whether sample data will be used

    Returns:
        Formatted plan text
    """
    lines = [
        "",
        "=" * 70,
        "INSPECTA DRY-RUN EXECUTION PLAN",
        "=" * 70,
        "",
        f"Mode                  : {mode.upper()}",
        f"Profile               : {profile_name.upper()}",
        f"Sample Data           : {'Yes' if use_sample else 'No (Real Hardware)'}",
        f"Timeout               : {timeout} seconds ({timeout // 60} min)",
        "Auto-Open Report      : No (dry-run only)",
        "",
        "FULL-MODE CONFIGURATION:",
        "-" * 70,
        f"  Stress Duration     : {runtime_profile.stress_duration_seconds} seconds",
        f"  Thermal Cycles      : {runtime_profile.enable_thermal_cycles}",
        f"  Memory Test Enabled : {runtime_profile.enable_memtest}",
        f"  SMART Timeline      : {runtime_profile.enable_smart_timeline}",
        f"  Retry Max Attempts  : {runtime_profile.retry_max_attempts}",
        f"  Safe-Stop Enabled   : {runtime_profile.safe_stop_enabled}",
        "",
        "PLANNED PROBES:",
        "-" * 70,
        "  1. Device Inventory (vendor, model, serial, BIOS)",
        "  2. Storage SMART Health (all drives: SATA, NVMe, USB)",
        "  3. Battery Health (cycle count, capacity, design)",
        "  4. Disk Performance (fio benchmark: read/write throughput)",
        "  5. CPU Benchmarking (sysbench: events/sec or frequency)",
    ]

    if mode == "full":
        lines.extend(
            [
                "  6. Thermal Stress Testing (CPU load + throttle detection)",
                "  7. Memory Testing (memtest86 integration [future])",
                "  8. Extended SMART Timeline (per-device snapshots)",
                "  9. Thermal Cycling Measurements (phase transitions)",
            ]
        )

    lines.extend(
        [
            "",
            "OUTPUT ARTIFACTS:",
            "-" * 70,
            "  report.json           : Main inspection report with scores",
            "  report.txt            : Human-readable text report",
            "  artifacts/",
            "    agent.log           : Detailed execution log",
            "    smart_*.json        : Raw SMART data per device",
            "    battery.json        : Battery health details",
            "    disk_perf.json      : fio benchmark summary",
            "    cpu_bench.json      : sysbench benchmark summary",
        ]
    )

    if mode == "full":
        lines.extend(
            [
                "    thermal_stress.json : Thermal test results",
                "    memtest.log         : Memory test results [future]",
            ]
        )

    lines.extend(
        [
            "",
            "TO EXECUTE THIS PLAN, run without --dry-run:",
            "-" * 70,
            "  inspecta run --mode full --output <dir> --modes-profile " + profile_name,
            "",
            "=" * 70,
            "",
        ]
    )

    return "\n".join(lines)


def _load_full_mode_checkpoint(checkpoint_path: Path) -> dict[str, Any] | None:
    try:
        with open(checkpoint_path, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return None
        data.setdefault("completed_steps", [])
        data.setdefault("state", {})
        return data
    except (OSError, json.JSONDecodeError):
        return None


def _save_full_mode_checkpoint(
    checkpoint_path: Path,
    checkpoint_data: dict[str, Any],
    completed_step: str,
    state_updates: dict[str, Any],
) -> None:
    completed_steps = set(checkpoint_data.get("completed_steps", []))
    completed_steps.add(completed_step)
    checkpoint_data["completed_steps"] = sorted(completed_steps)
    checkpoint_data["updated_at"] = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )

    state = checkpoint_data.setdefault("state", {})
    state.update(state_updates)

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as fh:
        json.dump(checkpoint_data, fh, indent=2)


if __name__ == "__main__":
    cli()
