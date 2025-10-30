# Developer Setup Guide

Complete guide for setting up a local development environment for device-inspector (inspecta).

**Estimated Setup Time:** 10-15 minutes

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Running Tests](#running-tests)
5. [Development Workflow](#development-workflow)
6. [IDE Setup](#ide-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.11 or 3.12**
- **Git**
- **pip** (usually comes with Python)

### System Tools (for full hardware testing)

- **dmidecode** - System information tool
  ```bash
  # Ubuntu/Debian
  sudo apt-get install dmidecode
  
  # Fedora/RHEL
  sudo dnf install dmidecode
  ```

- **smartmontools** - Storage health monitoring
  ```bash
  # Ubuntu/Debian
  sudo apt-get install smartmontools
  
  # Fedora/RHEL
  sudo dnf install smartmontools
  ```

> **Note:** System tools are NOT required for development with sample data. Use `--use-sample` flag to test without hardware access.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/mufthakherul/device-inspector.git
cd device-inspector

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests to verify setup
pytest -v

# 5. Try the CLI with sample data
python -m agent.cli run --mode quick --output ./test-output --use-sample

# 6. Install pre-commit hooks (optional but recommended)
pre-commit install
```

✅ **Setup complete!** You can now develop and test the agent.

---

## Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/mufthakherul/device-inspector.git
cd device-inspector
```

### Step 2: Virtual Environment

**Why?** Isolates project dependencies from system Python packages.

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Verify activation (should show venv in path)
which python
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Installed packages include:**
- `click` - CLI framework
- `jsonschema` - JSON validation
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Test mocking
- `black` - Code formatter
- `ruff` - Linter
- `bandit` - Security scanner
- `safety` - Dependency vulnerability scanner

### Step 4: Verify Setup

```bash
# Run all tests
pytest -v

# Check code style
black --check .
ruff check .

# Run security scan
bandit -r agent/

# Generate coverage report
pytest --cov=agent --cov-report=html
```

All tests should pass! Coverage report available in `htmlcov/index.html`.

---

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Run specific test file
pytest tests/test_inventory.py

# Run specific test function
pytest tests/test_inventory.py::test_parse_dmidecode_sample

# Run with coverage
pytest --cov=agent --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=agent --cov-report=html
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=agent --cov-report=html

# Open coverage report in browser
# Linux
xdg-open htmlcov/index.html
# Mac
open htmlcov/index.html
# Windows
start htmlcov/index.html
```

**Current Coverage:** ~36% (target: 60%+)

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code in `agent/` directory:
- `agent/cli.py` - CLI commands
- `agent/plugins/` - Feature plugins
- `agent/report.py` - Report generation
- `agent/scoring.py` - Scoring logic

### 3. Test Your Changes

```bash
# Run tests
pytest -v

# Test with sample data
python -m agent.cli run --mode quick --output ./test --use-sample

# Test specific command
python -m agent.cli inventory --use-sample

# Test with verbose logging
python -m agent.cli run --mode quick --output ./test --use-sample --verbose
```

### 4. Format and Lint

```bash
# Auto-format code
black .

# Check linting
ruff check .

# Fix linting issues automatically
ruff check --fix .
```

### 5. Run Pre-commit Hooks

```bash
# Install hooks (one-time)
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### 7. Open Pull Request

Go to GitHub and create a PR from your branch to `main`.

---

## IDE Setup

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- Ruff

**Settings** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

### PyCharm

1. **Configure Interpreter:**
   - Settings → Project → Python Interpreter
   - Select the venv interpreter

2. **Configure pytest:**
   - Settings → Tools → Python Integrated Tools
   - Set "Default test runner" to pytest

3. **Configure Black:**
   - Install Black plugin
   - Settings → Tools → Black → Enable

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'agent'

**Solution:** Make sure you're running from the project root:
```bash
cd device-inspector
python -m agent.cli --help
```

#### 2. Permission denied when running inventory

**Solution:** Use `--use-sample` flag or run with sudo:
```bash
# With sample data (no root needed)
python -m agent.cli inventory --use-sample

# With real hardware (requires root)
sudo python -m agent.cli inventory
```

#### 3. pytest not found

**Solution:** Activate virtual environment:
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### 4. Import errors in tests

**Solution:** Install in development mode:
```bash
pip install -e .
```

#### 5. Pre-commit hooks fail

**Solution:** Run formatters manually:
```bash
black .
ruff check --fix .
pre-commit run --all-files
```

#### 6. dmidecode or smartctl not found

**Solution for testing:** Use `--use-sample` flag:
```bash
python -m agent.cli run --mode quick --output ./test --use-sample
```

**Solution for production:** Install system tools:
```bash
# Ubuntu/Debian
sudo apt-get install dmidecode smartmontools

# Verify installation
which dmidecode
which smartctl
```

---

## Testing Without Root Access

Most development and testing can be done without root access:

```bash
# Test inventory with sample data
python -m agent.cli inventory --use-sample

# Full run with sample data
python -m agent.cli run --mode quick --output ./test-output --use-sample

# Run all tests (uses fixtures)
pytest -v
```

**Sample data location:** `samples/tool_outputs/`

---

## Next Steps

1. ✅ **Setup complete!** - You can now develop features
2. 📖 **Read documentation:**
   - [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
   - [PROJECT_STATUS.md](../PROJECT_STATUS.md) - Current progress
   - [NEXT_STEPS.md](../NEXT_STEPS.md) - Upcoming priorities
3. 🔍 **Pick an issue:**
   - Check GitHub issues for "good first issue" label
   - See NEXT_STEPS.md for prioritized tasks
4. 🧪 **Write tests first:**
   - Add test fixtures in `tests/fixtures/`
   - Follow existing test patterns
   - Aim for >60% coverage

---

## Additional Resources

- **Project Documentation:** [README.md](../README.md)
- **Feature Specifications:** [FEATURES.md](../FEATURES.md)
- **Development Roadmap:** [ROADMAP.md](../ROADMAP.md)
- **Security Policy:** [SECURITY.md](../SECURITY.md)

---

## Getting Help

If you encounter issues:

1. **Check documentation** - README, CONTRIBUTING, this guide
2. **Search existing issues** on GitHub
3. **Ask in discussions** - Open a GitHub Discussion
4. **Open an issue** - For bugs or unclear documentation

---

## Development Tips

### Performance

- Use `--use-sample` for faster iteration
- Mock subprocess calls in tests
- Cache expensive operations

### Debugging

```bash
# Verbose logging
python -m agent.cli run --mode quick --output ./test --verbose

# Check logs
cat test/artifacts/agent.log

# Python debugger
import pdb; pdb.set_trace()
```

### Code Quality

- Run `black` before committing
- Address `ruff` warnings
- Keep test coverage above 35%
- Write docstrings for new functions
- Follow existing code patterns

---

**Last Updated:** 2025-10-30  
**Questions?** Open a GitHub Discussion or issue.
