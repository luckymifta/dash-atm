@echo off
REM Git Pull Script for ATM Database Schema Updates
REM This script pulls the latest changes from a specific branch on GitHub

echo ====================================================
echo    Git Pull Script for ATM Database Schema Updates
echo ====================================================
echo.

REM Ask for the branch name if not provided
set BRANCH_NAME=db-schema-updates
set /P BRANCH_NAME=Enter the branch name to pull from [db-schema-updates]: 

echo Starting git operations for branch: %BRANCH_NAME%
echo.

REM Check if the branch exists locally
git show-ref --verify --quiet refs/heads/%BRANCH_NAME%
if %ERRORLEVEL% NEQ 0 (
    echo Branch %BRANCH_NAME% doesn't exist locally. Creating it...
    git checkout -b %BRANCH_NAME% origin/%BRANCH_NAME%
) else (
    echo Switching to branch %BRANCH_NAME%...
    git checkout %BRANCH_NAME%
)

REM Pull the latest changes
echo.
echo Pulling latest changes from origin/%BRANCH_NAME%...
git pull origin %BRANCH_NAME%

echo.
echo Done! Changes pulled from branch %BRANCH_NAME%
echo.
echo The following files have been updated:
echo - atm_database.py
echo - test_db_tables.py
echo - DATABASE_SCHEMA_ANALYSIS.md
echo - DATABASE_SCHEMA_UPDATE_SUMMARY.md
echo - check_db_schema_extended.py
echo - run_continuous_with_cash.bat
echo - run_continuous_with_cash.ps1
echo - WINDOWS_OPERATION_GUIDE.md
echo.
echo You can now run the script using: run_continuous_with_cash.bat
echo.
pause
