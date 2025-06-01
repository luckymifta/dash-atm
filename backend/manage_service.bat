@echo off
echo ========================================
echo  ATM Monitor - Service Management
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

:menu
echo.
echo ATM Monitor Service Management
echo ==============================
echo 1. Check service status
echo 2. Start service
echo 3. Stop service
echo 4. Restart service
echo 5. View service logs
echo 6. Remove service
echo 7. Reinstall service
echo 8. Exit
echo.
set /p choice="Please select an option (1-8): "

if "%choice%"=="1" goto check_status
if "%choice%"=="2" goto start_service
if "%choice%"=="3" goto stop_service
if "%choice%"=="4" goto restart_service
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto remove_service
if "%choice%"=="7" goto reinstall_service
if "%choice%"=="8" goto exit
echo Invalid choice. Please try again.
goto menu

:check_status
echo.
echo Checking ATM Monitor Service status...
sc query ATMMonitorService
if errorlevel 1 (
    echo Service is not installed
) else (
    echo.
    echo Service information:
    sc queryconfig ATMMonitorService
)
goto menu

:start_service
echo.
echo Starting ATM Monitor Service...
net start ATMMonitorService
if errorlevel 1 (
    echo Failed to start service
    echo Check logs and configuration
) else (
    echo Service started successfully
)
goto menu

:stop_service
echo.
echo Stopping ATM Monitor Service...
net stop ATMMonitorService
if errorlevel 1 (
    echo Failed to stop service or service not running
) else (
    echo Service stopped successfully
)
goto menu

:restart_service
echo.
echo Restarting ATM Monitor Service...
net stop ATMMonitorService
timeout /t 3 >nul
net start ATMMonitorService
if errorlevel 1 (
    echo Failed to restart service
) else (
    echo Service restarted successfully
)
goto menu

:view_logs
echo.
echo Recent service logs:
echo ====================
if exist "logs\service.log" (
    echo Last 20 lines of service.log:
    echo.
    powershell "Get-Content 'logs\service.log' -Tail 20"
) else (
    echo No service log file found
)
echo.
if exist "logs\combined_atm_retrieval.log" (
    echo Last 10 lines of application log:
    echo.
    powershell "Get-Content 'logs\combined_atm_retrieval.log' -Tail 10"
) else (
    echo No application log file found
)
goto menu

:remove_service
echo.
echo WARNING: This will remove the ATM Monitor Service
set /p confirm="Are you sure? (Y/N): "
if /i not "%confirm%"=="Y" goto menu

echo Stopping and removing service...
net stop ATMMonitorService >nul 2>&1
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python atm_service.py remove
) else (
    sc delete ATMMonitorService
)
echo Service removed
goto menu

:reinstall_service
echo.
echo Reinstalling ATM Monitor Service...
echo This will remove and reinstall the service
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" goto menu

call install_service.bat
goto menu

:exit
echo.
echo Goodbye!
pause
exit /b 0
