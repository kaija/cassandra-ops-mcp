#!/bin/bash
# Stop script for Cassandra MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cassandra MCP Server - Stop Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Find the process
PID=$(pgrep -f "python -m src.main" || true)

if [ -z "$PID" ]; then
    echo -e "${YELLOW}No running Cassandra MCP Server found.${NC}"
    exit 0
fi

echo -e "${YELLOW}Found Cassandra MCP Server process: PID $PID${NC}"
echo -e "${YELLOW}Sending SIGTERM for graceful shutdown...${NC}"

# Send SIGTERM for graceful shutdown
kill -TERM $PID

# Wait for process to stop (max 30 seconds)
TIMEOUT=30
ELAPSED=0
while kill -0 $PID 2>/dev/null; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo -e "${RED}Process did not stop gracefully. Forcing shutdown...${NC}"
        kill -KILL $PID
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    echo -n "."
done

echo ""
echo -e "${GREEN}Cassandra MCP Server stopped successfully.${NC}"
