[CmdletBinding()]
param(
    [ValidateSet("Base", "CAD")]
    [string]$Profile = "CAD",
    [switch]$WithVision,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating project environment: $venvPath"
    & $Python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw "Could not create .venv. Install Python 3.12 and retry." }
}

& $venvPython -c "import sys; print('Python:', sys.version.split()[0]); print('Environment:', sys.executable)"
if ($LASTEXITCODE -ne 0) { throw "The project environment is unavailable. Check .venv." }

$requirementsFile = if ($Profile -eq "CAD") { "requirements-cad.txt" } else { "requirements.txt" }
Write-Host "Installing $Profile dependencies..."
$pipArgs = @("--disable-pip-version-check", "--timeout", "300", "--retries", "5")
& $venvPython -m pip install @pipArgs -r (Join-Path $projectRoot $requirementsFile)
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Check the pip error above; rerun this script to retry." }

if ($WithVision) {
    Write-Host "Installing the optional vision adapter..."
    & $venvPython -m pip install @pipArgs -r (Join-Path $projectRoot "requirements-vision.txt")
    if ($LASTEXITCODE -ne 0) { throw "Vision dependency installation failed. Check the pip error above." }
}

& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) { throw "Installed dependencies have conflicts. See pip check output above." }

Write-Host "Setup complete. Start the workbench with: .\start_local.ps1"
