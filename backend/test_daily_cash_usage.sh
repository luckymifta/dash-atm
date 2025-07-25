#!/bin/bash

echo "🔍 Checking API server status..."
cd /Users/luckymifta/Documents/2. AREA/dash-atm/backend

# Check if server is running
python check_server.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🧪 Running performance tests for optimized Daily Cash Usage API..."
    echo "=================================================================="
    python test_performance.py
else
    echo ""
    echo "🚀 Server not running. Starting FastAPI server..."
    
    # Kill any existing process on port 8000
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    
    # Start the server in background
    nohup python -m uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
    
    # Wait for server to start
    echo "⏱️  Waiting for server to start..."
    sleep 8
    
    # Check again
    python check_server.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🧪 Running performance tests..."
        echo "=============================="
        python test_performance.py
    else
        echo "❌ Failed to start server. Check server.log for details:"
        tail -20 server.log
    fi
fi
