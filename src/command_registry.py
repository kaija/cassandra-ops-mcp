"""Command registry for managing and executing nodetool commands."""

from typing import Dict, List, Any, Callable, Optional, Set
from src.models import CommandResult
from src.interfaces import ICommandRegistry, INodeToolExecutor
from src.logging_config import get_logger


class CommandRegistry(ICommandRegistry):
    """Registry for managing supported nodetool commands."""
    
    # Define safe commands that are allowed for execution
    SAFE_COMMANDS: Set[str] = {
        # Monitoring commands
        "status", "ring", "info", "netstats",
        # Maintenance commands
        "repair", "snapshot", "cleanup", "compact",
        # Extended commands
        "getsstables", "getcompactionthroughput", "getconcurrentcompactors"
    }
    
    def __init__(self, executor: INodeToolExecutor):
        """Initialize command registry.
        
        Args:
            executor: NodeTool executor instance
        """
        self.executor = executor
        self.logger = get_logger("command_registry")
        self._commands: Dict[str, Dict[str, Any]] = {}
        self._initialize_commands()
    
    def _initialize_commands(self) -> None:
        """Initialize all supported commands with their metadata."""
        # Monitoring commands
        self._register_monitoring_commands()
        # Maintenance commands
        self._register_maintenance_commands()
        # Extended commands
        self._register_extended_commands()

    def _register_monitoring_commands(self) -> None:
        """Register basic monitoring commands."""
        self._commands["status"] = {
            "description": "Get cluster status and node information",
            "category": "monitoring",
            "requires_args": False,
            "safe": True
        }
        
        self._commands["ring"] = {
            "description": "Get token ring information",
            "category": "monitoring",
            "requires_args": False,
            "safe": True
        }
        
        self._commands["info"] = {
            "description": "Get node information",
            "category": "monitoring",
            "requires_args": False,
            "safe": True
        }
        
        self._commands["netstats"] = {
            "description": "Get network statistics",
            "category": "monitoring",
            "requires_args": False,
            "safe": True
        }

    def _register_maintenance_commands(self) -> None:
        """Register maintenance commands."""
        self._commands["repair"] = {
            "description": "Repair one or more tables",
            "category": "maintenance",
            "requires_args": False,
            "safe": True,
            "optional_args": ["keyspace", "table"]
        }
        
        self._commands["snapshot"] = {
            "description": "Take a snapshot of specified keyspaces",
            "category": "maintenance",
            "requires_args": False,
            "safe": True,
            "optional_args": ["tag", "keyspace"]
        }
        
        self._commands["cleanup"] = {
            "description": "Cleanup keys no longer belonging to a node",
            "category": "maintenance",
            "requires_args": False,
            "safe": True,
            "optional_args": ["keyspace", "table"]
        }
        
        self._commands["compact"] = {
            "description": "Force a major compaction",
            "category": "maintenance",
            "requires_args": False,
            "safe": True,
            "optional_args": ["keyspace", "table"]
        }

    def _register_extended_commands(self) -> None:
        """Register extended diagnostic commands."""
        self._commands["getsstables"] = {
            "description": "Get SSTables for a given key",
            "category": "extended",
            "requires_args": True,
            "safe": True,
            "required_args": ["keyspace", "table", "key"]
        }
        
        self._commands["getcompactionthroughput"] = {
            "description": "Get compaction throughput in MB/s",
            "category": "extended",
            "requires_args": False,
            "safe": True
        }
        
        self._commands["getconcurrentcompactors"] = {
            "description": "Get number of concurrent compactors",
            "category": "extended",
            "requires_args": False,
            "safe": True
        }

    def register_command(self, name: str, handler: Any) -> None:
        """Register a custom command handler.
        
        Args:
            name: Command name
            handler: Command metadata dictionary
        """
        if not isinstance(handler, dict):
            raise ValueError("Handler must be a dictionary with command metadata")
        
        # Validate command is in safe list
        if name not in self.SAFE_COMMANDS:
            self.logger.warning(f"Attempting to register unsafe command: {name}")
            raise ValueError(f"Command '{name}' is not in the safe commands list")
        
        self._commands[name] = handler
        self.logger.info(f"Registered command: {name}")
    
    def get_available_commands(self) -> List[str]:
        """Get list of all registered commands.
        
        Returns:
            List of command names
        """
        return list(self._commands.keys())

    def validate_command(self, name: str, args: Dict[str, Any]) -> bool:
        """Validate a command and its arguments.
        
        Args:
            name: Command name
            args: Command arguments
            
        Returns:
            True if command is valid, False otherwise
        """
        # Check if command exists
        if name not in self._commands:
            self.logger.error(f"Unknown command: {name}")
            return False
        
        command_meta = self._commands[name]
        
        # Check if command is safe
        if not command_meta.get("safe", False):
            self.logger.error(f"Unsafe command: {name}")
            return False
        
        # Validate required arguments
        if command_meta.get("requires_args", False):
            required_args = command_meta.get("required_args", [])
            for arg in required_args:
                if arg not in args or not args[arg]:
                    self.logger.error(f"Missing required argument '{arg}' for command '{name}'")
                    return False
        
        # Validate target_host if provided
        if "target_host" in args and args["target_host"]:
            # Basic validation - actual IP validation happens in executor
            if not isinstance(args["target_host"], str):
                self.logger.error(f"Invalid target_host type for command '{name}'")
                return False
        
        return True

    async def execute_command(self, name: str, args: Dict[str, Any]) -> CommandResult:
        """Execute a registered command.
        
        Args:
            name: Command name
            args: Command arguments including optional target_host
            
        Returns:
            CommandResult containing execution details
        """
        # Validate command first
        if not self.validate_command(name, args):
            from datetime import datetime
            return CommandResult(
                success=False,
                command=name,
                stdout="",
                stderr=f"Command validation failed for '{name}'",
                execution_time=0.0,
                timestamp=datetime.now(),
                target_host=args.get("target_host")
            )
        
        # Extract target_host if provided
        target_host = args.get("target_host")
        
        # Log command execution attempt
        self.logger.info(
            f"Executing command '{name}' with args: {args}" +
            (f" on host {target_host}" if target_host else "")
        )
        
        # Execute the command using the executor
        result = await self.executor.execute_command(name, target_host)
        
        return result
    
    def get_command_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific command.
        
        Args:
            name: Command name
            
        Returns:
            Command metadata dictionary or None if not found
        """
        return self._commands.get(name)
