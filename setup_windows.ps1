# VehiclesRent - Windows PowerShell Setup Script
# Run this in PowerShell: .\setup_windows.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  VehiclesRent - PostgreSQL Migration (Windows)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "Step 1: Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from python.org" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# Step 2: Install dependencies
Write-Host "Step 2: Installing dependencies..." -ForegroundColor Yellow
pip install psycopg2-binary python-dotenv 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# Step 3: Create .env file
Write-Host "Step 3: Creating .env file..." -ForegroundColor Yellow
if (Test-Path .env) {
    Write-Host "[WARNING] .env already exists. Creating backup..." -ForegroundColor Yellow
    Copy-Item .env .env.backup
    Write-Host "[OK] Backup created: .env.backup" -ForegroundColor Green
}

Copy-Item .env.production .env
Write-Host "[OK] .env file created from template" -ForegroundColor Green
Write-Host ""

# Step 4: Get password
Write-Host "Step 4: Database configuration" -ForegroundColor Yellow
Write-Host "Please enter your Supabase password:" -ForegroundColor Cyan
$password = Read-Host -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Replace password in .env
(Get-Content .env) -replace '\[YOUR-PASSWORD\]', $plainPassword | Set-Content .env
Write-Host "[OK] Password configured" -ForegroundColor Green
Write-Host ""

# Step 5: Generate SECRET_KEY
Write-Host "Step 5: Generating SECRET_KEY..." -ForegroundColor Yellow
$secretKey = python -c "import secrets; print(secrets.token_hex(32))"
(Get-Content .env) -replace 'your_secret_key_change_this_in_production_use_random_64_chars', $secretKey | Set-Content .env
Write-Host "[OK] SECRET_KEY generated and configured" -ForegroundColor Green
Write-Host ""

# Step 6: Test connection
Write-Host "Step 6: Testing database connection..." -ForegroundColor Yellow
$testScript = @"
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        database=os.getenv('SUPABASE_DB'),
        user=os.getenv('SUPABASE_USER'),
        password=os.getenv('SUPABASE_PASSWORD'),
        port=os.getenv('SUPABASE_PORT')
    )
    conn.close()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
"@

$result = python -c $testScript
if ($result -eq 'SUCCESS') {
    Write-Host "[OK] Database connection successful!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Database connection failed!" -ForegroundColor Red
    Write-Host "Result: $result" -ForegroundColor Red
    Write-Host "Please check your credentials in .env file" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

# Step 7: Initialize schema
Write-Host "Step 7: Database schema" -ForegroundColor Yellow
$initSchema = Read-Host "Initialize database schema in Supabase? (y/n)"
if ($initSchema -eq 'y' -or $initSchema -eq 'Y') {
    Write-Host ""
    Write-Host "Please complete these steps:" -ForegroundColor Cyan
    Write-Host "1. Go to: https://supabase.com/dashboard" -ForegroundColor White
    Write-Host "2. Select your project" -ForegroundColor White
    Write-Host "3. Go to SQL Editor" -ForegroundColor White
    Write-Host "4. Open file: supabase_schema.sql" -ForegroundColor White
    Write-Host "5. Copy all content and paste in SQL Editor" -ForegroundColor White
    Write-Host "6. Click 'Run'" -ForegroundColor White
    Write-Host ""
    notepad supabase_schema.sql
    Write-Host "Press any key after running SQL in Supabase..." -ForegroundColor Yellow
    pause
} else {
    Write-Host "[SKIP] Schema initialization skipped" -ForegroundColor Yellow
}
Write-Host ""

# Step 8: Migrate data
if (Test-Path database.db) {
    Write-Host "Step 8: Data migration" -ForegroundColor Yellow
    $migrateData = Read-Host "SQLite database found. Migrate data to PostgreSQL? (y/n)"
    if ($migrateData -eq 'y' -or $migrateData -eq 'Y') {
        Write-Host "Migrating data..." -ForegroundColor Cyan
        python migrate_sqlite_to_postgres.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Migration completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Migration failed" -ForegroundColor Red
        }
    } else {
        Write-Host "[SKIP] Migration skipped" -ForegroundColor Yellow
    }
} else {
    Write-Host "Step 8: No SQLite database found - skipping migration" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETED!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run application: python app_postgresql.py" -ForegroundColor White
Write-Host "  2. Open browser: http://localhost:5000" -ForegroundColor White
Write-Host "  3. Login: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Database: Supabase PostgreSQL" -ForegroundColor White
Write-Host "  Host: aws-1-ap-southeast-1.pooler.supabase.com" -ForegroundColor White
Write-Host "  Port: 6543 (Connection Pooler)" -ForegroundColor White
Write-Host "  Files: .env (configured)" -ForegroundColor White
Write-Host ""
Write-Host "Ready for production! " -NoNewline -ForegroundColor Green
Write-Host "🚀" -ForegroundColor Yellow
Write-Host ""
pause
