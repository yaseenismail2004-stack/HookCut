[CmdletBinding()]
param(
    [switch] $ApproveGeminiRequest,
    [string] $RetryJobId
)

$ErrorActionPreference = 'Stop'

if (-not $ApproveGeminiRequest) {
    throw 'Pass -ApproveGeminiRequest only after a human explicitly approves one extracted-audio request to Gemini.'
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$apiRoot = Join-Path $projectRoot 'apps\api'
$python = Join-Path $apiRoot '.venv\Scripts\python.exe'
$localDirectory = Join-Path $projectRoot '.local'
$apiLog = Join-Path $localDirectory 'gemini-live-api.out.log'
$apiErrorLog = Join-Path $localDirectory 'gemini-live-api.err.log'
$apiProcess = $null
$jobId = $null
$videoId = $null

function Get-LocalJson {
    param([string] $Uri)
    return Invoke-RestMethod -Uri $Uri -TimeoutSec 15
}

function Wait-ForTerminalJob {
    param([string] $Id, [int] $TimeoutSeconds = 180)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Seconds 1
        $current = Get-LocalJson -Uri ("http://127.0.0.1:8000/api/jobs/{0}" -f $Id)
    } while ($current.state -notin @('completed', 'failed', 'cancelled') -and (Get-Date) -lt $deadline)
    return $current
}

try {
    New-Item -ItemType Directory -Path $localDirectory -Force | Out-Null
    Remove-Item -LiteralPath $apiLog, $apiErrorLog -Force -ErrorAction SilentlyContinue
    $apiProcess = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'hookcut_api.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $apiRoot -RedirectStandardOutput $apiLog -RedirectStandardError $apiErrorLog -PassThru

    $healthy = $false
    for ($attempt = 0; $attempt -lt 20 -and -not $healthy; $attempt++) {
        Start-Sleep -Milliseconds 500
        try {
            $healthy = (Get-LocalJson -Uri 'http://127.0.0.1:8000/api/health').status -eq 'ok'
        } catch {
            # The API can still be starting; the bounded retry is intentional.
        }
    }
    if (-not $healthy) { throw 'The temporary API did not pass its health check.' }

    $capabilities = Get-LocalJson -Uri 'http://127.0.0.1:8000/api/system/capabilities'
    if (-not $capabilities.configuration.gemini_transcription_provider_available -or -not $capabilities.worker_running) {
        throw 'Gemini or the local worker is not ready.'
    }

    if ($RetryJobId) {
        $current = Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:8000/api/jobs/{0}/retry" -f $RetryJobId) -TimeoutSec 15
        $jobId = $current.id
        $videoId = $current.video_id
    } else {
        $video = @(Get-LocalJson -Uri 'http://127.0.0.1:8000/api/videos' | Where-Object { $_.status -eq 'ready' } | Select-Object -First 1)[0]
        if (-not $video) { throw 'No ready source is available.' }
        $createBody = @{ language_mode = 'auto'; provider = 'gemini'; approve_estimated_cost = $false } | ConvertTo-Json
        $job = Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:8000/api/videos/{0}/transcription-jobs" -f $video.id) -ContentType 'application/json' -Body $createBody -TimeoutSec 15
        $jobId = $job.id
        $videoId = $video.id
        $approvalDeadline = (Get-Date).AddSeconds(75)
        do {
            Start-Sleep -Milliseconds 750
            $current = Get-LocalJson -Uri ("http://127.0.0.1:8000/api/jobs/{0}" -f $jobId)
        } while ($current.state -notin @('awaiting_cost_approval', 'failed', 'cancelled', 'completed') -and (Get-Date) -lt $approvalDeadline)
        if ($current.state -ne 'awaiting_cost_approval') { throw "Job did not reach the cost gate: $($current.state)." }
        $current = Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:8000/api/jobs/{0}/approve-cost" -f $jobId) -TimeoutSec 15
    }
    $current = Wait-ForTerminalJob -Id $jobId

    $result = [ordered]@{
        job_id = $current.id
        state = $current.state
        stage = $current.current_stage
        error_code = $current.error_code
        estimated_cost_usd = $current.estimated_cost_usd
    }
    if ($current.state -eq 'completed') {
        $transcript = Get-LocalJson -Uri ("http://127.0.0.1:8000/api/videos/{0}/transcript" -f $videoId)
        $result.transcript_retrieved = $true
        $result.provider = $transcript.provider
        $result.model = $transcript.model
        $result.detected_language = $transcript.detected_language
        $result.segment_count = @($transcript.segments).Count
        $result.word_count = @($transcript.words).Count
    }
    [pscustomobject] $result | ConvertTo-Json -Compress
}
catch {
    if ($jobId -and $apiProcess -and -not $apiProcess.HasExited) {
        try {
            $active = Get-LocalJson -Uri ("http://127.0.0.1:8000/api/jobs/{0}" -f $jobId)
            if ($active.state -notin @('completed', 'failed', 'cancelled')) {
                Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:8000/api/jobs/{0}/cancel" -f $jobId) -TimeoutSec 15 | Out-Null
                Wait-ForTerminalJob -Id $jobId -TimeoutSeconds 150 | Out-Null
            }
        } catch {
            # Preserve the original bounded-verification error without printing private provider data.
        }
    }
    throw
}
finally {
    if ($apiProcess -and -not $apiProcess.HasExited) {
        Stop-Process -Id $apiProcess.Id
    }
}
