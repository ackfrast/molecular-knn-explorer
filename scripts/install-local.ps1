param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ToolsDir = Join-Path $ProjectDir ".local-tools"
$EnvironmentPrefix = Join-Path $ProjectDir ".molecular-knn-env"
$MicromambaExe = Join-Path $ToolsDir "micromamba.exe"
$EnvironmentFile = Join-Path $ProjectDir "environment-windows.yml"
$LocalTemp = Join-Path $ProjectDir ".local-temp"
$env:MAMBA_ROOT_PREFIX = Join-Path $ToolsDir "mamba-root"

if (-not [Environment]::Is64BitOperatingSystem) {
    throw "Molecular kNN Explorer requires 64-bit Windows."
}
if ($env:PROCESSOR_ARCHITECTURE -notin @("AMD64", "ARM64")) {
    throw "Unsupported Windows architecture: $env:PROCESSOR_ARCHITECTURE"
}
if (-not (Test-Path $EnvironmentFile)) {
    throw "Missing environment file: $EnvironmentFile"
}

New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
New-Item -ItemType Directory -Force -Path $LocalTemp | Out-Null
Set-Location $ProjectDir
$env:TEMP = $LocalTemp
$env:TMP = $LocalTemp

if (-not (Test-Path $MicromambaExe)) {
    Write-Host "Downloading Micromamba for Windows..."
    $Archive = Join-Path $LocalTemp "micromamba.tar.bz2"
    Invoke-WebRequest -Uri "https://micro.mamba.pm/api/micromamba/win-64/latest" -OutFile $Archive
    & tar.exe -xjf $Archive -C $ToolsDir
    if ($LASTEXITCODE -ne 0) {
        throw "Could not extract Micromamba. Windows 10/11 tar.exe is required."
    }
    $Extracted = Get-ChildItem -Path $ToolsDir -Recurse -Filter "micromamba.exe" | Select-Object -First 1
    if (-not $Extracted) {
        throw "Could not find micromamba.exe in the downloaded archive."
    }
    Copy-Item -Force $Extracted.FullName $MicromambaExe
}

if (Test-Path (Join-Path $EnvironmentPrefix "python.exe")) {
    Write-Host "Updating the project-local environment..."
    & $MicromambaExe install --yes --prefix $EnvironmentPrefix --file $EnvironmentFile
} else {
    Write-Host "Installing Python, RDKit, Streamlit, and scientific dependencies..."
    & $MicromambaExe create --yes --prefix $EnvironmentPrefix --file $EnvironmentFile
}
if ($LASTEXITCODE -ne 0) {
    throw "Environment installation failed. Existing research environments were not modified."
}

& $MicromambaExe run --prefix $EnvironmentPrefix python -c "import rdkit, streamlit, pandas, numpy; print('Core imports OK')"
if ($LASTEXITCODE -ne 0) {
    throw "Core dependency check failed."
}
if (-not $SkipTests) {
    & $MicromambaExe run --prefix $EnvironmentPrefix python -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Project tests failed."
    }
}

Write-Host "Removing downloaded package caches..."
& $MicromambaExe clean --all --yes
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Cache cleanup did not complete; the application is installed but may use extra disk space."
}

Write-Host ""
Write-Host "Installation complete. Double-click Run-Windows.bat to start the app."
