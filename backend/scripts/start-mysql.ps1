# Start local MySQL (Laragon 8.4.3 data dir used by this project)
$ErrorActionPreference = "Stop"
$mysqlRoot = "C:\laragon\bin\mysql\mysql-8.4.3-winx64"
$mysqld = Join-Path $mysqlRoot "bin\mysqld.exe"
$ini = Join-Path $mysqlRoot "my.ini"

$listening = netstat -an | Select-String "LISTENING" | Select-String ":3306"
if ($listening) {
    Write-Host "MySQL already listening on port 3306."
    exit 0
}

if (-not (Test-Path $mysqld)) {
    Write-Error "mysqld not found at $mysqld"
}

Write-Host "Starting MySQL..."
Start-Process -FilePath $mysqld -ArgumentList "--defaults-file=$ini" -WindowStyle Hidden
Start-Sleep -Seconds 3

$listening = netstat -an | Select-String "LISTENING" | Select-String ":3306"
if ($listening) {
    Write-Host "MySQL is running on port 3306."
} else {
    Write-Error "MySQL did not open port 3306. Check $mysqlRoot\*.err logs."
}
