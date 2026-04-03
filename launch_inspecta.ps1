param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "py"
}

$launcher = Join-Path $ProjectRoot "scripts\launch_inspecta.py"

& $python $launcher @ArgsList
$code = $LASTEXITCODE
exit $code
