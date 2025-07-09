# ATM Data Retrieval - Windows Operation Guide

This guide explains how to run the ATM data retrieval script in continuous mode on a Windows machine.

## Prerequisites

1. Python 3.7 or later installed on your Windows machine
2. Required Python packages installed (see `requirements.txt`)
3. Network access to the ATM monitoring APIs
4. Database credentials configured in `.env` file

## Running the Script

### Option 1: Using the Batch File

1. Open Command Prompt (cmd.exe)
2. Navigate to the backend directory:
   ```
   cd path\to\dash-atm\backend
   ```
3. Run the batch file:
   ```
   run_continuous_with_cash.bat
   ```

### Option 2: Using PowerShell

1. Open PowerShell
2. Navigate to the backend directory:
   ```
   cd path\to\dash-atm\backend
   ```
3. Run the PowerShell script:
   ```
   .\run_continuous_with_cash.ps1
   ```

### Option 3: Running Directly with Python

If you need to customize the parameters, you can run the Python script directly:

```
python combined_atm_retrieval_script.py --continuous --interval 900 --include-cash --save-to-db
```

## Configuration Parameters

The script supports the following command-line parameters:

| Parameter | Description |
|-----------|-------------|
| `--continuous` | Run in continuous operation mode |
| `--interval 900` | Set the interval to 15 minutes (900 seconds) |
| `--include-cash` or `--no-cash` | Include or exclude cash information retrieval |
| `--save-to-db` or `--no-db` | Enable or disable saving to the database |
| `--output-file FILENAME` | Specify a custom output JSON filename |
| `--verbose` | Enable verbose logging |
| `--demo` | Run in demo mode using sample data instead of real API calls |
| `--use-new-tables` | Use the new database tables with enhanced schema |
| `--status-only` | Get terminal status information only (quick mode) |

## Running as a Windows Service

For long-term deployment, it's recommended to run the script as a Windows service. You can use NSSM (the Non-Sucking Service Manager) to install the script as a service:

1. Download NSSM from http://nssm.cc/
2. Install the service:
   ```
   nssm install ATMDataRetrieval
   ```
3. In the dialog that appears:
   - Set the "Path" to your Python executable (e.g., `C:\Python39\python.exe`)
   - Set "Arguments" to `combined_atm_retrieval_script.py --continuous --interval 900 --include-cash --save-to-db`
   - Set "Startup directory" to your backend directory path
   - Configure other options as needed (log files, etc.)
4. Start the service:
   ```
   nssm start ATMDataRetrieval
   ```

## Logging

Logs are saved in the following locations:
- Script logs: `atm_retrieval.log`
- Continuous operation logs: `continuous_retrieval_YYYYMMDD_HHMMSS.log`

## Monitoring

You can monitor the script's operation by:
1. Checking the log files
2. Monitoring database records
3. Checking the timestamps of the latest JSON output files

## Troubleshooting

If you encounter issues:

1. **Database Connection Errors**:
   - Verify database credentials in the `.env` file
   - Check if the database server is accessible from your Windows machine

2. **API Connection Errors**:
   - Verify network connectivity to the ATM monitoring APIs
   - Check if the authentication credentials are valid

3. **Script Crashes**:
   - Check the log files for error messages
   - Ensure all required Python packages are installed

4. **Performance Issues**:
   - Consider adjusting the interval (default: 15 minutes)
   - Monitor CPU and memory usage during operation

## Support

For additional support, please contact the development team or refer to the project documentation.
