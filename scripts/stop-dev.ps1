$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stateFile = Join-Path $projectRoot '.local\dev-services.json'

if (-not (Test-Path -LiteralPath $stateFile)) {
    Write-Host 'No HookCut development service state file exists. Nothing was stopped.'
    exit 0
}

$saved = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
foreach ($service in @($saved.services)) {
    $process = Get-Process -Id $service.pid -ErrorAction SilentlyContinue
    if ($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $service.started_at_utc) {
        Stop-Process -Id $service.pid
        Write-Host "Stopped HookCut $($service.name) service."
    } else {
        Write-Host "Skipped $($service.name): its tracked process is no longer the process that was started for this project."
    }
}
Remove-Item -LiteralPath $stateFile -Force
