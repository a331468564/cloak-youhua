param(
  [int]$Port = 8765
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Url = "http://localhost:$Port/dashboard/"

Set-Location $ProjectRoot

Write-Host "Starting Ron Group dashboard server..."
Write-Host "Project root: $ProjectRoot"
Write-Host "Dashboard URL: $Url"
Write-Host ""
Write-Host "Keep this PowerShell window open while using the dashboard."
Write-Host "Press Ctrl+C here to stop the server."
Write-Host ""

Start-Process $Url

python -m http.server $Port --bind 127.0.0.1
