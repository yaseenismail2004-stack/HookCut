[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$results = [System.Collections.Generic.List[object]]::new()
$script:ffmpegPath = $null
$script:ffprobePath = $null
$script:hasCpuH264 = $false
$script:hasAac = $false

function Add-Result {
    param(
        [ValidateSet('PASS', 'WARNING', 'FAIL')] [string] $Status,
        [ValidateSet('CRITICAL', 'IMPORTANT', 'OPTIONAL')] [string] $Class,
        [string] $Check,
        [string] $Detail
    )

    $results.Add([pscustomobject]@{ Status = $Status; Class = $Class; Check = $Check; Detail = $Detail })
    Write-Host ('[{0}] [{1}] {2}: {3}' -f $Status, $Class, $Check, $Detail)
}

function Find-Executable {
    param([string[]] $Names)
    foreach ($name in $Names) {
        $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command) { return $command.Source }
    }
    return $null
}

function Invoke-Text {
    param([string] $Executable, [string[]] $Arguments)
    try {
        $output = & $Executable @Arguments 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) { return $output.Trim() }
    } catch { }
    return $null
}

function Test-ProjectPath {
    param([string] $Path)
    return $Path.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)
}

Write-Host "AI UGC Clipper environment validation"
Write-Host "Project path is intentionally not printed."

# 1-2. Operating system, architecture, and PowerShell.
$arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
try {
    $os = Get-CimInstance Win32_OperatingSystem
    Add-Result 'PASS' 'IMPORTANT' 'Windows version and architecture' ("{0}; {1}" -f $os.Caption, $arch)
} catch {
    Add-Result 'WARNING' 'IMPORTANT' 'Windows version and architecture' ("CIM query unavailable; fallback reports {0}; {1}" -f [System.Environment]::OSVersion.VersionString, $arch)
}
Add-Result 'PASS' 'IMPORTANT' 'PowerShell version' $PSVersionTable.PSVersion.ToString()

# 3-6. Node, npm, Python, and pip.
$nodePath = Find-Executable @('node.exe')
if ($nodePath) { Add-Result 'PASS' 'CRITICAL' 'Node.js' (Invoke-Text $nodePath @('--version')) } else { Add-Result 'FAIL' 'CRITICAL' 'Node.js' 'Not found. Install Node.js LTS: winget install OpenJS.NodeJS.LTS' }

$npmPath = Find-Executable @('npm.cmd', 'npm.exe')
if ($npmPath) { Add-Result 'PASS' 'CRITICAL' 'npm' (Invoke-Text $npmPath @('--version')) } else { Add-Result 'FAIL' 'CRITICAL' 'npm' 'Not found. Install Node.js LTS (includes npm): winget install OpenJS.NodeJS.LTS' }

$pythonPath = Find-Executable @('python.exe')
$pythonArgs = @('--version')
$pythonVersion = if ($pythonPath) { Invoke-Text $pythonPath $pythonArgs } else { $null }
if (-not $pythonVersion) {
    $pythonPath = Find-Executable @('py.exe')
    $pythonArgs = @('-3', '--version')
    $pythonVersion = if ($pythonPath) { Invoke-Text $pythonPath $pythonArgs } else { $null }
}
if ($pythonPath -and $pythonVersion) {
    Add-Result 'PASS' 'CRITICAL' 'Python' $pythonVersion
    $pipArgs = if ([System.IO.Path]::GetFileName($pythonPath).ToLowerInvariant() -eq 'py.exe') { @('-3', '-m', 'pip', '--version') } else { @('-m', 'pip', '--version') }
    $pipVersion = Invoke-Text $pythonPath $pipArgs
    if ($pipVersion) { Add-Result 'PASS' 'CRITICAL' 'pip' $pipVersion } else { Add-Result 'FAIL' 'CRITICAL' 'pip' 'Unavailable for the discovered Python. Install Python with pip: winget install Python.Python.3.12' }
} else {
    Add-Result 'FAIL' 'CRITICAL' 'Python' 'Neither python nor py is available. Install Python: winget install Python.Python.3.12'
    Add-Result 'FAIL' 'CRITICAL' 'pip' 'Python is unavailable. Install Python with pip: winget install Python.Python.3.12'
}

# 7-9. Git repository and identity.
$gitPath = Find-Executable @('git.exe')
if ($gitPath) {
    Add-Result 'PASS' 'IMPORTANT' 'Git' (Invoke-Text $gitPath @('--version'))
    $gitStatus = Invoke-Text $gitPath @('-c', "safe.directory=$projectRoot", 'status', '--porcelain')
    if ($null -ne $gitStatus) { Add-Result 'PASS' 'IMPORTANT' 'Git repository status' $(if ($gitStatus) { 'Repository has uncommitted changes.' } else { 'Repository is clean.' }) } else { Add-Result 'FAIL' 'IMPORTANT' 'Git repository status' 'Unable to read repository status.' }
    $gitName = Invoke-Text $gitPath @('-c', "safe.directory=$projectRoot", 'config', '--get', 'user.name')
    $gitEmail = Invoke-Text $gitPath @('-c', "safe.directory=$projectRoot", 'config', '--get', 'user.email')
    if ($gitName -and $gitEmail) { Add-Result 'PASS' 'IMPORTANT' 'Git identity' 'user.name and user.email are configured.' } else { Add-Result 'WARNING' 'IMPORTANT' 'Git identity' 'Missing user.name or user.email. Configure repository-local identity before committing; do not change global settings.' }
} else {
    Add-Result 'FAIL' 'IMPORTANT' 'Git' 'Not found. Install Git for Windows: winget install Git.Git'
    Add-Result 'FAIL' 'IMPORTANT' 'Git repository status' 'Git is unavailable.'
    Add-Result 'WARNING' 'IMPORTANT' 'Git identity' 'Git is unavailable.'
}

# 10-14. FFmpeg/ffprobe, codecs, filters, and encoders.
$script:ffmpegPath = Find-Executable @('ffmpeg.exe')
$script:ffprobePath = Find-Executable @('ffprobe.exe')
if ($script:ffmpegPath) {
    Add-Result 'PASS' 'CRITICAL' 'FFmpeg' ((Invoke-Text $script:ffmpegPath @('-version')).Split("`n")[0])
    $encoders = Invoke-Text $script:ffmpegPath @('-hide_banner', '-encoders')
    $filters = Invoke-Text $script:ffmpegPath @('-hide_banner', '-filters')
    $script:hasCpuH264 = [bool]($encoders -match '(?m)^\s*V.*\blibx264\b')
    $script:hasAac = [bool]($encoders -match '(?m)^\s*A.*\baac\b')
    if ($script:hasCpuH264) { Add-Result 'PASS' 'CRITICAL' 'CPU H.264 encoder' 'libx264 is available.' } else { Add-Result 'FAIL' 'CRITICAL' 'CPU H.264 encoder' 'libx264 is unavailable. Install a full FFmpeg build: winget install Gyan.FFmpeg' }
    if ($script:hasAac) { Add-Result 'PASS' 'CRITICAL' 'AAC encoder' 'Native AAC encoding is available.' } else { Add-Result 'FAIL' 'CRITICAL' 'AAC encoder' 'AAC encoding is unavailable. Install a full FFmpeg build: winget install Gyan.FFmpeg' }
    $filterChecks = @{
        'subtitles filter' = '\bsubtitles\b'; 'ASS subtitles filter' = '\bass\b'; 'scale filter' = '\bscale\b';
        'crop filter' = '\bcrop\b'; 'overlay filter' = '\boverlay\b'; 'blur filter' = '\b(boxblur|gblur|avgblur)\b'
    }
    foreach ($entry in $filterChecks.GetEnumerator()) {
        if ($filters -match $entry.Value) { Add-Result 'PASS' 'IMPORTANT' ("FFmpeg {0}" -f $entry.Key) 'Available.' } else { Add-Result 'WARNING' 'IMPORTANT' ("FFmpeg {0}" -f $entry.Key) 'Unavailable; subtitle or reframing capability may be reduced. Install a full FFmpeg build: winget install Gyan.FFmpeg' }
    }
    $hardware = @{'NVENC' = '\bh264_nvenc\b'; 'Intel Quick Sync' = '\bh264_qsv\b'; 'AMD AMF' = '\bh264_amf\b'}
    foreach ($entry in $hardware.GetEnumerator()) {
        if ($encoders -match $entry.Value) { Add-Result 'PASS' 'OPTIONAL' ("Hardware encoder {0}" -f $entry.Key) 'Detected.' } else { Add-Result 'WARNING' 'OPTIONAL' ("Hardware encoder {0}" -f $entry.Key) 'Not detected; CPU fallback remains required.' }
    }
} else {
    Add-Result 'FAIL' 'CRITICAL' 'FFmpeg' 'Not found. Install FFmpeg: winget install Gyan.FFmpeg'
    Add-Result 'FAIL' 'CRITICAL' 'CPU H.264 encoder' 'Cannot inspect without FFmpeg.'
    Add-Result 'FAIL' 'CRITICAL' 'AAC encoder' 'Cannot inspect without FFmpeg.'
    foreach ($filterName in @('subtitles filter', 'ASS subtitles filter', 'scale filter', 'crop filter', 'overlay filter', 'blur filter')) {
        Add-Result 'WARNING' 'IMPORTANT' ("FFmpeg {0}" -f $filterName) 'Cannot inspect without FFmpeg. Install a full FFmpeg build: winget install Gyan.FFmpeg'
    }
    foreach ($encoderName in @('NVENC', 'Intel Quick Sync', 'AMD AMF')) {
        Add-Result 'WARNING' 'OPTIONAL' ("Hardware encoder {0}" -f $encoderName) 'Cannot inspect without FFmpeg.'
    }
}
if ($script:ffprobePath) { Add-Result 'PASS' 'CRITICAL' 'ffprobe' ((Invoke-Text $script:ffprobePath @('-version')).Split("`n")[0]) } else { Add-Result 'FAIL' 'CRITICAL' 'ffprobe' 'Not found. Install FFmpeg (includes ffprobe): winget install Gyan.FFmpeg' }

# 15-18. Disk, safe write, long paths, and environment conflicts.
$driveName = [System.IO.Path]::GetPathRoot($projectRoot).Substring(0, 1)
$drive = Get-PSDrive -Name $driveName
$freeGb = [Math]::Round($drive.Free / 1GB, 2)
if ($freeGb -ge 20) { Add-Result 'PASS' 'CRITICAL' 'Project-drive free space' "$freeGb GB free (20 GB minimum)." } else { Add-Result 'FAIL' 'CRITICAL' 'Project-drive free space' "$freeGb GB free; at least 20 GB is required for 4 GB sources and renders." }

$tempDirectory = Join-Path $projectRoot (Join-Path 'work' ("environment-validation-" + [Guid]::NewGuid().ToString('N')))
try {
    if (-not (Test-ProjectPath $tempDirectory)) { throw 'Temporary validation directory escaped project root.' }
    New-Item -ItemType Directory -Path $tempDirectory -Force | Out-Null
    $testFile = Join-Path $tempDirectory 'write-test.txt'
    [System.IO.File]::WriteAllText($testFile, 'environment validation')
    if (-not (Test-Path -LiteralPath $testFile)) { throw 'Test file was not created.' }
    Remove-Item -LiteralPath $testFile -Force
    Add-Result 'PASS' 'CRITICAL' 'Project write permission and safe temporary-file cleanup' 'Created and deleted a test file inside the project-only validation directory.'
} catch {
    Add-Result 'FAIL' 'CRITICAL' 'Project write permission and safe temporary-file cleanup' $_.Exception.Message
} finally {
    if ((Test-Path -LiteralPath $tempDirectory) -and (Test-ProjectPath $tempDirectory)) { Remove-Item -LiteralPath $tempDirectory -Recurse -Force -ErrorAction SilentlyContinue }
}

$longPaths = Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name LongPathsEnabled -ErrorAction SilentlyContinue
if ($longPaths.LongPathsEnabled -eq 1) { Add-Result 'PASS' 'OPTIONAL' 'Windows long paths' 'Enabled.' } else { Add-Result 'WARNING' 'OPTIONAL' 'Windows long paths' 'Disabled or unavailable; keep project, media, and temporary paths short.' }

$envWarnings = [System.Collections.Generic.List[string]]::new()
if ($env:PYTHONHOME -and -not (Test-Path -LiteralPath $env:PYTHONHOME)) { $envWarnings.Add('PYTHONHOME points to a missing path.') }
if ($env:VIRTUAL_ENV -and $env:CONDA_PREFIX) { $envWarnings.Add('Both VIRTUAL_ENV and CONDA_PREFIX are set.') }
foreach ($variable in @('FFMPEG_BINARY', 'FFPROBE_BINARY')) { if ((Get-Item "Env:$variable" -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath (Get-Item "Env:$variable").Value)) { $envWarnings.Add("$variable points to a missing path.") } }
if ($envWarnings.Count) { Add-Result 'WARNING' 'IMPORTANT' 'Conflicting environment variables' ($envWarnings -join ' ') } else { Add-Result 'PASS' 'IMPORTANT' 'Conflicting environment variables' 'No known Python or FFmpeg environment conflicts detected.' }

# 19-21. Secrets, optional YouTube helper, and cloud connectivity.
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) { Add-Result 'WARNING' 'IMPORTANT' 'OPENAI_API_KEY' 'Not present. Cloud AI processing cannot run until it is set securely; its value is never printed.' } else { Add-Result 'PASS' 'IMPORTANT' 'OPENAI_API_KEY' 'Present; value not displayed.' }
$ytDlpPath = Find-Executable @('yt-dlp.exe', 'yt-dlp')
if ($ytDlpPath) { Add-Result 'PASS' 'OPTIONAL' 'yt-dlp' (Invoke-Text $ytDlpPath @('--version')) } else { Add-Result 'WARNING' 'OPTIONAL' 'yt-dlp' 'Not found. Authorized YouTube import remains unavailable until a compliant tool is selected and installed.' }
try {
    $online = Test-NetConnection -ComputerName 'api.openai.com' -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($online) { Add-Result 'PASS' 'IMPORTANT' 'Cloud AI connectivity' 'HTTPS connectivity to the AI endpoint is available.' } else { Add-Result 'WARNING' 'IMPORTANT' 'Cloud AI connectivity' 'HTTPS connectivity to the AI endpoint could not be confirmed.' }
} catch { Add-Result 'WARNING' 'IMPORTANT' 'Cloud AI connectivity' 'Connectivity could not be tested.' }

# 23. Path safety.
if ($projectRoot -match '["''`&|;<>%!]' -or $projectRoot.Length -gt 200) { Add-Result 'WARNING' 'OPTIONAL' 'Project path compatibility' 'Path has special characters or is long; use argument arrays and keep generated media paths short.' } else { Add-Result 'PASS' 'OPTIONAL' 'Project path compatibility' 'No known problematic characters or excessive path length detected.' }

# FFmpeg smoke test. The temporary directory is recreated only inside the project root.
if ($script:ffmpegPath -and $script:ffprobePath -and $script:hasCpuH264 -and $script:hasAac) {
    $smokeDirectory = Join-Path $projectRoot (Join-Path 'work' ("ffmpeg-smoke-" + [Guid]::NewGuid().ToString('N')))
    try {
        if (-not (Test-ProjectPath $smokeDirectory)) { throw 'Smoke-test directory escaped project root.' }
        New-Item -ItemType Directory -Path $smokeDirectory -Force | Out-Null
        $source = Join-Path $smokeDirectory 'synthetic-source.mp4'
        $output = Join-Path $smokeDirectory 'vertical-output.mp4'
        & $script:ffmpegPath '-y' '-f' 'lavfi' '-i' 'testsrc2=size=640x360:rate=30' '-f' 'lavfi' '-i' 'sine=frequency=1000:sample_rate=48000' '-t' '5' '-c:v' 'libx264' '-pix_fmt' 'yuv420p' '-c:a' 'aac' '-shortest' $source | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Synthetic source generation failed.' }
        $sourceProbe = Invoke-Text $script:ffprobePath @('-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',$source)
        if (-not $sourceProbe) { throw 'ffprobe could not read the synthetic source.' }
        & $script:ffmpegPath '-y' '-i' $source '-filter:v' 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p' '-c:v' 'libx264' '-c:a' 'aac' '-movflags' '+faststart' $output | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Vertical MP4 conversion failed.' }
        $probeJson = Invoke-Text $script:ffprobePath @('-v','error','-show_entries','stream=codec_type,width,height:format=duration','-of','json',$output)
        if (-not $probeJson) { throw 'ffprobe could not read the final output.' }
        $probe = $probeJson | ConvertFrom-Json
        $video = @($probe.streams | Where-Object { $_.codec_type -eq 'video' })[0]
        $audio = @($probe.streams | Where-Object { $_.codec_type -eq 'audio' })[0]
        $size = (Get-Item -LiteralPath $output).Length
        $duration = [double]$probe.format.duration
        if ($size -le 0 -or -not $video -or -not $audio -or $video.width -ne 1080 -or $video.height -ne 1920 -or $duration -le 0) { throw 'Final output failed size, stream, dimension, or duration verification.' }
        Add-Result 'PASS' 'CRITICAL' 'FFmpeg smoke test' 'Synthetic five-second video rendered to validated 1080x1920 H.264/AAC fast-start MP4.'
    } catch {
        Add-Result 'FAIL' 'CRITICAL' 'FFmpeg smoke test' $_.Exception.Message
    } finally {
        if ((Test-Path -LiteralPath $smokeDirectory) -and (Test-ProjectPath $smokeDirectory)) { Remove-Item -LiteralPath $smokeDirectory -Recurse -Force -ErrorAction SilentlyContinue }
    }
} else {
    Add-Result 'FAIL' 'CRITICAL' 'FFmpeg smoke test' 'Skipped because FFmpeg, ffprobe, libx264, or AAC is unavailable.'
}

$criticalFailures = @($results | Where-Object { $_.Class -eq 'CRITICAL' -and $_.Status -eq 'FAIL' }).Count
$importantFailures = @($results | Where-Object { $_.Class -eq 'IMPORTANT' -and $_.Status -eq 'FAIL' }).Count
$warnings = @($results | Where-Object { $_.Status -eq 'WARNING' }).Count
Write-Host "`nSummary: $criticalFailures critical failures, $importantFailures important failures, $warnings warnings."
if ($criticalFailures -eq 0) { Write-Host 'ENVIRONMENT READY — SAFE TO SCAFFOLD' } else { Write-Host 'ENVIRONMENT NOT READY' }
if ($criticalFailures -gt 0) { exit 1 }
