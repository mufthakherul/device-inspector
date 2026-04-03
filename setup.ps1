# Device Inspector (Inspecta) Setup Script for Windows
#
# Usage:
#   .\setup.ps1
#   .\setup.ps1 -Mode prod
#   .\setup.ps1 -InstallTools
#   .\setup.ps1 -SkipTests
#   .\setup.ps1 -Help

param(
    [ValidateSet("dev", "prod")]
    [string]$Mode = "dev",

    [switch]$InstallTools,
    [switch]$SkipTests,
    [switch]$Verbose,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectRoot "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

function ShowHelp {
    Write-Host @"
Device Inspector Setup Script for Windows

Usage:
  .\setup.ps1 [Options]

Options:
  -Mode {dev|prod}      Setup mode (default: dev)
  -InstallTools         Install optional system diagnostics tools
  -SkipTests            Skip running test suite
  -Verbose              Show detailed output
  -Help                 Show this help message
"@
    exit 0
}

function WriteSection {
    param([string]$Title)
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "  $Title"
    Write-Host "============================================================"
    Write-Host ""
}

function WriteInfo {
    param([string]$Message)
    Write-Host "[INFO] $Message"
}

function WriteSuccess {
    param([string]$Message)
    Write-Host "[OK]   $Message" -ForegroundColor Green
}

function WriteWarn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function WriteFail {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Get-PythonCommand {
    WriteSection "Detecting Python"

    foreach ($cmd in @("python", "py")) {
        try {
            $version = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                WriteSuccess "Found Python via '$cmd': $version"
                return $cmd
            }
        }
        catch {
            # continue
        }
    }

    WriteFail "Python 3.11+ not found on PATH."
    WriteInfo "Install Python from https://www.python.org/downloads/"
    return $null
}

function Test-PythonVersion {
    param([string]$PythonCmd)

    try {
        $version = & $PythonCmd -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>&1
        $parts = ($version -join "") -split "\."

        if ($parts.Count -lt 2) {
            WriteFail "Unexpected Python version format: $version"
            return $false
        }

        $major = [int]$parts[0]
        $minor = [int]$parts[1]

        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            WriteFail "Python $version found, but 3.11+ required."
            return $false
        }

        WriteSuccess "Python $version is supported"
        return $true
    }
    catch {
        WriteFail "Failed to check Python version: $_"
        return $false
    }
}

function New-VirtualEnvironment {
    WriteSection "Setting Up Virtual Environment"

    if (Test-Path $VenvDir) {
        WriteInfo "venv already exists at $VenvDir"
        return $true
    }

    & $script:PythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        WriteFail "Failed to create virtual environment"
        return $false
    }

    WriteSuccess "Virtual environment created"
    return $true
}

function Install-Dependencies {
    param([string]$SetupMode)

    WriteSection "Installing Python Dependencies"

    & $VenvPip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        WriteFail "Failed to upgrade pip"
        return $false
    }

    $req = Join-Path $ProjectRoot "requirements.txt"
    if (Test-Path $req) {
        & $VenvPip install -r $req
        if ($LASTEXITCODE -ne 0) {
            WriteFail "Failed to install requirements.txt"
            return $false
        }
    }

    if ($SetupMode -eq "dev") {
        $opt = Join-Path $ProjectRoot "requirements-optional.txt"
        if (Test-Path $opt) {
            & $VenvPip install -r $opt
            if ($LASTEXITCODE -ne 0) {
                WriteWarn "Optional dependencies failed to install"
            }
        }
    }

    # best-effort editable install
    & $VenvPip install -e $ProjectRoot
    if ($LASTEXITCODE -ne 0) {
        WriteWarn "Editable install failed; continuing with module execution from repo root"
        WriteWarn "Use: $VenvPython -m agent.cli ..."
    }

    WriteSuccess "Dependencies installation completed"
    return $true
}

function Invoke-CodeChecks {
    WriteSection "Running Code Quality Checks"

    & $VenvPython -m black --check .
    if ($LASTEXITCODE -eq 0) { WriteSuccess "black check passed" }
    else { WriteWarn "black check found formatting issues" }

    & $VenvPython -m ruff check .
    if ($LASTEXITCODE -eq 0) { WriteSuccess "ruff check passed" }
    else { WriteWarn "ruff check found lint issues" }
}

function Invoke-Tests {
    WriteSection "Running Tests"

    if (-not (Test-Path (Join-Path $ProjectRoot "tests"))) {
        WriteWarn "tests/ directory not found"
        return $true
    }

    & $VenvPython -m pytest -q (Join-Path $ProjectRoot "tests")
    if ($LASTEXITCODE -eq 0) {
        WriteSuccess "Tests passed"
    }
    else {
        WriteWarn "Some tests failed (non-blocking for setup)"
    }

    return $true
}

function Invoke-SmokeTest {
    WriteSection "Running CLI Smoke Test"

    $outputDir = Join-Path $ProjectRoot "test-smoke"

    & $VenvPython -m agent.cli run --mode quick --output $outputDir --use-sample *> $null

    if (Test-Path (Join-Path $outputDir "report.json")) {
        WriteSuccess "CLI smoke test passed"
    }
    else {
        WriteWarn "CLI smoke test did not produce report.json"
    }

    return $true
}

function Install-SystemTools {
    WriteSection "Installing Optional System Tools"
    WriteInfo "Run in an elevated terminal for system package installs."
    WriteInfo "smartmontools: winget install -e --id smartmontools.smartmontools"
}

function Show-NextSteps {
    WriteSection "Setup Complete"

    Write-Host @"
Next Steps:

1) Activate virtual environment:
   & "$VenvDir\Scripts\Activate.ps1"

2) Run with sample data:
   $VenvPython -m agent.cli run --mode quick --output ./reports/test --use-sample

3) Run real hardware inspection:
   $VenvPython -m agent.cli run --mode quick --output ./reports/mydevice --require-hardware

4) Use launcher precheck:
   $VenvPython scripts/launch_inspecta.py --setup-only
   $VenvPython scripts/launch_inspecta.py --require-hardware --install-tools
"@
}

function Main {
    if ($Help) {
        ShowHelp
    }

    $script:PythonCmd = Get-PythonCommand
    if (-not $PythonCmd) { exit 1 }

    if (-not (Test-PythonVersion $PythonCmd)) { exit 1 }
    if (-not (New-VirtualEnvironment)) { exit 1 }
    if (-not (Install-Dependencies $Mode)) { exit 1 }

    Invoke-CodeChecks

    if (-not $SkipTests) {
        Invoke-Tests
        Invoke-SmokeTest
    }

    if ($InstallTools) {
        Install-SystemTools
    }

    Show-NextSteps
}

try {
    Main
}
catch {
    WriteFail "Fatal setup error: $_"
    exit 1
}
