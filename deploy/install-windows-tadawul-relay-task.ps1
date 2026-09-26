$ErrorActionPreference = "Stop"

$TaskName = "MarefaTadawulRelay"
$Runner = Join-Path $PSScriptRoot "run-windows-tadawul-relay.ps1"
$Project = Split-Path -Parent $PSScriptRoot
$SourceSshKey = Join-Path $Project "output\github-actions-finengine-deploy"
$SshDir = Join-Path $env:USERPROFILE ".ssh"
$SshKey = Join-Path $SshDir "marefa-finengine-deploy"
$InstallLog = Join-Path $Project "output\local-relay\task-install.log"
$Account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $InstallLog) | Out-Null
Start-Transcript -Path $InstallLog -Force
try {

if (-not (Test-Path -LiteralPath $Runner)) {
    throw "Relay runner is missing: $Runner"
}
if (-not (Test-Path -LiteralPath $SourceSshKey)) {
    throw "Relay SSH key is missing: $SourceSshKey"
}

# Windows OpenSSH refuses a private key that the scheduled-task identity cannot
# read, or that inherits broad ACLs.  The installer runs elevated once and
# makes the key readable only by the interactive owner (plus SYSTEM).
& takeown.exe /F $SourceSshKey | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Could not take ownership of source SSH key" }
& icacls.exe $SourceSshKey /inheritance:r /grant:r "${Account}:(R)" /grant:r "SYSTEM:(F)" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Could not read source SSH key" }
New-Item -ItemType Directory -Force -Path $SshDir | Out-Null
Copy-Item -LiteralPath $SourceSshKey -Destination $SshKey -Force
& icacls.exe $SshKey /inheritance:r /grant:r "${Account}:(R)" /grant:r "SYSTEM:(F)" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Could not secure SSH key permissions" }

# Stop a previous detached relay process before replacing/restarting the task.
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like "*windows_tadawul_relay.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$PowerShell = Join-Path $PSHOME "powershell.exe"
if (-not (Test-Path -LiteralPath $PowerShell)) {
    $PowerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
}

$QuotedRunner = '"' + $Runner + '"'
$Action = New-ScheduledTaskAction `
    -Execute $PowerShell `
    -Argument "-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File $QuotedRunner"
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 15)
$Settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $Account `
    -LogonType Interactive `
    -RunLevel Limited

Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Archive historical Saudi financial statements (Codex even shard, raw only)." `
    -Force | Out-Null

Enable-ScheduledTask -TaskName $TaskName | Out-Null
Start-ScheduledTask -TaskName $TaskName

# Also start one detached run directly from this elevated, non-sandboxed
# installer.  This avoids waiting for Task Scheduler's first trigger and gives
# an observable process/log immediately; later runs remain scheduler-owned.
$DirectArguments = "-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`""
$DirectRun = Start-Process `
    -FilePath $PowerShell `
    -ArgumentList $DirectArguments `
    -WindowStyle Hidden `
    -PassThru
Set-Content -LiteralPath (Join-Path $Project "output\local-relay\direct-run.pid") `
    -Value $DirectRun.Id `
    -Encoding ascii

Start-Sleep -Seconds 2
$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host ""
Write-Host "Installed and started: $TaskName" -ForegroundColor Green
Write-Host "State: $($Task.State)"
Write-Host "Next run: $($Info.NextRunTime)"
Write-Host "Direct run PID: $($DirectRun.Id)"
Write-Host "Log: $(Join-Path (Split-Path -Parent $PSScriptRoot) 'output\local-relay\scheduler.log')"
}
finally {
    Stop-Transcript
}
