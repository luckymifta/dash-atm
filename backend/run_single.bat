@echo off
echo ========================================
echo  ATM Monitor - Single Execution
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

:: Check if .env file exists (unless demo mode)
echo %* | find "--demo" >nul
if errorlevel 1 (
    if not exist ".env" (
        echo ERROR: .env file not found
        echo Please create and configure .env file with your database settings
        echo Or use --demo flag for testing
        pause
        exit /b 1
    )
)

:: Set default arguments (can be overridden by command line)
set ARGS=%*

:: If no arguments provided, show help
if "%ARGS%"=="" (
    echo Usage examples:
    echo   %0 --demo                    # Demo mode for testing
    echo   %0 --save-to-db              # Single run with database save
    echo   %0 --demo --save-json        # Demo mode with JSON output
    echo   %0 --total-atms 20           # Custom ATM count
    echo   %0 --save-to-db --use-new-tables  # Use new JSONB tables
    echo.
    echo Available options:
    echo   --demo              Use demo mode (no real API calls)
    echo   --save-to-db        Save data to database
    echo   --use-new-tables    Use new JSONB tables
    echo   --save-json         Save JSON output files
    echo   --total-atms N      Set total ATM count (default: 14)
    echo   --quiet             Reduce logging output
    echo.
    set /p choice="Enter arguments (or press Enter for --demo): "
    if "!choice!"=="" set ARGS=--demo
    if not "!choice!"=="" set ARGS=!choice!
)

:: Create timestamp for logging
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do if not "%%I"=="" set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

:: Create log directory if it doesn't exist
if not exist "logs" mkdir logs

echo Starting ATM Monitor (single execution)...
echo Arguments: %ARGS%
echo Log file: logs\single_%timestamp%.log
echo.

:: Run the script with logging
python combined_atm_retrieval_script.py %ARGS% 2>&1 | tee logs\single_%timestamp%.log

:: Check exit code
if errorlevel 1 (
    echo.
    echo ERROR: Script exited with error code %errorlevel%
    echo Check the log file for details: logs\single_%timestamp%.log
    pause
    exit /b %errorlevel%
) else (
    echo.
    echo ✓ ATM Monitor completed successfully
    echo Check the log file for details: logs\single_%timestamp%.log
)

pause
