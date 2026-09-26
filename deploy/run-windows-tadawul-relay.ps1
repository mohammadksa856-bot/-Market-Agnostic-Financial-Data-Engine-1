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
# Let the relay use the tracked registry.  At startup it regenerates that file
# atomically from the complete market seed, companies.json and reviewed source
# registry batches, so newly researched issuer pages enter the next run without
# copying an untracked snapshot by hand.
# `all` is a durable two-stage run.  Raw documents reach local and AWS
# content-addressed storage before the independent enqueue stage touches
# SQLite.  A DB failure therefore remains in outbox.json for the next run and
# never causes a second download or upload.
& $Python $Script --stage all --batch-size 20 --max-documents 40 --timeout-seconds 20 --crawl-issuer-site --ssh-key $SshKey *>> (Join-Path $LogDir "scheduler.log")
exit $LASTEXITCODE
