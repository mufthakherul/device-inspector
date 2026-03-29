# Device Inspector (Inspecta) Setup Script for Windows
#
# Provides automated setup with Python environment, dependencies, and optional tools
#
# Usage:
#   .\setup.ps1                    # Full dev setup
#   .\setup.ps1 -Mode prod         # Production setup (minimal)
#   .\setup.ps1 -InstallTools      # Install optional system tools
#   .\setup.ps1 -Help              # Show help
#
# Requires PowerShell 5.0 or higher
# Run as administrator for system tool installation

param(
    [ValidateSet("dev", "prod")]
    [string]$Mode = "dev",
    
    [switch]$InstallTools,
    [switch]$SkipTests,
    [switch]$Verbose,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Configuration
# ============================================================================

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectRoot "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

# Color codes
$Colors = @{
    Red    = "`e[31m"
    Green  = "`e[32m"
    Yellow = "`e[33m"
    Blue   = "`e[34m"
    Reset  = "`e[0m"
}

# ============================================================================
# Help & Logging
# ============================================================================

function Show-Help {
    Write-Host @"
Device Inspector Setup Script for Windows

Usage:
  .\setup.ps1 [Options]

Options:
  -Mode {dev|prod}      Setup mode (default: dev)
                        dev:  Full setup with tests and optional tools
                        prod: Minimal production setup
  
  -InstallTools         Install optional system diagnostics tools
  
  -SkipTests            Skip running test suite
  
  -Verbose              Show detailed output
  
  -Help                 Show this help message

Examples:
  .\setup.ps1                      # Full development setup
  .\setup.ps1 -Mode prod           # Production setup
  .\setup.ps1 -InstallTools        # Install system tools
  .\setup.ps1 -SkipTests           # Skip tests

Requirements:
  - PowerShell 5.0 or higher
  - Administrator privileges (for optional tool installation)
  - Python 3.11 or higher on PATH

"@
    exit 0
}

function Log-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  $Title" -ForegroundColor Blue
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
}

function Log-Info {
    param([string]$Message)
    Write-Host "•  $Message" -ForegroundColor Blue
}

function Log-Success {
    param([string]$Message)
    Write-Host "✓  $Message" -ForegroundColor Green
}

function Log-Warn {
    param([string]$Message)
    Write-Host "⚠  $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "✗  $Message" -ForegroundColor Red
}

# ============================================================================
# Python Detection
# ============================================================================

function Get-PythonCommand {
    Log-Section "Detecting Python Installation"
    
    foreach ($cmd in @("python3", "python")) {
        try {
            $version = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Log-Success "Found: $version"
                return $cmd
            }
        }
        catch {
            # Continue to next candidate
        }
    }
    
    Log-Error "Python 3.11+ not found on PATH"
    Show-Python-Install-Help
    return $null
}

function Test-PythonVersion {
    param([string]$PythonCmd)
    
    try {
        $output = & $PythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
        $version = $output -join ""
        $parts = $version -split '\.'
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Log-Error "Python $version found, but 3.11+ required"
            Show-Python-Install-Help
            return $false
        }
        
        Log-Success "Python $version ✓"
        return $true
    }
    catch {
        Log-Error "Failed to check Python version"
        return $false
    }
}

function Show-Python-Install-Help {
    Log-Section "Python Installation Required"
    Log-Info "1. Visit: https://www.python.org/downloads/"
    Log-Info "2. Download Python 3.12 or 3.11 (Windows installer)"
    Log-Info "3. Run installer and CHECK 'Add Python to PATH'"
    Log-Info "4. Or use: winget install Python.Python.3.12"
    Log-Info "5. Restart PowerShell after installation"
}

# ============================================================================
# Virtual Environment
# ============================================================================

function New-VirtualEnvironment {
    Log-Section "Setting Up Virtual Environment"
    
    if (Test-Path $VenvDir) {
        Log-Info "venv already exists at $VenvDir"
        return $true
    }
    
    try {
        Log-Info "Creating virtual environment..."
        & $script:PythonCmd -m venv $VenvDir
        
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Failed to create virtual environment"
            return $false
        }
        
        Log-Success "Virtual environment created ✓"
        return $true
    }
    catch {
        Log-Error "Exception: $_"
        return $false
    }
}

# ============================================================================
# Dependencies
# ============================================================================

function Install-Dependencies {
    param([string]$SetupMode)
    
    Log-Section "Installing Python Dependencies"
    
    try {
        # Upgrade pip
        Log-Info "Upgrading pip..."
        & $VenvPip install --upgrade pip --quiet
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Failed to upgrade pip"
            return $false
        }
        
        # Install main requirements
        $reqFile = Join-Path $ProjectRoot "requirements.txt"
        if (Test-Path $reqFile) {
            Log-Info "Installing requirements.txt..."
            & $VenvPip install -r $reqFile --quiet
            if ($LASTEXITCODE -ne 0) {
                Log-Error "Failed to install dependencies"
                return $false
            }
        }
        
        # Install optional dependencies for dev mode
        if ($SetupMode -eq "dev") {
            $optReqFile = Join-Path $ProjectRoot "requirements-optional.txt"
            if (Test-Path $optReqFile) {
                Log-Info "Installing optional dependencies..."
                & $VenvPip install -r $optReqFile --quiet 2>$null
            }
        }
        
        # Install project in editable mode
        Log-Info "Installing project in editable mode..."
        & $VenvPip install -e $ProjectRoot --quiet
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Failed to install project"
            return $false
        }
        
        Log-Success "Dependencies installed ✓"
        return $true
    }
    catch {
        Log-Error "Exception: $_"
        return $false
    }
}

# ============================================================================
# Code Quality
# ============================================================================

function Invoke-CodeChecks {
    Log-Section "Running Code Quality Checks"
    
    # Black check
    Log-Info "Running Black format check..."
    & $VenvPython -m black --check . --quiet 2>$null
    if ($LASTEXITCODE -eq 0) {
        Log-Success "Black check passed ✓"
    }
    else {
        Log-Warn "Black check found formatting issues (non-critical)"
    }
    
    # Ruff check
    Log-Info "Running Ruff linter..."
    & $VenvPython -m ruff check . --quiet 2>$null
    if ($LASTEXITCODE -eq 0) {
        Log-Success "Ruff check passed ✓"
    }
    else {
        Log-Warn "Ruff check found issues (non-critical)"
    }
}

# ============================================================================
# Testing
# ============================================================================

function Invoke-Tests {
    Log-Section "Running Test Suite"
    
    if (-not (Test-Path (Join-Path $ProjectRoot "tests"))) {
        Log-Warn "Tests directory not found"
        return $true
    }
    
    try {
        Log-Info "Running pytest..."
        & $VenvPython -m pytest -q (Join-Path $ProjectRoot "tests") 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Log-Success "All tests passed ✓"
            return $true
        }
        else {
            Log-Warn "Some tests failed (non-critical)"
            return $true
        }
    }
    catch {
        Log-Warn "Failed to run tests: $_"
        return $true
    }
}

function Invoke-SmokeTest {
    Log-Section "Running CLI Smoke Test"
    
    $outputDir = Join-Path $ProjectRoot "test-smoke"
    
    try {
        Log-Info "Testing: inspecta run --mode quick --use-sample"
        
        & $VenvPython -m agent.cli run `
            --mode quick `
            --output $outputDir `
            --use-sample `
            2>$null | Out-Null
        
        $reportPath = Join-Path $outputDir "report.json"
        if (Test-Path $reportPath) {
            Log-Success "CLI smoke test passed ✓"
            Log-Info "Report generated: $reportPath"
            return $true
        }
    }
    catch {
        Log-Warn "CLI smoke test did not produce expected output"
    }
    
    return $true
}

# ============================================================================
# System Tools
# ============================================================================

function Install-SystemTools {
    Log-Section "Installing System Diagnostics Tools (Optional)"
    
    if (-not (Test-Administrator)) {
        Log-Warn "Not running as administrator - skipping system tool installation"
        Log-Info "To install tools, run PowerShell as administrator"
        return $true
    }
    
    Log-Info "Windows detected - optional tools:"
    Log-Info "SmartMonTools: winget install -e --id Argonaut.SmartMonTools"
    Log-Info "Or download from: https://www.smartmontools.org/wiki/Download"
    
    return $true
}

function Test-Administrator {
    try {
        $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole("Administrators")
    }
    catch {
        return $false
    }
}

# ============================================================================
# Next Steps
# ============================================================================

function Show-NextSteps {
    param([string]$SetupMode)
    
    $activateCmd = "$VenvDir\Scripts\Activate.ps1"
    
    Log-Section "Setup Complete!"
    
    Write-Host @"

Next Steps:

1. Activate Virtual Environment:
   & "$activateCmd"

2. Run inspecta with sample data (no admin needed):
   $VenvPython -m agent.cli run --mode quick --output ./reports/test --use-sample

3. Run real hardware inspection (requires admin):
   # Run PowerShell as administrator, then:
   $VenvPython -m agent.cli run --mode quick --output ./reports/mydevice

4. Check device inventory:
   $VenvPython -m agent.cli inventory --use-sample

5. View documentation:
   - Developer Guide: docs/DEV_SETUP.md
   - Architecture: docs/ARCHITECTURE.md
   - Contributing: CONTRIBUTING.md

6. Running tests:
   $VenvPython -m pytest -v

7. Code formatting:
   $VenvPython -m black .
   $VenvPython -m ruff check --fix .

For more details, see: README.md
Repository: https://github.com/mufthakherul/device-inspector

Happy developing! 🚀

"@
}

# ============================================================================
# Main Setup
# ============================================================================

function Main {
    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║   DEVICE-INSPECTOR (INSPECTA) SETUP WIZARD                   ║
║   Cross-Platform Project Initialization                      ║
╚══════════════════════════════════════════════════════════════╝

"@
    
    # Check arguments
    if ($Help) {
        Show-Help
    }
    
    # Detect Python
    $script:PythonCmd = Get-PythonCommand
    if (-not $PythonCmd) {
        exit 1
    }
    
    # Check version
    if (-not (Test-PythonVersion $PythonCmd)) {
        exit 1
    }
    
    # Create venv
    if (-not (New-VirtualEnvironment)) {
        exit 1
    }
    
    # Install dependencies
    if (-not (Install-Dependencies $Mode)) {
        exit 1
    }
    
    # Code checks
    Invoke-CodeChecks
    
    # Tests (unless skipped)
    if (-not $SkipTests) {
        Invoke-Tests
        Invoke-SmokeTest
    }
    
    # System tools (optional)
    if ($InstallTools) {
        Install-SystemTools
    }
    
    # Summary
    Show-NextSteps $Mode
}

# Run setup
try {
    Main
}
catch {
    Log-Error "Fatal error: $_"
    exit 1
}
