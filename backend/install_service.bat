@echo off
echo ========================================
echo  ATM Monitor - Windows Service Install
echo ========================================
echo.

:: Check for administrator privileges
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo ✓ Running with administrator privileges

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

echo ✓ Virtual environment found

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Check if service script exists
if not exist "atm_service.py" (
    echo ERROR: atm_service.py not found
    echo Please ensure all service files are present
    pause
    exit /b 1
)

echo ✓ Service script found

:: Check if main script exists
if not exist "combined_atm_retrieval_script.py" (
    echo ERROR: combined_atm_retrieval_script.py not found
    echo Please ensure all required files are present
    pause
    exit /b 1
)

echo ✓ Main script found

:: Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please configure .env file before starting the service
    echo Continue anyway? (Y/N)
    set /p choice=
    if /i not "%choice%"=="Y" (
        echo Installation cancelled
        pause
        exit /b 1
    )
)

:: Remove existing service if it exists
echo.
echo Checking for existing service...
sc query ATMMonitorService >nul 2>&1
if not errorlevel 1 (
    echo Found existing service, stopping and removing...
    net stop ATMMonitorService >nul 2>&1
    python atm_service.py remove
    if errorlevel 1 (
        echo WARNING: Could not remove existing service completely
        echo You may need to reboot and try again
    ) else (
        echo ✓ Existing service removed
    )
    timeout /t 3 >nul
)

:: Install the service
echo.
echo Installing ATM Monitor Service...
python atm_service.py install
if errorlevel 1 (
    echo ERROR: Service installation failed
    echo Check the error messages above
    pause
    exit /b 1
)

echo ✓ Service installed successfully

:: Set service description and startup type
echo.
echo Configuring service settings...
sc config ATMMonitorService start= auto
sc description ATMMonitorService "Continuous ATM data retrieval and monitoring service for the ATM Dashboard system"

:: Set service recovery options (restart on failure)
sc failure ATMMonitorService reset= 60 actions= restart/30000/restart/60000/restart/90000

echo ✓ Service configured

:: Ask if user wants to start the service now
echo.
echo Service installation completed successfully!
echo.
echo Service Details:
echo - Name: ATMMonitorService
echo - Display Name: ATM Monitor Continuous Service
echo - Startup Type: Automatic
echo - Recovery: Restart on failure
echo.
echo Management Commands:
echo   net start ATMMonitorService    - Start the service
echo   net stop ATMMonitorService     - Stop the service
echo   sc query ATMMonitorService     - Check service status
echo   sc delete ATMMonitorService    - Remove the service
echo.
set /p start_choice="Start the service now? (Y/N): "
if /i "%start_choice%"=="Y" (
    echo.
    echo Starting ATM Monitor Service...
    net start ATMMonitorService
    if errorlevel 1 (
        echo ERROR: Failed to start service
        echo Check Windows Event Viewer for details
        echo Ensure .env file is properly configured
    ) else (
        echo ✓ Service started successfully
        echo.
        echo The service is now running and will start automatically at boot
        echo Check logs\service.log for service output
    )
) else (
    echo.
    echo Service installed but not started
    echo To start manually: net start ATMMonitorService
)

echo.
echo Installation completed!
echo.
echo IMPORTANT NOTES:
echo 1. Ensure .env file is configured with correct database settings
echo 2. Service logs are written to logs\service.log
echo 3. The service will automatically restart if it fails
echo 4. Use Windows Services management console for advanced configuration
echo.
pause
