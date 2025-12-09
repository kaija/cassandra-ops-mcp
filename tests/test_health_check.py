"""Tests for health check system."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.health_check import HealthCheck
from src.models import CommandResult, NodeStatus


class TestHealthCheck:
    """Tests for HealthCheck class."""
    
    @pytest.fixture
    def mock_executor(self):
        """Create a mock NodeTool executor."""
        executor = Mock()
        executor.execute_command = AsyncMock()
        return executor
    
    @pytest.fixture
    def health_check(self, mock_executor):
        """Create a HealthCheck instance with mock executor."""
        return HealthCheck(mock_executor)
    
    @pytest.mark.asyncio
    async def test_check_health_healthy_cluster(self, health_check, mock_executor):
        """Test health check with all nodes up."""
        # Mock successful status command
        status_output = """Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.1  100 KB     256     100%    abc123                                rack1
UN  127.0.0.2  150 KB     256     100%    def456                                rack1
UN  127.0.0.3  200 KB     256     100%    ghi789                                rack1
"""
        
        mock_executor.execute_command.return_value = CommandResult(
            success=True,
            command="status",
            stdout=status_output,
            stderr="",
            execution_time=0.5,
            timestamp=datetime.now()
        )
        
        # Perform health check
        result = await health_check.check_health()
        
        # Verify result
        assert result.status == "healthy"
        assert result.cassandra_reachable is True
        assert result.node_count == 3
        assert result.up_nodes == 3
        assert result.down_nodes == 0
        assert len(result.nodes) == 3
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_check_health_degraded_cluster(self, health_check, mock_executor):
        """Test health check with some nodes down."""
        # Mock status command with mixed node states
        status_output = """Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.1  100 KB     256     100%    abc123                                rack1
DN  127.0.0.2  150 KB     256     100%    def456                                rack1
UN  127.0.0.3  200 KB     256     100%    ghi789                                rack1
"""
        
        mock_executor.execute_command.return_value = CommandResult(
            success=True,
            command="status",
            stdout=status_output,
            stderr="",
            execution_time=0.5,
            timestamp=datetime.now()
        )
        
        # Perform health check
        result = await health_check.check_health()
        
        # Verify result
        assert result.status == "degraded"
        assert result.cassandra_reachable is True
        assert result.node_count == 3
        assert result.up_nodes == 2
        assert result.down_nodes == 1
    
    @pytest.mark.asyncio
    async def test_check_health_unhealthy_cluster(self, health_check, mock_executor):
        """Test health check with all nodes down."""
        # Mock status command with all nodes down
        status_output = """Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
DN  127.0.0.1  100 KB     256     100%    abc123                                rack1
DN  127.0.0.2  150 KB     256     100%    def456                                rack1
"""
        
        mock_executor.execute_command.return_value = CommandResult(
            success=True,
            command="status",
            stdout=status_output,
            stderr="",
            execution_time=0.5,
            timestamp=datetime.now()
        )
        
        # Perform health check
        result = await health_check.check_health()
        
        # Verify result
        assert result.status == "unhealthy"
        assert result.cassandra_reachable is True
        assert result.node_count == 2
        assert result.up_nodes == 0
        assert result.down_nodes == 2
    
    @pytest.mark.asyncio
    async def test_check_health_cassandra_unreachable(self, health_check, mock_executor):
        """Test health check when Cassandra is unreachable."""
        # Mock failed status command
        mock_executor.execute_command.return_value = CommandResult(
            success=False,
            command="status",
            stdout="",
            stderr="Connection refused",
            execution_time=0.1,
            timestamp=datetime.now()
        )
        
        # Perform health check
        result = await health_check.check_health()
        
        # Verify result
        assert result.status == "unhealthy"
        assert result.cassandra_reachable is False
        assert result.error_message == "Cassandra cluster is not reachable"
    
    @pytest.mark.asyncio
    async def test_check_health_exception_handling(self, health_check, mock_executor):
        """Test health check handles exceptions gracefully."""
        # Mock executor to raise exception
        mock_executor.execute_command.side_effect = Exception("Test error")
        
        # Perform health check
        result = await health_check.check_health()
        
        # Verify result - when connectivity check fails, status is unhealthy
        assert result.status == "unhealthy"
        assert result.cassandra_reachable is False
        assert result.error_message == "Cassandra cluster is not reachable"
    
    @pytest.mark.asyncio
    async def test_check_cassandra_connectivity_success(self, health_check, mock_executor):
        """Test successful Cassandra connectivity check."""
        # Mock successful status command
        mock_executor.execute_command.return_value = CommandResult(
            success=True,
            command="status",
            stdout="Datacenter: dc1\n",
            stderr="",
            execution_time=0.5,
            timestamp=datetime.now()
        )
        
        # Check connectivity
        result = await health_check.check_cassandra_connectivity()
        
        # Verify result
        assert result is True
        mock_executor.execute_command.assert_called_once_with("status")
    
    @pytest.mark.asyncio
    async def test_check_cassandra_connectivity_failure(self, health_check, mock_executor):
        """Test failed Cassandra connectivity check."""
        # Mock failed status command
        mock_executor.execute_command.return_value = CommandResult(
            success=False,
            command="status",
            stdout="",
            stderr="Connection error",
            execution_time=0.1,
            timestamp=datetime.now()
        )
        
        # Check connectivity
        result = await health_check.check_cassandra_connectivity()
        
        # Verify result
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_cassandra_connectivity_timeout(self, health_check, mock_executor):
        """Test Cassandra connectivity check timeout."""
        # Mock executor to timeout
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(15)  # Longer than timeout
            return CommandResult(
                success=True,
                command="status",
                stdout="",
                stderr="",
                execution_time=15.0,
                timestamp=datetime.now()
            )
        
        mock_executor.execute_command.side_effect = slow_execute
        
        # Check connectivity
        result = await health_check.check_cassandra_connectivity()
        
        # Verify result
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_cassandra_connectivity_exception(self, health_check, mock_executor):
        """Test Cassandra connectivity check with exception."""
        # Mock executor to raise exception
        mock_executor.execute_command.side_effect = Exception("Network error")
        
        # Check connectivity
        result = await health_check.check_cassandra_connectivity()
        
        # Verify result
        assert result is False
    
    def test_parse_status_output_single_datacenter(self, health_check):
        """Test parsing status output with single datacenter."""
        output = """Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.1  100 KB     256     100%    abc123                                rack1
UN  127.0.0.2  150 KB     256     100%    def456                                rack2
"""
        
        nodes = health_check._parse_status_output(output)
        
        assert len(nodes) == 2
        assert nodes[0].address == "127.0.0.1"
        assert nodes[0].status == "U"
        assert nodes[0].state == "N"
        assert nodes[0].load == "100"
        assert nodes[0].datacenter == "datacenter1"
        # Rack is the last column
        assert nodes[0].rack == "rack1"
    
    def test_parse_status_output_multiple_datacenters(self, health_check):
        """Test parsing status output with multiple datacenters."""
        output = """Datacenter: dc1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.1  100 KB     256     50%     abc123                                rack1
Datacenter: dc2
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.2  150 KB     256     50%     def456                                rack1
"""
        
        nodes = health_check._parse_status_output(output)
        
        assert len(nodes) == 2
        assert nodes[0].datacenter == "dc1"
        assert nodes[1].datacenter == "dc2"
    
    def test_parse_status_output_mixed_states(self, health_check):
        """Test parsing status output with mixed node states."""
        output = """Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.1  100 KB     256     100%    abc123                                rack1
DN  127.0.0.2  150 KB     256     100%    def456                                rack1
UL  127.0.0.3  200 KB     256     100%    ghi789                                rack1
"""
        
        nodes = health_check._parse_status_output(output)
        
        assert len(nodes) == 3
        assert nodes[0].status == "U"
        assert nodes[0].state == "N"
        assert nodes[1].status == "D"
        assert nodes[1].state == "N"
        assert nodes[2].status == "U"
        assert nodes[2].state == "L"
    
    def test_parse_status_output_empty(self, health_check):
        """Test parsing empty status output."""
        output = ""
        
        nodes = health_check._parse_status_output(output)
        
        assert len(nodes) == 0
    
    @pytest.mark.asyncio
    async def test_health_check_result_to_dict(self, health_check, mock_executor):
        """Test HealthCheckResult to_dict conversion."""
        # Mock successful status command
        status_output = """Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address    Load       Tokens  Owns    Host ID                               Rack
UN  127.0.0.1  100 KB     256     100%    abc123                                rack1
"""
        
        mock_executor.execute_command.return_value = CommandResult(
            success=True,
            command="status",
            stdout=status_output,
            stderr="",
            execution_time=0.5,
            timestamp=datetime.now()
        )
        
        # Perform health check
        result = await health_check.check_health()
        result_dict = result.to_dict()
        
        # Verify dictionary structure
        assert "status" in result_dict
        assert "timestamp" in result_dict
        assert "cassandra" in result_dict
        assert result_dict["cassandra"]["reachable"] is True
        assert result_dict["cassandra"]["node_count"] == 1
        assert result_dict["cassandra"]["up_nodes"] == 1
        assert result_dict["cassandra"]["down_nodes"] == 0
        assert "nodes" in result_dict
        assert len(result_dict["nodes"]) == 1
