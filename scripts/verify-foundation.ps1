$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$apiRoot = Join-Path $projectRoot 'apps\api'
$webRoot = Join-Path $projectRoot 'apps\web'
$python = Join-Path $apiRoot '.venv\Scripts\python.exe'
$nextCli = Join-Path $webRoot 'node_modules\next\dist\bin\next'
$apiProcess = $null
$webProcess = $null

function Invoke-Checked {
    param(
        [string] $FilePath,
        [string[]] $Arguments,
        [string] $Description
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Description failed with exit code $LASTEXITCODE." }
}

try {
    Invoke-Checked -FilePath 'npm' -Arguments @('--prefix', $webRoot, 'run', 'lint') -Description 'Frontend lint'
    Invoke-Checked -FilePath 'npm' -Arguments @('--prefix', $webRoot, 'run', 'typecheck') -Description 'Frontend type check'
    Invoke-Checked -FilePath 'npm' -Arguments @('--prefix', $webRoot, 'run', 'test') -Description 'Frontend tests'
    Invoke-Checked -FilePath 'npm' -Arguments @('--prefix', $webRoot, 'run', 'build') -Description 'Frontend production build'
    Invoke-Checked -FilePath $python -Arguments @('-m', 'compileall', '-q', (Join-Path $apiRoot 'src')) -Description 'Python syntax check'
    Invoke-Checked -FilePath $python -Arguments @('-c', "import hookcut_api.main; print('backend import ok')") -Description 'Backend import check'
    Invoke-Checked -FilePath $python -Arguments @('-m', 'mypy', (Join-Path $apiRoot 'src')) -Description 'Backend type check'
    Invoke-Checked -FilePath $python -Arguments @('-m', 'pytest', (Join-Path $apiRoot 'tests')) -Description 'Backend tests'

    $apiProcess = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'hookcut_api.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $apiRoot -PassThru
    Start-Sleep -Seconds 2
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 10
    if ($health.status -ne 'ok' -or $health.service -ne 'hookcut-api') { throw 'Health endpoint returned an unexpected response.' }
    $capabilities = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/system/capabilities' -TimeoutSec 10
    if (-not $capabilities.python.available -or -not $capabilities.storage.directories_ready) { throw 'Capabilities endpoint returned an unexpected response.' }

    $webProcess = Start-Process -FilePath 'node.exe' -ArgumentList @($nextCli, 'start', '--hostname', '127.0.0.1', '--port', '3000') -WorkingDirectory $webRoot -PassThru
    Start-Sleep -Seconds 2
    $web = Invoke-WebRequest -Uri 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 10
    if ($web.StatusCode -ne 200 -or $web.Content -notmatch 'HookCut') { throw 'Frontend startup smoke test failed.' }
    Write-Host 'Foundation verification passed.'
}
finally {
    if ($webProcess -and -not $webProcess.HasExited) { Stop-Process -Id $webProcess.Id }
    if ($apiProcess -and -not $apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id }
}
