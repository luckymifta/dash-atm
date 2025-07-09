@echo off
REM ATM Data Retrieval Script - Continuous Operation with 15-minute interval
REM Includes cash information and saves to database
REM
REM This batch file runs the combined_atm_retrieval_script.py in continuous mode
REM with a 15-minute interval, saving data to the database.

echo ===================================================
echo ATM Data Retrieval - Continuous Operation (15-minute interval)
echo Includes Cash Information and Database Storage
echo ===================================================
echo.
echo Starting continuous operation at %TIME% on %DATE%
echo Press CTRL+C to stop the script
echo.

REM Set Python executable - adjust path if needed
set PYTHON_CMD=python

REM Run the script with appropriate parameters
%PYTHON_CMD% combined_atm_retrieval_script.py --continuous --interval 900 --include-cash --save-to-db

echo.
echo Script terminated at %TIME% on %DATE%
pause
