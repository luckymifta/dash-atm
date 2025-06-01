@echo off
echo ========================================
echo  ATM Monitor - Windows Installation
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✓ Python found
python --version

:: Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✓ pip found

:: Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo ✓ Virtual environment created
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check requirements.txt and try again
    pause
    exit /b 1
)

echo ✓ Dependencies installed successfully

:: Create necessary directories
echo.
echo Creating directories...
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "data" mkdir data
echo ✓ Directories created

:: Create sample configuration files if they don't exist
echo.
echo Setting up configuration files...

if not exist ".env" (
    echo Creating sample .env file...
    echo # ATM Monitor Database Configuration > .env
    echo. >> .env
    echo # Database connection details >> .env
    echo DB_HOST=your_database_host >> .env
    echo DB_PORT=5432 >> .env
    echo DB_NAME=dash >> .env
    echo DB_USER=your_username >> .env
    echo DB_PASS=your_password >> .env
    echo. >> .env
    echo # ATM System Configuration >> .env
    echo LOGIN_URL=your_login_url >> .env
    echo TOTAL_ATMS=14 >> .env
    echo LOG_LEVEL=INFO >> .env
    echo. >> .env
    echo # Operational Settings >> .env
    echo CONTINUOUS_INTERVAL=30 >> .env
    echo RETRY_INTERVAL=5 >> .env
    echo CONNECTION_RETRY_INTERVAL=15 >> .env
    echo MAX_RETRIES=3 >> .env
    echo ✓ Sample .env file created - PLEASE EDIT WITH YOUR SETTINGS
) else (
    echo ✓ .env file already exists
)

if not exist "config.json" (
    echo Creating sample config.json file...
    echo { > config.json
    echo   "operation": { >> config.json
    echo     "continuous_mode": true, >> config.json
    echo     "interval_minutes": 30, >> config.json
    echo     "retry_attempts": 3, >> config.json
    echo     "timeout_seconds": 300 >> config.json
    echo   }, >> config.json
    echo   "database": { >> config.json
    echo     "save_to_db": true, >> config.json
    echo     "use_new_tables": true, >> config.json
    echo     "connection_timeout": 30, >> config.json
    echo     "query_timeout": 60 >> config.json
    echo   }, >> config.json
    echo   "logging": { >> config.json
    echo     "level": "INFO", >> config.json
    echo     "file_rotation": true, >> config.json
    echo     "max_file_size": "10MB", >> config.json
    echo     "backup_count": 5 >> config.json
    echo   }, >> config.json
    echo   "atm_system": { >> config.json
    echo     "total_atms": 14, >> config.json
    echo     "demo_mode": false, >> config.json
    echo     "save_json": true >> config.json
    echo   } >> config.json
    echo } >> config.json
    echo ✓ Sample config.json file created
) else (
    echo ✓ config.json file already exists
)

:: Test installation
echo.
echo Testing installation...
python -c "import sys; print('Python version:', sys.version)"
python -c "import requests; print('✓ requests module working')"
python -c "import psycopg2; print('✓ psycopg2 module working')"
python -c "import dotenv; print('✓ python-dotenv module working')"

:: Test script syntax
echo.
echo Testing script syntax...
python -m py_compile combined_atm_retrieval_script.py
if errorlevel 1 (
    echo ERROR: combined_atm_retrieval_script.py has syntax errors
    pause
    exit /b 1
)
echo ✓ Main script syntax is valid

python -m py_compile db_connector.py
if errorlevel 1 (
    echo ERROR: db_connector.py has syntax errors
    pause
    exit /b 1
)
echo ✓ Database connector syntax is valid

echo.
echo ========================================
echo  Installation completed successfully!
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Edit .env file with your database credentials
echo 2. Edit config.json with your preferences  
echo 3. Test with: run_single.bat --demo
echo 4. Run continuous mode: run_continuous.bat
echo 5. Install as service: install_service.bat (as Administrator)
echo.
echo Configuration files created:
echo - .env (EDIT THIS WITH YOUR SETTINGS)
echo - config.json
echo.
echo Directories created:
echo - logs\
echo - output\
echo - data\
echo.
pause
