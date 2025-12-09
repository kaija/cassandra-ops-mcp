"""Core interface definitions for Cassandra MCP Server."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models import CommandResult, Config, HealthCheckResult
else:
    from src.models import CommandResult, Config


class IAuthenticationManager(ABC):
    """Interface for authentication management."""
    
    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        """Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if the API key is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def load_api_keys(self) -> List[str]:
        """Load API keys from configuration.
        
        Returns:
            List of valid API keys
        """
        pass
    
    @abstractmethod
    def log_auth_attempt(self, api_key: str, success: bool, ip: str) -> None:
        """Log an authentication attempt.
        
        Args:
            api_key: The API key used
            success: Whether authentication was successful
            ip: The IP address of the requester
        """
        pass


class INodeToolExecutor(ABC):
    """Interface for nodetool command execution."""
    
    @abstractmethod
    async def execute_command(
        self, 
        command: str, 
        target_host: Optional[str] = None
    ) -> CommandResult:
        """Execute a nodetool command.
        
        Args:
            command: The nodetool command to execute
            target_host: Optional target host IP address
            
        Returns:
            CommandResult containing execution details
        """
        pass
    
    @abstractmethod
    def build_command(
        self, 
        base_command: str, 
        args: List[str], 
        host: Optional[str]
    ) -> List[str]:
        """Build a complete nodetool command.
        
        Args:
            base_command: The base nodetool command
            args: Additional command arguments
            host: Optional target host
            
        Returns:
            List of command components
        """
        pass
    
    @abstractmethod
    def parse_output(self, command: str, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse command output.
        
        Args:
            command: The executed command
            stdout: Standard output
            stderr: Standard error
            
        Returns:
            Parsed output as dictionary
        """
        pass


class IConfigurationManager(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def load_config(self) -> Config:
        """Load configuration from file.
        
        Returns:
            Config object with loaded settings
        """
        pass
    
    @abstractmethod
    def validate_paths(self) -> bool:
        """Validate configured paths.
        
        Returns:
            True if all paths are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_java_home(self) -> str:
        """Get JAVA_HOME path.
        
        Returns:
            Path to Java installation
        """
        pass
    
    @abstractmethod
    def get_cassandra_bin_path(self) -> str:
        """Get Cassandra bin path.
        
        Returns:
            Path to Cassandra bin directory
        """
        pass
    
    @abstractmethod
    def reload_config(self) -> None:
        """Reload configuration from file."""
        pass


class ICommandRegistry(ABC):
    """Interface for command registry."""
    
    @abstractmethod
    def register_command(self, name: str, handler: Any) -> None:
        """Register a command handler.
        
        Args:
            name: Command name
            handler: Command handler function
        """
        pass
    
    @abstractmethod
    def get_available_commands(self) -> List[str]:
        """Get list of available commands.
        
        Returns:
            List of command names
        """
        pass
    
    @abstractmethod
    def validate_command(self, name: str, args: Dict[str, Any]) -> bool:
        """Validate a command and its arguments.
        
        Args:
            name: Command name
            args: Command arguments
            
        Returns:
            True if command is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_command(self, name: str, args: Dict[str, Any]) -> CommandResult:
        """Execute a registered command.
        
        Args:
            name: Command name
            args: Command arguments
            
        Returns:
            CommandResult containing execution details
        """
        pass


class IHealthCheck(ABC):
    """Interface for health check system."""
    
    @abstractmethod
    async def check_health(self) -> 'HealthCheckResult':
        """Perform health check.
        
        Returns:
            HealthCheckResult with current health status
        """
        pass
    
    @abstractmethod
    async def check_cassandra_connectivity(self) -> bool:
        """Check if Cassandra cluster is reachable.
        
        Returns:
            True if cluster is reachable, False otherwise
        """
        pass
