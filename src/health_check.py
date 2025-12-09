"""Health check system for Cassandra MCP Server."""

import asyncio
from datetime import datetime
from typing import Optional, List
from src.models import HealthCheckResult, NodeStatus
from src.interfaces import IHealthCheck, INodeToolExecutor
from src.logging_config import get_logger


class HealthCheck(IHealthCheck):
    """Health check system for monitoring Cassandra cluster connectivity."""
    
    def __init__(self, executor: INodeToolExecutor):
        """Initialize health check system.
        
        Args:
            executor: NodeTool executor for running health check commands
        """
        self.executor = executor
        self.logger = get_logger("health_check")
    
    async def check_health(self) -> HealthCheckResult:
        """Perform comprehensive health check.
        
        Returns:
            HealthCheckResult with current health status
        """
        timestamp = datetime.now()
        
        try:
            # Check Cassandra connectivity
            cassandra_reachable = await self.check_cassandra_connectivity()
            
            if not cassandra_reachable:
                self.logger.warning("Cassandra cluster is not reachable")
                return HealthCheckResult(
                    status="unhealthy",
                    timestamp=timestamp,
                    cassandra_reachable=False,
                    error_message="Cassandra cluster is not reachable"
                )
            
            # Get cluster status
            nodes, node_count, up_nodes, down_nodes = await self._get_cluster_status()
            
            # Determine overall health status
            if down_nodes == 0:
                status = "healthy"
            elif up_nodes > 0:
                status = "degraded"
            else:
                status = "unhealthy"
            
            self.logger.info(
                f"Health check completed: {status} - "
                f"{up_nodes}/{node_count} nodes up"
            )
            
            return HealthCheckResult(
                status=status,
                timestamp=timestamp,
                cassandra_reachable=True,
                node_count=node_count,
                up_nodes=up_nodes,
                down_nodes=down_nodes,
                nodes=nodes
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed with error: {e}", exc_info=True)
            return HealthCheckResult(
                status="degraded",
                timestamp=timestamp,
                cassandra_reachable=False,
                error_message=f"Health check error: {str(e)}",
                details={"exception_type": type(e).__name__}
            )
    
    async def check_cassandra_connectivity(self) -> bool:
        """Check if Cassandra cluster is reachable.
        
        Returns:
            True if cluster is reachable, False otherwise
        """
        try:
            # Try to execute a simple status command with a short timeout
            result = await asyncio.wait_for(
                self.executor.execute_command("status"),
                timeout=10.0
            )
            
            if result.success:
                self.logger.debug("Cassandra connectivity check: SUCCESS")
                return True
            else:
                self.logger.warning(
                    f"Cassandra connectivity check failed: {result.stderr}"
                )
                return False
                
        except asyncio.TimeoutError:
            self.logger.warning("Cassandra connectivity check timed out")
            return False
        except Exception as e:
            self.logger.error(
                f"Cassandra connectivity check error: {e}",
                exc_info=True
            )
            return False
    
    async def _get_cluster_status(self) -> tuple[List[NodeStatus], int, int, int]:
        """Get cluster status information.
        
        Returns:
            Tuple of (nodes list, total count, up count, down count)
        """
        try:
            # Execute status command
            result = await self.executor.execute_command("status")
            
            if not result.success:
                self.logger.warning(
                    f"Failed to get cluster status: {result.stderr}"
                )
                return [], 0, 0, 0
            
            # Parse the status output
            nodes = self._parse_status_output(result.stdout)
            
            # Count node states
            node_count = len(nodes)
            up_nodes = sum(1 for node in nodes if node.status == "U")
            down_nodes = sum(1 for node in nodes if node.status == "D")
            
            return nodes, node_count, up_nodes, down_nodes
            
        except Exception as e:
            self.logger.error(f"Error getting cluster status: {e}", exc_info=True)
            return [], 0, 0, 0
    
    def _parse_status_output(self, output: str) -> List[NodeStatus]:
        """Parse nodetool status output to extract node information.
        
        Args:
            output: Raw status output from nodetool
            
        Returns:
            List of NodeStatus objects
        """
        nodes = []
        current_datacenter = None
        
        for line in output.strip().split('\n'):
            line = line.strip()
            
            # Detect datacenter
            if line.startswith('Datacenter:'):
                current_datacenter = line.split(':', 1)[1].strip()
                continue
            
            # Parse node lines (start with U, D, N, etc.)
            if line and line[0] in ['U', 'D', 'N']:
                parts = line.split()
                if len(parts) >= 6:
                    # Extract status and state from first column (e.g., "UN", "DN")
                    status_state = parts[0]
                    status = status_state[0] if len(status_state) > 0 else "?"
                    state = status_state[1] if len(status_state) > 1 else "?"
                    
                    # Columns: Status, Address, Load, Tokens, Owns, Host ID, Rack
                    # parts[0] = Status (UN, DN, etc.)
                    # parts[1] = Address
                    # parts[2] = Load (may be "100 KB" - two parts)
                    # Need to handle load that may have units
                    
                    # Find rack - it's the last column
                    rack = parts[-1] if len(parts) > 6 else None
                    
                    node = NodeStatus(
                        address=parts[1],
                        status=status,
                        state=state,
                        load=parts[2],
                        datacenter=current_datacenter,
                        rack=rack
                    )
                    nodes.append(node)
        
        return nodes
