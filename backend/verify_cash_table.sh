#!/bin/bash
# verify_cash_table.sh - Helper script to run the terminal cash information table verification

# Default database settings
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-atm_monitor}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Display banner
echo "======================================================"
echo "  Terminal Cash Information Table Verification Tool   "
echo "======================================================"
echo

# Help function
function show_help {
  echo "Usage: $0 [OPTIONS]"
  echo
  echo "Options:"
  echo "  -h, --host HOST      Database host (default: $DB_HOST)"
  echo "  -p, --port PORT      Database port (default: $DB_PORT)"
  echo "  -d, --dbname NAME    Database name (default: $DB_NAME)"
  echo "  -u, --user USER      Database user (default: $DB_USER)"
  echo "  -w, --password PWD   Database password"
  echo "  -v, --verbose        Enable verbose output"
  echo "  --help               Show this help message"
  echo
  exit 1
}

# Parse command line options
VERBOSE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--host)
      DB_HOST="$2"
      shift 2
      ;;
    -p|--port)
      DB_PORT="$2"
      shift 2
      ;;
    -d|--dbname)
      DB_NAME="$2"
      shift 2
      ;;
    -u|--user)
      DB_USER="$2"
      shift 2
      ;;
    -w|--password)
      DB_PASSWORD="$2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE="--verbose"
      shift
      ;;
    --help)
      show_help
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      ;;
  esac
done

# Check if the verification script exists
if [ ! -f "verify_cash_information_table.py" ]; then
  SCRIPT_DIR=$(dirname "$(realpath "$0")")
  if [ -f "$SCRIPT_DIR/backend/verify_cash_information_table.py" ]; then
    cd "$SCRIPT_DIR/backend"
  elif [ -f "$SCRIPT_DIR/verify_cash_information_table.py" ]; then
    cd "$SCRIPT_DIR"
  else
    echo "Error: verify_cash_information_table.py not found."
    echo "Please run this script from the project root or backend directory."
    exit 1
  fi
fi

# Export database environment variables
export DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD

echo "Database connection settings:"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo

# Run the verification script
echo "Running verification script..."
echo "----------------------------------------------------"
python verify_cash_information_table.py $VERBOSE

# Check exit status
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo
  echo "⚠️  Verification failed with exit code $EXIT_CODE."
  echo "   Please check the error messages above."
else
  echo
  echo "✅ Verification completed successfully."
fi

exit $EXIT_CODE
