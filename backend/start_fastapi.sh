#!/bin/bash
# FastAPI Startup Script for ATM Monitoring API

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[START] ATM Monitoring FastAPI Server${NC}"
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[INFO] Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}[INFO] Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}[INFO] Installing dependencies...${NC}"
pip install -r requirements_fastapi.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING] .env file not found. Using default configuration.${NC}"
    echo -e "${YELLOW}[INFO] You can copy .env_fastapi.example to .env and customize it.${NC}"
fi

# Start the FastAPI server
echo -e "${GREEN}[START] Starting FastAPI server...${NC}"
echo -e "${GREEN}[INFO] API Documentation: http://localhost:8000/docs${NC}"
echo -e "${GREEN}[INFO] Alternative Docs: http://localhost:8000/redoc${NC}"
echo -e "${GREEN}[INFO] Health Check: http://localhost:8000/api/v1/health${NC}"
echo "======================================"

uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000 --reload
