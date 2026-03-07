param(
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $PSScriptRoot "run"
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$stopScript = Join-Path $PSScriptRoot "stop-servers.ps1"
if (Test-Path $stopScript) {
    & $stopScript -Quiet
}

foreach ($cmd in @("uv", "npm")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "Required command '$cmd' was not found in PATH."
    }
}

if ($InstallDeps) {
    Push-Location $backendDir
    try {
        uv sync
    }
    finally {
        Pop-Location
    }

    Push-Location $frontendDir
    try {
        npm install
    }
    finally {
        Pop-Location
    }
}

$backendOut = Join-Path $runDir "backend.out.log"
$backendErr = Join-Path $runDir "backend.err.log"
$frontendOut = Join-Path $runDir "frontend.out.log"
$frontendErr = Join-Path $runDir "frontend.err.log"

$backendProcess = Start-Process -FilePath "uv" -ArgumentList @("run", "python", "scripts/run.py") -WorkingDirectory $backendDir -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList @("run", "dev") -WorkingDirectory $frontendDir -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru

$backendProcess.Id | Set-Content -Path (Join-Path $runDir "backend.pid")
$frontendProcess.Id | Set-Content -Path (Join-Path $runDir "frontend.pid")

Write-Output "Backend started (PID: $($backendProcess.Id))"
Write-Output "Frontend started (PID: $($frontendProcess.Id))"
Write-Output "Logs:"
Write-Output "  $backendOut"
Write-Output "  $backendErr"
Write-Output "  $frontendOut"
Write-Output "  $frontendErr"
Write-Output "Backend loads env from backend/.env and backend/.env.local"
Write-Output "Frontend loads env from frontend/.env and frontend/.env.local"
