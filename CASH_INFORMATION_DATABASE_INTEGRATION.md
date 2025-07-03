# Cash Information Database Integration

This document outlines the implementation and verification of cash information retrieval and database integration in the ATM Dashboard application.

## Implementation Summary

The ATM Dashboard application now properly retrieves and stores cash information for ATM terminals in the database using environment variables loaded from a `.env` file.

### Key Features

1. **Environment Variable Loading**
   - Uses `python-dotenv` to load environment variables from `.env` file
   - Database connection parameters are loaded from environment variables
   - Defaults to sensible values if environment variables are not set

2. **Cash Information Retrieval**
   - Implemented within `CombinedATMRetriever` class
   - Command-line option `--include-cash-info` to enable cash data retrieval
   - Continuous operation mode supported

3. **Database Storage**
   - Cash information is stored in `terminal_cash_information` table
   - Connection parameters are loaded from environment variables
   - Support for both direct database connection and connector module

## Verification Tools

1. **Environment Variable Verification**
   - Run `verify_env_loading.py` to check environment variables
   - Shows which database connection parameters will be used

2. **Database Connection Testing**
   - Run `test_db_connection.py` to verify database connectivity
   - Tests connection and validates table structure

3. **Cash Table Structure Verification**
   - Run `verify_cash_information_table.py` to check table structure
   - Validates columns, indexes, and sample data

## Usage Examples

### Running with Cash Information Retrieval

```bash
python combined_atm_retrieval_script.py --include-cash-info --save-to-db
```

### Running in Continuous Mode

```bash
python combined_atm_retrieval_script.py --include-cash-info --save-to-db --continuous --interval 60
```

### Verifying Cash Table Structure

```bash
python verify_cash_information_table.py
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection problems:

1. Check that `.env` file exists in the backend directory
2. Verify environment variables using `verify_env_loading.py`
3. Test connection using `test_db_connection.py`
4. Ensure PostgreSQL server is running and accessible

### Missing Python Modules

Required Python modules:
```
python-dotenv
psycopg2
```

Install with:
```bash
pip install python-dotenv psycopg2
```
