$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = "C:/Users/Admin pc/AppData/Local/Programs/Python/Python313/python.exe"

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
    $args = @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$($service.Port)")

    Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $servicePath
    Write-Host "Started $($service.Name) on port $($service.Port)"
}

Write-Host "All services started."
Write-Host "Gateway: http://localhost:8000/docs"
Write-Host "Gateway health: http://localhost:8000/gateway/health"
