# Continuous Operation Mode for ATM Monitoring

## Overview

The combined ATM retrieval script now supports continuous operation, allowing it to run at regular intervals to provide ongoing monitoring of ATM status and cash information.

## Features

- **Continuous Execution**: Script will run repeatedly at specified intervals
- **Graceful Shutdown**: Properly handles termination signals to complete the current run before exiting
- **Configurable Interval**: Set your own time interval between runs (default: 300 seconds)
- **Run Tracking**: Logs each run with sequential run numbers and timestamps
- **Custom Output Directory**: Direct JSON output files to a specific location

## Usage

### Command Line Arguments

The following new arguments have been added:

- `--continuous`: Run in continuous operation mode
- `--interval`: Interval between runs in seconds (default: 300)
- `--output-dir`: Directory for JSON output files (default: ./cash_output)

### Example Commands

#### Basic Continuous Operation

```bash
python combined_atm_retrieval_script.py --continuous --interval 600 --save-to-db
```

This will run the script every 10 minutes (600 seconds) and save data to the database.

#### Continuous Cash Information Monitoring with JSON Output

```bash
python combined_atm_retrieval_script.py --continuous --interval 300 --include-cash-info --save-json --output-dir ./cash_data
```

This will:
- Run every 5 minutes (300 seconds)
- Include cash information retrieval
- Save output as JSON files in the ./cash_data directory

### Using the Helper Script

We've included a helper script for common continuous operation scenarios:

```bash
./run_continuous_atm_monitoring.sh
```

This script:
1. Sets up a 5-minute interval monitoring cycle
2. Includes cash information retrieval
3. Saves output to both the database and JSON files
4. Creates a log file of all operations

## Best Practices

1. For production deployments, consider using a process manager like systemd or PM2 to manage the script
2. Adjust the interval based on the importance of data freshness and server load
3. Implement log rotation if running for extended periods
4. Monitor disk usage if saving JSON files over long periods

## Implementation Details

The continuous operation feature uses Python's signal handling to catch SIGINT and SIGTERM signals, allowing the script to complete its current run before shutting down. This ensures no data loss or corruption during the retrieval process.
