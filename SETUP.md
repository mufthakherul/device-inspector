# Project Setup & Installation Guide

## Overview

This guide provides complete setup instructions for **device-inspector (inspecta)** across all platforms:
- **Windows** (10, 11, Server)
- **Linux** (Ubuntu, Debian, Fedora, RHEL, Arch, Alpine)
- **macOS** (10.13+)
- **Other Unix-like Systems**

The project includes automated setup scripts for all platforms that handle:
- ✅ Python environment detection/installation
- ✅ Virtual environment creation
- ✅ Dependency installation (production + optional)
- ✅ Optional system tools installation
- ✅ Code quality checks (formatting, linting)
- ✅ Test suite execution
- ✅ CLI smoke testing

---

## Quick Start by Platform

### 🪟 Windows

```powershell
# 1. Open PowerShell
# 2. Navigate to project directory
cd C:\path\to\device-inspector

# 3. Run setup script (full development setup)
.\setup.ps1

# 4. Activate virtual environment when done
.\venv\Scripts\Activate.ps1

# 5. Test the CLI
python -m agent.cli inventory --use-sample
```

**Options:**
```powershell
.\setup.ps1 -Mode prod           # Production setup (minimal)
.\setup.ps1 -InstallTools        # Install optional diagnostics tools
.\setup.ps1 -SkipTests           # Skip test suite
.\setup.ps1 -Help                # Show all options
```

### 🐧 Linux

```bash
# 1. Navigate to project directory
cd /path/to/device-inspector

# 2. Make setup script executable
chmod +x setup.sh

# 3. Run setup script (full development setup)
./setup.sh

# 4. Activate virtual environment when done
source venv/bin/activate

# 5. Test the CLI
python -m agent.cli inventory --use-sample
```

**Options:**
```bash
./setup.sh --mode prod           # Production setup (minimal)
./setup.sh --install-tools       # Install optional diagnostics tools (requires sudo)
./setup.sh --skip-tests          # Skip test suite
./setup.sh --help                # Show all options
```

### 🍎 macOS

```bash
# 1. Open Terminal
# 2. Navigate to project directory
cd /path/to/device-inspector

# 3. Make setup script executable
chmod +x setup.sh

# 4. Run setup script (full development setup)
./setup.sh

# 5. Activate virtual environment when done
source venv/bin/activate

# 6. Test the CLI
python -m agent.cli inventory --use-sample
```

**Options:** Same as Linux (see above)

---

## Detailed Setup Instructions

### Prerequisites

**Minimum Requirements:**
- Python 3.11 or 3.12
- pip (usually included with Python)
- Git (if cloning the repository)
- 2 GB free disk space

**Optional System Tools** (for full hardware diagnostics):
- Linux: `smartmontools`, `dmidecode`, `lm-sensors`, `fio`, `sysbench`, `memtester`
- macOS: `smartmontools` (via Homebrew)
- Windows: SmartMonTools, various WMI-based tools available

### Python Installation

#### Windows

**Option 1: Direct Download**
1. Visit https://www.python.org/downloads/
2. Download Python 3.12 installer (Windows x64)
3. Run installer and **CHECK "Add Python to PATH"**
4. Verify: Open PowerShell and run `python --version`

**Option 2: Windows Package Manager**
```powershell
winget install Python.Python.3.12
```

**Option 3: Chocolatey**
```powershell
choco install python3
```

#### Linux

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

**Fedora/RHEL:**
```bash
sudo dnf install python3.12 python3.12-venv python3.12-devel
```

**Arch:**
```bash
sudo pacman -S python
```

**Alpine:**
```bash
sudo apk add python3 python3-dev
```

#### macOS

**Homebrew:**
```bash
brew install python@3.12
```

**Direct Download:**
1. Visit https://www.python.org/downloads/macos/
2. Download Python 3.12 installer
3. Run installer

---

## Setup Modes

### Development Mode (Default)

```bash
# Includes:
# - Full test suite (pytest, pytest-cov, pytest-mock)
# - Code formatting tools (black, ruff)
# - Security scanners (bandit, safety)
# - PDF report generation (reportlab)

./setup.sh                  # Linux/macOS
.\setup.ps1                 # Windows
```

**Best for:**
- Developers
- Contributors
- Testing
- CI/CD pipelines

### Production Mode

```bash
# Includes:
# - Only core dependencies (click, jsonschema)
# - No test tools, no dev dependencies
# - Minimal disk footprint

./setup.sh --mode prod      # Linux/macOS
.\setup.ps1 -Mode prod      # Windows
```

**Best for:**
- End-users
- Lightweight deployments
- Embedded systems
- Minimal installations

---

## Manual Setup (No Scripts)

If you prefer manual setup or need custom configuration:

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install main dependencies
pip install -r requirements.txt

# Install optional dependencies (for PDF reports, tests, etc.)
pip install -r requirements-optional.txt

# Install project in editable mode
pip install -e .
```

### 3. Run Code Checks (Optional)

```bash
# Format check
python -m black --check .

# Lint check
python -m ruff check .

# Security scan
python -m bandit -r agent/

# Dependency vulnerabilities
python -m safety check
```

### 4. Run Tests (Optional)

```bash
# All tests
pytest -v

# With coverage
pytest --cov=agent --cov-report=html

# Specific test file
pytest tests/test_inventory.py -v
```

### 5. Smoke Test CLI

```bash
# Test with sample data (no root needed)
python -m agent.cli run --mode quick --output ./test-run --use-sample

# Check inventory
python -m agent.cli inventory --use-sample
```

---

## Installing Optional System Tools

### Why Install System Tools?

These tools enable real hardware diagnostics instead of simulated data:
- **smartmontools** - Storage health (SMART) data
- **dmidecode** - Hardware inventory
- **lm-sensors** - Thermal/sensor readings
- **fio** - Disk performance benchmarks
- **sysbench** - CPU benchmarks
- **memtester** - Memory testing

### Linux

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install smartmontools dmidecode lm-sensors fio sysbench memtester
```

**Fedora/RHEL:**
```bash
sudo dnf install smartmontools dmidecode lm_sensors fio sysbench memtester
```

**Arch:**
```bash
sudo pacman -S smartmontools dmidecode lm_sensors fio sysbench memtester
```

**Or use setup script:**
```bash
./setup.sh --install-tools
```

### macOS

**Homebrew:**
```bash
brew install smartmontools
```

### Windows

**SmartMonTools:**
1. Download from https://www.smartmontools.org/wiki/Download
2. Run installer (requires admin)

---

## Virtual Environment Management

### Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### Deactivate

```bash
deactivate
```

### Check Installed Packages

```bash
pip list
```

### Update All Packages

```bash
pip install --upgrade -r requirements.txt
```

---

## Common Setup Issues

### Issue: "Python not found" / Python not on PATH

**Solution:**
- Reinstall Python and **CHECK "Add Python to PATH"** during installation
- Or manually add Python directory to PATH
- Restart terminal/PowerShell after PATH changes

### Issue: "Permission denied" when running smartctl/dmidecode

**Solution:**
- Use `--use-sample` flag to test without hardware access
- For real hardware, prefix with `sudo` (Linux/macOS) or run as admin (Windows)

```bash
# Test without hardware access
python -m agent.cli inventory --use-sample

# Real hardware access (requires root/admin)
sudo python -m agent.cli inventory
```

### Issue: "Module not found" errors in tests

**Solution:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Clear pip cache: `pip cache purge` or delete `.pytest_cache/`

### Issue: PowerShell execution policy prevents script running

**Solution:**

```powershell
# Temporary: Allow scripts for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Then run setup
.\setup.ps1
```

Or run PowerShell as administrator and set permanent policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Tests fail on Windows (battery test failures)

**Expected Behavior:**
- Some battery tests fail on Windows vs Linux due to platform-specific APIs
- This is normal and non-blocking (104/107 tests pass on Windows)
- Use `--skip-tests` to skip if not needed

---

## Development Workflow After Setup

### Activate Environment

```bash
# Windows
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate
```

### Run Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_inventory.py -v

# With coverage
pytest --cov=agent --cov-report=html
```

### Format Code

```bash
# Format all Python files
python -m black .

# Check formatting only
python -m black --check .
```

### Run Linter

```bash
# Check for issues
python -m ruff check .

# Auto-fix issues
python -m ruff check --fix .
```

### Run Security Scans

```bash
# Code security
python -m bandit -r agent/

# Dependency vulnerabilities
python -m safety check
```

### Test CLI During Development

```bash
# With sample data (no privileged access needed)
python -m agent.cli run --mode quick --output ./reports/test --use-sample

# With real hardware (requires root/admin)
sudo python -m agent.cli run --mode quick --output ./reports/device1

# Verbose output for debugging
python -m agent.cli run --mode quick --use-sample --verbose

# Check inventory
python -m agent.cli inventory --use-sample
```

---

## CI/CD Pipeline Setup

### GitHub Actions

Example workflow for automatic testing:

```yaml
name: Setup and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Run setup script
        run: |
          chmod +x setup.sh
          ./setup.sh --skip-tests
      
      - name: Run tests
        run: |
          source venv/bin/activate
          pytest -v
```

---

## Docker Setup (Optional)

For containerized deployment:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    smartmontools \
    dmidecode \
    lm-sensors \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Setup Python environment
RUN python -m venv venv && \
    venv/bin/pip install --upgrade pip && \
    venv/bin/pip install -r requirements.txt && \
    venv/bin/pip install -e .

# Default command
ENTRYPOINT ["venv/bin/python", "-m", "agent.cli"]
CMD ["--help"]
```

Build:
```bash
docker build -t inspecta:latest .
```

Run:
```bash
docker run --rm inspecta run --mode quick --use-sample
```

---

## Platform-Specific Notes

### Windows-Specific

- **UAC/Admin Privs:** Some operations (smartctl, disk checks) require admin
- **Performance:** First run slower due to Windows Defender scanning
- **Path Handling:** Use forward slashes in Python paths or double-backslashes
- **Exit Codes:** Some tests expect exit code 10 for sample data; Windows may report differently

### Linux-Specific

- **Permissions:** Use `sudo` for hardware access (smartctl, dmidecode)
- **Package Managers:** Setup script auto-detects apt/dnf/pacman
- **Live USB:** For full diagnostics, consider booting minimal Linux image
- **SELinux:** May need policy configuration for some tools

### macOS-Specific

- **M1/M2 Macs:** Ensure Python 3.12 installed for native ARM64 (not Rosetta)
- **Homebrew:** Required for optional tools installation
- **Gatekeeper:** First run may require security validation
- **Admin:** Some SMART operations may require root

---

## Uninstallation

### Remove Virtual Environment

```bash
# Windows
rmdir /s venv

# Linux/macOS
rm -rf venv
```

### Remove Project

```bash
# Linux/macOS
rm -rf /path/to/device-inspector

# Windows
rmdir /s C:\path\to\device-inspector
```

---

## Getting Help

- 📖 **Documentation:** See [docs/](../docs/) directory
- 🐛 **Issues:** https://github.com/mufthakherul/inspecta-nexus/issues
- 💬 **Discussions:** https://github.com/mufthakherul/inspecta-nexus/discussions
- 📝 **Contributing:** See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Next Steps

1. ✅ Install Python and run setup script
2. 📖 Read [docs/DEV_SETUP.md](docs/DEV_SETUP.md) for development workflow
3. 🏗️ Review [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for codebase structure
4. 🧪 Run tests: `pytest -v`
5. 🚀 Try the CLI: `python -m agent.cli run --mode quick --use-sample`

Happy developing! 🎉
