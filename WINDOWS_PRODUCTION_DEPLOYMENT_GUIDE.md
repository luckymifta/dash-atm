# Windows Production Deployment Guide

## ATM Terminal Discovery Script - Windows Ready Version 2.0

This guide provides step-by-step instructions for deploying the enhanced ATM terminal discovery script on a Windows production environment.

## ✅ Pre-Deployment Verification

The script has been enhanced with the following Windows-specific improvements:

### 🔧 Windows Compatibility Enhancements

1. **Enhanced File Path Handling**
   - Cross-platform path normalization using `os.path.normpath()`
   - Proper UTF-8 encoding for all file operations
   - Windows directory creation with `os.makedirs(exist_ok=True)`

2. **Improved Session Configuration**
   - Windows-optimized HTTP session with connection pooling
   - Extended timeouts for Windows networking: `(30, 60)` seconds
   - Enhanced retry logic: 3 attempts on Windows vs 2 on other platforms

3. **Robust Error Handling**
   - Windows-specific error detection (WinError, SSL certificate issues)
   - Detailed error logging with Windows troubleshooting suggestions
   - Graceful degradation when network issues occur

4. **Production Logging**
   - Windows environment detection and validation logging
   - Performance metrics for troubleshooting
   - Detailed file location logging for debugging

## 🚀 Installation Steps

### 1. System Requirements

```bash
# Ensure Python 3.8+ is installed
python --version

# Check pip is available
pip --version
```

### 2. Create Project Directory

```cmd
# Create the project directory
mkdir C:\ATM-Monitoring
cd C:\ATM-Monitoring

# Create subdirectories
mkdir backend
mkdir logs
```

### 3. Install Dependencies

Create `requirements.txt`:
```
requests>=2.31.0
urllib3>=2.0.0
pytz>=2023.3
tqdm>=4.65.0
```

Install packages:
```cmd
pip install -r requirements.txt
```

### 4. Deploy the Script

Copy the enhanced script to your Windows environment:
```cmd
# Place the script in the backend directory
copy combined_atm_retrieval_script.py C:\ATM-Monitoring\backend\
```

## 🔧 Configuration

### 1. Environment Variables (Optional)

```cmd
# Set environment variables if needed
set ATM_DEMO_MODE=false
set ATM_TOTAL_COUNT=14
```

### 2. File Permissions

Ensure the script directory has write permissions for the discovery file:
```cmd
# Grant write permissions to the backend directory
icacls C:\ATM-Monitoring\backend /grant %USERNAME%:F /T
```

## 🎯 Execution

### 1. Test Mode First

Run in demo mode to test Windows compatibility:
```cmd
cd C:\ATM-Monitoring
python backend\combined_atm_retrieval_script.py --demo --total-atms 14
```

Expected output:
```
🚀 Initialized CombinedATMRetriever - Demo: True, Total ATMs: 14
💻 Platform: nt - Script optimized for Windows production
📁 Working directory: C:\ATM-Monitoring
📄 Script location: C:\ATM-Monitoring\backend\combined_atm_retrieval_script.py
```

### 2. Production Mode

Once testing is successful, run in production mode:
```cmd
python backend\combined_atm_retrieval_script.py --total-atms 14 --save-to-db
```

## 📊 Windows-Specific Features

### 1. Terminal Discovery Persistence

The script automatically creates and manages:
- `discovered_terminals.json` - Persistent terminal discovery storage
- Location: `C:\ATM-Monitoring\backend\discovered_terminals.json`

### 2. Enhanced Logging

Windows-specific log messages include:
- 🪟 Windows retry notifications
- 💻 Platform identification
- 📁 File location details
- ✅ Windows production validation

### 3. Error Recovery

Windows-specific error handling:
- **WinError detection**: Network connectivity issues
- **Certificate errors**: Windows certificate store problems  
- **Permission errors**: File system access issues
- **Timeout handling**: Extended timeouts for Windows networking

## 🔍 Monitoring and Troubleshooting

### 1. Log Files

Monitor these log files:
```
C:\ATM-Monitoring\combined_atm_retrieval.log  - Main application log
C:\ATM-Monitoring\backend\discovered_terminals.json - Terminal discovery data
```

### 2. Common Windows Issues

**Network Connectivity:**
```cmd
# Test network connectivity
ping 172.31.1.46
telnet 172.31.1.46 443
```

**Firewall Issues:**
```cmd
# Check Windows Firewall
netsh advfirewall show allprofiles
```

**Certificate Issues:**
```cmd
# Update certificates
certlm.msc
```

### 3. Performance Monitoring

The script logs Windows-specific performance metrics:
- HTTP session status
- Memory usage optimization
- Terminal processing speed
- Discovery file operations

## 🎯 Production Deployment Checklist

- [ ] ✅ Python 3.8+ installed
- [ ] ✅ Dependencies installed via pip
- [ ] ✅ Directory structure created
- [ ] ✅ File permissions configured
- [ ] ✅ Demo mode tested successfully
- [ ] ✅ Network connectivity verified
- [ ] ✅ Windows Firewall configured
- [ ] ✅ Log monitoring set up
- [ ] ✅ Discovery persistence tested
- [ ] ✅ Production run completed

## 🔄 Automated Scheduling (Optional)

Set up Windows Task Scheduler for automated runs:

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task
3. Set trigger (e.g., daily at 6:00 AM)
4. Set action:
   - Program: `python`
   - Arguments: `backend\combined_atm_retrieval_script.py --total-atms 14 --save-to-db`
   - Start in: `C:\ATM-Monitoring`

## 📈 Success Metrics

After deployment, verify these success indicators:

1. **Terminal Discovery**: All 14+ terminals found and processed
2. **Persistence**: `discovered_terminals.json` created and updated
3. **Database**: Terminal details saved to database successfully
4. **Logging**: Clean logs with Windows-optimized messages
5. **Performance**: Consistent execution times on Windows

## 🆘 Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Check discovery file growth and terminal counts
2. **Monthly**: Review log files for Windows-specific errors
3. **Quarterly**: Update dependencies and test compatibility

### Contact Information

For Windows-specific deployment issues:
- Check logs in `C:\ATM-Monitoring\combined_atm_retrieval.log`
- Verify discovery data in `discovered_terminals.json`
- Monitor Windows Event Viewer for system-level issues

---

## 🎉 Deployment Complete

The enhanced ATM terminal discovery script is now ready for production use on Windows environments with:

- ✅ **Comprehensive terminal search** across all 14+ ATMs
- ✅ **New terminal discovery** with persistent storage
- ✅ **Windows-optimized** networking and file operations
- ✅ **Robust error handling** for Windows-specific issues
- ✅ **Production logging** with detailed diagnostics

**Next Steps**: Schedule regular execution and monitor the discovery file for new terminals as your ATM network expands.
