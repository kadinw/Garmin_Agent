# Rebuilds GarminAgentSetup.exe from scripts/setup_wizard.py
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    py -3.13 -m venv (Join-Path $Root ".venv")
}

& $Python -m pip install --upgrade pyinstaller
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed --name GarminAgentSetup `
    --paths $Root `
    --hidden-import garmin_agent.gui `
    --hidden-import garmin_agent.prefs `
    --hidden-import garmin_agent.paths `
    --hidden-import garmin_agent.windows_setup `
    --distpath $Root --workpath (Join-Path $Root "build") `
    --specpath (Join-Path $Root "build") `
    (Join-Path $Root "scripts\setup_wizard.py")

Write-Host "Created $Root\GarminAgentSetup.exe"
