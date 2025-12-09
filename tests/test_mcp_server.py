"""Tests for MCP Server core implementation."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import json

from src.mcp_server import MCPServer
from src.models import CommandResult, Config
from src.authentication import AuthenticationManager
from src.command_registry import CommandRegistry
from src.nodetool_executor import NodeToolExecutor
from src.config_manager import ConfigurationManager


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return Config(
        api_keys=["test-key-123", "test-key-456"],
        java_home="/opt/jdk/",
        cassandra_bin_path="/usr/local/cassandra/bin"
    )


@pytest.fixture
def mock_config_manager(mock_config):
    """Create a mock configuration manager."""
    manager = Mock(spec=ConfigurationManager)
    manager.get_java_home.return_value = mock_config.java_home
    manager.get_cassandra_bin_path.return_value = mock_config.cassandra_bin_path
    manager.load_config.return_value = mock_config
    manager.validate_paths.return_value = True
    return manager


@pytest.fixture
def auth_manager(mock_config):
    """Create an authentication manager."""
    return AuthenticationManager(mock_config)


@pytest.fixture
def mock_executor(mock_config_manager):
    """Create a mock nodetool executor."""
    executor = Mock(spec=NodeToolExecutor)
    
    async def mock_execute(command, target_host=None):
        return CommandResult(
            success=True,
            command=command,
            stdout=f"Mock output for {command}",
            stderr="",
            execution_time=0.1,
            timestamp=datetime.now(),
            target_host=target_host
        )
    
    executor.execute_command = AsyncMock(side_effect=mock_execute)
    return executor



@pytest.fixture
def command_registry(mock_executor):
    """Create a command registry."""
    return CommandRegistry(mock_executor)


@pytest.fixture
def mcp_server(command_registry, auth_manager):
    """Create an MCP server instance."""
    return MCPServer(command_registry, auth_manager)


class TestMCPServer:
    """Test suite for MCP Server."""
    
    def test_initialization(self, mcp_server):
        """Test MCP server initialization."""
        assert mcp_server is not None
        assert mcp_server.get_tool_count() > 0
        assert len(mcp_server.get_tool_names()) > 0
    
    def test_tool_count(self, mcp_server):
        """Test that all commands are registered as tools."""
        # Should have tools for all registered commands
        assert mcp_server.get_tool_count() >= 11  # At least the basic commands
    
    def test_tool_names_format(self, mcp_server):
        """Test that tool names follow the correct format."""
        tool_names = mcp_server.get_tool_names()
        
        # All tool names should start with "cassandra_"
        for name in tool_names:
            assert name.startswith("cassandra_")
        
        # Should include basic monitoring commands
        assert "cassandra_status" in tool_names
        assert "cassandra_ring" in tool_names
        assert "cassandra_info" in tool_names
        assert "cassandra_netstats" in tool_names
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server):
        """Test list_tools handler."""
        tools = await mcp_server.handle_list_tools()
        
        assert len(tools) > 0
        
        # Check first tool structure
        tool = tools[0]
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, 'inputSchema')

    
    @pytest.mark.asyncio
    async def test_call_tool_without_api_key(self, mcp_server):
        """Test calling a tool without API key returns 401."""
        result = await mcp_server.handle_call_tool(
            "cassandra_status",
            {}
        )
        
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response["status"] == "error"
        assert response["error"]["code"] == "UNAUTHORIZED"
    
    @pytest.mark.asyncio
    async def test_call_tool_with_invalid_api_key(self, mcp_server):
        """Test calling a tool with invalid API key returns 403."""
        result = await mcp_server.handle_call_tool(
            "cassandra_status",
            {"api_key": "invalid-key"}
        )
        
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response["status"] == "error"
        assert response["error"]["code"] == "FORBIDDEN"
    
    @pytest.mark.asyncio
    async def test_call_tool_with_valid_api_key(self, mcp_server):
        """Test calling a tool with valid API key succeeds."""
        result = await mcp_server.handle_call_tool(
            "cassandra_status",
            {"api_key": "test-key-123"}
        )
        
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response["status"] == "success"
        assert "data" in response
    
    @pytest.mark.asyncio
    async def test_call_tool_with_target_host(self, mcp_server):
        """Test calling a tool with target host parameter."""
        result = await mcp_server.handle_call_tool(
            "cassandra_status",
            {
                "api_key": "test-key-123",
                "target_host": "192.168.1.100"
            }
        )
        
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response["status"] == "success"
        assert response["target_host"] == "192.168.1.100"

    
    @pytest.mark.asyncio
    async def test_call_tool_invalid_tool_name(self, mcp_server):
        """Test calling an invalid tool name."""
        result = await mcp_server.handle_call_tool(
            "invalid_tool",
            {"api_key": "test-key-123"}
        )
        
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response["status"] == "error"
        assert response["error"]["code"] == "INVALID_TOOL"
    
    @pytest.mark.asyncio
    async def test_authentication_logging(self, mcp_server, auth_manager):
        """Test that authentication attempts are logged."""
        with patch.object(auth_manager, 'log_auth_attempt') as mock_log:
            await mcp_server.handle_call_tool(
                "cassandra_status",
                {"api_key": "test-key-123", "client_ip": "192.168.1.1"}
            )
            
            # Verify log_auth_attempt was called
            mock_log.assert_called_once()
            args = mock_log.call_args[0]
            assert args[0] == "test-key-123"  # api_key
            assert args[1] is True  # success
            assert args[2] == "192.168.1.1"  # ip
    
    def test_tool_input_schema(self, mcp_server):
        """Test that tool input schemas are properly defined."""
        # Get a tool definition
        tool = mcp_server._tools[0]
        schema = tool.input_schema
        
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "target_host" in schema["properties"]
    
    @pytest.mark.asyncio
    async def test_response_format_success(self, mcp_server):
        """Test that successful responses follow the correct format."""
        result = await mcp_server.handle_call_tool(
            "cassandra_status",
            {"api_key": "test-key-123"}
        )
        
        response = json.loads(result[0].text)
        
        # Check required fields
        assert "status" in response
        assert "data" in response
        assert "execution_time" in response
        assert "timestamp" in response

    
    @pytest.mark.asyncio
    async def test_response_format_error(self, mcp_server):
        """Test that error responses follow the correct format."""
        result = await mcp_server.handle_call_tool(
            "cassandra_status",
            {}  # No API key
        )
        
        response = json.loads(result[0].text)
        
        # Check required fields for error
        assert "status" in response
        assert response["status"] == "error"
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert "timestamp" in response
    
    @pytest.mark.asyncio
    async def test_multiple_api_keys_support(self, mcp_server):
        """Test that multiple API keys are supported."""
        # Test with first key
        result1 = await mcp_server.handle_call_tool(
            "cassandra_status",
            {"api_key": "test-key-123"}
        )
        response1 = json.loads(result1[0].text)
        assert response1["status"] == "success"
        
        # Test with second key
        result2 = await mcp_server.handle_call_tool(
            "cassandra_status",
            {"api_key": "test-key-456"}
        )
        response2 = json.loads(result2[0].text)
        assert response2["status"] == "success"
