# Cassandra MCP Server Logging Guide

## Overview

The Cassandra MCP Server includes a comprehensive logging system that supports:
- Structured logging with JSON format
- Operation logging with detailed metrics
- Security event logging
- Performance metrics logging
- Log rotation and level filtering
- Error logging with stack traces

## Basic Usage

### Setting Up Logging

```python
from src.logging_config import setup_logging, get_logger

# Basic setup with console output
logger = setup_logging(log_level="INFO")

# Setup with file output and rotation
logger = setup_logging(
    log_level="DEBUG",
    log_file="logs/cassandra-mcp.log",
    max_log_size=10485760,  # 10MB
    backup_count=5
)

# Setup with structured JSON logging
logger = setup_logging(
    log_level="INFO",
    log_file="logs/cassandra-mcp.json",
    structured=True
)
```

### Getting a Logger

```python
from src.logging_config import get_logger

# Get the main logger
logger = get_logger()

# Get a module-specific logger
logger = get_logger("authentication")
logger = get_logger("nodetool")
```

### Basic Logging

```python
logger = get_logger("mymodule")

logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")

# Log with exception info
try:
    # Some operation
    pass
except Exception as e:
    logger.error("Operation failed", exc_info=True)
```

## Structured Operation Logging

### Using OperationLogger

```python
from src.logging_config import get_operation_logger

# Get an operation logger
op_logger = get_operation_logger("operations")

# Log a successful operation
op_logger.log_operation(
    operation="nodetool_status",
    parameters={"target_host": "192.168.1.100"},
    execution_time=1.234,
    success=True,
    result="Cluster status retrieved successfully"
)

# Log a failed operation
op_logger.log_operation(
    operation="nodetool_repair",
    parameters={"keyspace": "system"},
    execution_time=0.5,
    success=False,
    error="Connection timeout"
)

# Log with additional context
op_logger.log_operation(
    operation="snapshot",
    parameters={"tag": "backup_2024"},
    execution_time=2.5,
    success=True,
    node_count=3,
    snapshot_size="1.2GB"
)
```

### Security Event Logging

```python
# Log successful authentication
op_logger.log_security_event(
    event_type="authentication",
    success=True,
    details={
        "user": "admin",
        "ip": "192.168.1.50",
        "method": "api_key"
    }
)

# Log failed authentication
op_logger.log_security_event(
    event_type="authentication",
    success=False,
    details={
        "ip": "192.168.1.99",
        "reason": "invalid_api_key"
    }
)
```

### Performance Metrics Logging

```python
# Log performance metrics
op_logger.log_performance_metric(
    metric_name="command_execution_time",
    value=1.5,
    unit="seconds",
    command="status",
    node="192.168.1.100"
)

op_logger.log_performance_metric(
    metric_name="memory_usage",
    value=512.5,
    unit="MB",
    component="nodetool_executor"
)
```

## Structured JSON Logging

When structured logging is enabled, all log messages are formatted as JSON:

```json
{
  "timestamp": "2024-12-09T10:30:45.123456",
  "level": "INFO",
  "logger": "cassandra_mcp_server.operations",
  "message": "Operation 'nodetool_status' completed successfully",
  "module": "logging_config",
  "function": "log_operation",
  "line": 85,
  "extra": {
    "operation": "nodetool_status",
    "parameters": {"target_host": "192.168.1.100"},
    "execution_time": "1.234s",
    "success": true,
    "timestamp": "2024-12-09T10:30:45.123456"
  }
}
```

## Log Levels

The logging system supports standard Python log levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may cause the application to fail

### Configuring Log Levels

```python
# Set log level via configuration
setup_logging(log_level="DEBUG")  # Show all messages
setup_logging(log_level="INFO")   # Show INFO and above
setup_logging(log_level="WARNING") # Show WARNING and above
setup_logging(log_level="ERROR")  # Show ERROR and above
```

## Log Rotation

The logging system automatically rotates log files when they reach the configured size:

```python
setup_logging(
    log_file="logs/cassandra-mcp.log",
    max_log_size=10485760,  # 10MB
    backup_count=5          # Keep 5 backup files
)
```

This creates:
- `cassandra-mcp.log` (current log)
- `cassandra-mcp.log.1` (most recent backup)
- `cassandra-mcp.log.2`
- `cassandra-mcp.log.3`
- `cassandra-mcp.log.4`
- `cassandra-mcp.log.5` (oldest backup)

## Integration Examples

### In NodeTool Executor

```python
from src.logging_config import get_logger, get_operation_logger

class NodeToolExecutor:
    def __init__(self, config_manager):
        self.logger = get_logger("nodetool")
        self.op_logger = get_operation_logger("nodetool")
    
    async def execute_command(self, command, target_host=None):
        start_time = time.time()
        
        self.logger.info(f"Executing command: {command}")
        
        try:
            # Execute command
            result = await self._execute(command, target_host)
            execution_time = time.time() - start_time
            
            # Log operation
            self.op_logger.log_operation(
                operation=command,
                parameters={"target_host": target_host},
                execution_time=execution_time,
                success=True,
                result="Command completed"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log error
            self.logger.error(f"Command failed: {e}", exc_info=True)
            
            # Log operation failure
            self.op_logger.log_operation(
                operation=command,
                parameters={"target_host": target_host},
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
            
            raise
```

### In Authentication Manager

```python
from src.logging_config import get_logger, get_operation_logger

class AuthenticationManager:
    def __init__(self, config):
        self.logger = get_logger("auth")
        self.op_logger = get_operation_logger("auth")
    
    def validate_api_key(self, api_key, client_ip):
        is_valid = api_key in self._api_keys
        
        # Log security event
        self.op_logger.log_security_event(
            event_type="api_key_validation",
            success=is_valid,
            details={
                "ip": client_ip,
                "key_masked": self._mask_key(api_key)
            }
        )
        
        return is_valid
```

## Best Practices

1. **Use appropriate log levels**: DEBUG for detailed diagnostics, INFO for general flow, WARNING for potential issues, ERROR for actual problems.

2. **Include context**: Always include relevant context in log messages (operation name, parameters, execution time, etc.).

3. **Use structured logging for operations**: Use `OperationLogger` for command executions and operations that need detailed tracking.

4. **Log security events**: Always log authentication attempts, authorization failures, and other security-relevant events.

5. **Include exception info**: When logging errors, use `exc_info=True` to include stack traces.

6. **Don't log sensitive data**: Mask API keys, passwords, and other sensitive information before logging.

7. **Use module-specific loggers**: Create loggers for each module using `get_logger("module_name")`.

8. **Configure rotation**: Always configure log rotation to prevent disk space issues.

9. **Monitor log levels**: Use appropriate log levels in production to avoid excessive logging.

10. **Use performance metrics**: Log performance metrics for critical operations to track system health.

## Configuration

The logging system can be configured via the application configuration file:

```yaml
log_level: INFO
log_file: logs/cassandra-mcp.log
max_log_size: 10485760  # 10MB
backup_count: 5
```

## Troubleshooting

### Logs not appearing

- Check log level configuration
- Verify log file path is writable
- Ensure logging is initialized before use

### Log rotation not working

- Verify `max_log_size` is set correctly
- Check file permissions
- Ensure `backup_count` is greater than 0

### Performance issues

- Reduce log level in production (INFO or WARNING)
- Disable structured logging if not needed
- Increase rotation size to reduce I/O
