# Building Standalone Executables for Inspecta

This guide explains how to build standalone executable packages of Inspecta for Windows, macOS, and Linux that users can run without installing Python or dependencies.

## Overview

Inspecta uses PyInstaller to create standalone executables. The build process:
1. Bundles Python interpreter with the application
2. Includes all dependencies (click, jsonschema, etc.)
3. Packages sample data for testing
4. Creates launcher scripts for easy execution
5. Generates a zip file ready for distribution

## Prerequisites

### All Platforms
- Python 3.11 or later
- Git
- Internet connection (for downloading dependencies)

### Platform-Specific Requirements

**Windows:**
- No additional requirements

**macOS:**
- Xcode Command Line Tools: `xcode-select --install`

**Linux:**
- Build essentials: `sudo apt install build-essential`

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/mufthakherul/device-inspector.git
cd device-inspector
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-build.txt
pip install -e .
```

### 2. Build for Your Platform

```bash
python scripts/build_release.py
```

This will:
- Auto-detect your platform
- Build the executable
- Create a distribution package
- Generate a zip file in `dist/`

The output will be something like:
- `dist/inspecta-0.1.0-windows.zip` (Windows)
- `dist/inspecta-0.1.0-macos.zip` (macOS)
- `dist/inspecta-0.1.0-linux.zip` (Linux)

### 3. Test the Build

Extract the zip file and run:

**Windows:**
```cmd
# Extract inspecta-0.1.0-windows.zip
cd inspecta-0.1.0-windows
Run_Inspecta.bat
```

**macOS/Linux:**
```bash
# Extract inspecta-0.1.0-macos.zip
cd inspecta-0.1.0-macos
./run_inspecta.sh
```

## Advanced Build Options

### Build for Specific Platform

```bash
python scripts/build_release.py --platform windows
python scripts/build_release.py --platform macos
python scripts/build_release.py --platform linux
```

### Skip Zip Creation

```bash
python scripts/build_release.py --no-zip
```

This creates the package directory but doesn't zip it (useful for testing).

### Preserve Previous Build

```bash
python scripts/build_release.py --no-clean
```

This doesn't clean previous build artifacts before building (faster for iteration).

## Build Output Structure

After building, you'll have:

```
dist/
├── inspecta-0.1.0-windows/
│   ├── inspecta.exe              # Main executable
│   ├── Run_Inspecta.bat          # Launcher for sample data
│   ├── Run_Hardware_Inspection.bat  # Launcher for real hardware
│   ├── README.md                 # Full documentation
│   ├── LICENSE.txt               # License file
│   ├── QUICK_START.txt          # Quick start guide
│   └── samples/                  # Sample data for testing
└── inspecta-0.1.0-windows.zip   # Distribution package
```

## Automated Builds with GitHub Actions

The repository includes GitHub Actions workflows for automated builds.

### Manual Workflow Dispatch

1. Go to GitHub → Actions → "Build Release Packages"
2. Click "Run workflow"
3. Enter version number (e.g., 0.1.0)
4. Click "Run workflow"

Artifacts will be available in the workflow run.

### Release Builds

When you push a git tag, builds are automatically created:

```bash
git tag v0.1.0
git push origin v0.1.0
```

This will:
- Build for Windows, macOS, and Linux
- Create a GitHub Release
- Attach zip files to the release

## Troubleshooting

### PyInstaller "Module not found" errors

Add missing modules to `hiddenimports` in `inspecta.spec`:

```python
hiddenimports=[
    'agent.plugins.new_module',  # Add your module here
],
```

### Large Executable Size

The executable includes Python interpreter and all dependencies. Typical sizes:
- Windows: 15-25 MB
- macOS: 15-25 MB
- Linux: 15-20 MB

To reduce size:
- Exclude unused dependencies in `inspecta.spec`
- Use UPX compression (enabled by default)

### Antivirus False Positives (Windows)

PyInstaller executables may trigger antivirus warnings. This is a known issue.

**Solutions:**
1. Build and test locally before distribution
2. Submit executables to antivirus vendors for whitelisting
3. Sign the executable with a code signing certificate (recommended for production)

### macOS "App is damaged" or Gatekeeper warnings

Users may see security warnings on macOS.

**For users:**
```bash
xattr -d com.apple.quarantine inspecta
```

**For developers:**
Sign the app with an Apple Developer certificate (requires paid account).

### Linux Missing Libraries

On some Linux distributions, users may need to install system libraries:

```bash
sudo apt install libffi-dev libssl-dev
```

Consider building on older Ubuntu versions for better compatibility.

## Cross-Platform Building

PyInstaller creates executables for the platform it runs on. To build for multiple platforms:

1. **Use GitHub Actions** (recommended) - automatically builds for all platforms
2. **Use VMs or containers** - build on each platform separately
3. **Use CI services** - Travis CI, AppVeyor, etc.

You **cannot** cross-compile (e.g., build Windows executable on macOS).

## Code Signing (Production)

For production releases, sign your executables:

### Windows
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com inspecta.exe
```

### macOS
```bash
codesign --sign "Developer ID Application: Your Name" inspecta.app
```

Code signing:
- Prevents security warnings
- Builds user trust
- Required for macOS notarization

## Distribution Checklist

Before distributing a release:

- [ ] Build succeeds on all platforms
- [ ] Test with sample data on each platform
- [ ] Test on real hardware (if available)
- [ ] Check executable size is reasonable
- [ ] Verify all documentation is included
- [ ] Test launcher scripts work correctly
- [ ] Run antivirus scan on Windows build
- [ ] Update version number in all files
- [ ] Update CHANGELOG.md
- [ ] Create git tag
- [ ] Upload to GitHub Releases
- [ ] Announce release

## Updating the Build Configuration

Key files for build configuration:

- `inspecta.spec` - PyInstaller configuration
- `scripts/build_release.py` - Build script
- `.github/workflows/build-release.yml` - CI/CD workflow
- `requirements-build.txt` - Build dependencies

When adding new dependencies or files:
1. Update `inspecta.spec` if adding data files or hidden imports
2. Test local build
3. Test CI build
4. Update documentation

## Performance Optimization

PyInstaller executables are slightly slower to start than native Python scripts due to unpacking. For better performance:

1. **Use one-file mode** (default in our spec) - slower start but easier distribution
2. **Use one-folder mode** - faster start but multiple files to distribute
3. **Optimize imports** - only import what you need

To switch to one-folder mode, modify `inspecta.spec`:

```python
exe = EXE(
    pyz,
    a.scripts,
    # Remove these lines:
    # a.binaries,
    # a.zipfiles,
    # a.datas,
    # ...
    # And create separate COLLECT:
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='inspecta',
)
```

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Packaging Guide](https://packaging.python.org/)

## Support

For build issues:
1. Check this documentation
2. Check PyInstaller logs in `build/` directory
3. Open an issue on GitHub
4. Ask in discussions

---

**Last Updated:** 2025-10-30  
**Version:** 0.1.0
