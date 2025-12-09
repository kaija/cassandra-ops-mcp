# Cassandra MCP Server - Quick Start Guide

Get up and running with Cassandra MCP Server in minutes.

## Prerequisites

Choose one of the following:

### Option A: Local Installation
- Python 3.9+
- Java Runtime Environment (JRE) 8+
- Apache Cassandra (optional, for testing)

### Option B: Docker Installation
- Docker 20.10+
- Docker Compose 1.29+ (optional)

## Quick Start - Local

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd cassandra-mcp-server
   ```

2. **Run the startup script**
   ```bash
   ./scripts/start.sh
   ```
   
   The script will:
   - Create a virtual environment
   - Install dependencies
   - Copy example configuration (if needed)
   - Start the server

3. **Configure** (if first run)
   ```bash
   # Edit the configuration file
   nano config/config.yaml
   
   # Set your API keys, Java path, and Cassandra path
   ```

4. **Restart the server**
   ```bash
   ./scripts/start.sh
   ```

## Quick Start - Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cassandra-mcp-server
   ```

2. **Prepare configuration**
   ```bash
   cp config/config.yaml.example config/config.yaml
   nano config/config.yaml  # Edit with your settings
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

5. **Stop the server**
   ```bash
   docker-compose down
   ```

## Configuration Essentials

Edit `config/config.yaml`:

```yaml
# Required: Set your Java installation path
java_home: "/usr/lib/jvm/java-11-openjdk-amd64"

# Required: Set your Cassandra bin directory
cassandra_bin_path: "/opt/cassandra/bin"

# Required: Add at least one API key
api_keys:
  - "your-secure-api-key-here"

# Optional: Adjust logging
log_level: "INFO"
log_file: "logs/cassandra-mcp.log"
```

### Generate Secure API Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Verify Installation

### Check Server Status

The server should start and display:
```
============================================================
Cassandra MCP Server - Starting Initialization
============================================================
Loading configuration...
Logging system configured from config file
Validating configured paths...
...
Initialization Complete
  - Registered tools: 11
  - Available commands: status, ring, info, ...
============================================================
Cassandra MCP Server is now running
Press Ctrl+C to stop
```

### Test with MCP Client

The server communicates via MCP protocol over stdio. You can test it with an MCP client or AI host that supports the protocol.

Example tool call:
```json
{
  "name": "cassandra_status",
  "arguments": {
    "api_key": "your-api-key",
    "target_host": "192.168.1.100"
  }
}
```

## Common Commands

### Local Deployment

```bash
# Start server
./scripts/start.sh

# Stop server (in another terminal)
./scripts/stop.sh

# View logs
tail -f logs/cassandra-mcp.log

# Run tests
pytest
```

### Docker Deployment

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build
```

## Troubleshooting

### Issue: "JAVA_HOME path does not exist"

**Solution**: Update `java_home` in config.yaml with your Java installation path.

Find Java:
```bash
which java
# or
/usr/libexec/java_home  # macOS
```

### Issue: "nodetool not found"

**Solution**: Update `cassandra_bin_path` in config.yaml.

Find nodetool:
```bash
which nodetool
```

### Issue: "Authentication FAILED"

**Solution**: 
1. Verify API key is configured in config.yaml
2. Ensure API key is sent in tool call arguments
3. Check logs for details: `tail -f logs/cassandra-mcp.log`

### Issue: "Cassandra cluster is not reachable"

**Solution**:
1. Verify Cassandra is running: `nodetool status`
2. Check network connectivity
3. Verify firewall rules

## Next Steps

- Read the [API Usage Guide](docs/api_usage_guide.md) for detailed API documentation and examples
- Read the [Deployment Guide](docs/deployment_guide.md) for production setup
- Review [Logging Guide](docs/logging_guide.md) for monitoring
- Check the [README](README.md) for detailed documentation
- Explore the [examples/](examples/) directory for practical code examples
- Explore available nodetool commands in the command registry

## Available Tools

The server provides these MCP tools:

**Monitoring:**
- `cassandra_status` - Cluster status and node information
- `cassandra_ring` - Token ring information
- `cassandra_info` - Node information
- `cassandra_netstats` - Network statistics

**Maintenance:**
- `cassandra_repair` - Repair tables
- `cassandra_snapshot` - Create snapshots
- `cassandra_cleanup` - Cleanup keys
- `cassandra_compact` - Force compaction

**Extended:**
- `cassandra_getsstables` - Get SSTables for a key
- `cassandra_getcompactionthroughput` - Get compaction throughput
- `cassandra_getconcurrentcompactors` - Get concurrent compactors

Each tool supports optional `target_host` parameter to execute on specific nodes.

## Support

For issues:
1. Check logs: `logs/cassandra-mcp.log`
2. Review documentation in `docs/`
3. Run tests: `pytest -v`
4. Enable debug logging: Set `log_level: "DEBUG"` in config.yaml
