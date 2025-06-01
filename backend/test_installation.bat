@echo off
echo ========================================
echo  ATM Monitor - Quick Test
echo ========================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

echo Running quick validation tests...
echo.

:: Test 1: Python modules
echo 1. Testing Python modules...
python -c "import requests, psycopg2, dotenv, tqdm; print('✓ All required modules available')" 2>nul
if errorlevel 1 (
    echo ❌ Missing required Python modules
    echo Please run install.bat to install dependencies
    pause
    exit /b 1
)

:: Test 2: Script syntax
echo 2. Testing script syntax...
python -m py_compile combined_atm_retrieval_script.py 2>nul
if errorlevel 1 (
    echo ❌ Main script has syntax errors
    pause
    exit /b 1
)
echo ✓ Main script syntax valid

python -m py_compile db_connector.py 2>nul
if errorlevel 1 (
    echo ❌ Database connector has syntax errors
    pause
    exit /b 1
)
echo ✓ Database connector syntax valid

:: Test 3: Configuration files
echo 3. Testing configuration files...
if not exist ".env" (
    echo ⚠️  .env file not found - using template
    if exist ".env.template" (
        copy .env.template .env >nul
        echo ✓ Created .env from template (EDIT THIS FILE!)
    ) else (
        echo ❌ No .env template found
    )
) else (
    echo ✓ .env file exists
)

if not exist "config.json" (
    echo ⚠️  config.json not found
) else (
    echo ✓ config.json exists
)

:: Test 4: Directory structure
echo 4. Testing directory structure...
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "data" mkdir data
echo ✓ Required directories created

:: Test 5: Demo run
echo 5. Testing demo mode execution...
echo Running quick demo test (this may take 30 seconds)...
python combined_atm_retrieval_script.py --demo --save-json --total-atms 5 --quiet 2>nul
if errorlevel 1 (
    echo ❌ Demo test failed
    echo Check the logs for details
    pause
    exit /b 1
)
echo ✓ Demo test completed successfully

:: Test 6: Database connection (if configured)
echo 6. Testing database connection...
python -c "
import os
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()
    import db_connector
    conn = db_connector.get_db_connection()
    if conn:
        print('✓ Database connection successful')
        conn.close()
    else:
        print('⚠️  Database connection failed (check .env configuration)')
else:
    print('⚠️  .env file not configured (skipping database test)')
" 2>nul

echo.
echo ========================================
echo  Test Results Summary
echo ========================================
echo ✓ Python environment ready
echo ✓ All scripts have valid syntax
echo ✓ Directory structure created
echo ✓ Demo mode works correctly
echo.
echo NEXT STEPS:
echo 1. Edit .env file with your actual database credentials
echo 2. Test with real database: run_single.bat --save-to-db
echo 3. Start continuous mode: run_continuous.bat
echo 4. Install as service: install_service.bat (as Administrator)
echo.
echo Configuration status:
if exist ".env" (
    findstr /c:"your_database_host" .env >nul 2>&1
    if errorlevel 1 (
        echo ✓ .env appears to be configured
    ) else (
        echo ⚠️  .env needs configuration (contains template values)
    )
) else (
    echo ❌ .env file missing
)
echo.
pause
