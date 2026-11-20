[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8766
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Project environment not found. Run .\setup_env.ps1 first."
}

& $venvPython -c "import dotenv, jsonschema"
if ($LASTEXITCODE -ne 0) { throw "Base dependencies are missing. Run .\setup_env.ps1 -Profile Base." }

& $venvPython -c "import importlib.util; print('CAD: ' + ('available - preview and STEP enabled' if importlib.util.find_spec('cadquery') else 'not installed - parameter editing and validation only')); print('Vision CLI: ' + ('available' if importlib.util.find_spec('zhipuai') else 'not installed (optional)'))"
if ($LASTEXITCODE -ne 0) { throw "Could not inspect the project environment." }

Write-Host "Open http://127.0.0.1:$Port in your browser."
Write-Host "Press Ctrl+C here to stop the local server."
& $venvPython (Join-Path $projectRoot "ui_server.py") --port $Port
if ($LASTEXITCODE -ne 0) { throw "The local server stopped with exit code $LASTEXITCODE. Check whether port $Port is already in use." }
