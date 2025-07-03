# Database Connection Setup Guide

This guide explains how to properly configure database connections for the ATM Dashboard application.

## Environment Variables Setup

The application uses environment variables loaded from a `.env` file to configure database connections. This approach ensures that sensitive information like database passwords are not hardcoded into the application.

### 1. Create .env File

You can create a `.env` file manually or use the provided setup script:

```bash
# Run the setup script (interactive)
./setup_env.sh
```

Or manually copy the example file:
```bash
# Copy the example file
cp .env.example .env

# Edit the file with your database details
nano .env
```

### 2. Required Environment Variables

Make sure your `.env` file contains these database connection variables:

```
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=atm_database
DB_USER=postgres
DB_PASSWORD=your_database_password
```

## Verification and Testing

To verify that your environment variables are loaded correctly:

```bash
# Run the environment verification script
python verify_env_loading.py
```

To test the database connection:

```bash
# Test database connection using environment variables
python test_db_connection.py
```

## Troubleshooting

### Connection Issues

If you're encountering database connection issues:

1. Make sure your `.env` file is in the `backend/` directory
2. Check that the file has correct permissions
3. Ensure the database server is running and accessible
4. Verify your database credentials

### Missing dotenv Module

If you get an error about the `dotenv` module:

```bash
pip install python-dotenv
```

## Windows-Specific Notes

On Windows systems, environment variables can also be set at the system level:

1. Right-click on 'My Computer' or 'This PC' and select 'Properties'
2. Click 'Advanced system settings'
3. Click 'Environment Variables'
4. Add your database connection variables

## Script Files

- `verify_env_loading.py`: Checks that environment variables are loaded correctly
- `test_db_connection.py`: Tests connection to the database using environment variables
- `setup_env.sh`: Helper script to set up your `.env` file
