# Setup Checklist

This checklist can be used to verify all setup steps are complete.

---

## Pre-Setup Requirements

- [ ] Python 3.11 or 3.12 installed (`python --version` or `python3 --version`)
- [ ] Git installed (if cloning repository)
- [ ] ~2GB free disk space available
- [ ] For admin/system tools: Run as administrator (Windows) or have `sudo` access (Linux/macOS)

---

## Automated Setup (Recommended)

### Windows

- [ ] Open PowerShell
- [ ] Navigate to project directory
- [ ] Run: `.\setup.ps1`
- [ ] Wait for completion (~5-10 minutes)
- [ ] See "Setup Complete!" message
- [ ] Virtual environment at `venv\` directory
- [ ] Activate: `.\venv\Scripts\Activate.ps1`

### Linux / macOS

- [ ] Open Terminal/Bash
- [ ] Navigate to project directory
- [ ] Make script executable: `chmod +x setup.sh`
- [ ] Run: `./setup.sh`
- [ ] Wait for completion (~5-10 minutes)
- [ ] See "Setup Complete!" message
- [ ] Virtual environment at `venv/` directory
- [ ] Activate: `source venv/bin/activate`

---

## Verification

After setup completes, verify installation:

- [ ] Virtual environment exists
  - Windows: `venv\Scripts\python.exe` exists
  - Linux/macOS: `venv/bin/python` exists

- [ ] Python available in venv
  ```bash
  # Activate first
  python --version  # Should show 3.11 or 3.12
  ```

- [ ] Key packages installed
  ```bash
  pip list | grep -E "(click|jsonschema|pytest|black|ruff)"
  ```

- [ ] CLI works
  ```bash
  python -m agent.cli --help
  ```

- [ ] Tests pass (if not skipped)
  ```bash
  pytest -q
  # Should see: X passed
  ```

- [ ] Smoke test passes
  ```bash
  python -m agent.cli inventory --use-sample
  # Should show device info
  ```

---

## Post-Setup Configuration

### Optional: Install System Tools

For full hardware diagnostics (requires admin/sudo):

- [ ] Windows: Install SmartMonTools
  - Option 1: `winget install Argonaut.SmartMonTools`
  - Option 2: Download from https://www.smartmontools.org/wiki/Download

- [ ] Linux: Install diagnostics tools
  ```bash
  # Ubuntu/Debian
  sudo apt install smartmontools dmidecode lm-sensors
  
  # Fedora/RHEL
  sudo dnf install smartmontools dmidecode lm_sensors
  
  # Arch
  sudo pacman -S smartmontools dmidecode lm_sensors
  ```
  
  Or use: `./setup.sh --install-tools`

- [ ] macOS: Install via Homebrew
  ```bash
  brew install smartmontools
  ```

### Optional: IDE Setup

- [ ] VS Code Extensions Installed (if using VS Code)
  - [ ] Python (Microsoft)
  - [ ] Pylance
  - [ ] Black Formatter
  - [ ] Ruff

- [ ] Editor Settings
  - [ ] Format on save enabled
  - [ ] Ruff linter enabled
  - [ ] Python testing configured

---

## Development Ready

- [ ] Can activate venv: `source venv/bin/activate` (Linux/macOS) or `.\venv\Scripts\Activate.ps1` (Windows)
- [ ] Can run CLI: `python -m agent.cli inventory --use-sample`
- [ ] Can run tests: `pytest -v`
- [ ] Can format code: `python -m black .`
- [ ] Can lint code: `python -m ruff check .`
- [ ] Documentation accessible:
  - [ ] README.md reviewed
  - [ ] CONTRIBUTING.md read
  - [ ] docs/DEV_SETUP.md bookmarked
  - [ ] docs/ARCHITECTURE.md reviewed

---

## Common Issues & Troubleshooting

### Python Not Found After Installation
- [ ] Added Python to PATH during installation
- [ ] Restarted terminal/PowerShell
- [ ] Verified: `python --version` works

### Virtual Environment Creation Failed
- [ ] Check Python version: `python --version` (needs 3.11+)
- [ ] Try manual creation: `python -m venv venv`
- [ ] Check disk space (need ~500MB)

### Dependency Installation Failed
- [ ] Check internet connection
- [ ] Upgrade pip: `pip install --upgrade pip`
- [ ] Try again: `pip install -r requirements.txt`

### Tests Fail
- [ ] Ensure venv activated
- [ ] Some battery tests fail on cross-platform (expected)
- [ ] Use `--skip-tests` if tests block setup

### CLI Doesn't Run
- [ ] Check venv activated
- [ ] Check project installed: `pip list | grep inspecta`
- [ ] Try: `python -m agent.cli --help`

### Permission Denied on Hardware Tools
- [ ] Use sample data: `--use-sample` flag
- [ ] For real hardware on Linux/macOS: prefix with `sudo`
- [ ] On Windows: run PowerShell as Administrator

---

## Next Steps After Setup

1. **Read Documentation**
   - [ ] Read [docs/DEV_SETUP.md](docs/DEV_SETUP.md)
   - [ ] Review [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
   - [ ] Check [CONTRIBUTING.md](CONTRIBUTING.md)

2. **Explore Codebase**
   - [ ] Navigate `agent/` directory
   - [ ] Check `tests/` directory structure
   - [ ] Review `samples/` for test data

3. **Run Commands**
   - [ ] `python -m agent.cli run --mode quick --use-sample`
   - [ ] `python -m agent.cli inventory --use-sample`
   - [ ] `pytest -v` (run tests)

4. **Set Up Git**
   - [ ] Configure git user: `git config user.name "Your Name"`
   - [ ] Configure git email: `git config user.email "your@email.com"`
   - [ ] Create feature branch: `git checkout -b feature/your-feature`

5. **Make Your First Contribution**
   - [ ] Pick an issue or feature
   - [ ] Create tests
   - [ ] Implement feature
   - [ ] Run tests: `pytest -v`
   - [ ] Format code: `python -m black .`
   - [ ] Commit and push
   - [ ] Create pull request

---

## Setup Validation Script

Quick validation after setup:

```bash
# Activate venv first
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows

# Run validation
echo "Python version:"
python --version

echo "Installed packages:"
pip list

echo "CLI test:"
python -m agent.cli --help

echo "Inventory test:"
python -m agent.cli inventory --use-sample

echo "Tests:"
pytest -q

echo "All checks passed! ✓"
```

---

## Support & Help

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: https://github.com/mufthakherul/inspecta-nexus/issues
- 💬 Discussions: https://github.com/mufthakherul/inspecta-nexus/discussions
- 📝 Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- 🆘 Setup Guide: [SETUP.md](SETUP.md)

---

**Last Updated:** March 2026
**Status:** ✅ All setup automation complete
