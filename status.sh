#!/bin/bash

# Claude Remote UI - Status Script
# Check status of web server

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Claude Remote UI Status${NC}"
echo ""

# Check server
if [ -f ".pids/server.pid" ]; then
    SERVER_PID=$(cat .pids/server.pid)
    if ps -p $SERVER_PID > /dev/null; then
        echo -e "Server: ${GREEN}✓ Running${NC} (PID: $SERVER_PID)"
    else
        echo -e "Server: ${RED}✗ Not running${NC} (stale PID file)"
    fi
else
    echo -e "Server: ${RED}✗ Not running${NC}"
fi

# Check Telegram listener
if [ -f ".pids/telegram.pid" ]; then
    TELEGRAM_PID=$(cat .pids/telegram.pid)
    if ps -p $TELEGRAM_PID > /dev/null; then
        echo -e "Telegram: ${GREEN}✓ Running${NC} (PID: $TELEGRAM_PID)"
    else
        echo -e "Telegram: ${RED}✗ Not running${NC} (stale PID file)"
    fi
else
    echo -e "Telegram: ${RED}✗ Not running${NC}"
fi

echo ""

# Check if server is responding
if command -v curl > /dev/null; then
    # Read port from config.yaml
    PORT=$(grep "port:" config.yaml | awk '{print $2}')
    if curl -s http://localhost:${PORT}/health > /dev/null; then
        echo -e "Web UI: ${GREEN}✓ Accessible${NC} at http://localhost:${PORT}"
    else
        echo -e "Web UI: ${RED}✗ Not accessible${NC}"
    fi
fi

echo ""
echo -e "${BLUE}Telegram:${NC} Send messages to control Claude, use /status to check active pane"
