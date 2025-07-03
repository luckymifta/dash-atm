#!/bin/bash
# Script to run the combined ATM retrieval in continuous operation mode
# This script runs the ATM data retrieval with cash information at regular intervals

# Configuration
INTERVAL=300  # Time between runs in seconds (5 minutes)
OUTPUT_DIR="./cash_output"
TOTAL_ATMS=14
LOG_FILE="atm_continuous_monitor.log"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Starting ATM continuous monitoring..."
echo "- Interval: $INTERVAL seconds"
echo "- Output directory: $OUTPUT_DIR"
echo "- Log file: $LOG_FILE"
echo "- Press Ctrl+C to gracefully stop monitoring"
echo

# Start the script in continuous mode
python combined_atm_retrieval_script.py \
  --continuous \
  --interval "$INTERVAL" \
  --total-atms "$TOTAL_ATMS" \
  --include-cash-info \
  --save-json \
  --output-dir "$OUTPUT_DIR" \
  --save-to-db | tee -a "$LOG_FILE"
