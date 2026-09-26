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
# The market-wide foundation pass is deliberately raw-only.  Extraction and
# database enqueue consume the durable outbox later, independently, so neither
# reader failures nor SQLite can slow or invalidate source collection.
& $Python $Script --stage archive --batch-size 20 --max-documents 40 --timeout-seconds 20 --crawl-issuer-site --ssh-key $SshKey *>> (Join-Path $LogDir "scheduler.log")
exit $LASTEXITCODE
