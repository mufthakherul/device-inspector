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
from .plugins import inventory, smart
from .report import compose_report

logger = logging.getLogger("inspecta")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """inspecta — local-first device inspection (quick-mode scaffold)."""


@cli.command()
@click.option("--use-sample", is_flag=True, help="Use sample data instead of executing dmidecode")
def inventory_cmd(use_sample: bool) -> None:
    """Detect and display device hardware information.

    Requires root/sudo privileges unless --use-sample is specified.
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
)
@click.option("--output", required=True, type=click.Path(path_type=Path))
@click.option(
    "--profile", default="default", help="Buyer profile (Office, Gamer, etc.)"
)
@click.option("--no-prompt", is_flag=True, help="Don't prompt for consent (for CI).")
@click.option("--use-sample", is_flag=True, help="Use sample data for testing (no root required)")
def run(mode: str, output: Path, profile: str, no_prompt: bool, use_sample: bool) -> None:
    """Run an inspection. In this scaffold only `quick` is implemented.

    The command writes <output>/report.json and an `artifacts/` folder with
    small sample artifacts (or mocked outputs) so tests and CI can validate
    the pipeline without requiring native binaries.
    """
    logger.info("Starting inspecta run (mode=%s, profile=%s)", mode, profile)

    if mode != "quick":
        logger.error("Only quick mode is supported in this scaffold. Exiting.")
        raise SystemExit(20)

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Get device inventory
    try:
        device_info = inventory.get_inventory(use_sample=use_sample)
        logger.info("Detected device: %s %s", device_info.get("vendor"), device_info.get("model"))
    except inventory.InventoryError as e:
        logger.warning("Inventory detection failed: %s. Using placeholder.", e)
        device_info = {"vendor": "unknown", "model": "unknown", "serial": None}

    # Scan storage devices with SMART
    logger.info("Scanning storage devices...")
    smart_results = smart.scan_all_devices(use_sample=use_sample)

    if not smart_results:
        logger.warning("No storage devices found or SMART data unavailable")
        smart_status = "missing"
        tests_list = []
    else:
        smart_status = "ok"
        tests_list = []

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
                tests_list.append({
                    "name": f"smartctl_{device_name}",
                    "status": "ok",
                    "data": result["data"],
                    "status_detail": "sample" if use_sample else "executed",
                })

                logger.info("Collected SMART data for %s: %s",
                           result["device"], result["data"].get("model", "unknown"))
            else:
                # Add error to tests list
                tests_list.append({
                    "name": f"smartctl_{device_name}",
                    "status": "error",
                    "error": result.get("error", "Unknown error"),
                })
                logger.error("Failed to get SMART data for %s: %s",
                            result["device"], result.get("error", "Unknown"))

        if use_sample:
            smart_status = "sample"

    # Write placeholder memtester log and sensors CSV
    (artifacts_dir / "memtest.log").write_text(
        "Memtester placeholder\nOK\n", encoding="utf-8"
    )
    (artifacts_dir / "sensors.csv").write_text(
        "timestamp,cpu_temp,fan_rpm\n", encoding="utf-8"
    )

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

    # Exit codes: 0 success, 10 partial/warn, 20 failure
    # For scaffold, treat sample smart as WARN (10)
    if smart_status == "sample":
        logger.warning(
            "Quick run used sample artifacts; reporting partial success (WARN)"
        )
        raise SystemExit(10)


if __name__ == "__main__":
    cli()
