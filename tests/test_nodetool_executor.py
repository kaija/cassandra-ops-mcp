"""Tests for NodeTool executor."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.nodetool_executor import NodeToolExecutor
from src.models import CommandResult
from src.config_manager import ConfigurationManager


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager."""
    config_manager = Mock(spec=ConfigurationManager)
    config_manager.get_cassandra_bin_path.return_value = "/usr/local/cassandra/bin"
    config_manager.get_java_home.return_value = "/opt/jdk/"
    return config_manager


@pytest.fixture
def executor(mock_config_manager):
    """Create a NodeToolExecutor instance."""
    return NodeToolExecutor(mock_config_manager, timeout=30)


class TestNodeToolExecutor:
    """Test suite for NodeToolExecutor."""
    
    def test_build_command_without_host(self, executor):
        """Test building command without target host."""
        cmd = executor.build_command("status", [], None)
        
        assert cmd[0].endswith("nodetool")
        assert "status" in cmd
        assert "-h" not in cmd
    
    def test_build_command_with_host(self, executor):
        """Test building command with target host."""
        cmd = executor.build_command("status", ["--resolve-ip"], "192.168.1.100")
        
        assert cmd[0].endswith("nodetool")
        assert "-h" in cmd
        assert "192.168.1.100" in cmd
        assert "status" in cmd
        assert "--resolve-ip" in cmd
    
    def test_build_command_with_args(self, executor):
        """Test building command with additional arguments."""
        cmd = executor.build_command("repair", ["keyspace1", "table1"], None)
        
        assert cmd[0].endswith("nodetool")
        assert "repair" in cmd
        assert "keyspace1" in cmd
        assert "table1" in cmd
    
    def test_validate_ip_format_valid_ipv4(self, executor):
        """Test IP validation with valid IPv4 addresses."""
        assert executor._validate_ip_format("192.168.1.1") is True
        assert executor._validate_ip_format("10.0.0.1") is True
        assert executor._validate_ip_format("127.0.0.1") is True
        assert executor._validate_ip_format("255.255.255.255") is True
    
    def test_validate_ip_format_invalid_ipv4(self, executor):
        """Test IP validation with invalid IPv4 addresses."""
        assert executor._validate_ip_format("256.1.1.1") is False
        assert executor._validate_ip_format("192.168.1") is False
        assert executor._validate_ip_format("192.168.1.1.1") is False
        assert executor._validate_ip_format("abc.def.ghi.jkl") is False
        assert executor._validate_ip_format("") is False
    
    def test_validate_ip_format_valid_ipv6(self, executor):
        """Test IP validation with valid IPv6 addresses."""
        assert executor._validate_ip_format("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert executor._validate_ip_format("::1") is True
        assert executor._validate_ip_format("fe80::1") is True
    
    @pytest.mark.asyncio
    async def test_execute_command_invalid_ip(self, executor):
        """Test command execution with invalid IP format."""
        result = await executor.execute_command("status", target_host="invalid-ip")
        
        assert result.success is False
        assert "Invalid IP format" in result.stderr
        assert result.command == "status"
        assert result.target_host == "invalid-ip"
    
    def test_parse_output_status(self, executor):
        """Test parsing status command output."""
        status_output = """Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.1  100 KB     256     100%    abc123                                rack1
UN  127.0.0.2  200 KB     256     100%    def456                                rack1
"""
        parsed = executor.parse_output("status", status_output, "")
        
        assert "parsed_data" in parsed
        assert "nodes" in parsed["parsed_data"]
        assert len(parsed["parsed_data"]["nodes"]) == 2
        assert parsed["parsed_data"]["total_nodes"] == 2
    
    def test_parse_output_info(self, executor):
        """Test parsing info command output."""
        info_output = """ID               : abc123
Gossip active    : true
Thrift active    : false
Native Transport active: true
Load             : 100 KB
Generation No    : 1234567890
Uptime (seconds) : 3600
Heap Memory (MB) : 512 / 1024
"""
        parsed = executor.parse_output("info", info_output, "")
        
        assert "parsed_data" in parsed
        assert "ID" in parsed["parsed_data"]
        assert "Gossip active" in parsed["parsed_data"]
        assert parsed["parsed_data"]["ID"] == "abc123"
    
    def test_parse_output_generic(self, executor):
        """Test parsing generic command output."""
        output = "Command executed successfully"
        parsed = executor.parse_output("cleanup", output, "")
        
        assert "parsed_data" in parsed
        assert "output" in parsed["parsed_data"]
        assert parsed["parsed_data"]["output"] == output.strip()
    
    def test_get_environment(self, executor):
        """Test environment variable setup."""
        env = executor._get_environment()
        
        assert "JAVA_HOME" in env
        assert env["JAVA_HOME"] == "/opt/jdk/"
        assert "PATH" in env
        assert "/opt/jdk/bin" in env["PATH"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
