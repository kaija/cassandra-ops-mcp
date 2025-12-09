# Cassandra MCP Server - API Usage Guide

## Overview

The Cassandra MCP Server implements the Model Context Protocol (MCP), providing a standardized interface for AI assistants and applications to interact with Apache Cassandra clusters. This guide covers how to use the available tools and integrate them into your applications.

## Table of Contents

1. [MCP Protocol Basics](#mcp-protocol-basics)
2. [Authentication](#authentication)
3. [Available Tools](#available-tools)
4. [Usage Examples](#usage-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

## MCP Protocol Basics

### Transport

The server uses **stdio transport** for MCP communication:
- Messages are exchanged via standard input/output
- JSON-RPC 2.0 format
- Server-Sent Events (SSE) for streaming responses

### Message Format

All MCP messages follow JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "arg1": "value1",
      "arg2": "value2"
    }
  }
}
```

### Response Format

Successful responses:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Result data here"
      }
    ]
  }
}
```

Error responses:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Error description",
    "data": {
      "details": "Additional error information"
    }
  }
}
```

## Authentication

All tool calls require API key authentication.

### API Key Configuration

Configure API keys in `config/config.yaml`:

```yaml
api_keys:
  - "your-secure-api-key-here"
  - "another-api-key-for-different-client"
```

### Generating Secure API Keys

```bash
# Generate a secure random API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Using API Keys in Tool Calls

Include the `api_key` parameter in every tool call:

```json
{
  "name": "cassandra_status",
  "arguments": {
    "api_key": "your-secure-api-key-here"
  }
}
```

### Authentication Errors

**Missing API Key (401 Unauthorized):**
```json
{
  "error": {
    "code": -32000,
    "message": "Authentication required: API key missing"
  }
}
```

**Invalid API Key (403 Forbidden):**
```json
{
  "error": {
    "code": -32000,
    "message": "Authentication failed: Invalid API key"
  }
}
```

## Available Tools

### Monitoring Tools

#### 1. cassandra_status

Get cluster status and node information.

**Parameters:**
- `api_key` (required): Authentication key
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_status",
  "arguments": {
    "api_key": "your-api-key",
    "target_host": "192.168.1.100"
  }
}
```

**Response:**
```
Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address        Load       Tokens  Owns    Host ID                               Rack
UN  192.168.1.100  1.5 GB     256     33.3%   a1b2c3d4-...                          rack1
UN  192.168.1.101  1.4 GB     256     33.3%   e5f6g7h8-...                          rack1
UN  192.168.1.102  1.6 GB     256     33.4%   i9j0k1l2-...                          rack1
```

#### 2. cassandra_ring

Get token ring information.

**Parameters:**
- `api_key` (required): Authentication key
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_ring",
  "arguments": {
    "api_key": "your-api-key"
  }
}
```

#### 3. cassandra_info

Get detailed node information.

**Parameters:**
- `api_key` (required): Authentication key
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_info",
  "arguments": {
    "api_key": "your-api-key",
    "target_host": "192.168.1.100"
  }
}
```

**Response:**
```
ID                     : a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6
Gossip active          : true
Thrift active          : false
Native Transport active: true
Load                   : 1.5 GB
Generation No          : 1234567890
Uptime (seconds)       : 86400
Heap Memory (MB)       : 512.5 / 2048.0
Off Heap Memory (MB)   : 256.3
Data Center            : datacenter1
Rack                   : rack1
```

#### 4. cassandra_netstats

Get network statistics.

**Parameters:**
- `api_key` (required): Authentication key
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_netstats",
  "arguments": {
    "api_key": "your-api-key"
  }
}
```

### Maintenance Tools

#### 5. cassandra_repair

Repair tables in a keyspace.

**Parameters:**
- `api_key` (required): Authentication key
- `keyspace` (optional): Keyspace to repair (default: all keyspaces)
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_repair",
  "arguments": {
    "api_key": "your-api-key",
    "keyspace": "my_keyspace",
    "target_host": "192.168.1.100"
  }
}
```

**Response:**
```
[2024-12-09 10:30:45,123] Starting repair command on keyspace my_keyspace
[2024-12-09 10:30:45,456] Repair session started
[2024-12-09 10:35:12,789] Repair session completed successfully
```

#### 6. cassandra_snapshot

Create a snapshot of keyspace data.

**Parameters:**
- `api_key` (required): Authentication key
- `tag` (required): Snapshot tag name
- `keyspace` (optional): Keyspace to snapshot (default: all keyspaces)
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_snapshot",
  "arguments": {
    "api_key": "your-api-key",
    "tag": "backup_2024_12_09",
    "keyspace": "my_keyspace"
  }
}
```

**Response:**
```
Requested creating snapshot(s) for [my_keyspace] with snapshot name [backup_2024_12_09]
Snapshot directory: backup_2024_12_09
```

#### 7. cassandra_cleanup

Cleanup keys that no longer belong to a node.

**Parameters:**
- `api_key` (required): Authentication key
- `keyspace` (optional): Keyspace to cleanup (default: all keyspaces)
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_cleanup",
  "arguments": {
    "api_key": "your-api-key",
    "keyspace": "my_keyspace"
  }
}
```

#### 8. cassandra_compact

Force major compaction on tables.

**Parameters:**
- `api_key` (required): Authentication key
- `keyspace` (optional): Keyspace to compact (default: all keyspaces)
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_compact",
  "arguments": {
    "api_key": "your-api-key",
    "keyspace": "my_keyspace",
    "target_host": "192.168.1.100"
  }
}
```

### Extended Tools

#### 9. cassandra_getsstables

Get SSTables for a specific key.

**Parameters:**
- `api_key` (required): Authentication key
- `keyspace` (required): Keyspace name
- `table` (required): Table name
- `key` (required): Partition key
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_getsstables",
  "arguments": {
    "api_key": "your-api-key",
    "keyspace": "my_keyspace",
    "table": "my_table",
    "key": "user_123"
  }
}
```

#### 10. cassandra_getcompactionthroughput

Get compaction throughput in MB/s.

**Parameters:**
- `api_key` (required): Authentication key
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_getcompactionthroughput",
  "arguments": {
    "api_key": "your-api-key"
  }
}
```

**Response:**
```
Current compaction throughput: 16 MB/s
```

#### 11. cassandra_getconcurrentcompactors

Get number of concurrent compactors.

**Parameters:**
- `api_key` (required): Authentication key
- `target_host` (optional): Specific node IP address

**Example:**
```json
{
  "name": "cassandra_getconcurrentcompactors",
  "arguments": {
    "api_key": "your-api-key"
  }
}
```

**Response:**
```
Current concurrent compactors: 4
```

## Usage Examples

### Example 1: Check Cluster Health

```python
import json
import subprocess

def check_cluster_health(api_key):
    """Check the health of the Cassandra cluster."""
    
    # Prepare the MCP tool call
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "cassandra_status",
            "arguments": {
                "api_key": api_key
            }
        }
    }
    
    # Send request to MCP server via stdio
    # (Assuming server is running and connected)
    response = send_mcp_request(request)
    
    # Parse response
    if "result" in response:
        status_output = response["result"]["content"][0]["text"]
        print("Cluster Status:")
        print(status_output)
        return True
    else:
        print(f"Error: {response['error']['message']}")
        return False

# Usage
api_key = "your-secure-api-key"
check_cluster_health(api_key)
```

### Example 2: Create Backup Snapshot

```python
def create_backup(api_key, keyspace, tag):
    """Create a backup snapshot of a keyspace."""
    
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "cassandra_snapshot",
            "arguments": {
                "api_key": api_key,
                "keyspace": keyspace,
                "tag": tag
            }
        }
    }
    
    response = send_mcp_request(request)
    
    if "result" in response:
        print(f"Snapshot created: {tag}")
        print(response["result"]["content"][0]["text"])
        return True
    else:
        print(f"Snapshot failed: {response['error']['message']}")
        return False

# Usage
create_backup("your-api-key", "my_keyspace", "backup_2024_12_09")
```

### Example 3: Monitor Specific Node

```python
def monitor_node(api_key, node_ip):
    """Get detailed information about a specific node."""
    
    # Get node info
    info_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "cassandra_info",
            "arguments": {
                "api_key": api_key,
                "target_host": node_ip
            }
        }
    }
    
    info_response = send_mcp_request(info_request)
    
    # Get network stats
    netstats_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "cassandra_netstats",
            "arguments": {
                "api_key": api_key,
                "target_host": node_ip
            }
        }
    }
    
    netstats_response = send_mcp_request(netstats_request)
    
    # Display results
    if "result" in info_response and "result" in netstats_response:
        print(f"Node Information for {node_ip}:")
        print("=" * 50)
        print(info_response["result"]["content"][0]["text"])
        print("\nNetwork Statistics:")
        print("=" * 50)
        print(netstats_response["result"]["content"][0]["text"])
        return True
    else:
        print("Error retrieving node information")
        return False

# Usage
monitor_node("your-api-key", "192.168.1.100")
```

### Example 4: Perform Maintenance

```python
def perform_maintenance(api_key, keyspace):
    """Perform maintenance operations on a keyspace."""
    
    print(f"Starting maintenance on keyspace: {keyspace}")
    
    # Step 1: Repair
    print("\n1. Running repair...")
    repair_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "cassandra_repair",
            "arguments": {
                "api_key": api_key,
                "keyspace": keyspace
            }
        }
    }
    repair_response = send_mcp_request(repair_request)
    
    if "error" in repair_response:
        print(f"Repair failed: {repair_response['error']['message']}")
        return False
    
    print("Repair completed successfully")
    
    # Step 2: Cleanup
    print("\n2. Running cleanup...")
    cleanup_request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "cassandra_cleanup",
            "arguments": {
                "api_key": api_key,
                "keyspace": keyspace
            }
        }
    }
    cleanup_response = send_mcp_request(cleanup_request)
    
    if "error" in cleanup_response:
        print(f"Cleanup failed: {cleanup_response['error']['message']}")
        return False
    
    print("Cleanup completed successfully")
    
    # Step 3: Compact
    print("\n3. Running compaction...")
    compact_request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "cassandra_compact",
            "arguments": {
                "api_key": api_key,
                "keyspace": keyspace
            }
        }
    }
    compact_response = send_mcp_request(compact_request)
    
    if "error" in compact_response:
        print(f"Compaction failed: {compact_response['error']['message']}")
        return False
    
    print("Compaction completed successfully")
    print("\nMaintenance completed!")
    return True

# Usage
perform_maintenance("your-api-key", "my_keyspace")
```

### Example 5: Using with Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "cassandra": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/cassandra-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/cassandra-mcp-server"
      }
    }
  }
}
```

Then in Claude Desktop, you can ask:

```
"Check the status of my Cassandra cluster"
"Create a snapshot of the users keyspace with tag backup_today"
"Show me information about node 192.168.1.100"
"Run repair on the analytics keyspace"
```

## Error Handling

### Common Errors

#### Authentication Errors

```json
{
  "error": {
    "code": -32000,
    "message": "Authentication failed: Invalid API key"
  }
}
```

**Solution**: Verify API key is correct and configured in `config/config.yaml`

#### Connection Errors

```json
{
  "error": {
    "code": -32000,
    "message": "Failed to connect to Cassandra node: Connection timeout"
  }
}
```

**Solution**: 
- Verify Cassandra is running
- Check network connectivity
- Verify target_host IP is correct

#### Command Execution Errors

```json
{
  "error": {
    "code": -32000,
    "message": "Command execution failed: nodetool: Failed to connect to '192.168.1.100:7199'"
  }
}
```

**Solution**:
- Verify JMX port (7199) is accessible
- Check firewall rules
- Verify Cassandra is running on target node

#### Invalid Parameters

```json
{
  "error": {
    "code": -32602,
    "message": "Invalid parameters: keyspace is required"
  }
}
```

**Solution**: Provide all required parameters for the tool

### Error Handling Best Practices

1. **Always check for errors** in responses before processing results
2. **Log errors** for debugging and monitoring
3. **Implement retries** for transient errors (connection timeouts)
4. **Validate parameters** before sending requests
5. **Handle authentication errors** by refreshing API keys if needed

## Best Practices

### 1. Security

- **Rotate API keys regularly**
- **Use different API keys** for different clients/applications
- **Store API keys securely** (environment variables, secrets management)
- **Never commit API keys** to version control
- **Monitor authentication logs** for suspicious activity

### 2. Performance

- **Use target_host** to distribute load across nodes
- **Avoid running heavy operations** (repair, compact) during peak hours
- **Monitor execution times** and adjust timeouts if needed
- **Use snapshots** before major operations

### 3. Reliability

- **Implement error handling** for all tool calls
- **Use retries with exponential backoff** for transient errors
- **Monitor cluster health** regularly
- **Set up alerts** for critical errors
- **Test in non-production** environments first

### 4. Monitoring

- **Check logs regularly**: `logs/cassandra-mcp.log`
- **Monitor operation execution times**
- **Track authentication failures**
- **Set up health checks**
- **Use structured logging** for easier parsing

### 5. Maintenance

- **Schedule regular repairs** to maintain data consistency
- **Create snapshots** before major operations
- **Run cleanup** after node additions/removals
- **Monitor compaction** throughput and adjust if needed
- **Keep logs rotated** to prevent disk space issues

## Integration Patterns

### Pattern 1: Health Check Loop

```python
import time

def health_check_loop(api_key, interval=60):
    """Continuously monitor cluster health."""
    while True:
        try:
            response = call_tool("cassandra_status", {"api_key": api_key})
            if "error" in response:
                alert(f"Cluster health check failed: {response['error']}")
            else:
                log_health_status(response["result"])
        except Exception as e:
            alert(f"Health check exception: {e}")
        
        time.sleep(interval)
```

### Pattern 2: Automated Backup

```python
from datetime import datetime

def automated_backup(api_key, keyspaces):
    """Create automated backups with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for keyspace in keyspaces:
        tag = f"auto_backup_{keyspace}_{timestamp}"
        response = call_tool("cassandra_snapshot", {
            "api_key": api_key,
            "keyspace": keyspace,
            "tag": tag
        })
        
        if "error" in response:
            log_error(f"Backup failed for {keyspace}: {response['error']}")
        else:
            log_success(f"Backup created for {keyspace}: {tag}")
```

### Pattern 3: Multi-Node Operations

```python
def execute_on_all_nodes(api_key, nodes, operation, **kwargs):
    """Execute an operation on multiple nodes."""
    results = {}
    
    for node in nodes:
        kwargs["api_key"] = api_key
        kwargs["target_host"] = node
        
        response = call_tool(operation, kwargs)
        results[node] = response
    
    return results

# Usage
nodes = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
results = execute_on_all_nodes(
    "your-api-key",
    nodes,
    "cassandra_info"
)
```

## Troubleshooting

### Issue: Tool calls timing out

**Solution**: Increase timeout in your MCP client configuration or check Cassandra responsiveness

### Issue: Inconsistent results

**Solution**: Ensure you're querying the correct node with `target_host` parameter

### Issue: Authentication working locally but failing in production

**Solution**: Verify config.yaml is properly mounted in Docker/production environment

### Issue: Commands succeed but no output

**Solution**: Check log level configuration and ensure logs are being written

## Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Apache Cassandra Documentation](https://cassandra.apache.org/doc/)
- [Nodetool Reference](https://cassandra.apache.org/doc/latest/tools/nodetool/)
- [Deployment Guide](deployment_guide.md)
- [Logging Guide](logging_guide.md)

## Support

For issues and questions:
- Check server logs: `logs/cassandra-mcp.log`
- Enable debug logging: Set `log_level: "DEBUG"` in config.yaml
- Review error messages in responses
- Consult the deployment and logging guides

