"""Integration tests for Cassandra MCP Server."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.main import Application
from src.models import Config


class TestApplicationIntegration:
    """Test application integration and lifecycle."""
    
    @pytest.mark.asyncio
    async def test_application_initialization(self):
        """Test that application initializes all components correctly."""
        app = Application()
        
        # Mock config file to avoid file system dependency
        mock_config = Config(
            java_home="/usr/lib/jvm/java-11",
            cassandra_bin_path="/opt/cassandra/bin",
            api_keys=["test-key"],
            log_level="INFO"
        )
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.load_config.return_value = mock_config
            mock_config_manager.return_value.validate_paths.return_value = True
            mock_config_manager.return_value.get_java_home.return_value = "/usr/lib/jvm/java-11"
            mock_config_manager.return_value.get_cassandra_bin_path.return_value = "/opt/cassandra/bin"
            
            # Initialize application
            result = await app.initialize()
            
            # Verify initialization succeeded
            assert result is True
            assert app.config_manager is not None
            assert app.auth_manager is not None
            assert app.executor is not None
            assert app.command_registry is not None
            assert app.mcp_server is not None
            assert app.health_check is not None
    
    @pytest.mark.asyncio
    async def test_application_initialization_failure(self):
        """Test that application handles initialization failures gracefully."""
        app = Application()
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            # Simulate initialization failure
            mock_config_manager.side_effect = Exception("Config load failed")
            
            # Initialize application
            result = await app.initialize()
            
            # Verify initialization failed gracefully
            assert result is False
    
    @pytest.mark.asyncio
    async def test_application_shutdown(self):
        """Test that application shuts down gracefully."""
        app = Application()
        
        # Mock config file
        mock_config = Config(
            java_home="/usr/lib/jvm/java-11",
            cassandra_bin_path="/opt/cassandra/bin",
            api_keys=["test-key"],
            log_level="INFO"
        )
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.load_config.return_value = mock_config
            mock_config_manager.return_value.validate_paths.return_value = True
            mock_config_manager.return_value.get_java_home.return_value = "/usr/lib/jvm/java-11"
            mock_config_manager.return_value.get_cassandra_bin_path.return_value = "/opt/cassandra/bin"
            
            # Initialize application
            await app.initialize()
            app._running = True
            
            # Shutdown application
            await app.shutdown()
            
            # Verify shutdown completed
            assert app._running is False
    
    @pytest.mark.asyncio
    async def test_component_integration(self):
        """Test that all components integrate correctly."""
        app = Application()
        
        mock_config = Config(
            java_home="/usr/lib/jvm/java-11",
            cassandra_bin_path="/opt/cassandra/bin",
            api_keys=["test-key-123"],
            log_level="INFO"
        )
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.load_config.return_value = mock_config
            mock_config_manager.return_value.validate_paths.return_value = True
            mock_config_manager.return_value.get_java_home.return_value = "/usr/lib/jvm/java-11"
            mock_config_manager.return_value.get_cassandra_bin_path.return_value = "/opt/cassandra/bin"
            
            # Initialize application
            await app.initialize()
            
            # Verify component integration
            # 1. Config manager provides config to auth manager
            assert app.auth_manager.config == mock_config
            
            # 2. Executor uses config manager
            assert app.executor.config_manager == app.config_manager
            
            # 3. Command registry uses executor
            assert app.command_registry.executor == app.executor
            
            # 4. MCP server uses command registry and auth manager
            assert app.mcp_server.command_registry == app.command_registry
            assert app.mcp_server.auth_manager == app.auth_manager
            
            # 5. Health check uses executor
            assert app.health_check.executor == app.executor
            
            # 6. MCP server has registered tools
            assert app.mcp_server.get_tool_count() > 0
            
            # 7. Command registry has available commands
            commands = app.command_registry.get_available_commands()
            assert len(commands) > 0
            assert "status" in commands
            assert "ring" in commands
    
    @pytest.mark.asyncio
    async def test_end_to_end_tool_execution(self):
        """Test end-to-end tool execution through all layers."""
        app = Application()
        
        mock_config = Config(
            java_home="/usr/lib/jvm/java-11",
            cassandra_bin_path="/opt/cassandra/bin",
            api_keys=["valid-api-key"],
            log_level="INFO"
        )
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.load_config.return_value = mock_config
            mock_config_manager.return_value.validate_paths.return_value = True
            mock_config_manager.return_value.get_java_home.return_value = "/usr/lib/jvm/java-11"
            mock_config_manager.return_value.get_cassandra_bin_path.return_value = "/opt/cassandra/bin"
            
            # Initialize application
            await app.initialize()
            
            # Mock executor to avoid actual command execution
            from datetime import datetime
            from src.models import CommandResult
            
            mock_result = CommandResult(
                success=True,
                command="status",
                stdout="Datacenter: datacenter1\nUN  192.168.1.1  100 KB  256  100%  abc123  rack1",
                stderr="",
                execution_time=0.5,
                timestamp=datetime.now()
            )
            
            app.executor.execute_command = AsyncMock(return_value=mock_result)
            
            # Execute tool through MCP server
            result = await app.mcp_server.handle_call_tool(
                "cassandra_status",
                {"api_key": "valid-api-key", "client_ip": "127.0.0.1"}
            )
            
            # Verify result
            assert len(result) == 1
            assert result[0].type == "text"
            
            # Parse JSON response
            import json
            response = json.loads(result[0].text)
            
            # Verify response structure
            assert "status" in response
            assert response["status"] == "success"
            assert "data" in response
            assert "execution_time" in response
    
    @pytest.mark.asyncio
    async def test_authentication_flow(self):
        """Test authentication flow through the system."""
        app = Application()
        
        mock_config = Config(
            java_home="/usr/lib/jvm/java-11",
            cassandra_bin_path="/opt/cassandra/bin",
            api_keys=["valid-key"],
            log_level="INFO"
        )
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.load_config.return_value = mock_config
            mock_config_manager.return_value.validate_paths.return_value = True
            mock_config_manager.return_value.get_java_home.return_value = "/usr/lib/jvm/java-11"
            mock_config_manager.return_value.get_cassandra_bin_path.return_value = "/opt/cassandra/bin"
            
            # Initialize application
            await app.initialize()
            
            # Test valid authentication
            assert app.auth_manager.validate_api_key("valid-key") is True
            assert app.auth_manager.get_http_status_code("valid-key") == 200
            
            # Test invalid authentication
            assert app.auth_manager.validate_api_key("invalid-key") is False
            assert app.auth_manager.get_http_status_code("invalid-key") == 403
            
            # Test missing authentication
            assert app.auth_manager.validate_api_key("") is False
            assert app.auth_manager.get_http_status_code(None) == 401
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self):
        """Test health check integration with executor."""
        app = Application()
        
        mock_config = Config(
            java_home="/usr/lib/jvm/java-11",
            cassandra_bin_path="/opt/cassandra/bin",
            api_keys=["test-key"],
            log_level="INFO"
        )
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.load_config.return_value = mock_config
            mock_config_manager.return_value.validate_paths.return_value = True
            mock_config_manager.return_value.get_java_home.return_value = "/usr/lib/jvm/java-11"
            mock_config_manager.return_value.get_cassandra_bin_path.return_value = "/opt/cassandra/bin"
            
            # Initialize application
            await app.initialize()
            
            # Mock executor for health check
            from datetime import datetime
            from src.models import CommandResult
            
            mock_result = CommandResult(
                success=True,
                command="status",
                stdout="Datacenter: dc1\nUN  192.168.1.1  100 KB  256  100%  abc  rack1",
                stderr="",
                execution_time=0.3,
                timestamp=datetime.now()
            )
            
            app.executor.execute_command = AsyncMock(return_value=mock_result)
            
            # Perform health check
            health_result = await app.health_check.check_health()
            
            # Verify health check result
            assert health_result.status == "healthy"
            assert health_result.cassandra_reachable is True
            assert health_result.node_count == 1
            assert health_result.up_nodes == 1
            assert health_result.down_nodes == 0


class TestApplicationLifecycle:
    """Test application lifecycle management."""
    
    def test_application_initial_state(self):
        """Test application initial state."""
        app = Application()
        
        assert app.logger is None
        assert app.config_manager is None
        assert app.auth_manager is None
        assert app.executor is None
        assert app.command_registry is None
        assert app.mcp_server is None
        assert app.health_check is None
        assert app._running is False
    
    @pytest.mark.asyncio
    async def test_multiple_shutdown_calls(self):
        """Test that multiple shutdown calls are handled gracefully."""
        app = Application()
        
        mock_config = Config(
            java_home="/usr/lib/jvm/java-11",
            cassandra_bin_path="/opt/cassandra/bin",
            api_keys=["test-key"],
            log_level="INFO"
        )
        
        with patch('src.main.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.load_config.return_value = mock_config
            mock_config_manager.return_value.validate_paths.return_value = True
            mock_config_manager.return_value.get_java_home.return_value = "/usr/lib/jvm/java-11"
            mock_config_manager.return_value.get_cassandra_bin_path.return_value = "/opt/cassandra/bin"
            
            # Initialize application
            await app.initialize()
            app._running = True
            
            # Call shutdown multiple times
            await app.shutdown()
            await app.shutdown()  # Should not raise error
            
            # Verify state
            assert app._running is False
