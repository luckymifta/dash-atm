# ATM Data Retrieval System - Windows Operation Guide (Updated)

## Overview
This guide provides comprehensive step-by-step instructions for setting up and running the ATM data retrieval system on Windows with the latest database connection fixes.

## Prerequisites
1. **Python 3.8+** installed on Windows
2. **Git** for cloning the repository
3. **Network access** to the ATM monitoring system and database
4. **Database credentials** configured in `.env` file

## Setup Instructions

### 1. Clone Repository
```bash
git clone <repository-url>
cd backend
git checkout feature/sigit-cash-information
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
**CRITICAL**: Copy `.env.example` to `.env` and configure your database credentials:

```bash
copy .env.example .env
```

Edit `.env` file with your database settings:
```properties
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Email Configuration (optional)
MAILJET_API_KEY=your_mailjet_api_key
MAILJET_SECRET_KEY=your_mailjet_secret_key
MAILJET_FROM_EMAIL=your_from_email
```

### 4. Test Database Connection (IMPORTANT)
Before running the main script, test the database connection:
```bash
python test_db_connection.py
```
This should show "✓ ALL TESTS PASSED" if everything is configured correctly.

**If the test fails:**
1. Double-check your `.env` file settings
2. Verify network connectivity to the database host
3. Confirm database credentials are correct

## Running the Script

### Available Options
- `--no-cash`: Skip cash information retrieval
- `--no-db`: Skip database saving (save to JSON files only)
- `--demo`: Use demo mode with sample data
- `--continuous`: Run continuously (use with batch/PowerShell scripts)

### Single Run (Test Mode)
```bash
python combined_atm_retrieval_script.py
```

### Single Run Without Cash Info
```bash
python combined_atm_retrieval_script.py --no-cash
```

### Single Run Without Database (JSON Only)
```bash
python combined_atm_retrieval_script.py --no-db
```

## Continuous Operation

### Option 1: Batch Script (Recommended)
```bash
run_continuous_with_cash.bat
```

### Option 2: PowerShell Script
```powershell
.\run_continuous_with_cash.ps1
```

Both scripts will:
- Run every 15 minutes
- Include cash information retrieval
- Save data to database
- Log all operations
- Restart automatically on errors

## Script Parameters Reference

### Default Behavior (No Arguments)
- ✓ Retrieves terminal status data
- ✓ Includes cash information 
- ✓ Saves to database
- ✓ Saves to JSON files

### With `--no-cash`
- ✓ Retrieves terminal status data
- ✗ Skips cash information
- ✓ Saves to database
- ✓ Saves to JSON files

### With `--no-db`
- ✓ Retrieves terminal status data
- ✓ Includes cash information
- ✗ Skips database saving
- ✓ Saves to JSON files

### With `--demo`
- ✓ Uses demo/sample data
- ✓ Includes simulated cash info
- ✓ Saves to database (demo tables)
- ✓ Saves to JSON files

## Monitoring and Logs

### Log Files
- **combined_atm_retrieval.log**: Main application logs
- **Console output**: Real-time status and errors

### Checking Status
Monitor the console output or log files for:
- Successful data retrieval confirmations
- Database save confirmations
- Error messages and retry attempts
- Cash information processing status

### Key Success Indicators
Look for these messages in logs:
```
Successfully retrieved regional data for X terminals
Successfully processed cash information for X terminals
Successfully saved X regional records to database
Successfully saved X cash records to database
```

## Troubleshooting

### Database Connection Issues
1. **Verify `.env` file**: Ensure all database credentials are correct
2. **Test connection**: Run `python test_db_connection.py`
3. **Check network**: Ensure database host is accessible
4. **Verify credentials**: Confirm username/password are valid

### Authentication Issues
1. **Check credentials**: Verify login credentials in `atm_config.py`
2. **Network access**: Ensure access to `https://172.31.1.46`
3. **Firewall**: Check Windows firewall settings

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Script Errors
1. **Check Python version**: Must be 3.8+
2. **Review logs**: Check detailed error messages
3. **Restart script**: Many issues resolve with restart
4. **Demo mode**: Test with `--demo` flag first

## Performance Notes

### Resource Usage
- **Memory**: ~50-100MB during operation
- **Network**: Moderate bandwidth for API calls
- **CPU**: Low usage except during data processing

### Timing
- **Single run**: 30-60 seconds (depending on terminal count)
- **Cash retrieval**: Adds 10-30 seconds per run
- **Database save**: 1-5 seconds per run

## Production Deployment

### Service Installation (Optional)
For production deployment, consider installing as a Windows service:
1. Use tools like `NSSM` (Non-Sucking Service Manager)
2. Point to the PowerShell script
3. Configure automatic restart on failure

### Monitoring
- Set up log rotation for long-term operation
- Monitor disk space for JSON output files
- Set up alerts for consecutive failures

## File Structure
```
backend/
├── combined_atm_retrieval_script.py    # Main script
├── atm_config.py                       # Configuration
├── atm_auth.py                         # Authentication
├── atm_data_retriever.py              # Data retrieval
├── atm_cash_processor.py              # Cash processing
├── atm_data_processor.py              # Data processing
├── atm_database.py                    # Database operations
├── .env                               # Environment variables (YOU MUST CREATE THIS)
├── .env.example                       # Environment template
├── requirements.txt                   # Python dependencies
├── run_continuous_with_cash.bat       # Windows batch script
├── run_continuous_with_cash.ps1       # PowerShell script
└── test_db_connection.py              # Database connection test
```

## Latest Updates (Critical)

### Database Connection Fix
The latest version includes fixes for database connectivity issues:

1. **Environment Variable Loading**: The script now properly loads `.env` files using `python-dotenv`
2. **Database Configuration**: Improved database connection handling with explicit parameter passing
3. **Connection Testing**: Added `test_db_connection.py` to verify setup before running main script

### Required Steps for Existing Installations
If you're updating from a previous version:

1. **Pull latest changes**:
   ```bash
   git pull origin feature/sigit-cash-information
   ```

2. **Update dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Test database connection**:
   ```bash
   python test_db_connection.py
   ```

4. **Verify `.env` file exists and is configured properly**

## Support
For issues or questions:
1. Check the troubleshooting section above
2. Review log files for detailed error messages
3. Test individual components with provided test scripts
4. Verify all prerequisites are met

## Quick Start Checklist
- [ ] Python 3.8+ installed
- [ ] Repository cloned and on correct branch
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured with database credentials
- [ ] Database connection test passed (`python test_db_connection.py`)
- [ ] Single test run successful (`python combined_atm_retrieval_script.py`)
- [ ] Continuous operation started (`run_continuous_with_cash.bat`)
