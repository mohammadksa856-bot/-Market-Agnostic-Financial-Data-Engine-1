$ErrorActionPreference = "Stop"
$Project = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Project "output\local-relay-venv\Scripts\python.exe"
$Script = Join-Path $Project "scripts\windows_tadawul_relay.py"
$LogDir = Join-Path $Project "output\local-relay"
$SshKey = Join-Path $LogDir "deploy-key"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $Python)) {
    throw "Local relay virtual environment is missing: $Python"
}
if (-not (Test-Path $SshKey)) {
    throw "Local relay SSH key is missing: $SshKey"
}
& $Python $Script --batch-size 8 --max-documents 10 --crawl-issuer-site --ssh-key $SshKey *>> (Join-Path $LogDir "scheduler.log")
exit $LASTEXITCODE
