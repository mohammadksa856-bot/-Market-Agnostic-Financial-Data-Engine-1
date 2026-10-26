<#
.SYNOPSIS
  Download the MAREFA AWS recovery over HTTPS, verify every SHA256, and test-open the restored files.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\Receive-MarefaRecovery.ps1 -ListFile "$HOME\Downloads\download-list.tsv"

  Re-run with a fresh download-list.tsv when links expire: verified files are skipped, partial files resume.
  The report (verify-report.json) contains no links or credentials; send it back for the inventory.
#>
param(
    [Parameter(Mandatory = $true)][string]$ListFile,
    [string]$Dest = (Join-Path $env:USERPROFILE "Documents\Marefa-AWS-Recovery"),
    [switch]$ExtractFilesystems,
    [switch]$SkipArchiveListing
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 3

function Write-Step($text) { Write-Host ("[{0:HH:mm:ss}] {1}" -f (Get-Date), $text) }

# Native tools run with EAP=Continue: Windows PowerShell 5.1 turns their stderr into terminating errors otherwise.
function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$ErrorLog = "") {
    $previous = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try {
        if ($ErrorLog) { $out = & $Exe @Arguments 2>> $ErrorLog }
        else { $out = & $Exe @Arguments 2>&1 | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } }
        return [pscustomobject]@{ Code = $LASTEXITCODE; Output = @($out) }
    } finally { $ErrorActionPreference = $previous }
}

function Read-Magic([string]$Path, [int]$Count) {
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $buffer = New-Object byte[] $Count
        $read = $stream.Read($buffer, 0, $Count)
        return [System.Text.Encoding]::ASCII.GetString($buffer, 0, $read)
    } finally { $stream.Dispose() }
}

if (-not (Test-Path $ListFile)) { throw "List file not found: $ListFile" }
foreach ($tool in @("curl.exe", "tar.exe")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "$tool is required (built into Windows 10 1803 and later)" }
}

$rows = @(Get-Content -LiteralPath $ListFile -Encoding UTF8 | Select-Object -Skip 1 | Where-Object { $_.Trim() } | ForEach-Object {
    $f = $_ -split "`t", 4
    [pscustomobject]@{ Path = $f[0]; Size = [int64]$f[1]; Sha256 = $f[2].ToLower(); Url = $f[3] }
})
if ($rows.Count -eq 0) { throw "The list is empty" }
$total = [int64]($rows | Measure-Object -Property Size -Sum).Sum

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$objects = Join-Path $Dest "aws-objects"
$extracted = Join-Path $Dest "extracted"
New-Item -ItemType Directory -Force -Path $objects, $extracted | Out-Null

# ---------------------------------------------------------------- free space
$drive = Get-PSDrive -Name ((Resolve-Path $Dest).Path.Substring(0, 1))
$needed = [int64]($total * 1.05)
if ($ExtractFilesystems) { $needed = [int64]($total * 4) }   # compressed archives expand several times
Write-Step ("{0} files, {1:N2} GiB to download; {2:N2} GiB free on {3}:" -f $rows.Count, ($total / 1GB), ($drive.Free / 1GB), $drive.Name)
if ($drive.Free -lt $needed) {
    throw ("Not enough space: need {0:N2} GiB, have {1:N2} GiB. Free space or pass -Dest on another drive." -f ($needed / 1GB), ($drive.Free / 1GB))
}

# ---------------------------------------------------------------- download + verify
$results = @()
foreach ($row in $rows) {
    $target = Join-Path $objects ($row.Path -replace "/", "\")
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    $status = "pending"
    if ((Test-Path -LiteralPath $target) -and (Get-Item -LiteralPath $target).Length -eq $row.Size -and
        (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLower() -eq $row.Sha256) {
        $status = "verified (already present)"
    } else {
        Write-Step ("download {0} ({1:N2} GiB)" -f $row.Path, ($row.Size / 1GB))
        $part = "$target.part"
        $run = Invoke-Native "curl.exe" @("--fail", "--location", "--silent", "--show-error", "--retry", "5", "--retry-delay", "5",
                                          "--continue-at", "-", "--output", $part, $row.Url) (Join-Path $Dest "download-errors.log")
        if ($run.Code -eq 33) {  # server refused to resume: start the file again
            Remove-Item -Force -LiteralPath $part -ErrorAction SilentlyContinue
            $run = Invoke-Native "curl.exe" @("--fail", "--location", "--silent", "--show-error", "--retry", "5", "--retry-delay", "5",
                                              "--output", $part, $row.Url) (Join-Path $Dest "download-errors.log")
        }
        if ($run.Code -ne 0) {
            $status = "download failed (curl $($run.Code)); links may have expired: run presign again and re-run"
        } else {
            $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $part).Hash.ToLower()
            if ($hash -eq $row.Sha256 -and (Get-Item -LiteralPath $part).Length -eq $row.Size) {
                Move-Item -Force -LiteralPath $part -Destination $target
                $status = "verified"
            } else {
                Move-Item -Force -LiteralPath $part -Destination "$target.bad"
                $status = "SHA256 MISMATCH (kept as .bad, re-run to download again)"
            }
        }
    }
    Write-Step "  $status"
    $results += [pscustomobject]@{ path = $row.Path; size = $row.Size; sha256 = $row.Sha256; status = $status }
}
$verified = @($results | Where-Object { $_.status -like "verified*" })
$verified | ForEach-Object { "{0}  {1}" -f $_.sha256, $_.path } | Set-Content -Encoding ascii (Join-Path $Dest "SHA256SUMS.txt")

# ---------------------------------------------------------------- test opening
$script:tests = @()
function Add-Test($name, $ok, $detail) { $script:tests += [pscustomobject]@{ test = $name; ok = [bool]$ok; detail = "$detail" } }
$python = Get-Command python -ErrorAction SilentlyContinue
$pgRestore = Get-Command pg_restore -ErrorAction SilentlyContinue
$tarLog = Join-Path $Dest "tar-errors.log"

foreach ($item in $verified) {
    $file = Join-Path $objects ($item.path -replace "/", "\")
    $isArchive = $item.path -like "*.tar.gz"
    if ($isArchive -and $item.path -like "databases/*") {
        $out = Join-Path $extracted (($item.path -replace "/", "\") -replace "\.tar\.gz$", "")
        New-Item -ItemType Directory -Force -Path $out | Out-Null
        $run = Invoke-Native "tar.exe" @("-xzf", $file, "-C", $out) $tarLog
        Add-Test "extract $($item.path)" ($run.Code -eq 0) $out
    } elseif ($isArchive -and $item.path -like "filesystems/*" -and -not $SkipArchiveListing) {
        Write-Step "reading $($item.path) end to end"
        $run = Invoke-Native "tar.exe" @("-tzf", $file)
        Add-Test "read archive $($item.path)" ($run.Code -eq 0 -and $run.Output.Count -gt 0) "$($run.Output.Count) entries"
        if ($ExtractFilesystems) {
            $out = Join-Path $extracted (($item.path -replace "/", "\") -replace "\.tar\.gz$", "")
            New-Item -ItemType Directory -Force -Path $out | Out-Null
            $run = Invoke-Native "tar.exe" @("-xzf", $file, "-C", $out) $tarLog
            Add-Test "extract $($item.path) (exit $($run.Code))" $true "Linux symlinks and special files may be skipped on Windows; see tar-errors.log"
        }
    }
    if ($item.path -like "*.dump") {
        if ($pgRestore) {
            $run = Invoke-Native $pgRestore.Source @("--list", $file)
            Add-Test "pg_restore --list $($item.path)" ($run.Code -eq 0) "$($run.Output.Count) TOC entries"
        } else {
            Add-Test "PostgreSQL dump header $($item.path)" ((Read-Magic $file 5) -eq "PGDMP") "pg_restore not installed: header check only"
        }
    }
    if ($item.path -like "secrets/*") {
        Add-Test "secrets bundle $($item.path)" ((Read-Magic $file 1).Length -eq 1) "encrypted (AES256); passphrase stays in AWS SSM Parameter Store"
    }
}
$sqliteCheck = "import sqlite3,sys`nc=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True)`nprint(c.execute('pragma quick_check').fetchone()[0], c.execute(`"select count(*) from sqlite_master where type='table'`").fetchone()[0])"
Get-ChildItem -Path $extracted -Recurse -File -Filter "*.consistent.sqlite3" -ErrorAction SilentlyContinue | ForEach-Object {
    $db = $_.FullName
    if ($python) {
        $run = Invoke-Native $python.Source @("-c", $sqliteCheck, $db)
        $check = ($run.Output -join " ")
        Add-Test "open SQLite $($_.Name)" ($run.Code -eq 0 -and $check -like "ok *") "quick_check and tables: $check"
    } else {
        Add-Test "SQLite header $($_.Name)" ((Read-Magic $db 15) -eq "SQLite format 3") "python not installed: header check only"
    }
}

# ---------------------------------------------------------------- report (no links, no credentials)
$report = [pscustomobject]@{
    created = (Get-Date).ToString("o"); destination = $Dest
    files_expected = $rows.Count; files_verified = $verified.Count
    bytes_expected = $total; bytes_verified = [int64]($verified | Measure-Object -Property size -Sum).Sum
    free_space_after_gib = [math]::Round((Get-PSDrive -Name $drive.Name).Free / 1GB, 2)
    objects = $results; tests = $script:tests
}
$report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Dest "verify-report.json")
$failed = @($results | Where-Object { $_.status -notlike "verified*" }).Count + @($script:tests | Where-Object { -not $_.ok }).Count
Write-Step ("verified {0}/{1} files; {2} problem(s). Report: {3}" -f $verified.Count, $rows.Count, $failed, (Join-Path $Dest "verify-report.json"))
if ($failed) { exit 1 }
