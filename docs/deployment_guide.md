# Cassandra MCP Server - Deployment Guide

This guide covers various deployment options for the Cassandra MCP Server.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

## Local Development

### Prerequisites

- Python 3.9 or higher
- Java Runtime Environment (JRE) 8 or higher
- Apache Cassandra (for actual cluster operations)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cassandra-mcp-server
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Configure the application:
```bash
cp config/config.yaml.example config/config.yaml
# Edit config/config.yaml with your settings
```

5. Run the server:
```bash
python -m src.main
```

## Docker Deployment

### Building the Docker Image

Build the Docker image:
```bash
docker build -t cassandra-mcp-server:latest .
```

### Running with Docker

1. Prepare configuration:
```bash
cp config/config.yaml.example config/config.yaml
# Edit config/config.yaml with your settings
```

2. Run the container:
```bash
docker run -it --rm \
  -v $(pwd)/config/config.yaml:/app/config/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  cassandra-mcp-server:latest
```

### Running with Docker Compose

1. Prepare configuration:
```bash
cp config/config.yaml.example config/config.yaml
# Edit config/config.yaml with your settings
```

2. Start the service:
```bash
docker-compose up -d
```

3. View logs:
```bash
docker-compose logs -f cassandra-mcp-server
```

4. Stop the service:
```bash
docker-compose down
```

## Production Deployment

### System Requirements

- **CPU**: 1-2 cores minimum
- **Memory**: 512MB minimum, 1GB recommended
- **Disk**: 10GB minimum for logs and temporary files
- **Network**: Access to Cassandra cluster nodes

### Security Considerations

1. **API Keys**: Use strong, randomly generated API keys
   ```bash
   # Generate secure API key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **File Permissions**: Ensure configuration files have restricted permissions
   ```bash
   chmod 600 config/config.yaml
   ```

3. **Network Security**: 
   - Use firewall rules to restrict access
   - Consider using VPN or SSH tunneling for remote access
   - Enable TLS if exposing HTTP endpoints

4. **User Permissions**: Run as non-root user
   ```bash
   # Create dedicated user
   sudo useradd -r -s /bin/false cassandra-mcp
   sudo chown -R cassandra-mcp:cassandra-mcp /opt/cassandra-mcp-server
   ```

### Systemd Service (Linux)

Create a systemd service file `/etc/systemd/system/cassandra-mcp-server.service`:

```ini
[Unit]
Description=Cassandra MCP Server
After=network.target

[Service]
Type=simple
User=cassandra-mcp
Group=cassandra-mcp
WorkingDirectory=/opt/cassandra-mcp-server
Environment="PYTHONUNBUFFERED=1"
Environment="JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64"
ExecStart=/opt/cassandra-mcp-server/venv/bin/python -m src.main
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cassandra-mcp-server
sudo systemctl start cassandra-mcp-server
sudo systemctl status cassandra-mcp-server
```

## Configuration

### Configuration File Structure

```yaml
# Java and Cassandra paths
java_home: "/usr/lib/jvm/java-11-openjdk-amd64"
cassandra_bin_path: "/opt/cassandra/bin"

# API Keys for authentication
api_keys:
  - "your-secure-api-key-here"
  - "another-api-key-if-needed"

# Logging configuration
log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
log_file: "logs/cassandra-mcp.log"
max_log_size: 10485760  # 10MB in bytes

# Health check interval (seconds)
health_check_interval: 30
```

### Environment Variables

You can override configuration using environment variables:

- `JAVA_HOME`: Java installation path
- `CASSANDRA_BIN_PATH`: Cassandra bin directory path
- `LOG_LEVEL`: Logging level

### Hot Reload Configuration

The server supports hot-reloading of configuration without restart:

```bash
# Send SIGHUP signal to reload configuration
kill -HUP <pid>
```

## Monitoring

### Health Checks

The server includes a health check system that monitors:
- Cassandra cluster connectivity
- Node status and availability
- Server internal state

### Logging

Logs are written to:
- Console (stdout/stderr)
- Log file (configured in config.yaml)

Log levels:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

### Metrics

Monitor these key metrics:
- Command execution time
- Authentication success/failure rate
- Cassandra connectivity status
- Node up/down count

## Troubleshooting

### Common Issues

#### 1. Java Not Found

**Error**: `JAVA_HOME path does not exist`

**Solution**:
```bash
# Find Java installation
which java
# Or
update-alternatives --list java

# Update config.yaml with correct path
java_home: "/usr/lib/jvm/java-11-openjdk-amd64"
```

#### 2. Nodetool Not Found

**Error**: `nodetool not found`

**Solution**:
```bash
# Find Cassandra installation
which nodetool

# Update config.yaml with correct path
cassandra_bin_path: "/opt/cassandra/bin"
```

#### 3. Authentication Failures

**Error**: `Authentication FAILED`

**Solution**:
- Verify API key is correctly configured in config.yaml
- Check API key is being sent in requests
- Review authentication logs for details

#### 4. Connection Timeout

**Error**: `Cassandra cluster is not reachable`

**Solution**:
- Verify Cassandra is running: `nodetool status`
- Check network connectivity to Cassandra nodes
- Verify firewall rules allow connections
- Check Cassandra configuration (cassandra.yaml)

#### 5. Permission Denied

**Error**: `Permission denied` when executing nodetool

**Solution**:
```bash
# Make nodetool executable
chmod +x /opt/cassandra/bin/nodetool

# Verify user has access
ls -la /opt/cassandra/bin/nodetool
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```yaml
# config.yaml
log_level: "DEBUG"
```

### Viewing Logs

```bash
# Local deployment
tail -f logs/cassandra-mcp.log

# Docker deployment
docker-compose logs -f cassandra-mcp-server

# Systemd service
sudo journalctl -u cassandra-mcp-server -f
```

## Backup and Recovery

### Configuration Backup

Regularly backup your configuration:
```bash
cp config/config.yaml config/config.yaml.backup.$(date +%Y%m%d)
```

### Log Rotation

Logs are automatically rotated when they reach the configured size. Archive old logs:
```bash
# Compress old logs
gzip logs/cassandra-mcp.log.*

# Move to archive
mv logs/*.gz /archive/cassandra-mcp-logs/
```

## Upgrading

1. Backup current configuration
2. Stop the service
3. Update code/container
4. Review configuration changes
5. Start the service
6. Verify functionality

```bash
# Docker upgrade
docker-compose pull
docker-compose up -d

# Local upgrade
git pull
pip install -e ".[dev]"
sudo systemctl restart cassandra-mcp-server
```

## Support

For issues and questions:
- Check logs for error messages
- Review this deployment guide
- Consult the main README.md
- Check the logging guide: docs/logging_guide.md
