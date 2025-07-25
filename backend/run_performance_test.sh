#!/bin/bash

# Start FastAPI server in background if not running
echo "🚀 Starting FastAPI server for performance testing..."

# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the server in background
cd /Users/luckymifta/Documents/2. AREA/dash-atm/backend
nohup python -m uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &

# Wait for server to start
echo "⏱️  Waiting for server to start..."
sleep 5

# Check if server is running
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ Server is running!"
    
    # Run performance test
    echo "🧪 Running performance tests..."
    python test_performance.py
else
    echo "❌ Server failed to start. Check server.log for details."
    tail server.log
fi
