$ErrorActionPreference = "Stop"
$Project = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Project "output\local-relay-venv\Scripts\python.exe"
$Script = Join-Path $Project "scripts\windows_tadawul_relay.py"
$LogDir = Join-Path $Project "output\local-relay"
$SshKey = Join-Path $env:USERPROFILE ".ssh\marefa-finengine-deploy"
$State = Join-Path $LogDir "codex-even-state.json"
$Log = Join-Path $LogDir "codex-even.jsonl"
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
& $Python $Script --stage archive --shard even --financial-statements-only `
    --batch-size 20 --max-documents 200 --max-discovered-per-source 200 `
    --timeout-seconds 30 --crawl-issuer-site --state $State --log $Log `
    --ssh-key $SshKey *>> (Join-Path $LogDir "scheduler.log")
exit $LASTEXITCODE
