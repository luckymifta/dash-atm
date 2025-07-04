# DATABASE CONNECTION FIX AND VERIFICATION GUIDE

## Summary of Changes

The ATM dashboard scripts have been updated to ensure proper handling of database connections using environment variables:

1. Modified `combined_atm_retrieval_script.py` to prioritize the original `db_connector.py` which properly uses environment variables from `.env` files.
2. Enhanced the `save_cash_information_to_database` method to first try using the db_connector module, and only fall back to direct psycopg2 connection with environment variables.
3. Added better logging to show which database host is being used for connections.

## Why These Changes Were Made

Previously, the script was:
- Prioritizing `db_connector_new.py` which has hardcoded credentials
- Not consistently using environment variables across all database connections
- Not providing enough feedback about which database it was connecting to

This sometimes caused the script to connect to localhost:5432 instead of the intended PostgreSQL server, especially on Windows systems.

## How to Verify Database Connections

### 1. Use the test_db_connection.py script

```bash
# Run with environment variables
DB_HOST=your_host DB_PORT=5432 DB_NAME=atm_monitor DB_USER=postgres DB_PASSWORD=your_password python backend/test_db_connection.py

# Or specify parameters directly
python backend/test_db_connection.py --host your_host --port 5432 --dbname atm_monitor --user postgres --password your_password
```

### 2. Create and Use a .env File

Create a `.env` file in the root of your project with the following content:

```
DB_HOST=your_host
DB_PORT=5432
DB_NAME=atm_monitor
DB_USER=postgres
DB_PASSWORD=your_password
```

The `load_dotenv()` call at the top of the script will load these environment variables.

### 3. Verify Cash Information Database Operations

To specifically test the cash information database storage:

```bash
# Run the script with cash info enabled
python backend/combined_atm_retrieval_script.py --save-to-db --include-cash-info
```

Look for the log messages showing which database host is being used:
- `Connecting to database at [host]:[port] for cash information storage`
- `Successfully saved [number] cash information records to database`

### For Windows Users

If you're on Windows, you can set environment variables in your command prompt:

```cmd
set DB_HOST=your_host
set DB_PORT=5432
set DB_NAME=atm_monitor
set DB_USER=postgres
set DB_PASSWORD=your_password
python backend\combined_atm_retrieval_script.py --save-to-db --include-cash-info
```

Or in PowerShell:

```powershell
$env:DB_HOST="your_host"
$env:DB_PORT="5432"
$env:DB_NAME="atm_monitor"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_password"
python backend\combined_atm_retrieval_script.py --save-to-db --include-cash-info
```

## Continuous Operation Mode

The cash information retrieval also works in continuous operation mode:

```bash
python backend/combined_atm_retrieval_script.py --continuous --include-cash-info --save-to-db --interval 300
```

This will run the script every 5 minutes (300 seconds), continuously retrieving and storing cash information.

## Troubleshooting Database Connections

If you still encounter connection issues:

1. Check that PostgreSQL is running on the specified host
2. Verify that your network/firewall allows connections to the database port
3. Double-check your database credentials
4. Look for error messages in the log that might indicate connection problems
5. Try manually connecting to the database using psql or another PostgreSQL client
