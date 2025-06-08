#!/bin/bash
# ATM Monitor - Windows Deployment Package Creator
# This script copies all necessary files for Windows deployment

# Set source and destination directories
SOURCE_DIR="/Users/luckymifta/Documents/2. AREA/dash-atm/backend"
DEST_DIR="/Users/luckymifta/Documents/2. AREA/dash-atm/backend/windows_deployment_package"

echo "=========================================="
echo "ATM Monitor - Windows Deployment Package"
echo "=========================================="
echo ""

# Create destination directory
echo "Creating deployment package directory..."
mkdir -p "$DEST_DIR"
mkdir -p "$DEST_DIR/logs"
mkdir -p "$DEST_DIR/output"
mkdir -p "$DEST_DIR/data"

# Copy essential files
echo "Copying essential files..."

# Core application files
cp "$SOURCE_DIR/combined_atm_retrieval_script.py" "$DEST_DIR/"
cp "$SOURCE_DIR/db_connector_new.py" "$DEST_DIR/"
cp "$SOURCE_DIR/config.json" "$DEST_DIR/"
cp "$SOURCE_DIR/requirements_database.txt" "$DEST_DIR/"

# Windows batch scripts
cp "$SOURCE_DIR/install.bat" "$DEST_DIR/"
cp "$SOURCE_DIR/run_continuous.bat" "$DEST_DIR/"
cp "$SOURCE_DIR/run_single.bat" "$DEST_DIR/"
cp "$SOURCE_DIR/install_service.bat" "$DEST_DIR/"
cp "$SOURCE_DIR/manage_service.bat" "$DEST_DIR/"

# Configuration files
cp "$SOURCE_DIR/.env.template" "$DEST_DIR/"
cp "$SOURCE_DIR/atm_service.py" "$DEST_DIR/" 2>/dev/null || echo "Note: atm_service.py not found (optional)"

# Documentation
cp "$SOURCE_DIR/WINDOWS_DEPLOYMENT_PACKAGE.md" "$DEST_DIR/"
cp "$SOURCE_DIR/WINDOWS_DEPLOYMENT_GUIDE.md" "$DEST_DIR/" 2>/dev/null || echo "Note: WINDOWS_DEPLOYMENT_GUIDE.md not found"

# Optional files
cp "$SOURCE_DIR/query_database.py" "$DEST_DIR/" 2>/dev/null || echo "Note: query_database.py not found (optional)"
cp "$SOURCE_DIR/test_database_setup.py" "$DEST_DIR/" 2>/dev/null || echo "Note: test_database_setup.py not found (optional)"

echo ""
echo "✅ Deployment package created successfully!"
echo ""
echo "Package location: $DEST_DIR"
echo ""
echo "Files included:"
ls -la "$DEST_DIR" | grep -v "^d" | awk '{print "  " $9}' | grep -v "^  $"
echo ""
echo "Directories created:"
ls -la "$DEST_DIR" | grep "^d" | awk '{print "  " $9 "/"}' | grep -v "^  .$" | grep -v "^  ..$"
echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo "1. Copy the entire 'windows_deployment_package' folder to your Windows machine"
echo "2. Place it in: C:\\ATM_Monitor\\"
echo "3. Follow instructions in WINDOWS_DEPLOYMENT_PACKAGE.md"
echo "4. Run: install.bat (as Administrator)"
echo "5. Test: run_single.bat --demo --save-to-db --use-new-tables"
echo "6. Production: run_continuous.bat"
echo ""
echo "🎉 Ready for Windows deployment!"
