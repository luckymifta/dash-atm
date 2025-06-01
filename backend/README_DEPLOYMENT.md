# Combined ATM Retrieval Script - Windows Deployment Package

## 📦 Package Contents

This package contains everything needed to deploy the Combined ATM Retrieval Script on Windows:

### Core Files
- `combined_atm_retrieval_script.py` - Main application (1,764 lines)
- `db_connector.py` - Database connectivity module
- `atm_service.py` - Windows service wrapper

### Configuration Files
- `.env.template` - Environment variables template
- `config.json` - Application configuration
- `requirements.txt` - Python dependencies

### Windows Scripts
- `install.bat` - Complete installation script
- `run_single.bat` - Single execution
- `run_continuous.bat` - Continuous operation
- `install_service.bat` - Windows service installation
- `manage_service.bat` - Service management
- `test_installation.bat` - Installation validation

### Documentation
- `WINDOWS_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `README_DEPLOYMENT.md` - This file

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites
- Windows 10/11
- Python 3.8+ installed and in PATH
- Administrator access for service installation

### 2. Installation
```batch
# Create directory
mkdir C:\ATM_Monitor
cd C:\ATM_Monitor

# Copy all files to this directory
# Then run:
install.bat
```

### 3. Configuration
Edit `.env` file with your settings:
```env
DB_HOST=your_database_ip
DB_PORT=5432
DB_NAME=dash
DB_USER=your_username
DB_PASS=your_password
LOGIN_URL=your_atm_system_url
```

### 4. Test
```batch
test_installation.bat
run_single.bat --demo
```

### 5. Deploy
```batch
# For continuous operation
run_continuous.bat

# For Windows service (as Administrator)
install_service.bat
```

## ⚙️ Features

### Continuous Operation
- Runs every 30 minutes (configurable)
- Automatic error recovery
- Intelligent retry logic
- Graceful shutdown handling

### Database Integration
- PostgreSQL connectivity
- Automatic table creation
- Both original and JSONB table support
- Transactional data integrity

### Error Handling
- 15-minute waits for LOGIN_URL failures
- 5-minute waits for general errors
- Automatic restart on failure
- Comprehensive logging

### Windows Service
- Automatic startup with Windows
- Restart on failure
- Windows Event Log integration
- Service management tools

## 📊 Operational Modes

### Demo Mode
```batch
run_single.bat --demo
```
- No real API calls
- Tests all functionality
- Safe for development

### Single Execution
```batch
run_single.bat --save-to-db --use-new-tables
```
- One-time execution
- Database saving
- Manual operation

### Continuous Mode
```batch
run_continuous.bat
```
- Runs indefinitely
- 30-minute intervals
- Automatic error recovery

### Windows Service
```batch
install_service.bat
net start ATMMonitorService
```
- Background operation
- Automatic startup
- System integration

## 🗃️ Database Support

### Original Tables
- `regional_atm_counts` - Regional statistics
- `terminals` - Terminal information
- `terminal_faults` - Fault data

### New JSONB Tables
- `regional_data` - Enhanced regional data with JSONB
- `terminal_details` - Full terminal data with JSONB
- Raw API responses preserved

## 📋 Command Line Options

### Available Arguments
- `--continuous` - Run continuously
- `--demo` - Demo mode
- `--save-to-db` - Save to database
- `--use-new-tables` - Use JSONB tables
- `--save-json` - Save JSON files
- `--total-atms N` - ATM count
- `--quiet` - Reduce logging

### Usage Examples
```batch
# Demo test
run_single.bat --demo --save-json

# Production single run
run_single.bat --save-to-db --use-new-tables

# Continuous with new tables
run_continuous.bat --save-to-db --use-new-tables

# Custom ATM count
run_single.bat --total-atms 20 --save-to-db
```

## 🔧 Management Tools

### Service Management
```batch
manage_service.bat
```
Options:
1. Check service status
2. Start service
3. Stop service
4. Restart service
5. View logs
6. Remove service
7. Reinstall service

### Testing
```batch
test_installation.bat
```
Validates:
- Python environment
- Dependencies
- Script syntax
- Demo functionality
- Database connectivity

## 📁 Directory Structure

```
C:\ATM_Monitor\
├── combined_atm_retrieval_script.py
├── db_connector.py
├── atm_service.py
├── requirements.txt
├── .env
├── config.json
├── install.bat
├── run_single.bat
├── run_continuous.bat
├── install_service.bat
├── manage_service.bat
├── test_installation.bat
├── venv\                    # Virtual environment
├── logs\                    # Log files
├── output\                  # JSON output
└── data\                    # Data files
```

## 📊 Monitoring

### Log Files
- `logs\combined_atm_retrieval.log` - Application log
- `logs\service.log` - Service log
- `logs\continuous_YYYYMMDD_HHMMSS.log` - Session logs
- `logs\single_YYYYMMDD_HHMMSS.log` - Single run logs

### Metrics Tracked
- Total execution cycles
- Success/failure rates
- Connection failure counts
- Average execution time
- Memory usage
- Last successful run

### Health Monitoring
```batch
# Check service status
sc query ATMMonitorService

# View recent logs
type logs\service.log | more

# Monitor performance
tasklist /fi "imagename eq python.exe"
```

## 🔒 Security

### File Permissions
- Restrict `.env` file access
- Use dedicated service account
- Enable logging audit trails

### Network Security
- HTTPS for API connections
- SSL for database connections
- Firewall configuration

### Database Security
- Minimal privilege user
- Connection encryption
- Query logging

## 🛠️ Troubleshooting

### Common Issues

#### Installation Fails
- Run `install.bat` as Administrator
- Check Python installation
- Verify internet connectivity

#### Service Won't Start
- Check Windows Event Viewer
- Verify `.env` configuration
- Test with `run_single.bat --demo`

#### Database Connection Failed
- Verify `.env` settings
- Test network connectivity
- Check database server status

#### API Connection Issues
- Verify LOGIN_URL
- Check network/firewall
- Test with demo mode first

### Getting Help
1. Run `test_installation.bat`
2. Check log files in `logs\`
3. Verify configuration files
4. Test in demo mode
5. Contact system administrator

## 📞 Support

### Log Analysis
Check these files for issues:
- `logs\combined_atm_retrieval.log`
- `logs\service.log`
- Windows Event Viewer

### Configuration Validation
Use `test_installation.bat` to validate setup

### Emergency Recovery
```batch
# Stop service
net stop ATMMonitorService

# Reset configuration
copy .env.template .env

# Test basic functionality
run_single.bat --demo

# Restart service
net start ATMMonitorService
```

---

**Package Version**: 1.0  
**Compatible with**: Windows 10/11, Python 3.8+  
**Last Updated**: December 2024
