# Continuous Operation Feature Integration

## Summary
The continuous operation feature for the ATM Monitoring System has been successfully integrated into the main branch. This feature allows the ATM data retrieval script to run at regular intervals without manual intervention, providing ongoing monitoring of ATM status and cash information.

## Features Implemented
1. **Continuous Execution Mode**: Added `--continuous` flag to enable continuous operation
2. **Configurable Intervals**: Set the time between runs with `--interval` parameter (default: 15 minutes)
3. **Graceful Shutdown**: Proper signal handling for clean termination
4. **Run Tracking**: Sequential run numbering and timestamps
5. **Custom Output Directory**: Control where JSON output files are saved

## Technical Implementation
- Signal handling for SIGINT and SIGTERM to ensure clean shutdown
- Intelligent sleep mechanism that responds quickly to shutdown signals
- Dynamic JSON file naming with timestamps
- Performance tracking for each run
- Automatic output directory creation

## Usage Examples
Basic continuous operation:
```bash
python combined_atm_retrieval_script.py --continuous --total-atms 14 --include-cash-info --save-to-db --use-new-tables
```

Custom interval (30 minutes):
```bash
python combined_atm_retrieval_script.py --continuous --interval 1800 --include-cash-info --save-to-db
```

Helper script provided:
```bash
./backend/run_continuous_atm_monitoring.sh
```

## Files Modified/Added
1. `/backend/combined_atm_retrieval_script.py` - Added continuous operation functionality
2. `/backend/run_continuous_atm_monitoring.sh` - Helper script for continuous operation
3. `/backend/CONTINUOUS_OPERATION_README.md` - Documentation for the feature

## Deployment Notes
- The default interval is set to 15 minutes (900 seconds)
- For production deployment, consider using a process manager like systemd or PM2
- Implemented on: July 3, 2025
- Branch: `feature/continuous-operation` → Merged to `main`
