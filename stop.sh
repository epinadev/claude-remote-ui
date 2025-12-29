#!/bin/bash

# Claude Remote UI - Stop Script
# Stops the web server

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping Claude Remote UI...${NC}"

# Stop server
if [ -f ".pids/server.pid" ]; then
    SERVER_PID=$(cat .pids/server.pid)
    if ps -p $SERVER_PID > /dev/null; then
        kill $SERVER_PID
        echo -e "${GREEN}✓ Server stopped (PID: $SERVER_PID)${NC}"
    else
        echo -e "${RED}✗ Server not running${NC}"
    fi
    rm .pids/server.pid
else
    echo -e "${RED}✗ Server PID file not found${NC}"
fi

# Stop Telegram listener
if [ -f ".pids/telegram.pid" ]; then
    TELEGRAM_PID=$(cat .pids/telegram.pid)
    if ps -p $TELEGRAM_PID > /dev/null; then
        kill $TELEGRAM_PID
        echo -e "${GREEN}✓ Telegram listener stopped (PID: $TELEGRAM_PID)${NC}"
    else
        echo -e "${RED}✗ Telegram listener not running${NC}"
    fi
    rm .pids/telegram.pid
else
    echo -e "${RED}✗ Telegram PID file not found${NC}"
fi

echo -e "${BLUE}Claude Remote UI stopped${NC}"
