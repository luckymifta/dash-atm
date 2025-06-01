# Windows Deployment Guide for Combined ATM Retrieval Script

## 📋 Overview
This guide provides complete instructions for deploying the Combined ATM Retrieval Script on a Windows machine with database connectivity and continuous operation capabilities.

## 🗂️ Required Files for Windows Deployment

### Core Script Files
1. **`combined_atm_retrieval_script.py`** - Main application script
2. **`db_connector.py`** - Database connectivity module
3. **`requirements.txt`** - Python dependencies
4. **`.env`** - Environment configuration file
5. **`install.bat`** - Windows installation script
6. **`run_continuous.bat`** - Script to run continuously
7. **`run_single.bat`** - Script for single execution
8. **`install_service.bat`** - Windows service installation
9. **`atm_service.py`** - Windows service wrapper

### Configuration Files
- **`config.json`** - Application configuration
- **`logging.conf`** - Logging configuration

## 🚀 Quick Start Installation

### Step 1: Download and Extract Files
1. Create a folder: `C:\ATM_Monitor\`
2. Copy all deployment files to this folder
3. Ensure you have Python 3.8+ installed

### Step 2: Install Dependencies
```batch
# Right-click and "Run as Administrator"
cd C:\ATM_Monitor
install.bat
```

### Step 3: Configure Environment
1. Edit `.env` file with your database credentials:
```env
# Database connection details
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=dash
DB_USER=your_username
DB_PASS=your_password

# ATM System URL
LOGIN_URL=your_login_url
```

### Step 4: Test Installation
```batch
# Test single run
run_single.bat --demo

# Test continuous mode (5 minutes)
run_continuous.bat --demo
```

### Step 5: Install as Windows Service (Optional)
```batch
# Right-click and "Run as Administrator"
install_service.bat
```

## 📁 Detailed File Descriptions

### Core Application Files

#### `combined_atm_retrieval_script.py`
- Main application script with continuous operation capabilities
- Features: Error handling, retry logic, database integration, signal handling
- Size: ~1,764 lines with comprehensive functionality

#### `db_connector.py` 
- Database connectivity and table management
- Supports both original and new JSONB tables
- Automatic table creation and schema validation

### Windows Batch Scripts

#### `install.bat`
- Installs Python dependencies
- Creates necessary directories
- Sets up logging configuration
- Validates installation

#### `run_continuous.bat`
- Starts continuous operation mode
- Configurable intervals (default: 30 minutes)
- Automatic restart on failure
- Logging to files

#### `run_single.bat`
- Single execution mode
- Useful for testing and manual runs
- Command-line argument support

#### `install_service.bat`
- Installs application as Windows service
- Enables automatic startup
- Service management capabilities

## ⚙️ Configuration Options

### Environment Variables (`.env`)
```env
# Database Configuration
DB_HOST=88.222.214.26          # Database server IP/hostname
DB_PORT=5432                   # Database port
DB_NAME=dash                   # Database name
DB_USER=timlesdev              # Database username
DB_PASS=timlesdev              # Database password

# Application Configuration
LOGIN_URL="https://172.31.1.46/sigit/user/login?language=EN"
TOTAL_ATMS=14                  # Total ATM count for calculations
LOG_LEVEL=INFO                 # Logging level (DEBUG, INFO, WARNING, ERROR)

# Operational Settings
CONTINUOUS_INTERVAL=30         # Minutes between cycles
RETRY_INTERVAL=5               # Minutes between retries
CONNECTION_RETRY_INTERVAL=15   # Minutes for connection failures
MAX_RETRIES=3                  # Maximum retry attempts
```

### Application Configuration (`config.json`)
```json
{
  "operation": {
    "continuous_mode": true,
    "interval_minutes": 30,
    "retry_attempts": 3,
    "timeout_seconds": 300
  },
  "database": {
    "save_to_db": true,
    "use_new_tables": true,
    "connection_timeout": 30,
    "query_timeout": 60
  },
  "logging": {
    "level": "INFO",
    "file_rotation": true,
    "max_file_size": "10MB",
    "backup_count": 5
  },
  "atm_system": {
    "total_atms": 14,
    "demo_mode": false,
    "save_json": true
  }
}
```

## 🔧 Command Line Usage

### Basic Commands
```batch
# Single execution with database save
run_single.bat --save-to-db

# Continuous mode with new tables
run_continuous.bat --continuous --save-to-db --use-new-tables

# Demo mode for testing
run_single.bat --demo --save-json

# Specific ATM count
run_single.bat --total-atms 20 --save-to-db

# Quiet mode (reduced logging)
run_continuous.bat --continuous --quiet
```

### Available Arguments
- `--continuous` - Run in continuous mode
- `--demo` - Use demo mode (no real API calls)
- `--save-to-db` - Save data to database
- `--use-new-tables` - Use new JSONB tables
- `--save-json` - Save JSON output files
- `--total-atms N` - Set total ATM count
- `--quiet` - Reduce logging output

## 🖥️ Windows Service Installation

### Install Service
```batch
# Run as Administrator
cd C:\ATM_Monitor
install_service.bat
```

### Service Management
```batch
# Start service
net start ATMMonitorService

# Stop service
net stop ATMMonitorService

# Check service status
sc query ATMMonitorService

# Remove service
sc delete ATMMonitorService
```

### Service Configuration
The service runs with these default settings:
- **Service Name**: ATMMonitorService
- **Display Name**: ATM Monitor Continuous Service
- **Start Type**: Automatic
- **Log File**: `C:\ATM_Monitor\logs\service.log`

## 📊 Monitoring and Maintenance

### Log Files
- **`combined_atm_retrieval.log`** - Main application log
- **`service.log`** - Windows service log
- **`error.log`** - Error-specific log
- **`performance.log`** - Performance metrics

### Monitoring Metrics
The application tracks:
- Total execution cycles
- Successful/failed cycles
- Connection failures
- Average cycle duration
- Last successful execution
- Error counts by type

### Health Checks
```batch
# Check service status
run_single.bat --demo

# Validate database connection
python -c "import db_connector; print('OK' if db_connector.get_db_connection() else 'FAIL')"

# Test API connectivity
curl -k https://your-login-url
```

## 🛠️ Troubleshooting

### Common Issues

#### Database Connection Failed
1. Verify `.env` file configuration
2. Check database server accessibility
3. Validate credentials
4. Test network connectivity

#### Service Won't Start
1. Check Windows Event Viewer
2. Verify Python installation
3. Ensure all dependencies installed
4. Check file permissions

#### API Connection Issues
1. Verify LOGIN_URL in `.env`
2. Check network connectivity
3. Validate SSL certificates
4. Review firewall settings

### Error Codes
- **Exit Code 1**: Configuration error
- **Exit Code 2**: Database connection failed
- **Exit Code 3**: API connection failed
- **Exit Code 4**: Critical application error

## 📈 Performance Optimization

### Recommended Settings
- **RAM**: Minimum 2GB available
- **Disk**: 10GB free space for logs
- **Network**: Stable internet connection
- **CPU**: 2+ cores recommended

### Optimization Tips
1. Use SSD for better I/O performance
2. Configure log rotation to manage disk space
3. Monitor memory usage during continuous operation
4. Set appropriate timeout values for your network

## 🔒 Security Considerations

### File Permissions
- Restrict access to `.env` file
- Use dedicated service account
- Enable Windows Defender exclusions if needed

### Network Security
- Use HTTPS for all API connections
- Configure firewall rules appropriately
- Consider VPN for database connections

### Database Security
- Use dedicated database user with minimal privileges
- Enable SSL for database connections
- Regular security updates

## 📞 Support and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Check log files for errors
2. **Monthly**: Verify database table sizes
3. **Quarterly**: Update dependencies
4. **Annually**: Review security settings

### Backup Procedures
1. Backup configuration files (`.env`, `config.json`)
2. Export database schemas and critical data
3. Document custom configurations
4. Test restoration procedures

### Contact Information
For technical support and issues:
- Check log files first
- Review this documentation
- Contact system administrator
- Escalate to development team if needed

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Compatible with**: Windows 10/11, Python 3.8+
