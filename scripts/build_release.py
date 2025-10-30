#!/usr/bin/env python3
"""
Build script for creating standalone release packages of inspecta.

This script:
1. Builds the executable using PyInstaller
2. Creates a distribution package with documentation and samples
3. Creates a zip file ready for distribution

Usage:
    python scripts/build_release.py [--platform PLATFORM]

    PLATFORM: windows, macos, or auto-detect
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_platform():
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        subprocess.run(
            ["pyinstaller", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def build_executable(root_dir: Path, clean: bool = True):
    """Build the executable using PyInstaller."""
    print("=" * 60)
    print("Building executable with PyInstaller...")
    print("=" * 60)

    spec_file = root_dir / "inspecta.spec"
    if not spec_file.exists():
        print(f"Error: {spec_file} not found!")
        return False

    cmd = ["pyinstaller"]
    if clean:
        cmd.append("--clean")
    cmd.append(str(spec_file))

    try:
        subprocess.run(cmd, cwd=root_dir, check=True)
        print("\n[OK] Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        return False


def create_distribution_package(root_dir: Path, platform_name: str):
    """Create a distribution package with all necessary files."""
    print("\n" + "=" * 60)
    print("Creating distribution package...")
    print("=" * 60)

    dist_dir = root_dir / "dist"
    if not dist_dir.exists():
        print(f"Error: dist directory not found at {dist_dir}")
        return None

    # Find the executable
    if platform_name == "windows":
        exe_name = "inspecta.exe"
    elif platform_name == "macos":
        exe_name = "inspecta"  # Or inspecta.app for bundle
    else:
        exe_name = "inspecta"

    exe_path = dist_dir / exe_name
    if not exe_path.exists() and platform_name == "macos":
        # Check for .app bundle
        exe_path = dist_dir / "inspecta.app"

    if not exe_path.exists():
        print(f"Error: Executable not found at {exe_path}")
        return None

    # Create package directory
    version = "0.1.0"
    package_name = f"inspecta-{version}-{platform_name}"
    package_dir = dist_dir / package_name

    # Clean existing package directory
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    print(f"\nPackaging to: {package_dir}")

    # Copy executable
    print(f"  - Copying executable: {exe_name}")
    if exe_path.is_dir():
        shutil.copytree(exe_path, package_dir / exe_name)
    else:
        shutil.copy2(exe_path, package_dir / exe_name)

    # Copy documentation
    print("  - Copying documentation")

    # Use distribution-specific README for the package
    dist_readme = root_dir / "DISTRIBUTION_README.md"
    if dist_readme.exists():
        shutil.copy2(dist_readme, package_dir / "README.md")

    # Copy other documentation
    for doc in ["LICENSE.txt", "CHANGELOG.md"]:
        src = root_dir / doc
        if src.exists():
            shutil.copy2(src, package_dir / doc)

    # Copy samples for testing
    print("  - Copying sample data")
    samples_src = root_dir / "samples"
    samples_dst = package_dir / "samples"
    if samples_src.exists():
        shutil.copytree(samples_src, samples_dst)

    # Create launcher scripts
    print("  - Creating launcher scripts")
    create_launcher_scripts(package_dir, platform_name)

    # Create quick start guide
    print("  - Creating quick start guide")
    create_quick_start_guide(package_dir, platform_name)

    return package_dir


def create_launcher_scripts(package_dir: Path, platform_name: str):
    """Create easy-to-use launcher scripts for users."""

    if platform_name == "windows":
        # Create Windows batch file
        launcher = package_dir / "Run_Inspecta.bat"
        launcher_content = """@echo off
REM Inspecta Device Inspector Launcher
REM Double-click this file to run the tool

echo ============================================================
echo Inspecta Device Inspector v0.1.0
echo ============================================================
echo.

REM Check for admin rights (required for hardware access)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
    echo.
) else (
    echo WARNING: Not running as administrator!
    echo For full hardware inspection, right-click this file and
    echo select "Run as administrator"
    echo.
    echo Press any key to continue with limited functionality...
    pause
    echo.
)

REM Run with sample data (no admin required)
echo Running inspecta with sample data...
echo.
"%~dp0inspecta.exe" run --mode quick --output reports --use-sample --verbose

echo.
echo ============================================================
echo Inspection complete!
echo Report saved to: reports/report.json
echo.
echo To run on real hardware, run as administrator and remove
echo the --use-sample flag from this script.
echo ============================================================
echo.
pause
"""
        launcher.write_text(launcher_content, encoding="utf-8")

        # Create direct executable launcher
        real_launcher = package_dir / "Run_Hardware_Inspection.bat"
        real_content = """@echo off
REM Inspecta Hardware Inspector - Requires Administrator
REM Right-click and select "Run as administrator"

echo ============================================================
echo Inspecta Device Inspector - Hardware Inspection
echo ============================================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
    echo.
) else (
    echo ERROR: Administrator privileges required!
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Inspecting hardware...
echo This may take 2-10 minutes depending on your system.
echo.

"%~dp0inspecta.exe" run --mode quick --output reports --verbose

echo.
echo ============================================================
echo Inspection complete!
echo Report saved to: reports/report.json
echo ============================================================
echo.
pause
"""
        real_launcher.write_text(real_content, encoding="utf-8")

    elif platform_name in ["macos", "linux"]:
        # Create shell script launcher
        launcher = package_dir / "run_inspecta.sh"
        launcher_content = """#!/bin/bash
# Inspecta Device Inspector Launcher

echo "============================================================"
echo "Inspecta Device Inspector v0.1.0"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "WARNING: Not running as root!"
    echo "For full hardware inspection, run with sudo:"
    echo "  sudo ./run_inspecta.sh"
    echo ""
    echo "Running with sample data (no root required)..."
    echo ""
    ./inspecta run --mode quick --output reports --use-sample --verbose
else
    echo "Running with root privileges..."
    echo "Inspecting hardware... This may take 2-10 minutes."
    echo ""
    ./inspecta run --mode quick --output reports --verbose
fi

echo ""
echo "============================================================"
echo "Inspection complete!"
echo "Report saved to: reports/report.json"
echo "============================================================"
"""
        launcher.write_text(launcher_content, encoding="utf-8")
        launcher.chmod(0o755)  # Make executable


def create_quick_start_guide(package_dir: Path, platform_name: str):
    """Create a quick start guide for users."""

    if platform_name == "windows":
        guide_content = """# Inspecta Device Inspector - Quick Start Guide (Windows)

## What is Inspecta?

Inspecta is a local-first device inspection tool that helps you evaluate the condition of used laptops and PCs before purchase. It checks hardware health, storage devices, and generates a detailed report.

## Quick Start (No Installation Required!)

### Option 1: Test with Sample Data (Recommended First Try)
1. Double-click `Run_Inspecta.bat`
2. Wait for the inspection to complete
3. Check the `reports` folder for your report

This runs without administrator privileges and uses sample data to show you how the tool works.

### Option 2: Inspect Real Hardware
1. Right-click `Run_Hardware_Inspection.bat`
2. Select "Run as administrator"
3. Wait for the inspection to complete (2-10 minutes)
4. Check the `reports` folder for your report

**Note:** Administrator privileges are required to access hardware information (SMART data, BIOS info, etc.)

## Command Line Usage

For advanced users, you can run inspecta from Command Prompt:

```cmd
REM Show help
inspecta.exe --help

REM Run inspection with sample data
inspecta.exe run --mode quick --output ./my-report --use-sample

REM Run real hardware inspection (requires admin)
inspecta.exe run --mode quick --output ./my-report --verbose

REM Check device inventory only
inspecta.exe inventory --use-sample
```

## Output Files

After running, you'll find:
- `reports/report.json` - Complete inspection report with scores
- `reports/artifacts/agent.log` - Detailed execution log
- `reports/artifacts/smart_*.json` - SMART data from storage devices

## Troubleshooting

**"Access Denied" or permission errors:**
- Run as administrator (right-click → Run as administrator)
- Or use `--use-sample` flag for testing without admin rights

**"No storage devices found":**
- Make sure you're running as administrator
- Check that smartmontools is accessible (included in standalone builds)

**Need Help?**
- Read the full README.md
- Visit: https://github.com/mufthakherul/device-inspector
- Report issues: https://github.com/mufthakherul/device-inspector/issues

## System Requirements

- Windows 10 or later (64-bit)
- 100MB free disk space
- No additional software installation required!

## Privacy Note

Inspecta is local-first by default. All reports stay on your computer unless you explicitly choose to share them. No data is sent to any server.

## License

This software is provided for non-commercial use. See LICENSE.txt for details.

---

© 2025 mufthakherul
Version 0.1.0
"""
    else:  # macOS/Linux
        guide_content = """# Inspecta Device Inspector - Quick Start Guide (macOS/Linux)

## What is Inspecta?

Inspecta is a local-first device inspection tool that helps you evaluate the condition of used laptops and PCs before purchase. It checks hardware health, storage devices, and generates a detailed report.

## Quick Start (No Installation Required!)

### Option 1: Test with Sample Data (Recommended First Try)
```bash
./run_inspecta.sh
```

This runs without root privileges and uses sample data to show you how the tool works.

### Option 2: Inspect Real Hardware
```bash
sudo ./run_inspecta.sh
```

**Note:** Root privileges are required to access hardware information (SMART data, BIOS info, etc.)

## Command Line Usage

For advanced users:

```bash
# Show help
./inspecta --help

# Run inspection with sample data
./inspecta run --mode quick --output ./my-report --use-sample

# Run real hardware inspection (requires sudo)
sudo ./inspecta run --mode quick --output ./my-report --verbose

# Check device inventory only
sudo ./inspecta inventory
```

## macOS Security Note

On macOS, you may need to allow the application to run:
1. Go to System Preferences → Security & Privacy
2. Click "Open Anyway" if prompted
3. Or run: `xattr -d com.apple.quarantine inspecta`

## Output Files

After running, you'll find:
- `reports/report.json` - Complete inspection report with scores
- `reports/artifacts/agent.log` - Detailed execution log
- `reports/artifacts/smart_*.json` - SMART data from storage devices

## Troubleshooting

**"Permission denied" errors:**
- Run with sudo: `sudo ./run_inspecta.sh`
- Or use `--use-sample` flag for testing without root

**"No storage devices found":**
- Make sure you're running with sudo
- On Linux: Install smartmontools if not available
- On macOS: May need to approve disk access in Security settings

**macOS: "Cannot be opened because it is from an unidentified developer":**
- Go to System Preferences → Security & Privacy → General
- Click "Open Anyway"
- Or remove quarantine: `xattr -d com.apple.quarantine inspecta`

**Need Help?**
- Read the full README.md
- Visit: https://github.com/mufthakherul/device-inspector
- Report issues: https://github.com/mufthakherul/device-inspector/issues

## System Requirements

- macOS 10.15+ or Linux (Ubuntu 20.04+)
- 100MB free disk space
- For full functionality: smartmontools, dmidecode (usually pre-installed or available)

## Privacy Note

Inspecta is local-first by default. All reports stay on your computer unless you explicitly choose to share them. No data is sent to any server.

## License

This software is provided for non-commercial use. See LICENSE.txt for details.

---

© 2025 mufthakherul
Version 0.1.0
"""

    guide_path = package_dir / "QUICK_START.txt"
    guide_path.write_text(guide_content, encoding="utf-8")


def create_zip_package(package_dir: Path):
    """Create a zip file from the package directory."""
    print("\n" + "=" * 60)
    print("Creating zip package...")
    print("=" * 60)

    zip_name = package_dir.name
    zip_path = package_dir.parent / f"{zip_name}.zip"

    # Remove existing zip
    if zip_path.exists():
        zip_path.unlink()

    # Create zip
    print(f"\nCreating: {zip_path.name}")
    shutil.make_archive(str(package_dir), "zip", package_dir.parent, package_dir.name)

    # Get size
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Package created: {zip_path}")
    print(f"  Size: {size_mb:.2f} MB")

    return zip_path


def main():
    parser = argparse.ArgumentParser(
        description="Build standalone release package for inspecta"
    )
    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "auto"],
        default="auto",
        help="Target platform (default: auto-detect)",
    )
    parser.add_argument(
        "--no-clean", action="store_true", help="Don't clean previous build artifacts"
    )
    parser.add_argument(
        "--no-zip", action="store_true", help="Don't create zip package"
    )

    args = parser.parse_args()

    # Detect platform
    if args.platform == "auto":
        platform_name = get_platform()
    else:
        platform_name = args.platform

    print("=" * 60)
    print("Inspecta Release Builder")
    print("=" * 60)
    print(f"Platform: {platform_name}")
    print(f"Clean build: {not args.no_clean}")
    print("=" * 60)

    # Check dependencies
    if not check_pyinstaller():
        print("\n[ERROR] PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        return 1

    # Get root directory
    root_dir = Path(__file__).parent.parent

    # Build executable
    if not build_executable(root_dir, clean=not args.no_clean):
        return 1

    # Create distribution package
    package_dir = create_distribution_package(root_dir, platform_name)
    if not package_dir:
        return 1

    # Create zip
    if not args.no_zip:
        zip_path = create_zip_package(package_dir)
        if not zip_path:
            return 1

        print("\n" + "=" * 60)
        print("[SUCCESS] BUILD COMPLETE!")
        print("=" * 60)
        print(f"\nRelease package: {zip_path}")
        print(f"Distribution folder: {package_dir}")
        print("\nYou can now distribute the zip file to users.")
        print("Users can extract and run without installing anything!")
    else:
        print("\n" + "=" * 60)
        print("[SUCCESS] BUILD COMPLETE!")
        print("=" * 60)
        print(f"\nDistribution folder: {package_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
