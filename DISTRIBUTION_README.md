# Inspecta Device Inspector

**Version:** 0.1.0  
**Local-first device diagnostics for used laptops and PCs**

## Welcome!

Thank you for downloading Inspecta! This package contains everything you need to inspect a device's hardware health. **No installation or additional software required!**

## Quick Start

### 1. First Time? Try Sample Data

To see how Inspecta works without requiring administrator privileges:

**Windows:**
- Double-click `Run_Inspecta.bat`
- Wait a few seconds
- Check the `reports` folder for your report!

**macOS/Linux:**
- Open Terminal in this folder
- Run: `./run_inspecta.sh`
- Check the `reports` folder for your report!

### 2. Inspect Real Hardware

To inspect the actual device hardware:

**Windows:**
1. Right-click `Run_Hardware_Inspection.bat`
2. Select "Run as administrator"
3. Click "Yes" on the security prompt
4. Wait 2-10 minutes for inspection to complete
5. Find your report in the `reports` folder

**macOS/Linux:**
```bash
sudo ./run_inspecta.sh
```

## What You Get

After running an inspection, you'll find:

```
reports/
├── report.json              # Complete inspection report
└── artifacts/
    ├── agent.log           # Detailed execution log
    ├── smart_*.json        # Storage device health data
    └── ...                 # Additional diagnostic data
```

## Understanding Your Report

The `report.json` includes:

- **Overall Score** (0-100): Device health rating
- **Grade**: Excellent / Good / Fair / Poor
- **Device Info**: Vendor, model, serial number
- **Storage Health**: SMART data from all drives
- **Test Results**: Individual component checks

### Score Guide

- **90-100 (Excellent)**: Device is in great condition
- **75-89 (Good)**: Minor wear, suitable for most uses
- **50-74 (Fair)**: Some issues detected, repairs recommended
- **Below 50 (Poor)**: Significant problems, consider alternatives

## Advanced Usage

For command-line options:

**Windows:**
```cmd
inspecta.exe --help
inspecta.exe run --mode quick --output my-report --verbose
inspecta.exe inventory
```

**macOS/Linux:**
```bash
./inspecta --help
./inspecta run --mode quick --output my-report --verbose
./inspecta inventory
```

## Troubleshooting

### Windows: "Access Denied"
- Run as administrator (right-click → Run as administrator)

### Windows: "Windows protected your PC"
- Click "More info" → "Run anyway"
- This is safe - the software is open source

### macOS: "Cannot be opened because it is from an unidentified developer"
- Go to System Preferences → Security & Privacy
- Click "Open Anyway"
- Or run: `xattr -d com.apple.quarantine inspecta`

### "No storage devices found"
- Make sure you're running as administrator/root
- Check that hardware tools are accessible

### Still Having Issues?
- Check `QUICK_START.txt` for detailed troubleshooting
- Visit: https://github.com/mufthakherul/device-inspector
- Report bugs: https://github.com/mufthakherul/device-inspector/issues

## Privacy & Security

✅ **Local-first by default** - All data stays on your computer  
✅ **No internet connection required**  
✅ **No data collection or tracking**  
✅ **Open source** - Verify the code on GitHub  

You control your data. Reports are only shared if you choose to share them.

## System Requirements

- **Windows:** Windows 10 or later (64-bit)
- **macOS:** macOS 10.15 (Catalina) or later
- **Linux:** Ubuntu 20.04+ or equivalent
- **Disk Space:** 100 MB free
- **Privileges:** Administrator/root for hardware inspection

## What's Included in v0.1.0

✅ Device inventory (vendor, model, serial, BIOS)  
✅ Storage SMART health (SATA, NVMe, USB drives)  
✅ Multi-drive support  
✅ JSON reports with health scores  
✅ Detailed logging  
✅ Sample data for testing

### Coming in Future Versions

⏳ Battery health and cycle count  
⏳ CPU performance benchmarks  
⏳ Disk performance testing  
⏳ Memory testing  
⏳ PDF reports  
⏳ Thermal monitoring  

## Use Cases

**Buyers:** Run before purchasing a used device to verify condition  
**Sellers:** Provide reports to build trust and justify pricing  
**Technicians:** Quick diagnostics for device evaluation  
**Refurbishers:** Batch testing for inventory assessment  

## Documentation

📖 Full documentation: [README.md](README.md)  
🚀 Quick start: [QUICK_START.txt](QUICK_START.txt)  
📋 Project: https://github.com/mufthakherul/device-inspector  

## Support

Need help?
1. Check QUICK_START.txt for detailed instructions
2. Visit the GitHub repository for documentation
3. Open an issue if you find bugs
4. Join discussions for questions

## License

This software is provided for **non-commercial use** under a custom license.

✅ Free for personal use  
✅ Free for education  
✅ Free for research  
❌ Commercial use requires separate license  

See [LICENSE.txt](LICENSE.txt) for complete terms.

Commercial licensing: Contact the author via GitHub

## About

**Inspecta** is an open-source device inspection toolkit created to bring transparency to the used device market. Built with privacy and auditability as core principles.

**Author:** @mufthakherul  
**GitHub:** https://github.com/mufthakherul/device-inspector  
**Version:** 0.1.0  
**Released:** 2025-10-30  

---

**© 2025 mufthakherul**  
Thank you for using Inspecta!
