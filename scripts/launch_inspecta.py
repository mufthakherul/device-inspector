#!/usr/bin/env python3
"""Precheck launcher for inspecta.

This launcher:
1. Detects host OS and coarse device type (desktop/laptop/tablet/mobile).
2. Validates runtime readiness (venv, Python packages, optional hardware tools).
3. Executes setup script automatically when requirements are missing.
4. Runs `agent.cli run` with provided flags.

Designed for supported host platforms where setup scripts exist:
- Windows
- Linux
- macOS
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SUPPORTED_HOSTS = {"windows", "linux", "darwin"}

# DMI chassis type references (SMBIOS)
LAPTOP_CHASSIS = {8, 9, 10, 14, 31, 32}
TABLET_CHASSIS = {30}


@dataclass
class HostInfo:
    os_key: str
    os_name: str
    device_type: str


def _run_quiet(cmd: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _detect_windows_device_type() -> str:
    ps = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "(Get-CimInstance Win32_SystemEnclosure | "
            "Select-Object -ExpandProperty ChassisTypes | Select-Object -First 1)"
        ),
    ]
    try:
        result = _run_quiet(ps, timeout=5)
        if result.returncode != 0:
            return "unknown"
        value = (result.stdout or "").strip()
        if not value.isdigit():
            return "unknown"
        chassis = int(value)
        if chassis in LAPTOP_CHASSIS:
            return "laptop"
        if chassis in TABLET_CHASSIS:
            return "tablet"
        return "desktop"
    except Exception:
        return "unknown"


def _detect_linux_device_type() -> str:
    chassis_path = Path("/sys/class/dmi/id/chassis_type")
    try:
        if not chassis_path.exists():
            return "unknown"
        value = chassis_path.read_text(encoding="utf-8").strip()
        if not value.isdigit():
            return "unknown"
        chassis = int(value)
        if chassis in LAPTOP_CHASSIS:
            return "laptop"
        if chassis in TABLET_CHASSIS:
            return "tablet"
        return "desktop"
    except Exception:
        return "unknown"


def _detect_macos_device_type() -> str:
    try:
        result = _run_quiet(["sysctl", "-n", "hw.model"], timeout=5)
        model = (result.stdout or "").strip().lower()
        if "macbook" in model:
            return "laptop"
        if any(k in model for k in ("imac", "macmini", "macpro", "macstudio")):
            return "desktop"
    except Exception:
        pass
    return "unknown"


def detect_host_info() -> HostInfo:
    os_key = platform.system().lower()
    os_name = platform.platform()

    if os_key == "windows":
        device_type = _detect_windows_device_type()
    elif os_key == "linux":
        device_type = _detect_linux_device_type()
    elif os_key == "darwin":
        device_type = _detect_macos_device_type()
    else:
        device_type = "unsupported"

    return HostInfo(os_key=os_key, os_name=os_name, device_type=device_type)


def get_venv_python(project_root: Path, os_key: str) -> Path:
    if os_key == "windows":
        return project_root / "venv" / "Scripts" / "python.exe"
    return project_root / "venv" / "bin" / "python"


def check_core_python_packages(venv_python: Path) -> tuple[bool, str]:
    probe = [str(venv_python), "-c", "import click, jsonschema; print('ok')"]
    try:
        result = _run_quiet(probe, timeout=10)
    except Exception as exc:
        return False, f"Python package probe failed: {exc}"

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        return False, f"Core package imports failed: {stderr or 'unknown error'}"
    return True, "ok"


def required_tools_for_host(os_key: str, require_hardware: bool) -> list[str]:
    if not require_hardware:
        return []
    if os_key == "windows":
        return ["smartctl"]
    if os_key == "linux":
        return ["smartctl", "dmidecode"]
    if os_key == "darwin":
        return ["smartctl"]
    return []


def check_readiness(
    project_root: Path,
    host: HostInfo,
    require_hardware: bool,
) -> tuple[bool, list[str]]:
    problems: list[str] = []

    venv_python = get_venv_python(project_root, host.os_key)
    if not venv_python.exists():
        problems.append(f"Missing virtual environment interpreter: {venv_python}")
        return False, problems

    ok, message = check_core_python_packages(venv_python)
    if not ok:
        problems.append(message)

    for tool in required_tools_for_host(host.os_key, require_hardware):
        if shutil.which(tool) is None:
            problems.append(f"Missing required hardware tool: {tool}")

    return len(problems) == 0, problems


def build_setup_command(
    project_root: Path,
    host: HostInfo,
    mode: str,
    skip_tests: bool,
    install_tools: bool,
) -> list[str]:
    if host.os_key == "windows":
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(project_root / "setup.ps1"),
            "-Mode",
            mode,
        ]
        if skip_tests:
            cmd.append("-SkipTests")
        if install_tools:
            cmd.append("-InstallTools")
        return cmd

    cmd = ["bash", str(project_root / "setup.sh"), "--mode", mode]
    if skip_tests:
        cmd.append("--skip-tests")
    if install_tools:
        cmd.append("--install-tools")
    return cmd


def run_setup(
    project_root: Path,
    host: HostInfo,
    mode: str,
    skip_tests: bool,
    install_tools: bool,
) -> int:
    cmd = build_setup_command(
        project_root=project_root,
        host=host,
        mode=mode,
        skip_tests=skip_tests,
        install_tools=install_tools,
    )
    print(f"[launcher] Running setup: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root, check=False)
    return int(result.returncode)


def run_inspecta(
    project_root: Path,
    host: HostInfo,
    output_dir: Path,
    require_hardware: bool,
    extra_args: list[str],
) -> int:
    venv_python = get_venv_python(project_root, host.os_key)

    cmd = [
        str(venv_python),
        "-m",
        "agent.cli",
        "run",
        "--mode",
        "quick",
        "--output",
        str(output_dir),
        "--no-auto-open",
    ]

    if require_hardware:
        cmd.append("--require-hardware")
    cmd.extend(extra_args)

    print(f"[launcher] Starting inspecta: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root, check=False)
    return int(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspecta launcher with precheck + auto-setup",
    )
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Setup mode when auto-setup is needed.",
    )
    parser.add_argument(
        "--require-hardware",
        action="store_true",
        help="Enforce real-device run behavior and required host tools.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Pass skip-tests to setup when auto-setup runs.",
    )
    parser.add_argument(
        "--install-tools",
        action="store_true",
        help="Install optional/required host tools during setup when available.",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Run precheck/setup only; do not launch inspecta run command.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory for inspecta run. Defaults to reports/auto-<timestamp>.",
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Extra arguments forwarded to `agent.cli run`.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]

    host = detect_host_info()
    print(f"[launcher] Host OS: {host.os_name}")
    print(f"[launcher] Device type: {host.device_type}")

    if host.os_key not in SUPPORTED_HOSTS:
        print(
            "[launcher] Unsupported host for automated setup/run: "
            f"{host.os_key}. Supported hosts: windows, linux, macOS."
        )
        print(
            "[launcher] Mobile/embedded platforms (Android, iOS, HarmonyOS, "
            "Amazon Fire OS, etc.) require dedicated runtime packaging lanes."
        )
        return 2

    ready, problems = check_readiness(
        project_root=project_root,
        host=host,
        require_hardware=args.require_hardware,
    )
    if not ready:
        print("[launcher] Precheck found missing requirements:")
        for item in problems:
            print(f"  - {item}")

        setup_rc = run_setup(
            project_root=project_root,
            host=host,
            mode=args.mode,
            skip_tests=args.skip_tests,
            install_tools=(args.install_tools or args.require_hardware),
        )
        if setup_rc != 0:
            print(f"[launcher] Setup failed with exit code {setup_rc}")
            return setup_rc

        ready_after, problems_after = check_readiness(
            project_root=project_root,
            host=host,
            require_hardware=args.require_hardware,
        )
        if not ready_after:
            print("[launcher] Environment still not ready after setup:")
            for item in problems_after:
                print(f"  - {item}")
            return 3

    print("[launcher] Environment precheck passed.")

    if args.setup_only:
        print("[launcher] setup-only requested; exiting.")
        return 0

    if args.output:
        output_dir = Path(args.output)
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = project_root / "reports" / f"auto-{stamp}"

    output_dir.parent.mkdir(parents=True, exist_ok=True)

    extra_args = list(args.extra_args)
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    rc = run_inspecta(
        project_root=project_root,
        host=host,
        output_dir=output_dir,
        require_hardware=args.require_hardware,
        extra_args=extra_args,
    )
    print(f"[launcher] inspecta exit code: {rc}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
