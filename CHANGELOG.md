# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-10-28

### Added - Sprint 1 Complete ✅

#### Core Functionality
- **CLI Framework**: Full Click-based CLI with `inspecta run` and `inspecta inventory` commands
- **Inventory Detection**: Complete dmidecode integration with real hardware detection
  - Parse vendor, model, serial, BIOS version, chassis type, SKU, UUID, family
  - Graceful error handling for permission denied and missing tools
  - Installation command suggestions in error messages
- **SMART Execution**: Real smartctl execution on storage devices
  - Automatic device detection via /sys/block scanning
  - Multi-device support (SATA, NVMe, USB)
  - NVMe-specific flag handling (-d nvme)
  - Individual artifact files per device (smart_sda.json, smart_nvme0n1.json)
  - Comprehensive JSON parsing for SMART attributes

#### Error Handling & Logging
- **Custom Exceptions**: InspectaError, ToolNotFoundError, PermissionError, DeviceError, ParseError, TimeoutError
- **Structured Logging**: InspectaLogger class with dual output (console + file)
- **CLI Options**: --verbose/-v flag for debug output, --use-sample for testing without root

#### Testing & Quality
- **22 Unit Tests**: All passing with ~45% code coverage
  - 5 tests for inventory detection
  - 11 tests for SMART execution
  - 2 tests for schema validation
  - 3 tests for scoring logic
  - 1 test for SMART parsing
- **CI/CD Pipeline**: GitHub Actions with linting (Black, Ruff) and testing

#### Documentation
- **Sample Data**: dmidecode, smartctl (healthy/failing SATA, NVMe)
- **Comprehensive Guides**: README, CONTRIBUTING, PROJECT_STATUS, SPRINT_1_SUMMARY

### Infrastructure
- Repository structure with organized directories
- Python package configuration (pyproject.toml)
- Development guidelines and contribution workflow
- Pre-commit hooks configuration

## Unreleased

### Planned for Sprint 2
- Complete report.json schema with validation
- Code coverage reporting (pytest-cov)
- Disk performance testing (fio integration)
- Battery health detection (upower/powercfg)
- CPU benchmarking (sysbench)
- Complete scoring engine with profile-based recommendations
