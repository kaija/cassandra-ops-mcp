"""Main entry point for Cassandra MCP Server."""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

from src.config_manager import ConfigurationManager
from src.authentication import AuthenticationManager
from src.nodetool_executor import NodeToolExecutor
from src.command_registry import CommandRegistry
from src.mcp_server import MCPServer
from src.health_check import HealthCheck
from src.logging_config import setup_logging, get_logger


class Application:
    """Main application class with lifecycle management."""
    
    def __init__(self):
        """Initialize application."""
        self.logger = None
        self.config_manager: Optional[ConfigurationManager] = None
        self.auth_manager: Optional[AuthenticationManager] = None
        self.executor: Optional[NodeToolExecutor] = None
        self.command_registry: Optional[CommandRegistry] = None
        self.mcp_server: Optional[MCPServer] = None
        self.health_check: Optional[HealthCheck] = None
        self.shutdown_event = asyncio.Event()
        self._running = False
    
    async def initialize(self):
        """Initialize all application components."""
        # Initialize logging system first
        setup_logging(log_level="INFO")
        self.logger = get_logger("main")
        
        self.logger.info("=" * 60)
        self.logger.info("Cassandra MCP Server - Starting Initialization")
        self.logger.info("=" * 60)
        
        try:
            # Initialize configuration
            self.logger.info("Loading configuration...")
            self.config_manager = ConfigurationManager()
            config = self.config_manager.load_config()
            
            # Re-initialize logging with configuration settings
            setup_logging(
                log_level=config.log_level,
                log_file=config.log_file,
                max_log_size=config.max_log_size,
                structured=False  # Can be made configurable
            )
            self.logger = get_logger("main")
            self.logger.info("Logging system configured from config file")
            
            # Validate paths
            self.logger.info("Validating configured paths...")
            if not self.config_manager.validate_paths():
                self.logger.warning("Some configured paths are invalid, using defaults")
            else:
                self.logger.info("All configured paths validated successfully")
            
            # Initialize authentication
            self.logger.info("Initializing authentication manager...")
            self.auth_manager = AuthenticationManager(config)
            
            # Initialize nodetool executor
            self.logger.info("Initializing nodetool executor...")
            self.executor = NodeToolExecutor(self.config_manager)
            
            # Initialize command registry
            self.logger.info("Initializing command registry...")
            self.command_registry = CommandRegistry(self.executor)
            
            # Initialize health check
            self.logger.info("Initializing health check system...")
            self.health_check = HealthCheck(self.executor)
            
            # Initialize MCP server
            self.logger.info("Initializing MCP server...")
            self.mcp_server = MCPServer(self.command_registry, self.auth_manager)
            
            self.logger.info("=" * 60)
            self.logger.info(f"Initialization Complete")
            self.logger.info(f"  - Registered tools: {self.mcp_server.get_tool_count()}")
            self.logger.info(f"  - Available commands: {', '.join(self.command_registry.get_available_commands())}")
            self.logger.info(f"  - Java Home: {self.config_manager.get_java_home()}")
            self.logger.info(f"  - Cassandra Path: {self.config_manager.get_cassandra_bin_path()}")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Initialization failed: {e}", exc_info=True)
            else:
                print(f"Fatal error during initialization: {e}", file=sys.stderr)
            return False
    
    async def run(self):
        """Run the application."""
        if not await self.initialize():
            self.logger.error("Failed to initialize application")
            sys.exit(1)
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self._running = True
        self.logger.info("Cassandra MCP Server is now running")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            # Run the MCP server
            await self.mcp_server.run()
            
        except asyncio.CancelledError:
            self.logger.info("Server task cancelled")
        except Exception as e:
            self.logger.error(f"Server error: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            sig_name = signal.Signals(signum).name
            if self.logger:
                self.logger.info(f"Received signal {sig_name}, initiating shutdown...")
            self.shutdown_event.set()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if self.logger:
            self.logger.info("Signal handlers registered (SIGINT, SIGTERM)")
    
    async def shutdown(self):
        """Perform graceful shutdown of all components."""
        if not self._running:
            return
        
        self._running = False
        
        self.logger.info("=" * 60)
        self.logger.info("Cassandra MCP Server - Shutting Down")
        self.logger.info("=" * 60)
        
        try:
            # Shutdown components in reverse order of initialization
            if self.mcp_server:
                self.logger.info("Stopping MCP server...")
                # MCP server cleanup if needed
            
            if self.health_check:
                self.logger.info("Stopping health check system...")
                # Health check cleanup if needed
            
            if self.command_registry:
                self.logger.info("Cleaning up command registry...")
                # Command registry cleanup if needed
            
            if self.executor:
                self.logger.info("Cleaning up nodetool executor...")
                # Executor cleanup if needed
            
            if self.auth_manager:
                self.logger.info("Cleaning up authentication manager...")
                # Auth manager cleanup if needed
            
            if self.config_manager:
                self.logger.info("Cleaning up configuration manager...")
                # Config manager cleanup if needed
            
            self.logger.info("=" * 60)
            self.logger.info("Shutdown complete")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)


async def main():
    """Main function to start the MCP server."""
    app = Application()
    
    try:
        await app.run()
    except KeyboardInterrupt:
        if app.logger:
            app.logger.info("Server stopped by user (KeyboardInterrupt)")
        else:
            print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        if app.logger:
            app.logger.error(f"Fatal error: {e}", exc_info=True)
        else:
            print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
