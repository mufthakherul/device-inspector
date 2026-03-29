#!/usr/bin/env python3
"""
Cross-platform setup script for device-inspector (inspecta) project.

Supports: Windows, Linux, macOS, and other Unix-like systems.
Handles Python installation, virtual environment, dependencies, and optional tools.

Usage:
    python setup.py                    # Full setup with all defaults
    python setup.py --dev              # Development setup (includes tools)
    python setup.py --prod             # Production setup (minimal)
    python setup.py --install-tools    # Install optional platform tools
    python setup.py --help             # Show all options
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


class SetupManager:
    """Manages cross-platform project setup."""

    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.system = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)
        self.venv_path = project_root / "venv"
        self.python_exe = self._detect_python_exe()

    def log(self, msg: str, level: str = "INFO"):
        """Print formatted log messages."""
        levels = {"DEBUG": "▪", "INFO": "•", "WARN": "⚠", "ERROR": "✗", "SUCCESS": "✓"}
        icon = levels.get(level, "•")
        print(f"  {icon}  {msg}")

    def log_section(self, title: str):
        """Print section header."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")

    def _detect_python_exe(self) -> Optional[str]:
        """Detect available Python executable."""
        candidates = ["python3", "python"]
        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, "--version"], capture_output=True, timeout=5, text=True
                )
                if result.returncode == 0:
                    self.log(f"Found Python: {result.stdout.strip()}", "SUCCESS")
                    return cmd
            except FileNotFoundError:
                continue
        return None

    def check_python_version(self) -> bool:
        """Verify Python 3.11+ is available."""
        self.log_section("Checking Python Version")

        if not self.python_exe:
            self.log("Python 3.11+ not found on PATH", "ERROR")
            self._suggest_python_install()
            return False

        version_cmd = (
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        )
        result = subprocess.run(
            [self.python_exe, "-c", version_cmd],
            capture_output=True,
            text=True,
        )

        version = result.stdout.strip()
        major, minor = map(int, version.split("."))

        if major < 3 or (major == 3 and minor < 11):
            self.log(f"Python {version} found, but 3.11+ required", "ERROR")
            self._suggest_python_install()
            return False

        self.log(f"Python {version} ✓", "SUCCESS")
        return True

    def _suggest_python_install(self):
        """Show platform-specific Python installation instructions."""
        self.log_section("Python Installation Required")

        if self.system == "Windows":
            self.log("1. Visit: https://www.python.org/downloads/", "INFO")
            self.log("2. Download Python 3.12 or 3.11 (Windows installer)", "INFO")
            self.log("3. Run installer and CHECK 'Add Python to PATH'", "INFO")
            self.log("4. Or use: winget install Python.Python.3.12", "INFO")
        elif self.system == "Darwin":  # macOS
            self.log("1. Using Homebrew: brew install python@3.12", "INFO")
            self.log("2. Or visit: https://www.python.org/downloads/macos/", "INFO")
            self.log("3. Download and run macOS installer", "INFO")
        else:  # Linux
            msg = (
                "1. Ubuntu/Debian: sudo apt update && "
                "sudo apt install python3.12 python3.12-venv"
            )
            self.log(msg, "INFO")
            self.log(
                "2. Fedora/RHEL: sudo dnf install python3.12 python3.12-venv", "INFO"
            )
            self.log("3. Arch: sudo pacman -S python", "INFO")

    def create_venv(self) -> bool:
        """Create Python virtual environment."""
        self.log_section("Setting Up Virtual Environment")

        if self.venv_path.exists():
            self.log(f"venv already exists at {self.venv_path}", "INFO")
            return True

        try:
            self.log(f"Creating venv at {self.venv_path}...", "INFO")
            subprocess.run(
                [self.python_exe, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=not self.verbose,
            )
            self.log("Virtual environment created ✓", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to create venv: {e}", "ERROR")
            return False

    def get_venv_python(self) -> str:
        """Get path to venv Python executable."""
        if self.system == "Windows":
            return str(self.venv_path / "Scripts" / "python.exe")
        else:
            return str(self.venv_path / "bin" / "python")

    def get_venv_pip(self) -> str:
        """Get path to venv pip executable."""
        if self.system == "Windows":
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:
            return str(self.venv_path / "bin" / "pip")

    def install_dependencies(self, mode: str = "dev") -> bool:
        """Install Python dependencies."""
        self.log_section("Installing Python Dependencies")

        venv_pip = self.get_venv_pip()
        requirements_files = ["requirements.txt"]

        if mode == "dev":
            requirements_files.append("requirements-optional.txt")

        try:
            # Upgrade pip
            self.log("Upgrading pip...", "INFO")
            subprocess.run(
                [venv_pip, "install", "--upgrade", "pip"],
                check=True,
                capture_output=not self.verbose,
            )

            # Install requirements
            for req_file in requirements_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    self.log(f"Installing {req_file}...", "INFO")
                    subprocess.run(
                        [venv_pip, "install", "-r", str(req_path)],
                        check=True,
                        capture_output=not self.verbose,
                    )
                else:
                    self.log(f"Skipping {req_file} (not found)", "WARN")

            # Install project in editable mode
            self.log("Installing project in editable mode...", "INFO")
            subprocess.run(
                [venv_pip, "install", "-e", str(self.project_root)],
                check=True,
                capture_output=not self.verbose,
            )

            self.log("Dependencies installed ✓", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to install dependencies: {e}", "ERROR")
            return False

    def run_code_checks(self) -> bool:
        """Run formatting and linting checks."""
        self.log_section("Running Code Quality Checks")

        venv_python = self.get_venv_python()

        checks = [
            ("Black format check", [venv_python, "-m", "black", "--check", "."]),
            ("Ruff lint check", [venv_python, "-m", "ruff", "check", "."]),
        ]

        for check_name, cmd in checks:
            try:
                self.log(f"Running {check_name}...", "INFO")
                subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                )
                self.log(f"{check_name} ✓", "SUCCESS")
            except Exception as e:
                self.log(f"{check_name} failed: {e}", "WARN")

        return True

    def run_tests(self, verbose: bool = False) -> bool:
        """Run test suite."""
        self.log_section("Running Test Suite")

        venv_python = self.get_venv_python()
        cmd = [venv_python, "-m", "pytest", "-v", "--tb=short"]

        if not verbose:
            cmd.insert(3, "-q")

        try:
            result = subprocess.run(
                cmd, cwd=str(self.project_root), capture_output=False, text=True
            )

            if result.returncode == 0:
                self.log("All tests passed ✓", "SUCCESS")
                return True
            else:
                self.log(f"Some tests failed (exit code: {result.returncode})", "WARN")
                return False
        except Exception as e:
            self.log(f"Failed to run tests: {e}", "ERROR")
            return False

    def smoke_test_cli(self) -> bool:
        """Quick smoke test of CLI with sample data."""
        self.log_section("Running CLI Smoke Test")

        venv_python = self.get_venv_python()
        output_dir = self.project_root / "test-smoke"

        try:
            self.log("Running: inspecta run --mode quick --use-sample", "INFO")
            subprocess.run(
                [
                    venv_python,
                    "-m",
                    "agent.cli",
                    "run",
                    "--mode",
                    "quick",
                    "--output",
                    str(output_dir),
                    "--use-sample",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check if report was generated
            report_path = output_dir / "report.json"
            if report_path.exists():
                self.log("CLI smoke test passed ✓", "SUCCESS")
                self.log(f"Report generated: {report_path}", "INFO")
                return True
            else:
                self.log("CLI executed but no report generated", "WARN")
                return False
        except subprocess.TimeoutExpired:
            self.log("CLI smoke test timed out", "WARN")
            return False
        except Exception as e:
            self.log(f"CLI smoke test failed: {e}", "ERROR")
            return False

    def install_system_tools(self) -> bool:
        """Install optional system tools for hardware diagnostics."""
        self.log_section("Installing System Tools (Optional)")

        if self.system == "Windows":
            self._install_tools_windows()
        elif self.system == "Darwin":
            self._install_tools_macos()
        elif self.system == "Linux":
            self._install_tools_linux()
        else:
            self.log(f"Platform {self.system} not fully supported", "WARN")
            return False

        return True

    def _install_tools_windows(self):
        """Windows tool installation (requires admin)."""
        self.log("Windows detected - optional tools:", "INFO")
        self.log("SmartMonTools: winget install -e --id Argonaut.SmartMonTools", "INFO")
        url = "https://www.smartmontools.org/wiki/Download"
        self.log(f"Or download from: {url}", "INFO")

    def _install_tools_macos(self):
        """macOS tool installation (requires Homebrew)."""
        self.log("macOS detected - installing optional tools via Homebrew...", "INFO")

        tools = ["smartmontools"]
        for tool in tools:
            try:
                self.log(f"Checking {tool}...", "INFO")
                result = subprocess.run(
                    ["brew", "install", tool], capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.log(f"{tool} installed ✓", "SUCCESS")
                else:
                    self.log(f"Failed to install {tool}", "WARN")
            except FileNotFoundError:
                self.log("Homebrew not found. Install from: https://brew.sh/", "WARN")
                break

    def _install_tools_linux(self):
        """Linux tool installation (requires sudo)."""
        self.log("Linux detected - optional tools installation requires sudo", "INFO")

        # Detect package manager
        if shutil.which("apt-get"):
            tools = ["smartmontools", "dmidecode", "lm-sensors"]
            cmd = "sudo apt-get update && sudo apt-get install -y"
            cmd += " " + " ".join(tools)
        elif shutil.which("dnf"):
            tools = ["smartmontools", "dmidecode", "lm_sensors"]
            cmd = "sudo dnf install -y " + " ".join(tools)
        elif shutil.which("pacman"):
            tools = ["smartmontools", "dmidecode", "lm_sensors"]
            cmd = "sudo pacman -S --noconfirm " + " ".join(tools)
        else:
            self.log("No supported package manager found", "WARN")
            return

        self.log(f"To install tools, run: {cmd}", "INFO")

    def print_next_steps(self, mode: str = "dev"):
        """Print next steps and useful commands."""
        self.log_section("Setup Complete!")

        venv_activate = (
            ".\\venv\\Scripts\\activate"
            if self.system == "Windows"
            else "source venv/bin/activate"
        )

        venv_python = self.get_venv_python()

        print(f"""
Next Steps:

1. Activate Virtual Environment:
   {venv_activate}

2. Run inspecta with sample data (no root needed):
   {venv_python} -m agent.cli run --mode quick --output ./reports/test --use-sample

3. Run real hardware inspection (requires root/admin):
   sudo {venv_python} -m agent.cli run --mode quick --output ./reports/mydevice

4. Check device inventory:
   {venv_python} -m agent.cli inventory --use-sample

5. View documentation:
   - Developer Guide: docs/DEV_SETUP.md
   - Architecture: docs/ARCHITECTURE.md
   - Contributing: CONTRIBUTING.md

6. Running tests:
   {venv_python} -m pytest -v

7. Code formatting:
   {venv_python} -m black .
   {venv_python} -m ruff check --fix .

For more details, see: README.md
Repository: https://github.com/mufthakherul/device-inspector
""")

    def run_setup(
        self,
        mode: str = "dev",
        skip_tests: bool = False,
        skip_tools: bool = True,
    ):
        """Execute full setup workflow."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║   DEVICE-INSPECTOR (INSPECTA) SETUP WIZARD                   ║
║   Cross-Platform Project Initialization                      ║
╚══════════════════════════════════════════════════════════════╝
""")

        # Step 1: Check Python
        if not self.check_python_version():
            sys.exit(1)

        # Step 2: Create venv
        if not self.create_venv():
            sys.exit(1)

        # Step 3: Install dependencies
        if not self.install_dependencies(mode=mode):
            sys.exit(1)

        # Step 4: Code checks
        self.run_code_checks()

        # Step 5: Tests
        if not skip_tests:
            self.run_tests(verbose=False)
            self.smoke_test_cli()

        # Step 6: Optional system tools
        if not skip_tools and mode == "dev":
            try:
                self.install_system_tools()
            except Exception as e:
                self.log(f"Optional tool installation skipped: {e}", "WARN")

        # Final summary
        self.print_next_steps(mode=mode)


def main():
    epilog = (
        "Examples:\n"
        "  python setup.py              # Full dev setup\n"
        "  python setup.py --prod       # Production (minimal)"
    )
    parser = argparse.ArgumentParser(
        description="Cross-platform setup for device-inspector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Setup mode: dev=full with tests, prod=minimal (default: dev)",
    )
    parser.add_argument(
        "--skip-tests", action="store_true", help="Skip running test suite"
    )
    parser.add_argument(
        "--install-tools",
        action="store_true",
        help="Install optional system tools (smartmontools, dmidecode, etc.)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    project_root = Path(__file__).parent.resolve()
    manager = SetupManager(project_root, verbose=args.verbose)

    try:
        manager.run_setup(
            mode=args.mode,
            skip_tests=args.skip_tests,
            skip_tools=not args.install_tools,
        )
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
