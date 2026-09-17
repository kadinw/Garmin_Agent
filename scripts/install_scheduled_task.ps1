# Installs a Windows Scheduled Task that emails Garmin data once a day.
# Run from PowerShell:  powershell -ExecutionPolicy Bypass -File scripts\install_scheduled_task.ps1

param(
    [string]$Time = "07:00",
    [string]$TaskName = "Garmin Agent Daily Report",
    [switch]$SkipDeps
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Launcher = Join-Path $Root "scripts\run_daily.bat"
$Requirements = Join-Path $Root "requirements.txt"

Write-Host "Project root: $Root"

if (-not (Test-Path $VenvPython)) {
    if ($SkipDeps) {
        throw "The program is not installed yet. Click Save and turn on the daily email first."
    }
    Write-Host "Creating Python virtual environment..."
    py -3.13 -m venv (Join-Path $Root ".venv")
    if (-not (Test-Path $VenvPython)) {
        python -m venv (Join-Path $Root ".venv")
    }
}

if (-not $SkipDeps) {
    Write-Host "Installing Python dependencies..."
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r $Requirements
}

$Action = New-ScheduledTaskAction -Execute $Launcher -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "Scheduled task '$TaskName' will run daily at $Time."
Write-Host "Run once interactively first so Garmin tokens can be saved:"
Write-Host "  $VenvPython $Root\run_daily.py"
