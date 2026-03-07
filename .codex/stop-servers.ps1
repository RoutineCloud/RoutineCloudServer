param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$runDir = Join-Path $PSScriptRoot "run"
$pidFiles = @(
    @{ Name = "backend"; Path = Join-Path $runDir "backend.pid" },
    @{ Name = "frontend"; Path = Join-Path $runDir "frontend.pid" }
)

foreach ($entry in $pidFiles) {
    if (-not (Test-Path $entry.Path)) {
        continue
    }

    $pidValue = (Get-Content -Path $entry.Path -Raw).Trim()
    if ($pidValue -match "^\d+$") {
        $process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $process.Id -Force
            if (-not $Quiet) {
                Write-Output "Stopped $($entry.Name) (PID: $($process.Id))"
            }
        }
    }

    Remove-Item -Path $entry.Path -Force
}
