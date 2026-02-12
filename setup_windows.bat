@echo off
REM VehiclesRent - Windows Quick Setup for PostgreSQL
REM Run this in Command Prompt or PowerShell

echo ============================================================
echo   VehiclesRent - PostgreSQL Migration (Windows)
echo ============================================================
echo.

REM Step 1: Check Python
echo Step 1: Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Step 2: Install dependencies
echo Step 2: Installing dependencies...
pip install psycopg2-binary python-dotenv --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Step 3: Setup .env file
echo Step 3: Setting up .env file...
if exist .env (
    echo [WARNING] .env already exists. Creating backup...
    copy .env .env.backup >nul
    echo [OK] Backup created: .env.backup
)

copy .env.production .env >nul
echo [OK] .env file created
echo.

REM Step 4: Edit .env file
echo Step 4: Opening .env file for editing...
echo.
echo IMPORTANT: You need to edit .env file manually
echo Please replace [YOUR-PASSWORD] with your actual Supabase password
echo.
pause
notepad .env
echo.

REM Step 5: Generate SECRET_KEY
echo Step 5: Generating SECRET_KEY...
python -c "import secrets; print(secrets.token_hex(32))" > temp_key.txt
set /p SECRET_KEY=<temp_key.txt
del temp_key.txt

echo Generated SECRET_KEY: %SECRET_KEY%
echo.
echo Please copy this key and replace it in .env file
echo.
pause
notepad .env
echo.

REM Step 6: Test connection
echo Step 6: Testing database connection...
python -c "import psycopg2; import os; from dotenv import load_dotenv; load_dotenv(); conn = psycopg2.connect(host=os.getenv('SUPABASE_HOST'), database=os.getenv('SUPABASE_DB'), user=os.getenv('SUPABASE_USER'), password=os.getenv('SUPABASE_PASSWORD'), port=os.getenv('SUPABASE_PORT')); conn.close(); print('[OK] Database connection successful!')"

if errorlevel 1 (
    echo [ERROR] Database connection failed
    echo Please check your .env file credentials
    pause
    exit /b 1
)
echo.

REM Step 7: Ask about schema
echo Step 7: Database schema initialization
echo.
set /p SCHEMA="Do you want to initialize database schema? (y/n): "
if /i "%SCHEMA%"=="y" (
    echo Initializing schema...
    echo Please run the SQL in Supabase SQL Editor manually
    echo File: supabase_schema.sql
    pause
) else (
    echo [SKIP] Schema initialization skipped
)
echo.

REM Step 8: Ask about migration
if exist database.db (
    echo Step 8: Data migration
    echo.
    set /p MIGRATE="SQLite database found. Migrate data? (y/n): "
    if /i "%MIGRATE%"=="y" (
        echo Migrating data...
        python migrate_sqlite_to_postgres.py
        if errorlevel 1 (
            echo [ERROR] Migration failed
        ) else (
            echo [OK] Migration completed
        )
    ) else (
        echo [SKIP] Migration skipped
    )
) else (
    echo Step 8: No SQLite database found
)
echo.

REM Summary
echo ============================================================
echo   SETUP COMPLETED!
echo ============================================================
echo.
echo Next steps:
echo 1. Verify .env file has correct password
echo 2. Run: python app_postgresql.py
echo 3. Test: http://localhost:5000
echo 4. Login: admin / admin123
echo.
echo Configuration:
echo   - .env file: Ready
echo   - Database: Supabase PostgreSQL
echo   - Host: aws-1-ap-southeast-1.pooler.supabase.com
echo   - Port: 6543
echo.
pause
