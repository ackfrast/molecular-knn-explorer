param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8501,
    [switch]$NoBrowser,
    [ValidateRange(1, 10)]
    [int]$MaxRetries = 5,
    [ValidateRange(5, 120)]
    [int]$ReadyTimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$EnvironmentPrefix = Join-Path $ProjectDir ".molecular-knn-env"
$PythonExe = Join-Path $EnvironmentPrefix "python.exe"
$TempDir = Join-Path $ProjectDir ".local-temp"
if (-not (Test-Path $PythonExe)) {
    throw "Molecular kNN Explorer is not installed. Double-click Install-Windows.bat first."
}

New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
Set-Location $ProjectDir

function Get-AvailableLoopbackPort([int]$PreferredPort) {
    $Listener = $null
    try {
        $Listener = [System.Net.Sockets.TcpListener]::new(
            [System.Net.IPAddress]::Loopback, $PreferredPort
        )
        $Listener.Start()
        return [int]$Listener.LocalEndpoint.Port
    }
    finally {
        if ($null -ne $Listener) { $Listener.Stop() }
    }
}

function Test-StreamlitReady([string]$Url) {
    try {
        $Response = Invoke-WebRequest -UseBasicParsing -Uri "$Url/_stcore/health" -TimeoutSec 2
        return $Response.StatusCode -eq 200 -and $Response.Content.Trim() -eq "ok"
    }
    catch { return $false }
}

$AppProcess = $null
$SelectedPort = $null
try {
    for ($Attempt = 1; $Attempt -le $MaxRetries; $Attempt++) {
        try {
            if ($Attempt -eq 1) {
                $SelectedPort = Get-AvailableLoopbackPort $Port
            } else {
                $SelectedPort = Get-AvailableLoopbackPort 0
            }
        }
        catch {
            Write-Warning "Could not allocate a loopback port on attempt $Attempt."
            continue
        }

        if ($Attempt -eq 1 -and $SelectedPort -ne $Port) {
            Write-Host "Port $Port is busy; using $SelectedPort instead."
        }
        $LocalUrl = "http://127.0.0.1:$SelectedPort"
        $LogBase = Join-Path $TempDir ("streamlit-{0}" -f [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss-fff"))
        $StdOutLog = "$LogBase.out.log"
        $StdErrLog = "$LogBase.err.log"
        $Arguments = @(
            "-m", "streamlit", "run", "app.py",
            "--server.address", "127.0.0.1",
            "--server.port", "$SelectedPort",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        )
        $AppProcess = Start-Process -FilePath $PythonExe -ArgumentList $Arguments -WorkingDirectory $ProjectDir `
            -PassThru -RedirectStandardOutput $StdOutLog -RedirectStandardError $StdErrLog

        $Ready = $false
        $Deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
        while ((Get-Date) -lt $Deadline -and -not $AppProcess.HasExited) {
            if (Test-StreamlitReady $LocalUrl) { $Ready = $true; break }
            Start-Sleep -Milliseconds 500
        }
        if ($Ready) { break }

        if (-not $AppProcess.HasExited) {
            Stop-Process -Id $AppProcess.Id -Force
        }
        $AppProcess = $null
        Write-Warning "Streamlit did not become ready on $LocalUrl. Retrying ($Attempt/$MaxRetries)."
    }

    if (-not $Ready -or $null -eq $AppProcess) {
        throw "Streamlit failed to start after $MaxRetries attempt(s). Check .local-temp for logs."
    }

    Write-Host "Molecular kNN Explorer is ready: $LocalUrl"
    Write-Host "Only this computer can access the app. Press Ctrl+C here to stop it."
    if (-not $NoBrowser) {
        try { Start-Process $LocalUrl | Out-Null }
        catch { Write-Warning "Could not open the default browser. Open this URL manually: $LocalUrl" }
    } else {
        Write-Host "Browser launch disabled; open the URL manually if needed."
    }

    while (-not $AppProcess.HasExited) { Start-Sleep -Seconds 1 }
    if ($AppProcess.ExitCode -ne 0) {
        throw "Streamlit exited with code $($AppProcess.ExitCode). Check .local-temp for logs."
    }
}
finally {
    if ($null -ne $AppProcess -and -not $AppProcess.HasExited) {
        Stop-Process -Id $AppProcess.Id -Force
    }
}
