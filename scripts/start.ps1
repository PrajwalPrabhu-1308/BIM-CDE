# CDE SaaS Platform - Quick Start Script (PowerShell)
# This script handles database setup and server startup

param(
    [ValidateSet('full', 'quick', 'clean')]
    [string]$Mode = 'quick'
)

$baseDir = "c:\Users\prajw\Desktop\CDE-MVP"
$dbName = "cde_saas"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CDE SaaS Platform - Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Kill existing processes
Write-Host "`n[1] Checking for running processes..." -ForegroundColor Yellow
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "Stopping existing Python processes..." -ForegroundColor Yellow
    Stop-Process -InputObject $pythonProcs -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
}

# Database setup
if ($Mode -eq 'full' -or $Mode -eq 'clean') {
    Write-Host "`n[2] Setting up database..." -ForegroundColor Yellow
    
    if ($Mode -eq 'clean') {
        Write-Host "Creating fresh database..."
        $sql = @"
DROP DATABASE IF EXISTS $dbName;
CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"@
        $sql | mysql -u root -p | Out-Null
        
        Write-Host "Loading schema..." -ForegroundColor Yellow
        mysql -u root -p $dbName < "$baseDir\schema_saas.sql" | Out-Null
        Write-Host "✓ Database ready" -ForegroundColor Green
    }
    else {
        Write-Host "✓ Database check skipped (use -Mode clean for full reset)" -ForegroundColor Green
    }
}

# Start server
Write-Host "`n[3] Starting API Server..." -ForegroundColor Yellow
Write-Host "Server will run on http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Cyan

Set-Location $baseDir
& python main_saas.py
