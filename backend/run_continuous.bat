@echo off
echo ========================================
echo  ATM Monitor - Continuous Operation
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

:: Check if main script exists
if not exist "combined_atm_retrieval_script.py" (
    echo ERROR: combined_atm_retrieval_script.py not found
    echo Please ensure the script is in the current directory
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please create and configure .env file with your database settings
    pause
    exit /b 1
)

:: Set default arguments
set ARGS=--continuous --save-to-db --use-new-tables

:: Add any command line arguments passed to this script
set ARGS=%ARGS% %*

:: Create timestamp for logging
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do if not "%%I"=="" set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

:: Create log directory if it doesn't exist
if not exist "logs" mkdir logs

echo Starting ATM Monitor in continuous mode...
echo Arguments: %ARGS%
echo Log file: logs\continuous_%timestamp%.log
echo.
echo Press Ctrl+C to stop the service
echo.

:: Run the script with logging
python combined_atm_retrieval_script.py %ARGS% 2>&1 | tee logs\continuous_%timestamp%.log

:: Check exit code
if errorlevel 1 (
    echo.
    echo ERROR: Script exited with error code %errorlevel%
    echo Check the log file for details: logs\continuous_%timestamp%.log
    pause
    exit /b %errorlevel%
)

echo.
echo ATM Monitor stopped successfully
pause
