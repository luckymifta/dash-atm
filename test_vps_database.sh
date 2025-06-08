#!/bin/bash

# Quick Database Connection Test for VPS
# Tests PostgreSQL connection on localhost for dash-atm deployment

echo "=== PostgreSQL Connection Test ==="
echo "Testing local PostgreSQL connection..."

# Test 1: Check if PostgreSQL service is running
echo -n "1. PostgreSQL service status: "
if systemctl is-active --quiet postgresql; then
    echo "✅ RUNNING"
else
    echo "❌ NOT RUNNING"
    echo "   Starting PostgreSQL..."
    systemctl start postgresql
    if systemctl is-active --quiet postgresql; then
        echo "   ✅ PostgreSQL started successfully"
    else
        echo "   ❌ Failed to start PostgreSQL"
        exit 1
    fi
fi

# Test 2: Check if development_db exists
echo -n "2. Database 'development_db' exists: "
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw development_db; then
    echo "✅ EXISTS"
else
    echo "❌ NOT FOUND"
    echo "   Creating database..."
    sudo -u postgres createdb development_db
    if [ $? -eq 0 ]; then
        echo "   ✅ Database created successfully"
    else
        echo "   ❌ Failed to create database"
        exit 1
    fi
fi

# Test 3: Check if user 'timlesdev' exists
echo -n "3. User 'timlesdev' exists: "
if sudo -u postgres psql -d development_db -tAc "SELECT 1 FROM pg_roles WHERE rolname='timlesdev'" | grep -q 1; then
    echo "✅ EXISTS"
else
    echo "❌ NOT FOUND"
    echo "   Creating user..."
    sudo -u postgres psql -d development_db -c "CREATE USER timlesdev WITH PASSWORD 'timlesdev';"
    sudo -u postgres psql -d development_db -c "GRANT ALL PRIVILEGES ON DATABASE development_db TO timlesdev;"
    if [ $? -eq 0 ]; then
        echo "   ✅ User created successfully"
    else
        echo "   ❌ Failed to create user"
        exit 1
    fi
fi

# Test 4: Test connection with timlesdev user
echo -n "4. Connection test with timlesdev: "
if PGPASSWORD=timlesdev psql -h localhost -U timlesdev -d development_db -c "\q" 2>/dev/null; then
    echo "✅ SUCCESS"
else
    echo "❌ FAILED"
    echo "   Troubleshooting..."
    
    # Check pg_hba.conf configuration
    echo "   Checking PostgreSQL authentication configuration..."
    HBA_FILE=$(sudo -u postgres psql -t -c "SHOW hba_file;" | xargs)
    echo "   HBA file: $HBA_FILE"
    
    # Ensure local connections are allowed
    if grep -q "^local.*all.*all.*trust" "$HBA_FILE" || grep -q "^local.*all.*all.*md5" "$HBA_FILE"; then
        echo "   ✅ Local authentication configured"
    else
        echo "   ⚠️  Adding local authentication rule..."
        sudo sed -i '/^local.*all.*postgres/a local   all             all                                     md5' "$HBA_FILE"
        sudo systemctl reload postgresql
        echo "   ✅ PostgreSQL configuration updated"
    fi
    
    # Test again
    echo -n "   Retesting connection: "
    if PGPASSWORD=timlesdev psql -h localhost -U timlesdev -d development_db -c "\q" 2>/dev/null; then
        echo "✅ SUCCESS"
    else
        echo "❌ STILL FAILED"
        echo "   Manual intervention may be required"
        exit 1
    fi
fi

# Test 5: Check if ATM tables exist (optional)
echo -n "5. ATM tables exist: "
TABLE_COUNT=$(PGPASSWORD=timlesdev psql -h localhost -U timlesdev -d development_db -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%atm%';" 2>/dev/null)
if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "✅ FOUND ($TABLE_COUNT tables)"
else
    echo "⚠️  NO ATM TABLES (will be created by application)"
fi

echo ""
echo "=== Connection Test Summary ==="
echo "✅ PostgreSQL is ready for dash-atm deployment"
echo "✅ Database: development_db"
echo "✅ User: timlesdev"
echo "✅ Host: localhost:5432"
echo ""
echo "Ready to proceed with deployment!"
