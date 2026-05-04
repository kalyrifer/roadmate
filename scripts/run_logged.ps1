<#
.SYNOPSIS
    Runs an arbitrary command with its working directory and mirrors stdout +
    stderr to both the current PowerShell console and a log file.

.DESCRIPTION
    Used by run_with_tunnel.bat to spawn the backend (uvicorn) and the
    frontend (vite) so that:
      * the user still sees live output in the spawned window
      * a copy of every line is appended to logs\<service>.log so the parent
        bat can dump it on failure (e.g. backend never bound :8000)
      * the window stays open via -NoExit if the child crashes — no more
        windows that disappear before you can read the traceback

.EXAMPLE
    powershell -NoExit -NoProfile -ExecutionPolicy Bypass `
        -File scripts\run_logged.ps1 `
        -LogPath D:\RoadMate\logs\backend.log `
        -WorkDir D:\RoadMate `
        -- D:\RoadMate\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
#>
param(
    [Parameter(Mandatory = $true)][string]$LogPath,
    [Parameter(Mandatory = $true)][string]$WorkDir,
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Cmd
)

if (-not (Test-Path $WorkDir)) {
    Write-Error "Working dir does not exist: $WorkDir"
    exit 1
}
Set-Location $WorkDir

$logDir = Split-Path -Parent $LogPath
if ($logDir -and -not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Clean previous log so the parent bat can `type` only the current run.
"" | Out-File -FilePath $LogPath -Encoding utf8

$exe = $Cmd[0]
$exeArgs = @()
if ($Cmd.Count -gt 1) {
    $exeArgs = $Cmd[1..($Cmd.Count - 1)]
}

Write-Host "[run_logged] working dir: $WorkDir"
Write-Host "[run_logged] log file:    $LogPath"
Write-Host "[run_logged] launching:   $exe $($exeArgs -join ' ')"
Write-Host ""

# 2>&1 merges stderr into stdout so Tee-Object captures both.
& $exe @exeArgs 2>&1 | Tee-Object -FilePath $LogPath -Append

$rc = $LASTEXITCODE
Write-Host ""
Write-Host "[run_logged] process exited with code $rc"
exit $rc
