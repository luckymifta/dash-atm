@echo off
echo ========================================
echo  ATM Monitor - Deployment Package
echo ========================================
echo.

:: Create deployment package
echo Creating Windows deployment package...
echo.

:: Check if all required files exist
set MISSING_FILES=0

echo Checking required files...
if not exist "combined_atm_retrieval_script.py" (
    echo ❌ combined_atm_retrieval_script.py missing
    set MISSING_FILES=1
)
if not exist "db_connector.py" (
    echo ❌ db_connector.py missing
    set MISSING_FILES=1
)
if not exist "atm_service.py" (
    echo ❌ atm_service.py missing
    set MISSING_FILES=1
)
if not exist "requirements.txt" (
    echo ❌ requirements.txt missing
    set MISSING_FILES=1
)
if not exist ".env.template" (
    echo ❌ .env.template missing
    set MISSING_FILES=1
)
if not exist "config.json" (
    echo ❌ config.json missing
    set MISSING_FILES=1
)

:: Check batch scripts
if not exist "install.bat" (
    echo ❌ install.bat missing
    set MISSING_FILES=1
)
if not exist "run_single.bat" (
    echo ❌ run_single.bat missing
    set MISSING_FILES=1
)
if not exist "run_continuous.bat" (
    echo ❌ run_continuous.bat missing
    set MISSING_FILES=1
)
if not exist "install_service.bat" (
    echo ❌ install_service.bat missing
    set MISSING_FILES=1
)
if not exist "manage_service.bat" (
    echo ❌ manage_service.bat missing
    set MISSING_FILES=1
)
if not exist "test_installation.bat" (
    echo ❌ test_installation.bat missing
    set MISSING_FILES=1
)

:: Check documentation
if not exist "WINDOWS_DEPLOYMENT_GUIDE.md" (
    echo ❌ WINDOWS_DEPLOYMENT_GUIDE.md missing
    set MISSING_FILES=1
)
if not exist "README_DEPLOYMENT.md" (
    echo ❌ README_DEPLOYMENT.md missing
    set MISSING_FILES=1
)

if %MISSING_FILES%==1 (
    echo.
    echo ❌ Some required files are missing
    echo Cannot create deployment package
    pause
    exit /b 1
)

echo ✓ All required files found
echo.

:: Create deployment package directory
set PACKAGE_DIR=ATM_Monitor_Windows_Deployment
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

echo Creating deployment package structure...

:: Copy core files
copy "combined_atm_retrieval_script.py" "%PACKAGE_DIR%\" >nul
copy "db_connector.py" "%PACKAGE_DIR%\" >nul
copy "atm_service.py" "%PACKAGE_DIR%\" >nul
copy "requirements.txt" "%PACKAGE_DIR%\" >nul
copy ".env.template" "%PACKAGE_DIR%\" >nul
copy "config.json" "%PACKAGE_DIR%\" >nul

:: Copy batch scripts
copy "install.bat" "%PACKAGE_DIR%\" >nul
copy "run_single.bat" "%PACKAGE_DIR%\" >nul
copy "run_continuous.bat" "%PACKAGE_DIR%\" >nul
copy "install_service.bat" "%PACKAGE_DIR%\" >nul
copy "manage_service.bat" "%PACKAGE_DIR%\" >nul
copy "test_installation.bat" "%PACKAGE_DIR%\" >nul

:: Copy documentation
copy "WINDOWS_DEPLOYMENT_GUIDE.md" "%PACKAGE_DIR%\" >nul
copy "README_DEPLOYMENT.md" "%PACKAGE_DIR%\" >nul

:: Create directories
mkdir "%PACKAGE_DIR%\logs"
mkdir "%PACKAGE_DIR%\output"
mkdir "%PACKAGE_DIR%\data"

:: Create deployment info file
echo ATM Monitor Windows Deployment Package > "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo ========================================= >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo. >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo Package Created: %DATE% %TIME% >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo Package Version: 1.0 >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo Compatible with: Windows 10/11, Python 3.8+ >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo. >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo QUICK START: >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo 1. Run install.bat as Administrator >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo 2. Edit .env file with your database settings >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo 3. Test with: test_installation.bat >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo 4. Deploy with: run_continuous.bat >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo. >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo For Windows Service installation: >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo Run install_service.bat as Administrator >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo. >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"
echo See README_DEPLOYMENT.md for complete instructions >> "%PACKAGE_DIR%\DEPLOYMENT_INFO.txt"

:: Create file list
echo Package Contents: > "%PACKAGE_DIR%\FILE_LIST.txt"
echo ================== >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo. >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo Core Application Files: >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - combined_atm_retrieval_script.py (Main application) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - db_connector.py (Database connectivity) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - atm_service.py (Windows service wrapper) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo. >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo Configuration Files: >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - .env.template (Environment variables template) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - config.json (Application configuration) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - requirements.txt (Python dependencies) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo. >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo Windows Scripts: >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - install.bat (Installation script) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - run_single.bat (Single execution) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - run_continuous.bat (Continuous operation) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - install_service.bat (Service installation) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - manage_service.bat (Service management) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - test_installation.bat (Installation testing) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo. >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo Documentation: >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - README_DEPLOYMENT.md (Quick start guide) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - WINDOWS_DEPLOYMENT_GUIDE.md (Complete guide) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - DEPLOYMENT_INFO.txt (Package information) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - FILE_LIST.txt (This file) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo. >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo Directories: >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - logs\ (Log files) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - output\ (JSON output files) >> "%PACKAGE_DIR%\FILE_LIST.txt"
echo - data\ (Data files) >> "%PACKAGE_DIR%\FILE_LIST.txt"

:: Display package information
echo.
echo ========================================
echo  Deployment Package Created Successfully
echo ========================================
echo.
echo Package Directory: %PACKAGE_DIR%
echo.
echo Package Contents:
echo ✓ Core application files (3)
echo ✓ Configuration files (3)
echo ✓ Windows batch scripts (6)
echo ✓ Documentation files (2)
echo ✓ Directory structure created
echo.
echo Package Size:
for /f %%A in ('dir "%PACKAGE_DIR%" /s /-c /q ^| find "File(s)"') do echo %%A
echo.
echo NEXT STEPS:
echo 1. Copy the '%PACKAGE_DIR%' folder to your Windows machine
echo 2. Follow instructions in README_DEPLOYMENT.md
echo.
echo The package is ready for Windows deployment!
echo.
pause
