#!/bin/bash

# Fix Virtual Environment Permissions and Install Backend Dependencies
# Run this script as root on your VPS

echo "=== Fixing Virtual Environment Permissions and Installing Dependencies ==="

# Navigate to backend directory
cd /var/www/dash-atm/backend

echo "1. Changing virtual environment ownership to www-data..."
chown -R www-data:www-data venv/

echo "2. Verifying ownership change..."
ls -la venv/

echo "3. Activating virtual environment and installing dependencies..."
# Use sudo -u www-data to run commands as www-data user
sudo -u www-data bash << 'EOF'
cd /var/www/dash-atm/backend
source venv/bin/activate

echo "Installing/upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "Installing FastAPI and Uvicorn..."
pip install fastapi uvicorn[standard]

echo "Installing all requirements from requirements.txt..."
pip install -r requirements.txt

echo "Verifying installations..."
pip list | grep -E "(fastapi|uvicorn|sqlalchemy|psycopg2)"

echo "Testing Python imports..."
python -c "import fastapi; import uvicorn; print('FastAPI and Uvicorn imported successfully')"

deactivate
EOF

echo "4. Setting proper permissions for the entire application..."
chown -R www-data:www-data /var/www/dash-atm/
chmod -R 755 /var/www/dash-atm/

echo "5. Creating log directory with proper permissions..."
mkdir -p /var/log/dash-atm
chown -R www-data:www-data /var/log/dash-atm
chmod -R 755 /var/log/dash-atm

echo "6. Restarting PM2 backend services..."
pm2 restart dash-atm-main-api
pm2 restart dash-atm-user-api

echo "7. Checking PM2 status..."
pm2 status

echo "8. Testing backend services..."
sleep 5

echo "Testing main API (port 8000)..."
curl -s -o /dev/null -w "Main API Response: %{http_code}\n" http://localhost:8000/docs || echo "Main API not responding"

echo "Testing user API (port 8001)..."
curl -s -o /dev/null -w "User API Response: %{http_code}\n" http://localhost:8001/docs || echo "User API not responding"

echo "9. Checking recent PM2 logs..."
echo "=== Main API Logs ==="
pm2 logs dash-atm-main-api --lines 10 --nostream

echo "=== User API Logs ==="
pm2 logs dash-atm-user-api --lines 10 --nostream

echo "=== Fix Complete ==="
echo "If services are still not running, check the logs above for specific errors."
echo "You can also check individual logs with:"
echo "  pm2 logs dash-atm-main-api"
echo "  pm2 logs dash-atm-user-api"
