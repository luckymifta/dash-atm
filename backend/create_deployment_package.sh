#!/bin/bash
# ATM Data Retrieval System - VPS Deployment Package Creator
# This script creates a deployment package for your VPS

echo "==============================================="
echo "ATM DATA RETRIEVAL SYSTEM - DEPLOYMENT PACKAGE"
echo "==============================================="

# Create deployment directory
DEPLOY_DIR="atm_deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

echo "Creating deployment package in: $DEPLOY_DIR"

# Copy essential files
echo "Copying core files..."
cp combined_atm_retrieval_script.py "$DEPLOY_DIR/"
cp db_connector_new.py "$DEPLOY_DIR/"
cp setup_database.py "$DEPLOY_DIR/"
cp test_database_setup.py "$DEPLOY_DIR/"
cp query_database.py "$DEPLOY_DIR/"
cp requirements_database.txt "$DEPLOY_DIR/"
cp DATABASE_SETUP_GUIDE.md "$DEPLOY_DIR/"

# Create VPS-specific files
echo "Creating VPS deployment files..."

# Create VPS setup script
cat > "$DEPLOY_DIR/vps_setup.sh" << 'EOF'
#!/bin/bash
# VPS Setup Script for ATM Data Retrieval System

echo "Setting up ATM Data Retrieval System on VPS..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and PostgreSQL client
echo "Installing Python and PostgreSQL..."
sudo apt install -y python3 python3-pip python3-venv postgresql-client

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv atm_env
source atm_env/bin/activate

# Install Python requirements
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements_database.txt

# Make scripts executable
chmod +x *.py
chmod +x *.sh

echo "VPS setup completed!"
echo "Next steps:"
echo "1. Run: python3 setup_database.py"
echo "2. Test: python3 test_database_setup.py"
echo "3. Run: python3 combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables"
EOF

# Create systemd service file
cat > "$DEPLOY_DIR/atm-retrieval.service" << 'EOF'
[Unit]
Description=ATM Data Retrieval System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/atm-system
Environment=PATH=/home/ubuntu/atm-system/atm_env/bin
ExecStart=/home/ubuntu/atm-system/atm_env/bin/python combined_atm_retrieval_script.py --continuous --save-to-db --use-new-tables
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Create deployment script for VPS
cat > "$DEPLOY_DIR/deploy_to_vps.sh" << 'EOF'
#!/bin/bash
# Deployment script for VPS

VPS_HOST="88.222.214.26"
VPS_USER="ubuntu"  # Change this to your VPS username
DEPLOY_PATH="/home/$VPS_USER/atm-system"

echo "Deploying to VPS: $VPS_HOST"

# Create directory on VPS
ssh $VPS_USER@$VPS_HOST "mkdir -p $DEPLOY_PATH"

# Copy files to VPS
echo "Copying files to VPS..."
scp *.py $VPS_USER@$VPS_HOST:$DEPLOY_PATH/
scp *.txt $VPS_USER@$VPS_HOST:$DEPLOY_PATH/
scp *.md $VPS_USER@$VPS_HOST:$DEPLOY_PATH/
scp *.sh $VPS_USER@$VPS_HOST:$DEPLOY_PATH/
scp *.service $VPS_USER@$VPS_HOST:$DEPLOY_PATH/

echo "Files copied successfully!"
echo "Next steps on VPS:"
echo "1. ssh $VPS_USER@$VPS_HOST"
echo "2. cd $DEPLOY_PATH"
echo "3. chmod +x vps_setup.sh && ./vps_setup.sh"
echo "4. source atm_env/bin/activate"
echo "5. python3 setup_database.py"
EOF

# Create environment configuration
cat > "$DEPLOY_DIR/env_config.py" << 'EOF'
#!/usr/bin/env python3
"""
Environment Configuration for ATM Data Retrieval System
Customize these settings for your VPS deployment
"""

# Database Configuration
DATABASE_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

# ATM System Configuration
ATM_CONFIG = {
    'login_url': "https://172.31.1.46/sigit/user/login?language=EN",
    'logout_url': "https://172.31.1.46/sigit/user/logout",
    'reports_url': "https://172.31.1.46/sigit/reports/dashboards?terminal_type=ATM&status_filter=Status",
    'dashboard_url': "https://172.31.1.46/sigit/terminal/searchTerminalDashBoard?number_of_occurrences=30&terminal_type=ATM",
    'username': "Lucky.Saputra",
    'password': "TimlesMon2025@"
}

# Operational Settings
OPERATION_CONFIG = {
    'total_atms': 14,
    'continuous_interval_minutes': 30,
    'demo_mode': False,
    'save_to_database': True,
    'use_new_tables': True,
    'save_json': True,
    'timezone': 'Asia/Dili'  # UTC+9
}

# Logging Configuration
LOGGING_CONFIG = {
    'log_file': 'atm_retrieval.log',
    'log_level': 'INFO',
    'max_log_size_mb': 50,
    'backup_count': 5
}
EOF

# Create Docker configuration (optional)
cat > "$DEPLOY_DIR/Dockerfile" << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements_database.txt .
RUN pip install --no-cache-dir -r requirements_database.txt

# Copy application files
COPY *.py ./
COPY *.md ./

# Create user for security
RUN useradd -m -u 1000 atmuser && chown -R atmuser:atmuser /app
USER atmuser

# Default command
CMD ["python", "combined_atm_retrieval_script.py", "--continuous", "--save-to-db", "--use-new-tables"]
EOF

# Create docker-compose file
cat > "$DEPLOY_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  atm-retrieval:
    build: .
    container_name: atm-retrieval-system
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./logs:/app/logs
      - ./saved_data:/app/saved_data
    networks:
      - atm-network
    depends_on:
      - db

  db:
    image: postgres:14
    container_name: atm-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: development_db
      POSTGRES_USER: timlesdev
      POSTGRES_PASSWORD: timlesdev
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - atm-network

volumes:
  postgres_data:

networks:
  atm-network:
    driver: bridge
EOF

# Create README for deployment
cat > "$DEPLOY_DIR/README_DEPLOYMENT.md" << 'EOF'
# ATM Data Retrieval System - VPS Deployment

## Quick Start on VPS

### 1. Upload to VPS
```bash
# On your local machine:
chmod +x deploy_to_vps.sh
./deploy_to_vps.sh
```

### 2. Setup on VPS
```bash
# SSH to your VPS:
ssh ubuntu@88.222.214.26
cd /home/ubuntu/atm-system
chmod +x vps_setup.sh
./vps_setup.sh
```

### 3. Initialize Database
```bash
source atm_env/bin/activate
python3 setup_database.py
python3 test_database_setup.py
```

### 4. Run System
```bash
# Test run:
python3 combined_atm_retrieval_script.py --demo --save-to-db --use-new-tables

# Production run:
python3 combined_atm_retrieval_script.py --continuous --save-to-db --use-new-tables
```

### 5. Install as Service (Optional)
```bash
sudo cp atm-retrieval.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable atm-retrieval.service
sudo systemctl start atm-retrieval.service
```

## Configuration Files

- `db_connector_new.py` - Database connection with your credentials
- `combined_atm_retrieval_script.py` - Main ATM data retrieval script
- `env_config.py` - Environment configuration
- `requirements_database.txt` - Python dependencies

## Database Tables

Your system creates these tables automatically:
- `regional_data` - Regional ATM statistics with JSONB storage
- `terminal_details` - Individual terminal data with fault information
- `regional_atm_counts` - Legacy compatibility table

## Monitoring

Check logs:
```bash
tail -f atm_retrieval.log
```

Check service status:
```bash
sudo systemctl status atm-retrieval.service
```

Query database:
```bash
python3 query_database.py
```

## Database Access

Host: 88.222.214.26
Port: 5432
Database: development_db
Username: timlesdev
Password: timlesdev
EOF

# Make scripts executable
chmod +x "$DEPLOY_DIR"/*.sh
chmod +x "$DEPLOY_DIR"/*.py

# Create tar package
echo "Creating deployment package..."
tar -czf "${DEPLOY_DIR}.tar.gz" "$DEPLOY_DIR"

echo ""
echo "✅ Deployment package created successfully!"
echo ""
echo "Package: ${DEPLOY_DIR}.tar.gz"
echo "Directory: $DEPLOY_DIR"
echo ""
echo "Files included:"
ls -la "$DEPLOY_DIR"
echo ""
echo "To deploy to your VPS:"
echo "1. Extract: tar -xzf ${DEPLOY_DIR}.tar.gz"
echo "2. Upload to VPS: scp -r $DEPLOY_DIR ubuntu@88.222.214.26:/home/ubuntu/"
echo "3. SSH to VPS and run setup: ssh ubuntu@88.222.214.26"
echo "4. cd /home/ubuntu/$DEPLOY_DIR && ./vps_setup.sh"
echo ""
echo "🎉 Ready for deployment!"
