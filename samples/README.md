# Sample Data & Test Fixtures

This directory contains sample tool outputs and example reports for testing and documentation purposes.

## Directory Structure

```
samples/
├── artifacts/               # Sample output artifacts
│   ├── smart_nvme0.json    # Example NVMe SMART data
│   ├── memtest.log         # Placeholder memory test output
│   └── sensors.csv         # Placeholder sensor data
├── tool_outputs/           # Raw tool outputs for testing
│   ├── dmidecode_sample.txt           # Sample dmidecode output
│   ├── smartctl_sata_healthy.json     # Healthy SATA drive SMART data
│   └── smartctl_sata_failing.json     # Failing SATA drive with errors
└── sample_report.json      # Complete example report.json

```

## Tool Outputs

### dmidecode_sample.txt
Sample output from `dmidecode` command showing system information.
- **Source:** Dell Latitude laptop (anonymized)
- **Use:** Testing inventory detection without root access

### smartctl_sata_healthy.json
SMART data from a healthy SATA SSD.
- **Source:** Samsung 860 EVO 500GB
- **Status:** Healthy drive with no errors
- **Use:** Testing SMART parser with good drive data

### smartctl_sata_failing.json
SMART data from a failing SATA HDD.
- **Source:** WDC WD5000AAKX 500GB
- **Status:** Drive with reallocated sectors
- **Use:** Testing failure detection and scoring

## Using Sample Data

All agent commands support `--use-sample` flag to use these sample files instead of requiring real hardware access:

```bash
# Test inventory without root
inspecta inventory --use-sample

# Test full run with sample data
inspecta run --mode quick --output ./test-output --use-sample
```

## Adding New Samples

When adding new sample data:

1. **Anonymize personal information** - Remove serial numbers, owner names, etc.
2. **Document the source** - Note device model, condition, and purpose
3. **Add to this README** - Update the documentation
4. **Use in tests** - Create corresponding test cases

## Data Privacy

All sample data has been anonymized:
- Serial numbers redacted or replaced with placeholder values
- Personal identifiers removed
- System-specific details generalized where appropriate

## License

Sample data is provided for testing and documentation purposes only.
Not for commercial redistribution.
