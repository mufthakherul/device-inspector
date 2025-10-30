# Inspecta v1 Distribution Guide

**Version:** 0.1.0  
**Last Updated:** 2025-10-30

## Overview

This document describes how to distribute and use the standalone Inspecta v1 CLI packages for Windows and macOS. Users can run the tool with a **single click** without installing Python, dependencies, or any additional services.

## Distribution Packages

Inspecta v1 is distributed as zip files containing everything needed:

- **Windows:** `inspecta-0.1.0-windows.zip` (~20-25 MB)
- **macOS:** `inspecta-0.1.0-macos.zip` (~20-25 MB)
- **Linux:** `inspecta-0.1.0-linux.zip` (~15-20 MB)

## What's Inside Each Package

Each distribution package contains:

```
inspecta-0.1.0-{platform}/
├── inspecta[.exe]              # Main executable (no installation needed!)
├── Run_Inspecta.*              # Double-click launcher (uses sample data)
├── Run_Hardware_Inspection.*   # Hardware inspection launcher
├── README.md                   # Full documentation
├── LICENSE.txt                 # License information
├── CHANGELOG.md                # Version history
├── QUICK_START.txt            # Quick start guide
└── samples/                    # Sample data for testing
    ├── tool_outputs/           # Sample device outputs
    └── artifacts/              # Sample report artifacts
```

## Installation for End Users

### Step 1: Download

Download the appropriate package for your operating system:
- Windows users: `inspecta-0.1.0-windows.zip`
- macOS users: `inspecta-0.1.0-macos.zip`

### Step 2: Extract

**Windows:**
1. Right-click the downloaded zip file
2. Select "Extract All..."
3. Choose a destination folder
4. Click "Extract"

**macOS:**
1. Double-click the downloaded zip file
2. It will automatically extract to the Downloads folder

### Step 3: Run

**No installation required!** Just double-click the launcher:

**Windows:** Double-click `Run_Inspecta.bat`  
**macOS:** Double-click `run_inspecta.sh` (or open Terminal and run it)

That's it! The tool will run with sample data to show you how it works.

## Usage Modes

### Mode 1: Test with Sample Data (Recommended First)

**Purpose:** See how the tool works without requiring administrator privileges.

**Windows:**
```cmd
Double-click: Run_Inspecta.bat
```

**macOS/Linux:**
```bash
./run_inspecta.sh
```

This runs the inspection using pre-recorded sample data and creates a report in the `reports/` folder.

**No administrator/root privileges required!**

### Mode 2: Inspect Real Hardware

**Purpose:** Inspect the actual hardware of the device.

**Windows:**
1. Right-click `Run_Hardware_Inspection.bat`
2. Select "Run as administrator"
3. Click "Yes" on the UAC prompt
4. Wait for inspection to complete (2-10 minutes)

**macOS/Linux:**
```bash
sudo ./run_inspecta.sh
```

This inspects the real hardware and creates a detailed report with actual device data.

**Administrator/root privileges required** to access hardware information (SMART data, BIOS info, etc.)

### Mode 3: Command Line (Advanced Users)

For advanced usage, you can run the executable directly:

**Windows:**
```cmd
# Show help
inspecta.exe --help

# Run with sample data
inspecta.exe run --mode quick --output ./my-report --use-sample

# Inspect real hardware (run as administrator)
inspecta.exe run --mode quick --output ./my-report --verbose

# Check device inventory
inspecta.exe inventory --use-sample
```

**macOS/Linux:**
```bash
# Show help
./inspecta --help

# Run with sample data
./inspecta run --mode quick --output ./my-report --use-sample

# Inspect real hardware
sudo ./inspecta run --mode quick --output ./my-report --verbose

# Check device inventory
sudo ./inspecta inventory
```

## Understanding the Output

After running an inspection, you'll find:

```
reports/
├── report.json                 # Main inspection report
└── artifacts/
    ├── agent.log              # Detailed execution log
    ├── smart_*.json           # SMART data from storage devices
    ├── memtest.log            # Memory test results (placeholder in v1)
    └── sensors.csv            # Temperature/fan data (placeholder in v1)
```

### Report Structure

The `report.json` contains:

- **Device Information:** Vendor, model, serial number, BIOS version
- **Overall Score:** 0-100 health score
- **Grade:** Excellent/Good/Fair/Poor
- **Test Results:** Individual test outcomes
- **Storage Health:** SMART data for all drives
- **Timestamps:** When the inspection was performed

Example report excerpt:
```json
{
  "report_version": "1.0",
  "generated_at": "2025-10-30T15:40:00Z",
  "agent_version": "0.1.0",
  "device": {
    "vendor": "Dell Inc.",
    "model": "XPS 15 9560",
    "serial": "ABC12345"
  },
  "summary": {
    "overall_score": 83,
    "grade": "Good",
    "recommendation": "Suitable for general use"
  }
}
```

## System Requirements

### Windows
- **OS:** Windows 10 or later (64-bit)
- **Disk Space:** 100 MB free
- **Privileges:** Administrator (for real hardware inspection)

### macOS
- **OS:** macOS 10.15 (Catalina) or later
- **Disk Space:** 100 MB free
- **Privileges:** Root/sudo (for real hardware inspection)

### Linux
- **OS:** Ubuntu 20.04+ or equivalent
- **Disk Space:** 100 MB free
- **Privileges:** Root/sudo (for real hardware inspection)
- **Optional:** smartmontools, dmidecode (for full hardware access)

## Platform-Specific Notes

### Windows

**Administrator Privileges:**
To run with real hardware inspection, you must "Run as administrator":
1. Right-click the launcher or executable
2. Select "Run as administrator"
3. Click "Yes" on the UAC prompt

**Antivirus Warnings:**
Some antivirus software may flag PyInstaller executables as suspicious. This is a false positive. The executable is safe and open source. You can:
1. Add an exception in your antivirus
2. Build from source yourself (see BUILDING.md)
3. Check the code on GitHub: https://github.com/mufthakherul/device-inspector

**Windows Defender SmartScreen:**
If you see "Windows protected your PC":
1. Click "More info"
2. Click "Run anyway"

### macOS

**Gatekeeper / Security Warnings:**
macOS may show "cannot be opened because it is from an unidentified developer":

**Solution 1 - UI Method:**
1. Go to System Preferences → Security & Privacy → General
2. Click "Open Anyway" next to the blocked app
3. Click "Open" when prompted again

**Solution 2 - Command Line:**
```bash
xattr -d com.apple.quarantine inspecta
```

**Root Privileges:**
Use `sudo` to run hardware inspections:
```bash
sudo ./run_inspecta.sh
```

Enter your password when prompted.

### Linux

**Making Scripts Executable:**
If the launcher won't run, make it executable:
```bash
chmod +x run_inspecta.sh
chmod +x inspecta
```

**Optional Dependencies:**
For full hardware access, install:
```bash
sudo apt install smartmontools dmidecode
```

Most modern Linux distributions include these by default.

## Troubleshooting

### "Access Denied" or Permission Errors

**Cause:** The tool needs administrator/root privileges to access hardware.

**Solution:**
- Windows: Run as administrator (right-click → Run as administrator)
- macOS/Linux: Use sudo (`sudo ./run_inspecta.sh`)
- Or: Use `--use-sample` flag for testing without privileges

### "No Storage Devices Found"

**Cause:** SMART tools not accessible or insufficient privileges.

**Solution:**
- Make sure you're running as administrator/root
- Windows: SMART may not work on some NVMe drives (driver issue)
- macOS: May need to approve disk access in Security settings

### Slow Startup (1-2 seconds)

**Cause:** PyInstaller executables need to unpack on first run.

**Solution:** This is normal. Subsequent runs may be faster.

### Reports Folder Not Created

**Cause:** Insufficient write permissions in the current directory.

**Solution:**
- Run from a folder where you have write permissions
- Don't run from system directories like C:\Windows or /System
- Or specify a different output: `--output ~/Desktop/my-report`

### macOS: "App is Damaged and Can't Be Opened"

**Cause:** Gatekeeper quarantine on downloaded files.

**Solution:**
```bash
xattr -d com.apple.quarantine inspecta
```

Or download and extract from a trusted source.

## Distribution Best Practices

### For Sellers/Technicians

**When selling a used device:**
1. Run Inspecta on the device
2. Include the report.json with the listing
3. Offer to re-run in buyer's presence
4. Package the zip file with the device

**When buying a used device:**
1. Bring Inspecta on a USB drive
2. Run it on-site before purchase
3. Review the report before paying
4. Keep the report for records

### For Refurbishers

**Batch processing:**
1. Extract Inspecta to a central location
2. Create a batch script to run on each device
3. Save reports with device serial numbers
4. Archive reports for warranty/support

Example batch script (Windows):
```cmd
@echo off
for /d %%d in (C:\Devices\*) do (
    cd %%d
    C:\Inspecta\inspecta.exe run --output %%d\report --verbose
)
```

### For Marketplaces

**Integration options:**
1. Provide Inspecta as a download link to sellers
2. Accept report.json uploads as verification
3. Display health scores in listings
4. Require inspection for high-value items

## Privacy and Data Handling

### What Data is Collected?

Inspecta collects:
- Hardware identifiers (serial numbers, model numbers)
- BIOS/firmware versions
- Storage device health data (SMART)
- System timestamps
- Performance metrics

### Where is Data Stored?

**By default: Locally only!**
- Reports stay on your computer
- No data is sent to any server
- No internet connection required

### Sharing Reports

Reports can be shared if you choose:
- Email the report.json
- Upload to your preferred storage
- Print or screenshot for records

**Recommendation:** Review the report before sharing and redact any sensitive information if needed.

## Support and Resources

### Documentation
- Full README: [README.md](../README.md)
- Build Guide: [BUILDING.md](BUILDING.md)
- Project Status: [PROJECT_STATUS.md](../PROJECT_STATUS.md)

### Online Resources
- GitHub: https://github.com/mufthakherul/device-inspector
- Report Issues: https://github.com/mufthakherul/device-inspector/issues
- Discussions: https://github.com/mufthakherul/device-inspector/discussions

### Getting Help

1. Check QUICK_START.txt in the package
2. Read the troubleshooting section above
3. Search existing GitHub issues
4. Open a new issue with details

### Contributing

Inspecta is open source! Contributions welcome:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Licensing

Inspecta is provided under a custom non-commercial license. See [LICENSE.txt](../LICENSE.txt) for details.

**Summary:**
- ✅ Free for personal use
- ✅ Free for non-commercial use
- ✅ Free for education and research
- ❌ Commercial use requires separate license

Contact the author for commercial licensing inquiries.

## Version History

**v0.1.0 (2025-10-30)** - Initial v1 Release
- ✅ Quick-mode inspection
- ✅ Device inventory detection
- ✅ SMART health checking (SATA, NVMe, USB drives)
- ✅ Structured JSON reports
- ✅ Standalone executables (Windows, macOS, Linux)
- ✅ Single-click launchers
- ✅ Sample data for testing
- ⏳ Battery health (coming in v0.2.0)
- ⏳ CPU benchmarking (coming in v0.2.0)
- ⏳ PDF reports (coming in v0.2.0)

See [CHANGELOG.md](../CHANGELOG.md) for complete history.

## Future Plans

**v0.2.0 - Enhanced Diagnostics:**
- Battery health and cycle count
- CPU performance benchmarking
- Disk performance testing (fio)
- PDF report generation

**v0.3.0 - Advanced Features:**
- Memory testing
- Thermal monitoring
- GPU detection and health
- Profile-based scoring (Office, Developer, Gamer)

**v1.0.0 - Production Ready:**
- Full bootable diagnostics (live ISO)
- Comprehensive hardware coverage
- Advanced reporting
- API for integrations

See [ROADMAP.md](../ROADMAP.md) for detailed plans.

---

**© 2025 mufthakherul**  
**Version:** 0.1.0  
**License:** Custom Non-Commercial  
**GitHub:** https://github.com/mufthakherul/device-inspector
