# Architecture Overview

Technical architecture for device-inspector (inspecta) agent and reporting system.

**Last Updated:** 2025-10-30  
**Version:** 0.1.0 (MVP Phase)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Plugin System](#plugin-system)
5. [Report Generation](#report-generation)
6. [Scoring Engine](#scoring-engine)
7. [Technology Stack](#technology-stack)
8. [Design Decisions](#design-decisions)

---

## System Overview

Device-inspector is a **local-first hardware diagnostics toolkit** that:
- Executes system commands to gather hardware information
- Parses tool outputs into structured data
- Computes health scores based on hardware metrics
- Generates auditable JSON reports with raw artifacts

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                       (agent/cli.py)                         │
│   Commands: run, inventory                                   │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
│  • Coordinate plugin execution                               │
│  • Manage artifacts directory                                │
│  • Handle errors and logging                                 │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Plugin System                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Inventory   │  │    SMART     │  │   Battery    │      │
│  │   Plugin     │  │    Plugin    │  │   Plugin     │ ...  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│    dmidecode          smartctl            upower            │
└─────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Layer                          │
│  • Parse tool outputs                                        │
│  • Extract metrics                                           │
│  • Validate data                                             │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                     Scoring Engine                           │
│                   (agent/scoring.py)                         │
│  • Calculate category scores                                 │
│  • Apply profile weights                                     │
│  • Generate recommendations                                  │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Report Generation                          │
│                   (agent/report.py)                          │
│  • Compose report.json                                       │
│  • Validate against schema                                   │
│  • Generate PDF (future)                                     │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                        Output                                │
│  report.json + artifacts/ directory                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. CLI Layer (`agent/cli.py`)

**Responsibilities:**
- Parse command-line arguments
- Validate user input
- Coordinate workflow execution
- Handle user-facing errors

**Key Components:**
- `cli()` - Main command group
- `run()` - Execute full inspection
- `inventory_cmd()` - Hardware detection only

**Design Pattern:** Command pattern with Click framework

---

### 2. Plugin System (`agent/plugins/`)

**Architecture:**
```
agent/plugins/
├── __init__.py
├── inventory.py      # System information
├── smart.py          # Storage health
├── battery.py        # Battery health (future)
├── cpu.py            # CPU benchmarking (future)
└── memory.py         # Memory testing (future)
```

**Plugin Interface:**
Each plugin provides:
1. **Execution function** - Runs system tool
2. **Parser function** - Extracts structured data
3. **Error handling** - Graceful degradation

**Example: SMART Plugin**
```python
def scan_all_devices(use_sample=False):
    """Detect and scan all storage devices."""
    # 1. Device detection
    devices = detect_storage_devices()
    
    # 2. Execute smartctl for each device
    results = []
    for device in devices:
        result = execute_smartctl(device, use_sample)
        results.append(result)
    
    # 3. Return structured data
    return results
```

---

### 3. Scoring Engine (`agent/scoring.py`)

**Architecture:**
```
Scoring Engine
├── Category Scorers
│   ├── score_storage()
│   ├── score_battery()
│   ├── score_memory()
│   └── score_cpu()
├── Profile Weights
│   ├── Office (storage 40%, battery 30%, memory 20%, cpu 10%)
│   ├── Developer (cpu 35%, memory 30%, storage 25%, battery 10%)
│   └── Gamer (cpu 40%, gpu 30%, storage 20%, memory 10%)
└── Overall Score Calculator
    └── Weighted average across categories
```

**Scoring Algorithm:**
```python
def score_storage(smart_data):
    """Score storage health (0-100)."""
    base_score = 90
    
    # Deduct for SMART warnings
    if reallocated_sectors > 0:
        base_score -= 30
    if pending_sectors > 0:
        base_score -= 20
    if power_on_hours > threshold:
        base_score -= 10
    
    return max(0, base_score)
```

---

### 4. Report Generation (`agent/report.py`)

**Report Structure:**
```json
{
  "report_version": "1.0.0",
  "generated_at": "2025-10-30T12:00:00Z",
  "agent": {
    "name": "inspecta",
    "version": "0.1.0"
  },
  "device": {
    "vendor": "Dell",
    "model": "Latitude 7490",
    "serial": "ABC123"
  },
  "summary": {
    "overall_score": 85,
    "grade": "Good",
    "recommendation": "Suitable for office work"
  },
  "scores": {
    "storage": 90,
    "battery": 80,
    "memory": 85,
    "cpu_thermal": 85
  },
  "tests": [...],
  "artifacts": ["smart_sda.json", "agent.log"],
  "evidence": {
    "manifest_sha256": null,
    "signed": false
  }
}
```

---

## Data Flow

### Inspection Workflow

```
1. User Invocation
   $ inspecta run --mode quick --output ./output
        │
        ▼
2. CLI Initialization
   • Parse arguments
   • Setup logging
   • Create output directories
        │
        ▼
3. Device Detection (Inventory Plugin)
   • Execute dmidecode
   • Parse system info
   • Extract vendor, model, serial
        │
        ▼
4. Storage Scan (SMART Plugin)
   • Detect storage devices (/sys/block)
   • Execute smartctl per device
   • Parse SMART attributes
   • Write artifacts (smart_*.json)
        │
        ▼
5. Score Calculation
   • Analyze SMART attributes
   • Calculate storage health score
   • Apply profile weights
        │
        ▼
6. Report Generation
   • Compose report.json
   • Include all metadata
   • Validate against schema
        │
        ▼
7. Output
   • Write report.json
   • Save artifacts/
   • Log completion
```

---

## Plugin System

### Plugin Design Pattern

**Goal:** Extensibility without modifying core code

**Pattern:** Each plugin is self-contained module with standard interface

**Benefits:**
- Easy to add new hardware checks
- Plugins can fail gracefully
- Testing in isolation
- Parallel execution (future)

### Plugin Interface

```python
# Standard plugin interface
class Plugin:
    def detect(self):
        """Detect if this plugin can run."""
        pass
    
    def execute(self, use_sample=False):
        """Run the hardware check."""
        pass
    
    def parse(self, raw_output):
        """Parse raw output into structured data."""
        pass
    
    def score(self, parsed_data):
        """Calculate health score."""
        pass
```

### Adding a New Plugin

**Example: CPU Temperature Plugin**

1. **Create plugin file** (`agent/plugins/cpu_temp.py`)
2. **Implement execution** (call `sensors` command)
3. **Implement parser** (extract temperature data)
4. **Add to orchestrator** (call in `cli.py`)
5. **Add tests** (`tests/test_cpu_temp.py`)
6. **Add sample data** (`samples/tool_outputs/sensors_sample.txt`)

---

## Scoring Engine

### Scoring Philosophy

**Principles:**
1. **Transparent** - All scores are explainable
2. **Deterministic** - Same input = same score
3. **Auditable** - Raw data included in report
4. **Profile-aware** - Scores weighted by use case

### Category Scores (0-100)

- **Storage (90-100):** No errors, low hours
- **Storage (70-89):** Minor warnings, moderate hours
- **Storage (40-69):** Reallocated sectors, high hours
- **Storage (0-39):** Critical errors, imminent failure

### Overall Score Calculation

```python
# Profile weights
profiles = {
    "office": {"storage": 0.40, "battery": 0.30, "memory": 0.20, "cpu": 0.10},
    "developer": {"cpu": 0.35, "memory": 0.30, "storage": 0.25, "battery": 0.10},
    "gamer": {"cpu": 0.40, "gpu": 0.30, "storage": 0.20, "memory": 0.10}
}

# Calculate weighted average
overall = sum(score * weight for score, weight in zip(scores, weights))
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Why? |
|-----------|-----------|------|
| Language | Python 3.11+ | System integration, rich ecosystem |
| CLI Framework | Click | Best-in-class CLI with validation |
| Testing | pytest | Industry standard, plugin ecosystem |
| Linting | Ruff + Black | Fast, comprehensive, auto-fix |
| Schema | JSON Schema | Standardized validation |

### System Dependencies

| Tool | Purpose | Required? |
|------|---------|-----------|
| dmidecode | System info | Yes (Linux) |
| smartctl | Storage health | Yes |
| fio | Disk performance | Sprint 2 |
| upower | Battery info | Sprint 2 |
| sysbench | CPU benchmark | Sprint 2 |

---

## Design Decisions

### 1. Why Local-First?

**Decision:** All processing happens locally, no cloud dependencies

**Rationale:**
- Privacy concerns with hardware data
- Works offline
- No vendor lock-in
- Faster execution

### 2. Why JSON + PDF Reports?

**Decision:** JSON for machines, PDF for humans

**Rationale:**
- JSON: Machine-readable, parseable, archivable
- PDF: Human-friendly, printable, shareable
- Both: Different audiences, different needs

### 3. Why Plugin Architecture?

**Decision:** Modular plugin system vs monolithic

**Rationale:**
- Extensibility: Easy to add new checks
- Maintainability: Isolated concerns
- Testing: Test plugins independently
- Graceful degradation: One plugin failure doesn't break all

### 4. Why Python?

**Decision:** Python vs Go/Rust/Shell

**Rationale:**
- Rich ecosystem for system tools
- Easy subprocess management
- JSON parsing built-in
- Fast development iteration
- Good testing frameworks

### 5. Why Schema Validation?

**Decision:** Strict JSON Schema vs ad-hoc validation

**Rationale:**
- Guarantees report compatibility
- Catches bugs early
- Enables third-party integrations
- Self-documenting

---

## Future Architecture

### Phase 2: Backend (Optional)

```
Agent (Local) → API Gateway → Backend Services → Database
                                ├── Report Storage
                                ├── Analytics
                                └── Viewer Web App
```

### Phase 3: Bootable Image

```
Live USB → Minimal Linux → Inspecta Agent → Report to USB
         → No OS interference
         → Full hardware access
```

---

## Performance Considerations

### Current Performance

- **Quick mode:** ~30 seconds (with real hardware)
- **Sample mode:** <5 seconds (no hardware)
- **Report size:** ~50-100KB (JSON + artifacts)

### Optimization Strategies

1. **Parallel execution** - Run plugins concurrently
2. **Caching** - Cache device detection
3. **Incremental updates** - Reuse previous results
4. **Minimal data** - Only collect what's needed

---

## Security Considerations

### Current Measures

1. **No network calls** - Fully offline
2. **Read-only operations** - No disk writes outside output dir
3. **Input validation** - Schema validation, subprocess args
4. **Security scanning** - Bandit in CI

### Future Enhancements

1. **Report signing** - Cryptographic signatures
2. **Manifest checksums** - Tamper detection
3. **Audit logging** - Who ran what when

---

## Testing Strategy

### Test Pyramid

```
         ┌──────────────────┐
         │   E2E Tests      │  (Future: Real hardware)
         └──────────────────┘
       ┌────────────────────────┐
       │  Integration Tests     │  (Full CLI runs)
       └────────────────────────┘
    ┌───────────────────────────────┐
    │      Unit Tests               │  (Parsers, scoring)
    └───────────────────────────────┘
```

### Test Data

- **Sample outputs** in `samples/tool_outputs/`
- **Test fixtures** in `tests/fixtures/`
- **Mock subprocess** calls in unit tests

---

## Development Principles

1. **Fail gracefully** - Missing tool? Show helpful error
2. **Sample data first** - Test without hardware
3. **Document everything** - Code + docs + tests
4. **Security conscious** - Audit all subprocess calls
5. **Transparent scoring** - Explain every number

---

## Contributing to Architecture

When proposing architectural changes:

1. **Open discussion** - Explain problem and solution
2. **Consider alternatives** - Why this vs that?
3. **Update docs** - This file, FEATURES.md, etc.
4. **Prototype first** - Validate approach
5. **Get feedback** - Before implementing fully

---

## References

- **FEATURES.md** - Detailed feature specifications
- **PROJECT_GOAL.md** - Mission and objectives
- **ROADMAP.md** - Implementation timeline
- **CONTRIBUTING.md** - Development guidelines

---

**Questions?** Open a GitHub Discussion or issue.
