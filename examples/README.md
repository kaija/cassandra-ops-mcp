# Cassandra MCP Server - Examples

This directory contains practical examples for using the Cassandra MCP Server.

## Available Examples

1. **basic_usage.py** - Basic tool calls and cluster monitoring
2. **backup_automation.py** - Automated backup and snapshot management
3. **health_monitoring.py** - Continuous health monitoring and alerting
4. **mcp_client_example.py** - Complete MCP client implementation with proper lifecycle management

## Prerequisites

```bash
# Install required packages
pip install mcp pyyaml

# Ensure Cassandra MCP Server is configured
cp ../config/config.yaml.example ../config/config.yaml
# Edit config.yaml with your settings
```

## Running Examples

Each example can be run independently:

```bash
# Basic usage
python examples/basic_usage.py

# Health monitoring
python examples/health_monitoring.py

# Backup automation
python examples/backup_automation.py
```

## Configuration

All examples expect the following environment variables or configuration:

- `CASSANDRA_MCP_API_KEY`: Your API key for authentication
- `CASSANDRA_MCP_SERVER_PATH`: Path to the MCP server (default: ../src/main.py)

You can set these in a `.env` file:

```bash
CASSANDRA_MCP_API_KEY=your-secure-api-key-here
CASSANDRA_MCP_SERVER_PATH=/path/to/cassandra-mcp-server/src/main.py
```

## Example Structure

Each example follows this structure:

1. **Setup**: Import required modules and configure connection
2. **Helper Functions**: Reusable functions for MCP communication
3. **Main Logic**: Demonstration of specific functionality
4. **Error Handling**: Proper error handling and logging
5. **Cleanup**: Resource cleanup and graceful shutdown

## Integration with AI Assistants

These examples can be adapted for use with AI assistants like Claude Desktop. See the API Usage Guide for configuration details.

## Support

For questions or issues with examples:
- Review the [API Usage Guide](../docs/api_usage_guide.md)
- Check the [Deployment Guide](../docs/deployment_guide.md)
- Examine server logs: `../logs/cassandra-mcp.log`

