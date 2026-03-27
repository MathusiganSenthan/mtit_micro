param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

function Resolve-Python {
    if ($env:MICRO_PYTHON -and (Test-Path $env:MICRO_PYTHON)) {
        return $env:MICRO_PYTHON
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $resolved = & py -3 -c "import sys; print(sys.executable)"
        if ($LASTEXITCODE -eq 0 -and $resolved) {
            return $resolved.Trim()
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    throw "Python executable not found. Install Python 3.11+ or set MICRO_PYTHON env var."
}

$python = Resolve-Python

$services = @(
    @{ Name = "auth-service"; Port = 8001 },
    @{ Name = "user-service"; Port = 8002 },
    @{ Name = "product-service"; Port = 8003 },
    @{ Name = "order-service"; Port = 8004 },
    @{ Name = "notification-service"; Port = 8005 },
    @{ Name = "feedback-service"; Port = 8006 },
    @{ Name = "api-gateway"; Port = 8000 }
)

foreach ($service in $services) {
    $servicePath = Join-Path $root $service.Name
    $envFile = Join-Path $servicePath ".env"
    $envExample = Join-Path $servicePath ".env.example"

    if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
        Copy-Item $envExample $envFile
        Write-Host "Created .env for $($service.Name) from .env.example"
    }

    if (-not $SkipInstall) {
        & $python -m pip install -r (Join-Path $servicePath "requirements.txt")
    }

    $args = @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$($service.Port)")
    Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $servicePath
    Write-Host "Started $($service.Name) on port $($service.Port)"
}

Write-Host "Waiting for services to become healthy..."
foreach ($service in $services) {
    $healthUrl = "http://localhost:$($service.Port)/health"
    $ok = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -lt 400) {
                $ok = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    if ($ok) {
        Write-Host "Healthy: $($service.Name) ($healthUrl)"
    }
    else {
        Write-Warning "Service did not report healthy in time: $($service.Name) ($healthUrl)"
    }
}

Write-Host "All services launched."
Write-Host "Gateway docs: http://localhost:8000/docs"
Write-Host "Gateway health: http://localhost:8000/gateway/health"
