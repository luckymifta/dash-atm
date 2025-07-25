#!/bin/bash

echo "🔬 DAILY CASH USAGE API - COMPREHENSIVE TESTING"
echo "==============================================="

cd /Users/luckymifta/Documents/2. AREA/dash-atm/backend

# Step 1: Check server status
echo "🔍 Step 1: Checking server status..."
python check_server.py

if [ $? -ne 0 ]; then
    echo ""
    echo "🚀 Starting FastAPI server..."
    
    # Kill any existing process
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # Start server
    nohup python -m uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
    
    echo "⏱️  Waiting for server startup..."
    sleep 10
    
    # Check again
    python check_server.py
    if [ $? -ne 0 ]; then
        echo "❌ Failed to start server. Check logs:"
        tail -10 server.log
        exit 1
    fi
fi

echo ""
echo "🧪 Step 2: Running comprehensive functionality tests..."
python test_comprehensive.py

echo ""
echo "⚡ Step 3: Running performance tests with optimized SQL..."
python test_performance.py

echo ""
echo "✅ ALL TESTING COMPLETE!"
echo "📋 Check the results above to verify:"
echo "   - ✅ Individual terminal functionality"
echo "   - ✅ Data validation and edge cases"
echo "   - ✅ Chart.js integration features"
echo "   - ✅ Performance with large date ranges"
echo "   - ✅ Calculation accuracy (start_amount - end_amount)"
