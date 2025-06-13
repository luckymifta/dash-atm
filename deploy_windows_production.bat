@echo off
REM Windows Production Deployment Script for ATM Terminal Discovery
REM This script automates the deployment and testing of the enhanced ATM script

echo.
echo ====================================================================
echo           ATM Terminal Discovery - Windows Deployment
echo ====================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is available
python --version

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✅ pip is available

REM Create directory structure
echo.
echo Creating directory structure...
if not exist "C:\ATM-Monitoring" mkdir "C:\ATM-Monitoring"
if not exist "C:\ATM-Monitoring\backend" mkdir "C:\ATM-Monitoring\backend"
if not exist "C:\ATM-Monitoring\logs" mkdir "C:\ATM-Monitoring\logs"

echo ✅ Directory structure created

REM Create requirements.txt
echo.
echo Creating requirements.txt...
(
echo requests>=2.31.0
echo urllib3>=2.0.0
echo pytz>=2023.3
echo tqdm>=4.65.0
) > "C:\ATM-Monitoring\requirements.txt"

echo ✅ Requirements file created

REM Install dependencies
echo.
echo Installing Python dependencies...
cd /d "C:\ATM-Monitoring"
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Copy script (assumes script is in current directory)
echo.
echo Copying ATM script...
if exist "combined_atm_retrieval_script.py" (
    copy "combined_atm_retrieval_script.py" "C:\ATM-Monitoring\backend\"
    echo ✅ Script copied to C:\ATM-Monitoring\backend\
) else if exist "backend\combined_atm_retrieval_script.py" (
    copy "backend\combined_atm_retrieval_script.py" "C:\ATM-Monitoring\backend\"
    echo ✅ Script copied to C:\ATM-Monitoring\backend\
) else (
    echo WARNING: Script not found in current directory
    echo Please manually copy combined_atm_retrieval_script.py to C:\ATM-Monitoring\backend\
)

REM Test installation
echo.
echo Testing installation...
cd /d "C:\ATM-Monitoring"

REM Quick Python test
python -c "
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
try:
    from combined_atm_retrieval_script import CombinedATMRetriever
    print('✅ Script import successful')
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    print('✅ Retriever instance created')
    discovered = retriever.load_discovered_terminals()
    print(f'✅ Terminal discovery system: {len(discovered)} terminals loaded')
    print('🎉 Installation test completed successfully!')
except Exception as e:
    print(f'❌ Installation test failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if errorlevel 1 (
    echo.
    echo ERROR: Installation test failed
    echo Please check the error messages above
    pause
    exit /b 1
)

REM Success message
echo.
echo ====================================================================
echo                    DEPLOYMENT SUCCESSFUL!
echo ====================================================================
echo.
echo Installation Location: C:\ATM-Monitoring
echo Script Location: C:\ATM-Monitoring\backend\combined_atm_retrieval_script.py
echo.
echo NEXT STEPS:
echo.
echo 1. Test in demo mode:
echo    cd C:\ATM-Monitoring
echo    python backend\combined_atm_retrieval_script.py --demo --total-atms 14
echo.
echo 2. Run in production mode:
echo    python backend\combined_atm_retrieval_script.py --total-atms 14 --save-to-db
echo.
echo 3. Monitor logs:
echo    type combined_atm_retrieval.log
echo.
echo 4. Check discovered terminals:
echo    type backend\discovered_terminals.json
echo.
echo For detailed instructions, see: WINDOWS_PRODUCTION_DEPLOYMENT_GUIDE.md
echo.

pause
