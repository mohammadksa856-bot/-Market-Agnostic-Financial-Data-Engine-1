$ErrorActionPreference = "Stop"
$Project = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Project "output\local-relay-venv\Scripts\python.exe"
$Script = Join-Path $Project "scripts\windows_tadawul_relay.py"
$LogDir = Join-Path $Project "output\local-relay"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $Python)) {
    throw "Local relay virtual environment is missing: $Python"
}

& $Python $Script --batch-size 8 *>> (Join-Path $LogDir "scheduler.log")
exit $LASTEXITCODE
