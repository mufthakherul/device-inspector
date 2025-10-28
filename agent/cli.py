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

    # Try to use smartctl wrapper to parse a system file; fallback to sample
    sample_smart = (
        Path(__file__).parent.parent / "samples" / "artifacts" / "smart_nvme0.json"
    )
    if sample_smart.exists():
        with open(sample_smart, "r", encoding="utf-8") as fh:
            smart_json = json.load(fh)
        parsed = smart.parse_smart_json(smart_json)
        # write artifact copy
        (artifacts_dir / "smart_nvme0.json").write_text(
            json.dumps(smart_json, indent=2), encoding="utf-8"
        )
        smart_status = "sample"
    else:
        parsed = {"note": "smartctl not available; sample not found"}
        smart_status = "missing"

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
        smart=parsed,
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
