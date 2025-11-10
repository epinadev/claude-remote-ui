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

echo -e "${BLUE}Stopping Claude Remote UI Web Server...${NC}"

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

echo -e "${BLUE}Claude Remote UI stopped${NC}"
