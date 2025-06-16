# Terminal Record Deletion Utility

This utility provides scripts to delete database records from the `terminal_details` and `regional_data` tables that don't match a specified list of terminal IDs.

## Purpose

The scripts will keep records only for the following terminal IDs and delete all others:
```
83, 2603, 87, 88, 2604, 85, 147, 49, 86, 2605, 169, 90, 89, 93
```

## Available Scripts

1. **delete_unwanted_terminals.py** - Standard version that deletes records from both tables
2. **delete_unwanted_terminals_v2.py** - Advanced version that checks table schemas first and adapts deletion strategy
3. **run_terminal_deletion.sh** - A shell script that makes it easy to run either version

## Requirements

- Python 3.6+
- asyncpg package
- dotenv package

You can install the required packages with:
```
pip install asyncpg python-dotenv
```

## Usage

### Option 1: Using the shell script (recommended)

```bash
./run_terminal_deletion.sh
```

This will guide you through the process with a simple menu.

### Option 2: Running Python scripts directly

```bash
# Standard version
python3 delete_unwanted_terminals.py

# Advanced version with schema detection
python3 delete_unwanted_terminals_v2.py
```

## What the scripts do

1. Connect to the PostgreSQL database using credentials from environment variables or defaults
2. Identify records in the `terminal_details` table that don't match the specified terminal IDs
3. Delete these records after confirmation from the user
4. Attempt to delete corresponding records in the `regional_data` table if possible
5. Log all actions to both console and log files

## Safety Features

- The scripts require explicit user confirmation before deleting any records
- Operations are performed within a database transaction
- Comprehensive logging to both console and files
- Records are counted before and after deletion for verification

## Logs

The scripts create log files:
- `delete_terminals.log` for the standard version
- `delete_terminals_v2.log` for the advanced version

These logs contain detailed information about the deletion process, including counts of records deleted and any errors encountered.
