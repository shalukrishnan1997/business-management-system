# Stop local mysqld started for this project
$procs = Get-Process mysqld -ErrorAction SilentlyContinue
if (-not $procs) {
    Write-Host "No mysqld process found."
    exit 0
}

$procs | Stop-Process -Force
Write-Host "Stopped mysqld (PID(s): $($procs.Id -join ', '))."
