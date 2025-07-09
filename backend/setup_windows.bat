@echo off
echo ====================================================
echo ATM Data Retrieval System - Windows Setup Script
echo ====================================================
echo.

:: Check if .env file exists
if exist ".env" (
    echo ✅ .env file already exists
    echo.
    echo Current database configuration:
    findstr /B "DB_" .env
    echo.
    echo If you need to update the database credentials, edit the .env file manually.
    echo.
    goto :check_python
) else (
    echo ⚠️  .env file not found
    echo.
    echo Creating .env file from template...
    
    if exist ".env.template" (
        copy ".env.template" ".env" > nul
        echo ✅ .env file created from template
        echo.
        echo ⚠️  IMPORTANT: Please edit the .env file with your actual database credentials!
        echo.
        echo Current template values:
        findstr /B "DB_" .env
        echo.
        echo You need to update these values with your actual database details.
        echo.
        pause
    ) else (
        echo ❌ .env.template not found. Creating a basic .env file...
        echo # ATM Monitor Database Configuration > .env
        echo. >> .env
        echo # Database connection details >> .env
        echo DB_HOST=your_database_host >> .env
        echo DB_PORT=5432 >> .env
        echo DB_NAME=your_database_name >> .env
        echo DB_USER=your_database_user >> .env
        echo DB_PASSWORD=your_database_password >> .env
        echo.
        echo ✅ Basic .env file created
        echo ⚠️  IMPORTANT: Please edit the .env file with your actual database credentials!
        echo.
        pause
    )
)

:check_python
:: Check Python installation
echo Checking Python installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.7+ and add it to your PATH.
    pause
    exit /b 1
) else (
    python --version
    echo ✅ Python is installed
)
echo.

:: Check if requirements.txt exists and install dependencies
echo Checking Python dependencies...
if exist "requirements.txt" (
    echo Installing Python dependencies...
    python -m pip install -r requirements.txt
    echo ✅ Dependencies installed
) else (
    echo ⚠️  requirements.txt not found. Installing basic dependencies...
    python -m pip install psycopg2-binary requests python-dotenv pytz
    echo ✅ Basic dependencies installed
)
echo.

:: Test database connection
echo Testing database connection...
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('Testing database configuration...')
print(f'DB_HOST: {os.environ.get(\"DB_HOST\", \"NOT SET\")}')
print(f'DB_PORT: {os.environ.get(\"DB_PORT\", \"NOT SET\")}')
print(f'DB_NAME: {os.environ.get(\"DB_NAME\", \"NOT SET\")}')
print(f'DB_USER: {os.environ.get(\"DB_USER\", \"NOT SET\")}')
password = os.environ.get('DB_PASSWORD') or os.environ.get('DB_PASS', '')
print(f'DB_PASSWORD: {\"SET\" if password else \"NOT SET\"}')

if not password:
    print('❌ DATABASE PASSWORD NOT SET!')
    print('Please edit the .env file and set your database password.')
    exit(1)
else:
    print('✅ Database configuration looks good.')
    
    # Test actual connection
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=password
        )
        conn.close()
        print('✅ Database connection successful!')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        print('Please check your database credentials in the .env file.')
        exit(1)
"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Setup incomplete. Please fix the issues above before running the ATM script.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo ✅ Setup completed successfully!
echo ====================================================
echo.
echo You can now run the ATM data retrieval script using:
echo   run_continuous_with_cash.bat
echo.
echo Or manually with:
echo   python combined_atm_retrieval_script.py --continuous --interval 900
echo.
pause
