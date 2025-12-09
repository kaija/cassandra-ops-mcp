# Cassandra MCP Server

MCP (Model Context Protocol) server for Apache Cassandra cluster diagnostics and maintenance.

## Features

- Remote monitoring of Cassandra cluster status
- Execute nodetool commands via API
- API key authentication
- Configurable Java and Cassandra paths
- Structured logging
- Health check endpoints

## Project Structure

```
.
├── src/                       # Source code
│   ├── __init__.py
│   ├── models.py             # Data models
│   ├── interfaces.py         # Core interfaces
│   ├── logging_config.py     # Logging setup
│   ├── config_manager.py     # Configuration management
│   ├── authentication.py     # API key authentication
│   ├── nodetool_executor.py  # Nodetool command execution
│   ├── command_registry.py   # Command registration and validation
│   ├── mcp_server.py         # MCP Server core implementation
│   └── main.py               # Application entry point
├── tests/                    # Test suite
├── config/                   # Configuration files
│   └── config.yaml.example
├── pyproject.toml            # Project dependencies
└── README.md
```

## Installation

### Option 1: Local Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -e .
```

3. For development:
```bash
pip install -e ".[dev]"
```

### Option 2: Docker Installation

1. Build the Docker image:
```bash
docker build -t cassandra-mcp-server:latest .
```

2. Or use Docker Compose:
```bash
docker-compose up -d
```

See [Deployment Guide](docs/deployment_guide.md) for detailed deployment instructions.

## Configuration

1. Copy the example configuration:
```bash
cp config/config.yaml.example config/config.yaml
```

2. Edit `config/config.yaml` with your settings:
   - Set `java_home` to your Java installation path
   - Set `cassandra_bin_path` to your Cassandra bin directory
   - Add your API keys
   - Configure logging preferences

## Usage

### Local Execution

Run the MCP server:
```bash
python -m src.main
```

The server will start and listen for MCP protocol messages via stdio transport.

### Docker Execution

Using Docker:
```bash
docker run -it --rm \
  -v $(pwd)/config/config.yaml:/app/config/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  cassandra-mcp-server:latest
```

Using Docker Compose:
```bash
docker-compose up
```

### Graceful Shutdown

The server supports graceful shutdown via signals:
- Press `Ctrl+C` or send `SIGINT` to stop the server
- Send `SIGTERM` for graceful termination

The server will properly clean up all resources before exiting.

## API Usage and Examples

### Quick Start Examples

Check out the `examples/` directory for practical usage examples:

- **basic_usage.py** - Basic cluster monitoring and status checks
- **backup_automation.py** - Automated backup and snapshot management
- **health_monitoring.py** - Continuous health monitoring with alerts

Run an example:
```bash
export CASSANDRA_MCP_API_KEY="your-api-key"
python examples/basic_usage.py
```

### API Documentation

For detailed API usage, tool descriptions, and integration patterns, see:
- [API Usage Guide](docs/api_usage_guide.md) - Complete API reference with examples
- [Examples README](examples/README.md) - Guide to running examples

### Available Tools

The server provides 11 MCP tools for Cassandra operations:

**Monitoring:** `cassandra_status`, `cassandra_ring`, `cassandra_info`, `cassandra_netstats`

**Maintenance:** `cassandra_repair`, `cassandra_snapshot`, `cassandra_cleanup`, `cassandra_compact`

**Extended:** `cassandra_getsstables`, `cassandra_getcompactionthroughput`, `cassandra_getconcurrentcompactors`

See the [API Usage Guide](docs/api_usage_guide.md) for detailed documentation on each tool.

## Running Tests

```bash
pytest
```

For property-based tests with verbose output:
```bash
pytest -v --hypothesis-show-statistics
```

Run specific test files:
```bash
pytest tests/test_mcp_server.py -v
```

## Requirements

- Python 3.9+
- Apache Cassandra (for actual cluster operations)
- Java Runtime Environment

## License

See LICENSE file for details.
