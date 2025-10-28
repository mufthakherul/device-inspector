# Next Steps — device-inspector (inspecta)

**Last Updated:** 2025-10-28  
**For Version:** 0.1.0 → 0.2.0 (MVP Phase 1)  
**Timeframe:** Next 2-4 weeks

This document provides **prioritized, actionable next steps** for moving the device-inspector project from its current state (15% complete) toward MVP completion. Each section includes specific tasks, acceptance criteria, estimated effort, and implementation guidance.

---

## Table of Contents

1. [Immediate Priorities (This Week)](#immediate-priorities-this-week)
2. [Sprint 1 Completion (Next 2 Weeks)](#sprint-1-completion-next-2-weeks)
3. [Sprint 2 Preparation](#sprint-2-preparation)
4. [Technical Debt & Quality](#technical-debt--quality)
5. [Documentation Updates](#documentation-updates)
6. [Quick Wins](#quick-wins)
7. [Issue Creation Checklist](#issue-creation-checklist)

---

## Immediate Priorities (This Week)

### Priority 1: Complete Inventory Plugin ⭐⭐⭐

**Goal:** Enable the agent to detect and report device hardware information.

**Tasks:**

1. **Implement `inventory.py` plugin** (`agent/plugins/inventory.py`)
   - Add Linux dmidecode wrapper for BIOS/system info
   - Parse vendor, model, serial number, BIOS version
   - Handle cases where dmidecode requires root access
   - Provide graceful fallback if dmidecode unavailable

2. **Add inventory command to CLI**
   - Update `cli.py` to add `inspecta inventory` subcommand
   - Output device JSON to stdout or file
   - Include error handling for permission issues

3. **Create tests**
   - `tests/test_inventory_parser.py` with sample dmidecode outputs
   - Mock dmidecode execution in integration test
   - Test permission error handling

**Acceptance Criteria:**
- [ ] `inspecta inventory` runs successfully on Linux
- [ ] Returns JSON with vendor, model, serial, BIOS fields
- [ ] Handles permission errors with clear message
- [ ] 3+ unit tests pass for inventory parsing

**Estimated Effort:** 4-6 hours  
**Dependencies:** None  
**Reference:** FEATURES.md section 1.1, ROADMAP.md Sprint 1

---

### Priority 2: Real smartctl Execution ⭐⭐⭐

**Goal:** Execute smartctl on actual devices, not just parse sample data.

**Tasks:**

1. **Update `smart.py` plugin to execute smartctl**
   - Use `subprocess.run()` to execute `smartctl --json -a /dev/sdX`
   - Detect available storage devices (scan /dev/sd*, /dev/nvme*)
   - Handle NVMe devices with `smartctl -d nvme` flag
   - Add timeout and error handling

2. **Implement device detection**
   - Scan `/sys/block/` for block devices
   - Filter out loop, ram, and virtual devices
   - Detect device type (SATA, NVMe, USB)

3. **Update report generation**
   - Include smartctl execution results in artifacts
   - Handle multiple drives (iterate over all detected)
   - Store each device's SMART data separately

4. **Add comprehensive tests**
   - Mock smartctl subprocess for unit tests
   - Test error cases (device busy, permission denied, not available)
   - Test multi-drive scenarios

**Acceptance Criteria:**
- [ ] Agent executes real smartctl on detected devices
- [ ] Handles SATA and NVMe devices correctly
- [ ] Creates artifacts/smart_{device}.json for each drive
- [ ] Gracefully handles smartctl errors with clear messages
- [ ] 5+ tests covering execution scenarios

**Estimated Effort:** 6-8 hours  
**Dependencies:** None  
**Reference:** FEATURES.md section 1.2, ROADMAP.md Sprint 1

---

### Priority 3: Enhance Error Handling & Logging ⭐⭐

**Goal:** Provide clear, actionable error messages and detailed logging.

**Tasks:**

1. **Improve CLI error messages**
   - Add user-friendly error messages for common failures
   - Suggest installation commands for missing tools
   - Include links to troubleshooting documentation

2. **Add structured logging**
   - Write detailed logs to `output/artifacts/agent.log`
   - Include timestamps, log levels, context
   - Log all subprocess executions and results

3. **Create error handling utilities**
   - Add `agent/exceptions.py` with custom exception classes
   - Implement consistent error handling patterns
   - Add retry logic where appropriate (e.g., device busy)

**Acceptance Criteria:**
- [ ] Clear error messages for missing tools (smartctl, dmidecode)
- [ ] agent.log contains detailed execution information
- [ ] Custom exceptions for common error scenarios
- [ ] Error messages include troubleshooting suggestions

**Estimated Effort:** 3-4 hours  
**Dependencies:** None  
**Reference:** FEATURES.md section 13

---

## Sprint 1 Completion (Next 2 Weeks)

### Task 4: Complete report.json Schema Implementation ⭐⭐

**Goal:** Ensure report.json fully conforms to documented schema.

**Tasks:**

1. **Implement missing report.json fields**
   - Add all fields from REPORT_SCHEMA.md
   - Ensure proper nesting and structure
   - Include evidence section with manifest placeholder

2. **Add JSON Schema validation**
   - Load `schemas/report-schema-1.0.0.json`
   - Validate report before writing
   - Provide clear validation errors

3. **Update tests**
   - Ensure all tests generate valid reports
   - Add test for schema compliance
   - Test with various report configurations

**Acceptance Criteria:**
- [ ] report.json matches REPORT_SCHEMA.md specification
- [ ] JSON Schema validation passes for all reports
- [ ] Schema validation integrated in CI
- [ ] 2+ tests for schema edge cases

**Estimated Effort:** 4-5 hours  
**Dependencies:** None  
**Reference:** REPORT_SCHEMA.md, schemas/report-schema-1.0.0.json

---

### Task 5: Expand Test Coverage ⭐⭐

**Goal:** Achieve 50%+ code coverage with comprehensive tests.

**Tasks:**

1. **Add parser tests**
   - Create sample outputs for each tool (dmidecode, smartctl variations)
   - Store in `tests/fixtures/` directory
   - Test with healthy and failing device outputs

2. **Add integration tests**
   - Test full CLI run with all mocked tools
   - Test artifact generation and structure
   - Test error scenarios end-to-end

3. **Set up coverage reporting**
   - Add pytest-cov to requirements
   - Configure coverage in pyproject.toml
   - Add coverage badge to README (future)

4. **Add CI coverage check**
   - Update `.github/workflows/ci.yml`
   - Fail CI if coverage drops below threshold (50%)
   - Generate coverage report as artifact

**Acceptance Criteria:**
- [ ] Test coverage ≥50% (target 60%)
- [ ] 15+ unit tests total
- [ ] 3+ integration tests
- [ ] Coverage reporting in CI

**Estimated Effort:** 6-8 hours  
**Dependencies:** None  
**Reference:** ROADMAP.md Sprint 1

---

### Task 6: Add Sample Outputs & Fixtures ⭐

**Goal:** Provide realistic sample data for testing and documentation.

**Tasks:**

1. **Collect sample tool outputs**
   - Run dmidecode on a Linux system, save output
   - Run smartctl on SATA and NVMe devices
   - Collect healthy and failing device outputs
   - Redact any personal information

2. **Add to repository**
   - Create `samples/tool_outputs/` directory
   - Store as text or JSON files
   - Document source and device type

3. **Use in tests**
   - Load fixtures in test files
   - Test parsers with real-world data
   - Ensure parsers handle variations

**Acceptance Criteria:**
- [ ] 5+ sample tool outputs in repository
- [ ] Samples cover common device types
- [ ] Tests use real sample data
- [ ] Samples documented in README

**Estimated Effort:** 2-3 hours  
**Dependencies:** Access to test systems  
**Reference:** FEATURES.md, tests/

---

## Sprint 2 Preparation

These tasks prepare for Sprint 2 (Disk perf, battery, CPU, scoring).

### Task 7: Research & Prototype Integrations ⭐

**Goal:** Validate approach for next sprint's tool integrations.

**Tasks:**

1. **fio (disk performance)**
   - Test fio quick jobs (128MB read/write)
   - Identify optimal fio parameters
   - Create sample fio output for parsing

2. **upower/powercfg (battery)**
   - Test upower on Linux laptop
   - Test powercfg /batteryreport on Windows (if available)
   - Design parser for battery health metrics

3. **sysbench (CPU benchmark)**
   - Test sysbench cpu --threads=1 quick run
   - Identify performance scoring baseline
   - Create sample sysbench output

**Acceptance Criteria:**
- [ ] Prototype fio wrapper working
- [ ] Battery health data extraction tested
- [ ] CPU benchmark baseline established
- [ ] Sample outputs saved for Sprint 2

**Estimated Effort:** 4-5 hours  
**Dependencies:** Access to test hardware  
**Reference:** ROADMAP.md Sprint 2

---

### Task 8: Design Scoring Engine Complete ⭐

**Goal:** Define complete scoring algorithm for all categories.

**Tasks:**

1. **Document scoring formulas**
   - Create `docs/SCORING_ALGORITHM.md`
   - Define exact formulas for each category
   - Document weight rationale
   - Add scoring examples

2. **Implement scoring functions**
   - Complete `scoring.py` with all categories
   - Add configurable thresholds
   - Implement profile-specific scoring

3. **Add comprehensive scoring tests**
   - Test each category independently
   - Test overall score calculation
   - Test profile recommendations

**Acceptance Criteria:**
- [ ] SCORING_ALGORITHM.md document created
- [ ] All scoring functions implemented
- [ ] 10+ scoring tests passing
- [ ] Profile recommendations working

**Estimated Effort:** 5-6 hours  
**Dependencies:** None  
**Reference:** FEATURES.md section 3, PROJECT_GOAL.md

---

## Technical Debt & Quality

### Task 9: Add Security Scanning ⭐

**Goal:** Automate security vulnerability detection.

**Tasks:**

1. **Add Bandit (Python security linter)**
   - Add to requirements.txt
   - Configure in pyproject.toml
   - Add to CI pipeline
   - Fix any identified issues

2. **Add Safety (dependency scanning)**
   - Scan requirements.txt for vulnerabilities
   - Add to CI as informational check
   - Document vulnerability response process

3. **Enable Dependabot**
   - Configure .github/dependabot.yml
   - Set up automated PRs for updates
   - Define auto-merge rules for patches

**Acceptance Criteria:**
- [ ] Bandit runs in CI
- [ ] Safety scans dependencies
- [ ] Dependabot configured
- [ ] No critical security issues

**Estimated Effort:** 2-3 hours  
**Dependencies:** None  
**Reference:** SECURITY.md, CONTRIBUTING.md

---

### Task 10: Improve CI Pipeline ⭐

**Goal:** Enhance CI with coverage, caching, and artifacts.

**Tasks:**

1. **Add code coverage reporting**
   - Use pytest-cov
   - Upload to Codecov or similar
   - Add coverage badge to README

2. **Add dependency caching**
   - Cache pip packages between runs
   - Reduce CI execution time

3. **Generate and archive artifacts**
   - Save test reports
   - Archive coverage reports
   - Keep sample generated reports

4. **Add matrix testing**
   - Test on Python 3.11 and 3.12
   - Consider testing on Ubuntu 20.04 and 22.04

**Acceptance Criteria:**
- [ ] Coverage reporting in CI
- [ ] CI runs faster with caching
- [ ] Test artifacts available for download
- [ ] Multi-version Python testing

**Estimated Effort:** 3-4 hours  
**Dependencies:** None  
**Reference:** .github/workflows/ci.yml

---

## Documentation Updates

### Task 11: Create Developer Setup Guide ⭐

**Goal:** Make it easier for new developers to get started.

**Tasks:**

1. **Create `docs/DEV_SETUP.md`**
   - Step-by-step setup instructions
   - Include virtual environment setup
   - Document required system tools
   - Add troubleshooting section

2. **Add example commands**
   - Installation verification steps
   - Running tests locally
   - Running the agent in dev mode
   - Debugging tips

3. **Create Docker dev environment (optional)**
   - Dockerfile with all dependencies
   - docker-compose for testing
   - Include in Dev Setup guide

**Acceptance Criteria:**
- [ ] DEV_SETUP.md created with clear steps
- [ ] New developer can set up in <15 minutes
- [ ] Troubleshooting section covers common issues
- [ ] Optional Docker setup documented

**Estimated Effort:** 3-4 hours  
**Dependencies:** None  
**Reference:** CONTRIBUTING.md

---

### Task 12: Update README with Implementation Status ⭐

**Goal:** Keep README accurate with current capabilities.

**Tasks:**

1. **Add implementation status section**
   - Create "Current Status" section
   - List implemented vs planned features
   - Update "Status" line at top
   - Add link to PROJECT_STATUS.md

2. **Update quickstart for current capabilities**
   - Show what actually works today
   - Remove references to unimplemented features
   - Add "Coming Soon" section

3. **Add development badges**
   - CI status badge
   - Python version badge
   - License badge
   - Coverage badge (when ready)

**Acceptance Criteria:**
- [ ] README accurately reflects current state
- [ ] Users understand what works vs what's planned
- [ ] CI and license badges visible
- [ ] Links to status documentation

**Estimated Effort:** 1-2 hours  
**Dependencies:** None  
**Reference:** README.md, PROJECT_STATUS.md

---

## Quick Wins

These are small tasks with high impact that can be done quickly.

### Quick Win 1: Add More Sample Data (30 min)

- Add 2-3 more sample smart outputs (SSD, HDD, failing)
- Add sample dmidecode output
- Document in samples/README.md

### Quick Win 2: Improve CLI Help Text (30 min)

- Enhance docstrings in cli.py
- Add examples to --help output
- Include link to documentation

### Quick Win 3: Add Pre-commit Hooks (45 min)

- Configure pre-commit with Black, Ruff, detect-secrets
- Document in CONTRIBUTING.md
- Test pre-commit workflow

### Quick Win 4: Create Issue Templates (1 hour)

- Create detailed bug report template
- Create feature request template
- Add custom issue labels
- Reference in CONTRIBUTING.md

### Quick Win 5: Add ARCHITECTURE.md (1-2 hours)

- Create visual/text architecture overview
- Explain plugin system design
- Document data flow
- Add component diagram (text/ASCII or actual image)

---

## Issue Creation Checklist

To help organize this work, create GitHub issues for each major task:

### Sprint 1 Issues

- [ ] **Issue #X:** Implement inventory plugin with dmidecode integration
- [ ] **Issue #X:** Add real smartctl execution to SMART plugin
- [ ] **Issue #X:** Enhance error handling and structured logging
- [ ] **Issue #X:** Complete report.json schema implementation
- [ ] **Issue #X:** Expand test coverage to 50%+
- [ ] **Issue #X:** Add sample tool outputs and test fixtures

### Sprint 2 Prep Issues

- [ ] **Issue #X:** Research and prototype fio disk performance integration
- [ ] **Issue #X:** Design and document complete scoring algorithm
- [ ] **Issue #X:** Prototype battery health parsing (upower/powercfg)
- [ ] **Issue #X:** Prototype CPU benchmark with sysbench

### Quality & Infrastructure Issues

- [ ] **Issue #X:** Add Bandit and Safety security scanning to CI
- [ ] **Issue #X:** Enhance CI with coverage, caching, and matrix testing
- [ ] **Issue #X:** Create comprehensive developer setup guide
- [ ] **Issue #X:** Update README with current implementation status

### Quick Win Issues (Good First Issues)

- [ ] **Issue #X:** Add more sample tool outputs for testing
- [ ] **Issue #X:** Improve CLI help text and examples
- [ ] **Issue #X:** Configure and document pre-commit hooks
- [ ] **Issue #X:** Create detailed issue templates
- [ ] **Issue #X:** Create ARCHITECTURE.md with component overview

**Label Suggestions:**
- Sprint 1, Sprint 2
- good first issue (for quick wins)
- documentation, testing, enhancement
- priority: high/medium/low

---

## Implementation Order Recommendation

If you can dedicate focused time, follow this order for maximum momentum:

### Week 1 (8-12 hours)

1. Implement inventory plugin (Priority 1) — 6 hours
2. Add real smartctl execution (Priority 2) — 6 hours

**Outcome:** Basic hardware detection working

### Week 2 (8-12 hours)

3. Enhance error handling (Priority 3) — 4 hours
4. Complete report schema (Task 4) — 4 hours
5. Expand test coverage (Task 5) — 4 hours

**Outcome:** Sprint 1 complete, solid foundation

### Week 3 (8-10 hours)

6. Research Sprint 2 integrations (Task 7) — 4 hours
7. Add security scanning (Task 9) — 3 hours
8. Create dev setup guide (Task 11) — 3 hours

**Outcome:** Ready for Sprint 2, better contributor experience

### Week 4 (6-8 hours)

9. Design complete scoring (Task 8) — 6 hours
10. Quick wins as time permits — 2 hours

**Outcome:** Sprint 2 ready to start

---

## Success Metrics

Track these to measure progress:

**Week 1:**
- [ ] Inventory and SMART plugins execute on real hardware
- [ ] 3+ new tests added and passing
- [ ] Agent successfully generates report.json with real device data

**Week 2 (Sprint 1 Complete):**
- [ ] 15+ tests passing
- [ ] 50%+ code coverage
- [ ] All Sprint 1 acceptance criteria met
- [ ] CI fully green

**Week 3:**
- [ ] Sprint 2 prototypes validated
- [ ] Security scanning active
- [ ] Developer documentation improved

**Week 4:**
- [ ] Scoring engine complete
- [ ] Ready to begin Sprint 2 implementation

---

## Getting Help

If you get stuck on any of these tasks:

1. **Review Documentation:** FEATURES.md has detailed specs
2. **Check ROADMAP:** Sprint definitions include guidance
3. **Reference Samples:** Use existing code patterns
4. **Ask for Help:** Open a discussion on GitHub

---

## Maintenance Going Forward

After completing these next steps:

1. **Update PROJECT_STATUS.md** after each sprint
2. **Keep CHANGELOG.md** current with each feature
3. **Groom backlog** regularly — close completed issues
4. **Run retrospectives** — what's working, what's not?

---

## Appendix: Estimated Total Effort

**Immediate Priorities (Week 1):** 14-18 hours  
**Sprint 1 Completion (Week 2):** 12-16 hours  
**Sprint 2 Prep (Week 3):** 9-11 hours  
**Technical Debt (Week 3-4):** 5-7 hours  
**Documentation (Week 3-4):** 4-6 hours  
**Quick Wins:** 3-5 hours (distributed)

**Total for MVP Foundation:** 47-63 hours of focused development

With consistent effort (10-15 hours/week), Sprint 1 completion and Sprint 2 readiness achievable in 4 weeks.

---

**Document Version:** 1.0  
**Created:** 2025-10-28  
**Next Review:** After Sprint 1 completion

**Remember:** These are prioritized recommendations. Adjust based on available time, resources, and project goals. The most important thing is consistent progress toward the MVP vision outlined in the excellent documentation already in place.
