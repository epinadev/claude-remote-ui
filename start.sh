#!/bin/bash

# Claude Remote UI - Start Script
# Starts the web server in the background

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Claude Remote UI Web Server...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found. Run ./install.sh first${NC}"
    exit 1
fi

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}Error: config.yaml not found. Copy config.yaml.example to config.yaml${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Create PID directory if it doesn't exist
mkdir -p .pids

# Start server in background
echo -e "${GREEN}Starting server...${NC}"
nohup python server.py > logs/server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > .pids/server.pid
echo -e "  Server PID: $SERVER_PID"

# Start Telegram listener in background
echo -e "${GREEN}Starting Telegram listener...${NC}"
nohup python telegram_listener.py > logs/telegram.log 2>&1 &
TELEGRAM_PID=$!
echo $TELEGRAM_PID > .pids/telegram.pid
echo -e "  Telegram PID: $TELEGRAM_PID"

# Wait a moment to check if processes started successfully
sleep 2

# Check if server is still running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✓ Server running${NC}"
else
    echo -e "${RED}✗ Server failed to start. Check logs/server.log${NC}"
    exit 1
fi

# Check if Telegram listener is still running
if ps -p $TELEGRAM_PID > /dev/null; then
    echo -e "${GREEN}✓ Telegram listener running${NC}"
else
    echo -e "${RED}✗ Telegram listener failed to start. Check logs/telegram.log${NC}"
fi

echo ""
echo -e "${BLUE}Claude Remote UI is running!${NC}"
# Read port from config.yaml
PORT=$(grep "port:" config.yaml | awk '{print $2}')
echo -e "  Web UI: ${GREEN}http://localhost:${PORT}${NC}"
echo -e "  Logs: logs/server.log, logs/telegram.log"
echo ""
echo -e "${BLUE}Notifications:${NC} Telegram (send messages back to control Claude)"
echo ""
echo -e "To stop: ${GREEN}./stop.sh${NC}"
echo -e "To view logs: ${GREEN}tail -f logs/server.log logs/telegram.log${NC}"
