[CmdletBinding()]
param(
    [switch] $ApiOnly,
    [switch] $Lan
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$apiRoot = Join-Path $projectRoot 'apps\api'
$webRoot = Join-Path $projectRoot 'apps\web'
$python = Join-Path $apiRoot '.venv\Scripts\python.exe'
$nextCli = Join-Path $webRoot 'node_modules\next\dist\bin\next'
$stateDirectory = Join-Path $projectRoot '.local'
$stateFile = Join-Path $stateDirectory 'dev-services.json'
$apiOutputLog = Join-Path $stateDirectory 'api-dev.out.log'
$apiErrorLog = Join-Path $stateDirectory 'api-dev.err.log'
$webOutputLog = Join-Path $stateDirectory 'web-dev.out.log'
$webErrorLog = Join-Path $stateDirectory 'web-dev.err.log'
$listenHost = '127.0.0.1'
$lanIp = $null

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

if ($Lan) {
    $networkAddress = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
        Select-Object -First 1
    if (-not $networkAddress) { throw 'No private LAN IPv4 address was found. Connect to Wi-Fi or Ethernet first.' }
    $lanIp = $networkAddress.IPAddress
    $listenHost = '0.0.0.0'
}

Push-Location $apiRoot
try {
    & $python -m alembic -c alembic.ini upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Database migration failed. The API was not started." }
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
Remove-Item -LiteralPath $apiOutputLog, $apiErrorLog, $webOutputLog, $webErrorLog -Force -ErrorAction SilentlyContinue
$services = @()
$previousWebOrigin = $env:WEB_ORIGIN
$previousApiUrl = $env:NEXT_PUBLIC_API_BASE_URL
if ($Lan) {
    $env:WEB_ORIGIN = "http://${lanIp}:3000"
    $env:NEXT_PUBLIC_API_BASE_URL = "http://${lanIp}:8000"
}
$apiProcess = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'hookcut_api.main:app', '--host', $listenHost, '--port', '8000') -WorkingDirectory $apiRoot -RedirectStandardOutput $apiOutputLog -RedirectStandardError $apiErrorLog -PassThru
$services += [pscustomobject]@{ name = 'api'; pid = $apiProcess.Id; started_at_utc = $apiProcess.StartTime.ToUniversalTime().ToString('o') }

if (-not $ApiOnly) {
    $webProcess = Start-Process -FilePath 'node.exe' -ArgumentList @($nextCli, 'dev', '--hostname', $listenHost, '--port', '3000') -WorkingDirectory $webRoot -RedirectStandardOutput $webOutputLog -RedirectStandardError $webErrorLog -PassThru
    $services += [pscustomobject]@{ name = 'web'; pid = $webProcess.Id; started_at_utc = $webProcess.StartTime.ToUniversalTime().ToString('o') }
}
$env:WEB_ORIGIN = $previousWebOrigin
$env:NEXT_PUBLIC_API_BASE_URL = $previousApiUrl

@{ services = $services } | ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding utf8
if ($ApiOnly) {
    Write-Host 'HookCut API service started: http://127.0.0.1:8000 (logs: .local\api-dev.out.log)'
} elseif ($Lan) {
    Write-Host "HookCut LAN development services started. Open http://${lanIp}:3000 on a phone connected to the same Wi-Fi."
} else {
    Write-Host 'HookCut development services started. API: http://127.0.0.1:8000 | Web: http://127.0.0.1:3000 | Logs: .local\*-dev.*.log'
}
