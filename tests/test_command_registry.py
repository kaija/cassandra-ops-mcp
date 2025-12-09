"""Tests for CommandRegistry implementation."""

import pytest
from unittest.mock import Mock, AsyncMock
from src.command_registry import CommandRegistry
from src.models import CommandResult
from datetime import datetime


class TestCommandRegistry:
    """Test suite for CommandRegistry."""
    
    @pytest.fixture
    def mock_executor(self):
        """Create a mock NodeToolExecutor."""
        executor = Mock()
        executor.execute_command = AsyncMock()
        return executor
    
    @pytest.fixture
    def registry(self, mock_executor):
        """Create a CommandRegistry instance."""
        return CommandRegistry(mock_executor)
    
    def test_get_available_commands(self, registry):
        """Test getting list of available commands."""
        commands = registry.get_available_commands()
        
        # Check monitoring commands
        assert "status" in commands
        assert "ring" in commands
        assert "info" in commands
        assert "netstats" in commands
        
        # Check maintenance commands
        assert "repair" in commands
        assert "snapshot" in commands
        assert "cleanup" in commands
        assert "compact" in commands
        
        # Check extended commands
        assert "getsstables" in commands
        assert "getcompactionthroughput" in commands
        assert "getconcurrentcompactors" in commands

    def test_validate_command_valid(self, registry):
        """Test validating a valid command."""
        assert registry.validate_command("status", {}) is True
        assert registry.validate_command("repair", {}) is True
        assert registry.validate_command("info", {"target_host": "192.168.1.1"}) is True
    
    def test_validate_command_unknown(self, registry):
        """Test validating an unknown command."""
        assert registry.validate_command("unknown_command", {}) is False
    
    def test_validate_command_missing_required_args(self, registry):
        """Test validating command with missing required arguments."""
        # getsstables requires keyspace, table, and key
        assert registry.validate_command("getsstables", {}) is False
        assert registry.validate_command("getsstables", {"keyspace": "test"}) is False
        assert registry.validate_command("getsstables", {
            "keyspace": "test",
            "table": "users",
            "key": "123"
        }) is True
    
    def test_validate_command_invalid_target_host_type(self, registry):
        """Test validating command with invalid target_host type."""
        assert registry.validate_command("status", {"target_host": 123}) is False

    @pytest.mark.asyncio
    async def test_execute_command_success(self, registry, mock_executor):
        """Test executing a valid command."""
        # Setup mock response
        expected_result = CommandResult(
            success=True,
            command="status",
            stdout="UN 192.168.1.1",
            stderr="",
            execution_time=0.5,
            timestamp=datetime.now(),
            target_host=None
        )
        mock_executor.execute_command.return_value = expected_result
        
        # Execute command
        result = await registry.execute_command("status", {})
        
        # Verify
        assert result.success is True
        assert result.command == "status"
        mock_executor.execute_command.assert_called_once_with("status", None)
    
    @pytest.mark.asyncio
    async def test_execute_command_with_target_host(self, registry, mock_executor):
        """Test executing command with target host."""
        expected_result = CommandResult(
            success=True,
            command="info",
            stdout="ID: 123",
            stderr="",
            execution_time=0.3,
            timestamp=datetime.now(),
            target_host="192.168.1.1"
        )
        mock_executor.execute_command.return_value = expected_result
        
        result = await registry.execute_command("info", {"target_host": "192.168.1.1"})
        
        assert result.success is True
        assert result.target_host == "192.168.1.1"
        mock_executor.execute_command.assert_called_once_with("info", "192.168.1.1")

    @pytest.mark.asyncio
    async def test_execute_command_validation_failure(self, registry, mock_executor):
        """Test executing an invalid command."""
        result = await registry.execute_command("unknown_command", {})
        
        assert result.success is False
        assert "validation failed" in result.stderr.lower()
        mock_executor.execute_command.assert_not_called()
    
    def test_register_command_safe(self, registry):
        """Test registering a safe command."""
        # Register a command that's in the safe list
        handler = {
            "description": "Test command",
            "category": "test",
            "requires_args": False,
            "safe": True
        }
        
        # This should work since 'status' is in SAFE_COMMANDS
        registry.register_command("status", handler)
        
        # Verify it was registered
        metadata = registry.get_command_metadata("status")
        assert metadata["description"] == "Test command"
    
    def test_register_command_unsafe(self, registry):
        """Test registering an unsafe command."""
        handler = {
            "description": "Unsafe command",
            "category": "test",
            "requires_args": False,
            "safe": True
        }
        
        # This should fail since 'dangerous_command' is not in SAFE_COMMANDS
        with pytest.raises(ValueError, match="not in the safe commands list"):
            registry.register_command("dangerous_command", handler)

    def test_get_command_metadata(self, registry):
        """Test getting command metadata."""
        metadata = registry.get_command_metadata("status")
        
        assert metadata is not None
        assert metadata["description"] == "Get cluster status and node information"
        assert metadata["category"] == "monitoring"
        assert metadata["safe"] is True
        
        # Test non-existent command
        assert registry.get_command_metadata("nonexistent") is None
    
    def test_command_categories(self, registry):
        """Test that commands are properly categorized."""
        # Monitoring
        assert registry.get_command_metadata("status")["category"] == "monitoring"
        assert registry.get_command_metadata("ring")["category"] == "monitoring"
        
        # Maintenance
        assert registry.get_command_metadata("repair")["category"] == "maintenance"
        assert registry.get_command_metadata("snapshot")["category"] == "maintenance"
        
        # Extended
        assert registry.get_command_metadata("getsstables")["category"] == "extended"
        assert registry.get_command_metadata("getcompactionthroughput")["category"] == "extended"
