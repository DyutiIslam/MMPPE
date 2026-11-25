$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$LogDir = Join-Path $PSScriptRoot 'logs'
$Log = Join-Path $LogDir 'bootstrap.log'
$Venv = Join-Path $Root '.mmppe_env'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
$Requirements = Join-Path $Root 'requirements.txt'
$PythonVersion = '3.12.10'
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
$Installer = Join-Path $env:TEMP "mmppe-python-$PythonVersion-amd64.exe"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Step([string]$Text) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Text"
    Write-Host $Text
    Add-Content -Path $Log -Value $line
}
function Fail([string]$Message, [int]$Code = 1) {
    Write-Host ""
    Write-Host "[MMPPE ERROR] $Message" -ForegroundColor Red
    Add-Content -Path $Log -Value "ERROR: $Message"
    exit $Code
}
function Test-Python([string]$Exe) {
    if (-not $Exe -or -not (Test-Path $Exe)) { return $false }
    & $Exe -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] < (3,14) else 1)" *> $null
    return ($LASTEXITCODE -eq 0)
}
function Find-Python {
    $candidates = @(
        (Join-Path $env:LocalAppData 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:ProgramFiles 'Python312\python.exe')
    )
    if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Python312\python.exe') }
    foreach ($candidate in $candidates) { if (Test-Python $candidate) { return $candidate } }
    try {
        $cmd = Get-Command python.exe -ErrorAction Stop
        if (Test-Python $cmd.Source) { return $cmd.Source }
    } catch {}
    try {
        $py = Get-Command py.exe -ErrorAction Stop
        $resolved = & $py.Source -3.12 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and (Test-Python $resolved)) { return $resolved }
    } catch {}
    return $null
}

Clear-Content -Path $Log -ErrorAction SilentlyContinue
Write-Host "============================================================"
Write-Host " MMPPE - Multimodal Multi-Participant Physiological"
Write-Host " Experiment Platform | V0.2 RC1"
Write-Host "============================================================"
Write-Host ""
Write-Step '[1/7] Checking local runtime...'
$Python = Find-Python
if (-not $Python) {
    Write-Step 'No compatible Python runtime found. Installing a private per-user Python 3.12 runtime...'
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $PythonUrl -OutFile $Installer
    } catch {
        Fail "Python is not installed and the official Python installer could not be downloaded. Check internet/proxy access. $($_.Exception.Message)" 11
    }
    try {
        $p = Start-Process -FilePath $Installer -ArgumentList '/quiet','InstallAllUsers=0','PrependPath=0','Include_launcher=1','Include_pip=1','Include_test=0','Shortcuts=0' -Wait -PassThru
        if ($p.ExitCode -ne 0) { Fail "Python installer returned code $($p.ExitCode). The PC may restrict application installation." 12 }
    } finally { Remove-Item $Installer -Force -ErrorAction SilentlyContinue }
    $Python = Find-Python
    if (-not $Python) { Fail 'Python installation completed but the runtime could not be located.' 13 }
}
Write-Step "Runtime ready: $(& $Python --version 2>&1)"

Write-Step '[2/7] Preparing isolated MMPPE environment...'
if (-not (Test-Path $VenvPython)) {
    & $Python -m venv $Venv 2>&1 | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPython)) { Fail 'Could not create the isolated .mmppe_env environment.' 21 }
} else { Write-Step 'Existing isolated MMPPE environment found.' }

Write-Step '[3/7] Verifying/installing pinned dependencies...'
& $VenvPython -m pip install --disable-pip-version-check -r $Requirements 2>&1 | Tee-Object -FilePath $Log -Append
if ($LASTEXITCODE -ne 0) { Fail 'Dependency installation/verification failed. Check internet/proxy access or organizational software restrictions.' 31 }

Write-Step '[4/7] Checking package integrity and imports...'
Push-Location $Root
try {
    & $VenvPython -m mmppe.release_check --imports 2>&1 | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -ne 0) { Fail 'MMPPE package integrity check failed.' 41 }

    Write-Step '[5/7] Running local application boot/health test...'
    & $VenvPython -m mmppe.release_check --boot 2>&1 | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -ne 0) { Fail 'MMPPE application could not pass its local health test.' 51 }

    Write-Step '[6/7] Setup qualification passed.'
    Write-Step '[7/7] Starting MMPPE...'
    Write-Host ''
    Write-Host 'The browser will open automatically. Keep this window open while MMPPE is running.'
    Write-Host 'Press CTRL+C to stop MMPPE.'
    Write-Host ''
    & $VenvPython -m mmppe.launch
    if ($LASTEXITCODE -ne 0) { Fail "MMPPE server stopped with code $LASTEXITCODE." 61 }
} finally { Pop-Location }
exit 0
