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

## [Unreleased] - 2025-10-30

### Added - Infrastructure & Quality Improvements

#### Testing & Coverage
- **pytest-cov Integration**: Added coverage reporting to test suite
  - HTML, XML, and terminal coverage reports
  - Coverage threshold set at 35% (current: 36.26%)
  - Coverage reports uploaded as CI artifacts
- **Additional Sample Data**: Added NVMe SMART sample output
- **Sample Documentation**: Created comprehensive samples/README.md

#### Security & Code Quality
- **Security Scanning**: Integrated Bandit for Python security analysis
- **Dependency Scanning**: Added Safety for vulnerability detection
- **Dependabot**: Configured automated dependency updates for Python and GitHub Actions
- **Enhanced Pre-commit Hooks**: 
  - Added file checks (trailing whitespace, EOF, large files)
  - Added security checks (detect-private-key)
  - Added YAML/JSON validation
  - Integrated Bandit security scanning

#### CI/CD Improvements
- **Matrix Testing**: Added Python 3.11 and 3.12 testing
- **Pip Caching**: Improved CI performance with dependency caching
- **Coverage Reporting**: Coverage reports in CI with artifacts
- **Security Scans**: Bandit runs on every CI build

#### CLI Improvements
- **Enhanced Help Text**: Comprehensive documentation in CLI commands
  - Detailed usage examples
  - Installation requirements
  - Exit code documentation
  - Output structure explanation
- **Better Command Organization**: Improved option descriptions and formatting

#### Documentation
- **samples/README.md**: Complete guide to sample data and test fixtures
- **Updated Configuration**: Enhanced pyproject.toml with coverage and bandit settings

### Changed
- **Coverage Threshold**: Set initial threshold at 35% (target: 60%+)
- **Linting Configuration**: Ignore complexity warnings temporarily (C901)
- **Pre-commit Configuration**: Modernized with additional security checks

### Infrastructure
- **Dependabot**: Weekly automated dependency updates
- **CI Matrix**: Multi-version Python testing (3.11, 3.12)
- **Security Pipeline**: Automated security scanning in CI

### Planned for Sprint 2
- Complete report.json schema with validation
- Increase test coverage to 60%+
- Disk performance testing (fio integration)
- Battery health detection (upower/powercfg)
- CPU benchmarking (sysbench)
- Complete scoring engine with profile-based recommendations
