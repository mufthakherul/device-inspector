# Packaging Checklist for Inspecta v1 Releases

This checklist ensures that standalone executable packages are complete, tested, and ready for distribution.

## Pre-Build Checklist

Before building release packages:

- [ ] Version number updated in all files:
  - [ ] `pyproject.toml`
  - [ ] `agent/__init__.py`
  - [ ] `README.md`
  - [ ] `docs/DISTRIBUTION.md`
  - [ ] `DISTRIBUTION_README.md`
  - [ ] `inspecta.spec`
  - [ ] `scripts/build_release.py`

- [ ] CHANGELOG.md updated with release notes

- [ ] All tests passing:
  ```bash
  pytest tests/
  ```

- [ ] Linting clean:
  ```bash
  ruff check .
  black --check .
  ```

- [ ] Documentation reviewed and up to date

- [ ] Security scan completed:
  ```bash
  bandit -r agent/
  safety check
  ```

## Build Checklist

For each target platform (Windows, macOS, Linux):

### Windows Build

- [ ] Build environment: Windows 10+ with Python 3.11+
- [ ] Build command succeeds:
  ```cmd
  python scripts/build_release.py --platform windows
  ```
- [ ] Output files created:
  - [ ] `dist/inspecta-{version}-windows/inspecta.exe`
  - [ ] `dist/inspecta-{version}-windows/Run_Inspecta.bat`
  - [ ] `dist/inspecta-{version}-windows/Run_Hardware_Inspection.bat`
  - [ ] `dist/inspecta-{version}-windows/README.md`
  - [ ] `dist/inspecta-{version}-windows/LICENSE.txt`
  - [ ] `dist/inspecta-{version}-windows/QUICK_START.txt`
  - [ ] `dist/inspecta-{version}-windows/samples/`
  - [ ] `dist/inspecta-{version}-windows.zip`

- [ ] Executable properties:
  - [ ] File size reasonable (15-25 MB)
  - [ ] No obvious packing errors in build log
  - [ ] Antivirus scan clean (false positives are common but note them)

### macOS Build

- [ ] Build environment: macOS 10.15+ with Python 3.11+
- [ ] Build command succeeds:
  ```bash
  python scripts/build_release.py --platform macos
  ```
- [ ] Output files created:
  - [ ] `dist/inspecta-{version}-macos/inspecta`
  - [ ] `dist/inspecta-{version}-macos/run_inspecta.sh`
  - [ ] `dist/inspecta-{version}-macos/README.md`
  - [ ] `dist/inspecta-{version}-macos/LICENSE.txt`
  - [ ] `dist/inspecta-{version}-macos/QUICK_START.txt`
  - [ ] `dist/inspecta-{version}-macos/samples/`
  - [ ] `dist/inspecta-{version}-macos.zip`

- [ ] Executable properties:
  - [ ] File size reasonable (15-25 MB)
  - [ ] Execute bit set: `chmod +x inspecta`
  - [ ] Shell script executable: `chmod +x run_inspecta.sh`

### Linux Build

- [ ] Build environment: Ubuntu 20.04+ with Python 3.11+
- [ ] Build command succeeds:
  ```bash
  python scripts/build_release.py --platform linux
  ```
- [ ] Output files created:
  - [ ] `dist/inspecta-{version}-linux/inspecta`
  - [ ] `dist/inspecta-{version}-linux/run_inspecta.sh`
  - [ ] `dist/inspecta-{version}-linux/README.md`
  - [ ] `dist/inspecta-{version}-linux/LICENSE.txt`
  - [ ] `dist/inspecta-{version}-linux/QUICK_START.txt`
  - [ ] `dist/inspecta-{version}-linux/samples/`
  - [ ] `dist/inspecta-{version}-linux.zip`

- [ ] Executable properties:
  - [ ] File size reasonable (15-20 MB)
  - [ ] Execute bit set: `chmod +x inspecta`
  - [ ] Shell script executable: `chmod +x run_inspecta.sh`

## Testing Checklist

For each platform build, test the following:

### Basic Functionality Tests

**Test 1: Help Command**
```bash
./inspecta --help  # or inspecta.exe --help on Windows
```
- [ ] Help text displays correctly
- [ ] Version number is correct
- [ ] No errors or warnings

**Test 2: Sample Data Test (No Admin)**
- [ ] Run launcher: `Run_Inspecta.bat` (Windows) or `./run_inspecta.sh` (Mac/Linux)
- [ ] Executes without errors
- [ ] Creates `reports/` directory
- [ ] Generates `reports/report.json`
- [ ] Generates `reports/artifacts/agent.log`
- [ ] Exit code is 10 (sample data warning)
- [ ] Report contains sample device data
- [ ] Overall score is present (e.g., 83)

**Test 3: Inventory Command (Sample)**
```bash
./inspecta inventory --use-sample
```
- [ ] Displays device information as JSON
- [ ] Contains vendor, model, serial, BIOS fields
- [ ] No errors

**Test 4: Hardware Inspection (Admin/Root)**

*Note: This requires actual hardware and admin/root privileges*

Windows (as administrator):
```cmd
inspecta.exe run --mode quick --output test-hw --verbose
```

macOS/Linux (with sudo):
```bash
sudo ./inspecta run --mode quick --output test-hw --verbose
```

- [ ] Detects real device information
- [ ] Scans storage devices successfully
- [ ] Creates SMART artifacts for each drive
- [ ] Report contains real hardware data
- [ ] Exit code is 0 (success)
- [ ] No unexpected errors in logs

### Platform-Specific Tests

**Windows Specific:**
- [ ] Batch files execute without errors
- [ ] UAC prompt appears for hardware inspection
- [ ] Windows Defender SmartScreen warning (expected) - document bypass
- [ ] Executable runs from different directories
- [ ] No Python installation required
- [ ] Works on clean Windows 10/11 VM

**macOS Specific:**
- [ ] Shell scripts execute without errors
- [ ] Gatekeeper warning (expected) - document bypass
- [ ] Can remove quarantine: `xattr -d com.apple.quarantine inspecta`
- [ ] sudo prompt appears for hardware inspection
- [ ] Executable runs from different directories
- [ ] No Python installation required
- [ ] Works on clean macOS 10.15+ VM

**Linux Specific:**
- [ ] Shell scripts execute without errors
- [ ] sudo prompt appears for hardware inspection
- [ ] Executable runs from different directories
- [ ] No Python installation required
- [ ] Works on clean Ubuntu 20.04/22.04 VM

### Documentation Tests

- [ ] README.md is clear and accurate
- [ ] QUICK_START.txt is helpful for first-time users
- [ ] LICENSE.txt is included and readable
- [ ] All documentation references correct version
- [ ] GitHub links work
- [ ] No broken internal links

### Security Tests

**For All Platforms:**
- [ ] No hardcoded credentials or secrets
- [ ] No PII in sample data
- [ ] Executable does not trigger malware alerts (beyond false positives)
- [ ] Check with VirusTotal (expect some false positives)
- [ ] Verify digital signature (if signed)

**Windows Specific:**
- [ ] Scan with Windows Defender
- [ ] Scan with at least one third-party AV (Malwarebytes, etc.)
- [ ] Check for SmartScreen reputation (new releases may be flagged)

### Performance Tests

- [ ] Startup time reasonable (<3 seconds)
- [ ] Sample data test completes in <10 seconds
- [ ] Hardware inspection completes in 2-10 minutes (varies by hardware)
- [ ] Memory usage reasonable during execution
- [ ] No memory leaks over multiple runs
- [ ] Executable size is reasonable (not bloated)

### Edge Case Tests

- [ ] Run from directory with spaces in path
- [ ] Run from non-English system locale
- [ ] Run with minimal disk space (100 MB free)
- [ ] Run without write permissions (should show clear error)
- [ ] Run with output directory that doesn't exist (should create it)
- [ ] Run multiple times (overwrites previous reports correctly)
- [ ] Interrupt execution (Ctrl+C) - handles gracefully

## Package Verification

Before distribution:

- [ ] Extract zip on clean system
- [ ] Verify all expected files present
- [ ] Verify file permissions (executable bits, etc.)
- [ ] Verify no extra/unexpected files
- [ ] Verify total package size is reasonable
- [ ] Verify README.md is the distribution version, not dev version

## Distribution Checklist

### GitHub Release

- [ ] Create git tag: `git tag v{version}`
- [ ] Push tag: `git push origin v{version}`
- [ ] GitHub Actions workflow completes successfully
- [ ] Download artifacts from workflow
- [ ] Upload to GitHub Releases
- [ ] Write release notes with:
  - [ ] Version number
  - [ ] Release date
  - [ ] What's new/changed
  - [ ] Known issues
  - [ ] Download links for each platform
  - [ ] Installation instructions
  - [ ] Link to documentation

### Release Notes Template

```markdown
# Inspecta v{version}

**Released:** {date}

## Downloads

- Windows: [inspecta-{version}-windows.zip]({url})
- macOS: [inspecta-{version}-macos.zip]({url})
- Linux: [inspecta-{version}-linux.zip]({url})

## What's New

- Feature 1
- Feature 2
- Bug fix 1

## Installation

No installation required! Just download, extract, and run.

See the [Distribution Guide](docs/DISTRIBUTION.md) for detailed instructions.

## Known Issues

- Issue 1 (workaround)
- Issue 2 (tracking)

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md)
```

### Post-Release

- [ ] Verify download links work
- [ ] Update README.md with latest release link
- [ ] Update PROJECT_STATUS.md
- [ ] Announce release (if applicable):
  - [ ] GitHub Discussions
  - [ ] Social media
  - [ ] Mailing list
- [ ] Monitor for bug reports
- [ ] Create issues for any problems found

## Rollback Plan

If critical issues are found post-release:

1. **Immediate:**
   - [ ] Add warning to release notes
   - [ ] Mark release as "Pre-release" in GitHub
   - [ ] Document the issue and workaround

2. **Short-term:**
   - [ ] Fix the issue in a hotfix branch
   - [ ] Test thoroughly
   - [ ] Release patch version (e.g., v0.1.1)
   - [ ] Mark previous release as deprecated

3. **Communication:**
   - [ ] Update GitHub release notes
   - [ ] Post in discussions
   - [ ] Notify users who downloaded the affected version

## Testing Matrix

Maintain a testing matrix to track which configurations have been tested:

| Platform | Version | Python 3.11 | Python 3.12 | Test Status | Tester |
|----------|---------|-------------|-------------|-------------|--------|
| Windows 10 | {version} | ✅ | ✅ | PASS | {name} |
| Windows 11 | {version} | ✅ | ✅ | PASS | {name} |
| macOS 12 | {version} | ✅ | ❌ | PASS | {name} |
| macOS 13 | {version} | ✅ | ✅ | PASS | {name} |
| Ubuntu 20.04 | {version} | ✅ | ❌ | PASS | {name} |
| Ubuntu 22.04 | {version} | ✅ | ✅ | PASS | {name} |

## Sign-off

Release manager sign-off:

- [ ] All checklist items completed
- [ ] Testing passed on all target platforms
- [ ] Documentation is complete and accurate
- [ ] Known issues documented
- [ ] Release notes prepared
- [ ] Ready for public distribution

**Release Manager:** ________________  
**Date:** ________________  
**Version:** ________________

---

**Template Version:** 1.0  
**Last Updated:** 2025-10-30
