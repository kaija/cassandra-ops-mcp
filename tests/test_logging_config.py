"""Tests for logging configuration and structured logging."""

import pytest
import logging
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.logging_config import (
    setup_logging,
    get_logger,
    get_operation_logger,
    StructuredFormatter,
    OperationLogger
)


class TestStructuredFormatter:
    """Tests for StructuredFormatter."""
    
    def test_format_basic_record(self):
        """Test formatting a basic log record."""
        formatter = StructuredFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        # Format the record
        result = formatter.format(record)
        
        # Parse JSON
        log_data = json.loads(result)
        
        # Verify structure
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 10
    
    def test_format_with_exception(self):
        """Test formatting a log record with exception."""
        formatter = StructuredFormatter()
        
        # Create exception
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        # Create log record with exception
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        # Format the record
        result = formatter.format(record)
        
        # Parse JSON
        log_data = json.loads(result)
        
        # Verify exception info
        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert "Test error" in log_data["exception"]["message"]
        assert "traceback" in log_data["exception"]
    
    def test_format_with_extra_data(self):
        """Test formatting a log record with extra data."""
        formatter = StructuredFormatter()
        
        # Create log record with extra data
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=30,
            msg="Operation completed",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.extra_data = {
            "operation": "test_op",
            "duration": 1.5,
            "success": True
        }
        
        # Format the record
        result = formatter.format(record)
        
        # Parse JSON
        log_data = json.loads(result)
        
        # Verify extra data
        assert "extra" in log_data
        assert log_data["extra"]["operation"] == "test_op"
        assert log_data["extra"]["duration"] == 1.5
        assert log_data["extra"]["success"] is True


class TestOperationLogger:
    """Tests for OperationLogger."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock(spec=logging.Logger)
    
    @pytest.fixture
    def operation_logger(self, mock_logger):
        """Create an OperationLogger with mock logger."""
        return OperationLogger(mock_logger)
    
    def test_log_operation_success(self, operation_logger, mock_logger):
        """Test logging a successful operation."""
        operation_logger.log_operation(
            operation="test_command",
            parameters={"arg1": "value1"},
            execution_time=1.234,
            success=True,
            result="Success"
        )
        
        # Verify logger was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        # Check message
        assert "test_command" in call_args[0][0]
        assert "completed successfully" in call_args[0][0]
        
        # Check extra data
        extra_data = call_args[1]["extra"]["extra_data"]
        assert extra_data["operation"] == "test_command"
        assert extra_data["parameters"] == {"arg1": "value1"}
        assert extra_data["execution_time"] == "1.234s"
        assert extra_data["success"] is True
        assert extra_data["result"] == "Success"
    
    def test_log_operation_failure(self, operation_logger, mock_logger):
        """Test logging a failed operation."""
        operation_logger.log_operation(
            operation="test_command",
            parameters={"arg1": "value1"},
            execution_time=0.5,
            success=False,
            error="Command failed"
        )
        
        # Verify logger was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Check message
        assert "test_command" in call_args[0][0]
        assert "failed" in call_args[0][0]
        assert "Command failed" in call_args[0][0]
        
        # Check extra data
        extra_data = call_args[1]["extra"]["extra_data"]
        assert extra_data["success"] is False
        assert extra_data["error"] == "Command failed"
    
    def test_log_security_event_success(self, operation_logger, mock_logger):
        """Test logging a successful security event."""
        operation_logger.log_security_event(
            event_type="authentication",
            success=True,
            details={"user": "test_user", "ip": "192.168.1.1"}
        )
        
        # Verify logger was called with INFO level
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        
        assert call_args[0][0] == logging.INFO
        assert "authentication" in call_args[0][1]
        
        # Check extra data
        extra_data = call_args[1]["extra"]["extra_data"]
        assert extra_data["event_type"] == "authentication"
        assert extra_data["success"] is True
        assert extra_data["details"]["user"] == "test_user"
    
    def test_log_security_event_failure(self, operation_logger, mock_logger):
        """Test logging a failed security event."""
        operation_logger.log_security_event(
            event_type="authentication",
            success=False,
            details={"user": "test_user", "ip": "192.168.1.1"}
        )
        
        # Verify logger was called with WARNING level
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        
        assert call_args[0][0] == logging.WARNING
    
    def test_log_performance_metric(self, operation_logger, mock_logger):
        """Test logging a performance metric."""
        operation_logger.log_performance_metric(
            metric_name="command_execution_time",
            value=1.5,
            unit="seconds",
            command="status"
        )
        
        # Verify logger was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        # Check message
        assert "command_execution_time" in call_args[0][0]
        assert "1.5seconds" in call_args[0][0]
        
        # Check extra data
        extra_data = call_args[1]["extra"]["extra_data"]
        assert extra_data["metric"] == "command_execution_time"
        assert extra_data["value"] == 1.5
        assert extra_data["unit"] == "seconds"
        assert extra_data["command"] == "status"


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        logger = setup_logging(log_level="INFO")
        
        assert logger.name == "cassandra_mcp_server"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            logger = setup_logging(
                log_level="DEBUG",
                log_file=str(log_file)
            )
            
            assert logger.level == logging.DEBUG
            assert len(logger.handlers) == 2  # Console + File
            
            # Verify log file was created
            assert log_file.parent.exists()
    
    def test_setup_logging_structured(self):
        """Test logging setup with structured format."""
        logger = setup_logging(
            log_level="INFO",
            structured=True
        )
        
        # Check that handlers use StructuredFormatter
        for handler in logger.handlers:
            assert isinstance(handler.formatter, StructuredFormatter)
    
    def test_setup_logging_log_rotation(self):
        """Test logging setup with rotation parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            logger = setup_logging(
                log_level="INFO",
                log_file=str(log_file),
                max_log_size=1024,
                backup_count=3
            )
            
            # Find the rotating file handler
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    file_handler = handler
                    break
            
            assert file_handler is not None
            assert file_handler.maxBytes == 1024
            assert file_handler.backupCount == 3
    
    def test_setup_logging_level_filtering(self):
        """Test that log level filtering works correctly."""
        logger = setup_logging(log_level="WARNING")
        
        # Logger should be set to WARNING level
        assert logger.level == logging.WARNING
        
        # All handlers should also be set to WARNING
        for handler in logger.handlers:
            assert handler.level == logging.WARNING


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_default(self):
        """Test getting default logger."""
        logger = get_logger()
        
        assert logger.name == "cassandra_mcp_server"
    
    def test_get_logger_with_name(self):
        """Test getting logger with specific name."""
        logger = get_logger("test_module")
        
        assert logger.name == "cassandra_mcp_server.test_module"
    
    def test_get_logger_hierarchy(self):
        """Test logger hierarchy."""
        parent_logger = get_logger()
        child_logger = get_logger("child")
        
        # Child logger should be descendant of parent
        assert child_logger.parent == parent_logger or \
               child_logger.name.startswith(parent_logger.name)


class TestGetOperationLogger:
    """Tests for get_operation_logger function."""
    
    def test_get_operation_logger_default(self):
        """Test getting default operation logger."""
        op_logger = get_operation_logger()
        
        assert isinstance(op_logger, OperationLogger)
        assert op_logger.logger.name == "cassandra_mcp_server"
    
    def test_get_operation_logger_with_name(self):
        """Test getting operation logger with specific name."""
        op_logger = get_operation_logger("operations")
        
        assert isinstance(op_logger, OperationLogger)
        assert op_logger.logger.name == "cassandra_mcp_server.operations"


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_end_to_end_logging(self, caplog):
        """Test end-to-end logging flow."""
        import logging
        caplog.set_level(logging.INFO)
        
        # Setup logging
        logger = setup_logging(log_level="INFO")
        
        # Log some messages
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Verify messages were logged
        assert "Test info message" in caplog.text
        assert "Test warning message" in caplog.text
        assert "Test error message" in caplog.text
    
    def test_operation_logging_integration(self, caplog):
        """Test operation logging integration."""
        import logging
        caplog.set_level(logging.INFO)
        
        # Setup logging
        setup_logging(log_level="INFO")
        op_logger = get_operation_logger("test")
        
        # Log an operation
        op_logger.log_operation(
            operation="test_operation",
            parameters={"key": "value"},
            execution_time=1.0,
            success=True
        )
        
        # Verify operation was logged
        assert "test_operation" in caplog.text
        assert "completed successfully" in caplog.text
