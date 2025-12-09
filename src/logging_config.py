"""Logging configuration for Cassandra MCP Server."""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for log records."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


class OperationLogger:
    """Logger for structured operation logging."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize operation logger.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
    
    def log_operation(
        self,
        operation: str,
        parameters: Dict[str, Any],
        execution_time: float,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log an operation with structured data.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            execution_time: Execution time in seconds
            success: Whether operation succeeded
            result: Operation result (optional)
            error: Error message if failed (optional)
            **kwargs: Additional context data
        """
        log_data = {
            "operation": operation,
            "parameters": parameters,
            "execution_time": f"{execution_time:.3f}s",
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if result:
            log_data["result"] = result
        
        if error:
            log_data["error"] = error
        
        # Add any additional context
        log_data.update(kwargs)
        
        # Create log record with extra data
        if success:
            self.logger.info(
                f"Operation '{operation}' completed successfully",
                extra={"extra_data": log_data}
            )
        else:
            self.logger.error(
                f"Operation '{operation}' failed: {error}",
                extra={"extra_data": log_data}
            )
    
    def log_security_event(
        self,
        event_type: str,
        success: bool,
        details: Dict[str, Any],
        **kwargs
    ) -> None:
        """Log a security event.
        
        Args:
            event_type: Type of security event
            success: Whether event was successful
            details: Event details
            **kwargs: Additional context
        """
        log_data = {
            "event_type": event_type,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        log_data.update(kwargs)
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(
            level,
            f"Security event: {event_type}",
            extra={"extra_data": log_data}
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        **kwargs
    ) -> None:
        """Log a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            **kwargs: Additional context
        """
        log_data = {
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        log_data.update(kwargs)
        
        self.logger.info(
            f"Performance metric: {metric_name}={value}{unit}",
            extra={"extra_data": log_data}
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_log_size: int = 10485760,  # 10MB
    backup_count: int = 5,
    structured: bool = False
) -> logging.Logger:
    """Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_log_size: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        structured: Use structured JSON logging format
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("cassandra_mcp_server")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter based on structured flag
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_log_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}, Structured: {structured}")
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (optional, defaults to cassandra_mcp_server)
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"cassandra_mcp_server.{name}")
    return logging.getLogger("cassandra_mcp_server")


def get_operation_logger(name: Optional[str] = None) -> OperationLogger:
    """Get an operation logger instance.
    
    Args:
        name: Logger name (optional)
        
    Returns:
        OperationLogger instance
    """
    logger = get_logger(name)
    return OperationLogger(logger)
