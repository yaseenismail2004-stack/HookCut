[CmdletBinding()]
param(
    [switch] $ApiOnly
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$apiRoot = Join-Path $projectRoot 'apps\api'
$webRoot = Join-Path $projectRoot 'apps\web'
$python = Join-Path $apiRoot '.venv\Scripts\python.exe'
$nextCli = Join-Path $webRoot 'node_modules\next\dist\bin\next'
$stateDirectory = Join-Path $projectRoot '.local'
$stateFile = Join-Path $stateDirectory 'dev-services.json'

function Test-TrackedProcess {
    param([pscustomobject] $Service)
    $process = Get-Process -Id $Service.pid -ErrorAction SilentlyContinue
    if (-not $process) { return $false }
    return $process.StartTime.ToUniversalTime().ToString('o') -eq $Service.started_at_utc
}

if (Test-Path -LiteralPath $stateFile) {
    $saved = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
    $active = @($saved.services | Where-Object { Test-TrackedProcess $_ })
    if ($active.Count -gt 0) {
        throw "HookCut development services are already running. Use scripts/stop-dev.ps1 before starting another set."
    }
    Remove-Item -LiteralPath $stateFile -Force
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend virtual environment is missing. Create apps/api/.venv and install backend dependencies first."
}
if (-not $ApiOnly -and -not (Test-Path -LiteralPath $nextCli)) {
    throw "Frontend dependencies are missing. Run npm --prefix apps/web install first."
}

New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$services = @()
$apiProcess = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'hookcut_api.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $apiRoot -PassThru
$services += [pscustomobject]@{ name = 'api'; pid = $apiProcess.Id; started_at_utc = $apiProcess.StartTime.ToUniversalTime().ToString('o') }

if (-not $ApiOnly) {
    $webProcess = Start-Process -FilePath 'node.exe' -ArgumentList @($nextCli, 'dev', '--hostname', '127.0.0.1', '--port', '3000') -WorkingDirectory $webRoot -PassThru
    $services += [pscustomobject]@{ name = 'web'; pid = $webProcess.Id; started_at_utc = $webProcess.StartTime.ToUniversalTime().ToString('o') }
}

@{ services = $services } | ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding utf8
if ($ApiOnly) {
    Write-Host 'HookCut API service started: http://127.0.0.1:8000'
} else {
    Write-Host 'HookCut development services started. API: http://127.0.0.1:8000 | Web: http://127.0.0.1:3000'
}
