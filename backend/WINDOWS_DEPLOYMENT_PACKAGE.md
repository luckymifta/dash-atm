# 🚀 ATM Retrieval Script - Windows Deployment Package

## 📦 Required Files for Windows Machine

Copy the following files from your macOS backend folder to your Windows machine:

### 🗂️ **Essential Files (Must Copy)**

#### **Core Application Files:**
1. `combined_atm_retrieval_script.py` - Main ATM retrieval script
2. `db_connector_new.py` - New PostgreSQL database connector 
3. `config.json` - Application configuration
4. `requirements_database.txt` - Python dependencies

#### **Windows Batch Scripts:**
5. `install.bat` - Windows installation script
6. `run_continuous.bat` - Continuous operation script
7. `run_single.bat` - Single execution script
8. `install_service.bat` - Windows service installer
9. `manage_service.bat` - Service management script

#### **Configuration Templates:**
10. `.env.template` - Environment configuration template
11. `atm_service.py` - Windows service wrapper (if running as service)

### 🔧 **Windows Deployment Steps**

## Step 1: Create Directory Structure
```batch
# Create main directory
mkdir C:\ATM_Monitor
cd C:\ATM_Monitor

# Create subdirectories
mkdir logs
mkdir output
mkdir data
```

## Step 2: Copy Files
Copy all the files listed above to `C:\ATM_Monitor\`

## Step 3: Create Environment Configuration
```batch
# Copy template to active config
copy .env.template .env

# Edit .env file with your specific settings:
# - Database credentials (already configured for your PostgreSQL)
# - ATM system URL
# - Operational parameters
```

## Step 4: Install Dependencies
```batch
# Run as Administrator
cd C:\ATM_Monitor
install.bat
```

## Step 5: Test Installation
```batch
# Test with demo mode first
run_single.bat --demo --save-to-db --use-new-tables

# If demo works, test continuous mode for 5 minutes
run_continuous.bat --demo
```

## Step 6: Production Run
```batch
# Run continuous production mode
run_continuous.bat

# OR install as Windows service for automatic startup
install_service.bat
```

---

## 📋 **Command Reference**

### **Single Execution Commands:**
```batch
# Demo mode (safe testing)
run_single.bat --demo --save-to-db --use-new-tables

# Production single run
run_single.bat --save-to-db --use-new-tables

# Production with JSON export
run_single.bat --save-to-db --use-new-tables --save-json
```

### **Continuous Operation Commands:**
```batch
# Demo continuous mode (for testing)
run_continuous.bat --demo

# Production continuous mode (recommended)
run_continuous.bat

# Continuous with custom interval (e.g., every 15 minutes)
run_continuous.bat --interval 15
```

### **Service Management Commands:**
```batch
# Install as Windows service (run as Administrator)
install_service.bat

# Start/Stop/Restart service
manage_service.bat start
manage_service.bat stop
manage_service.bat restart

# Check service status
manage_service.bat status
```

---

## 🎯 **Recommended Production Setup**

### **Option A: Manual Continuous Mode**
```batch
cd C:\ATM_Monitor
run_continuous.bat
```
- Keeps terminal window open
- Easy to monitor and stop
- Logs to `logs\continuous_YYYYMMDD_HHMMSS.log`

### **Option B: Windows Service (Advanced)**
```batch
# One-time setup (as Administrator)
cd C:\ATM_Monitor
install_service.bat

# Service runs automatically on Windows startup
# Managed through Windows Services console
```

---

## 📊 **Database Configuration**

Your `.env` file should contain:
```ini
# Database (already configured for your PostgreSQL)
DB_HOST=88.222.214.26
DB_PORT=5432
DB_NAME=development_db
DB_USER=timlesdev
DB_PASS=timlesdev

# ATM System
LOGIN_URL=https://172.31.1.46/sigit/user/login?language=EN

# Operation Settings
CONTINUOUS_INTERVAL=30  # minutes between runs
SAVE_TO_DB=true
USE_NEW_TABLES=true
```

---

## 🔍 **Monitoring & Logs**

- **Real-time monitoring**: Watch the terminal/command prompt
- **Log files**: Check `logs\` directory for detailed execution logs
- **Database verification**: Use `query_database.py` (if copied) to check data
- **Service logs**: Windows Event Viewer (if running as service)

---

## ⚠️ **Important Notes**

1. **Database is ready**: Your PostgreSQL database is already set up and cleaned
2. **Test first**: Always run with `--demo` flag initially
3. **Network access**: Ensure Windows machine can reach both:
   - Database server: `88.222.214.26:5432`
   - ATM system: `172.31.1.46`
4. **Firewall**: Configure Windows Firewall if needed
5. **Python version**: Ensure Python 3.8+ is installed
6. **Administrator rights**: Required for service installation

---

## 🎉 **Quick Start Command**

After copying files and setting up `.env`:
```batch
cd C:\ATM_Monitor
install.bat
run_single.bat --demo --save-to-db --use-new-tables
```

If demo succeeds:
```batch
run_continuous.bat
```

**Your ATM data will be automatically saved to the PostgreSQL database!** 🚀
