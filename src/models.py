"""Core data models for Cassandra MCP Server."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Config:
    """Configuration model for the MCP server."""
    
    java_home: str = "/opt/jdk/"
    cassandra_bin_path: str = "/usr/local/cassandra/bin"
    api_keys: List[str] = field(default_factory=list)
    log_level: str = "INFO"
    log_file: str = "cassandra-mcp.log"
    max_log_size: int = 10485760  # 10MB
    health_check_interval: int = 30


@dataclass
class CommandResult:
    """Result of a nodetool command execution."""
    
    success: bool
    command: str
    stdout: str
    stderr: str
    execution_time: float
    timestamp: datetime
    target_host: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command result to dictionary format."""
        return {
            "status": "success" if self.success else "error",
            "data": self.stdout if self.success else None,
            "error": self.stderr if not self.success else None,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "target_host": self.target_host
        }


@dataclass
class MCPTool:
    """MCP tool definition model."""
    
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert tool definition to MCP format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class ErrorResponse:
    """Error response model."""
    
    status: str = "error"
    error_code: str = ""
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary format."""
        return {
            "status": self.status,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            },
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class NodeStatus:
    """Status information for a Cassandra node."""
    
    address: str
    status: str  # U (Up) or D (Down)
    state: str   # N (Normal), L (Leaving), J (Joining), M (Moving)
    load: str
    datacenter: Optional[str] = None
    rack: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Health check result model."""
    
    status: str  # healthy, unhealthy, degraded
    timestamp: datetime
    cassandra_reachable: bool
    node_count: int = 0
    up_nodes: int = 0
    down_nodes: int = 0
    nodes: List[NodeStatus] = field(default_factory=list)
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health check result to dictionary format."""
        result = {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "cassandra": {
                "reachable": self.cassandra_reachable,
                "node_count": self.node_count,
                "up_nodes": self.up_nodes,
                "down_nodes": self.down_nodes
            }
        }
        
        if self.error_message:
            result["error"] = self.error_message
        
        if self.details:
            result["details"] = self.details
        
        if self.nodes:
            result["nodes"] = [
                {
                    "address": node.address,
                    "status": node.status,
                    "state": node.state,
                    "load": node.load,
                    "datacenter": node.datacenter,
                    "rack": node.rack
                }
                for node in self.nodes
            ]
        
        return result
