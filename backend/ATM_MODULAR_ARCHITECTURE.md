# ATM Data Retrieval System - Modular Architecture

This document describes the refactored ATM data retrieval system that replaces the previous monolithic `combined_atm_retrieval_script_integrated.py` with a clean, modular architecture.

## Overview

The system has been broken down into focused, maintainable modules that each handle a specific responsibility:

- **Configuration Management**: Centralized configuration and constants
- **Authentication**: Login/logout and session management
- **Data Retrieval**: Regional and terminal data retrieval
- **Cash Processing**: Cash information retrieval and processing
- **Data Processing**: Processing raw data into structured formats
- **Database Operations**: All database save operations
- **Orchestration**: Main coordination logic

## Module Structure

### 1. `atm_config.py`
**Purpose**: Centralized configuration management
- Contains all URLs, credentials, and system settings
- Database configuration management
- Timezone settings
- Expected terminal IDs and parameter values
- Demo data configurations

### 2. `atm_auth.py`
**Purpose**: Authentication and session management
- Login/logout functionality
- Session management and token handling
- Retry logic for authentication failures
- Session validation

**Key Classes**:
- `ATMAuthenticator`: Main authentication handler

### 3. `atm_data_retriever.py`
**Purpose**: Data retrieval operations
- Regional data retrieval
- Terminal details retrieval
- Terminal status information
- HTTP request handling with proper error handling and retries

**Key Classes**:
- `ATMDataRetriever`: Main data retrieval handler

### 4. `atm_cash_processor.py`
**Purpose**: Cash information processing
- Cash information retrieval for terminals
- Cash data processing and validation
- Cassette information processing
- Demo cash data generation

**Key Classes**:
- `ATMCashProcessor`: Cash information handler

### 5. `atm_data_processor.py`
**Purpose**: Data processing and formatting
- Processing raw regional data
- Processing terminal details
- Processing cash information
- Status summary generation
- Data validation and cleaning

**Key Classes**:
- `ATMDataProcessor`: Data processing handler

### 6. `atm_database.py`
**Purpose**: Database operations
- Saving regional data to database
- Saving terminal details to database
- Saving cash information to database
- Database connection management
- Transaction handling

**Key Classes**:
- `ATMDatabaseManager`: Database operations handler

### 7. `combined_atm_retrieval_script.py`
**Purpose**: Main orchestration script
- Coordinates all modules
- Provides command-line interface
- Handles overall process flow
- Error handling and logging
- JSON output generation

**Key Classes**:
- `ATMOrchestrator`: Main orchestration handler

## Usage

### Command Line Interface

```bash
# Run in demo mode
python combined_atm_retrieval_script.py --demo

# Run without cash information
python combined_atm_retrieval_script.py --no-cash

# Run without database save
python combined_atm_retrieval_script.py --no-db

# Get terminal status only (quick mode)
python combined_atm_retrieval_script.py --status-only

# Use new database tables
python combined_atm_retrieval_script.py --use-new-tables

# Specify output file
python combined_atm_retrieval_script.py --output-file custom_output.json

# Enable verbose logging
python combined_atm_retrieval_script.py --verbose
```

### Programmatic Usage

```python
from combined_atm_retrieval_script import ATMOrchestrator

# Create orchestrator
orchestrator = ATMOrchestrator(demo_mode=False, save_to_db=True)

# Run full retrieval
success = orchestrator.run_full_retrieval(
    include_cash=True,
    use_new_tables=False
)

# Get status only
status_info = orchestrator.get_terminal_status_only()
```

## Features

### Modular Design
- Each module has a single responsibility
- Easy to test individual components
- Clear separation of concerns
- Maintainable and extensible

### Error Handling
- Comprehensive error handling at each level
- Graceful degradation
- Proper logging throughout
- Transaction rollback on database errors

### Demo Mode
- Built-in demo mode for testing
- Demo data generation
- No real API calls in demo mode

### Flexible Configuration
- Environment variable support
- Centralized configuration
- Easy to modify settings

### Database Support
- PostgreSQL support with psycopg2
- Automatic table creation
- JSONB support for complex data
- Transaction handling

### Logging
- Comprehensive logging system
- File and console output
- Configurable log levels
- Detailed error reporting

## Data Flow

1. **Initialization**: Load configuration and initialize modules
2. **Authentication**: Login and establish session
3. **Regional Data**: Retrieve regional information
4. **Terminal Details**: Retrieve terminal details
5. **Cash Information**: Retrieve cash information (optional)
6. **Data Processing**: Process all raw data
7. **Database Save**: Save to database (optional)
8. **Output**: Generate JSON output and summary
9. **Cleanup**: Logout and cleanup

## Migration from Monolithic Script

The old monolithic script has been replaced with this modular system:

- **Old**: `combined_atm_retrieval_script_integrated.py` (monolithic)
- **New**: Multiple focused modules + orchestration script

### Benefits of Migration

1. **Maintainability**: Easier to maintain and debug
2. **Testability**: Each module can be tested independently
3. **Reusability**: Modules can be reused in other scripts
4. **Extensibility**: Easy to add new features
5. **Readability**: Clear separation of concerns

## Testing

Each module can be tested independently:

```python
# Test authentication
from atm_auth import ATMAuthenticator
auth = ATMAuthenticator(demo_mode=True)
session = auth.login()

# Test data retrieval
from atm_data_retriever import ATMDataRetriever
retriever = ATMDataRetriever(demo_mode=True)
regional_data = retriever.get_regional_data(session)

# Test cash processing
from atm_cash_processor import ATMCashProcessor
cash_processor = ATMCashProcessor(demo_mode=True)
cash_info = cash_processor.get_cash_information(session, ['83', '88'])
```

## Error Handling

The system includes comprehensive error handling:

- **Authentication errors**: Retry logic with exponential backoff
- **Network errors**: Timeout handling and retries
- **Database errors**: Transaction rollback and connection cleanup
- **Data processing errors**: Validation and error logging
- **System errors**: Graceful degradation and cleanup

## Logging

Logging is configured at multiple levels:

- **INFO**: General operation information
- **WARNING**: Non-critical issues
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information (with --verbose flag)

Log files are written to `atm_retrieval.log` and also output to console.

## Performance

The modular design provides several performance benefits:

- **Parallel processing**: Modules can be run in parallel where appropriate
- **Caching**: Session and data caching
- **Efficient database operations**: Batch operations and transactions
- **Memory management**: Proper cleanup and resource management

## Future Enhancements

The modular architecture makes it easy to add:

- **Additional data sources**: New retrieval modules
- **Different output formats**: XML, CSV, etc.
- **Advanced caching**: Redis or in-memory caching
- **Monitoring and metrics**: Performance monitoring
- **API endpoints**: REST API wrapper
- **Scheduled execution**: Cron job integration

## Dependencies

- `requests`: HTTP client
- `psycopg2`: PostgreSQL driver
- `pytz`: Timezone handling
- `json`: JSON processing
- `argparse`: Command-line argument parsing
- `logging`: Logging framework

## Configuration

Environment variables for database configuration:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: atm_monitor)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password

## Security

- Credentials are managed through environment variables
- Session management with proper logout
- Database connections are properly closed
- Input validation and sanitization

## Conclusion

This modular architecture provides a robust, maintainable, and extensible foundation for ATM data retrieval operations. The clear separation of concerns makes it easy to understand, test, and extend the system as requirements evolve.
