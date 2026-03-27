$ports = @(8000, 8001, 8002, 8003, 8004, 8005, 8006)

foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        try {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped process $($conn.OwningProcess) on port $port"
        }
        catch {
            Write-Host "Could not stop process $($conn.OwningProcess) on port $port"
        }
    }
}

Write-Host "Stop script completed."
