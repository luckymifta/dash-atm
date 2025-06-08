## Essential Files for Windows Deployment

Copy these **8 files** to your Windows machine:

### **Core Scripts:**
1. `combined_atm_retrieval_script.py` - Main ATM retrieval script
2. `db_connector_new.py` - Database connector (has your credentials built-in)

### **Configuration:**
3. `all_terminals_config.json` - Terminal configuration
4. `config.json` - Application configuration (if exists)

### **Dependencies:**
5. `requirements.txt` - Python packages

### **Windows Batch Files:**
6. `install.bat` - Setup script
7. `run_continuous.bat` - Continuous mode runner
8. `test_installation.bat` - Testing script

## **No .env File Needed!**

Your database credentials are already hardcoded in `db_connector_new.py`:
- Host: 88.222.214.26
- Port: 5432  
- Database: development_db
- Username: timlesdev
- Password: timlesdev

## **Commands to Run on Windows:**

1. **Setup (run once):**
```cmd
install.bat
```

2. **Run continuous mode with database:**
```cmd
python combined_atm_retrieval_script.py --continuous --save-to-db --use-new-tables
```

**OR use the batch file:**
```cmd
run_continuous.bat
```

That's it! No .env file required. 🎯
