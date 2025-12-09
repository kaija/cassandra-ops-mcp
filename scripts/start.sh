#!/bin/bash
# Startup script for Cassandra MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cassandra MCP Server - Startup Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import mcp" 2>/dev/null; then
    echo -e "${YELLOW}Dependencies not installed. Installing...${NC}"
    pip install -e .
    echo -e "${GREEN}Dependencies installed.${NC}"
fi

# Check if configuration exists
if [ ! -f "config/config.yaml" ]; then
    echo -e "${YELLOW}Configuration file not found.${NC}"
    if [ -f "config/config.yaml.example" ]; then
        echo -e "${YELLOW}Copying example configuration...${NC}"
        cp config/config.yaml.example config/config.yaml
        echo -e "${RED}Please edit config/config.yaml with your settings before running.${NC}"
        exit 1
    else
        echo -e "${RED}No configuration file or example found!${NC}"
        exit 1
    fi
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo -e "${GREEN}Starting Cassandra MCP Server...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

python -m src.main
