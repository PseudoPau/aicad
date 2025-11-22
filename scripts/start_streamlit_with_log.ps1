$env:PYTHONPATH = '.'
$python = 'D:/miniconda3/envs/aicad_hackathon/python.exe'
$args = @('-m','streamlit','run','frontend/app.py')
$logDir = "output/analysis"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir "streamlit_run.log"
# Start Streamlit and tee output to log file (pass args as array to avoid module parsing issues)
# Prevent PowerShell from throwing NativeCommandError when the child process returns a non-zero exit code
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'SilentlyContinue'
try {
	& $python @args 2>&1 | Tee-Object -FilePath $logFile
} finally {
	$ErrorActionPreference = $prevEAP
}
