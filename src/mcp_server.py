"""MCP Server core implementation for Cassandra cluster management."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.models import MCPTool, ErrorResponse
from src.interfaces import ICommandRegistry, IAuthenticationManager
from src.logging_config import get_logger


class MCPServer:
    """MCP Server implementation for Cassandra nodetool operations."""
    
    def __init__(
        self,
        command_registry: ICommandRegistry,
        auth_manager: IAuthenticationManager
    ):
        """Initialize MCP Server.
        
        Args:
            command_registry: Command registry for executing nodetool commands
            auth_manager: Authentication manager for API key validation
        """
        self.command_registry = command_registry
        self.auth_manager = auth_manager
        self.logger = get_logger("mcp_server")
        self.server = Server("cassandra-mcp-server")
        self._register_handlers()
        self._tools: List[MCPTool] = []
        self._initialize_tools()
    
    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available MCP tools."""
            return await self.handle_list_tools()
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a tool by name."""
            return await self.handle_call_tool(name, arguments)

    def _initialize_tools(self) -> None:
        """Initialize MCP tool definitions for all supported commands."""
        # Get available commands from registry
        available_commands = self.command_registry.get_available_commands()
        
        for cmd_name in available_commands:
            metadata = self.command_registry.get_command_metadata(cmd_name)
            if metadata:
                tool = self._create_tool_definition(cmd_name, metadata)
                self._tools.append(tool)
        
        self.logger.info(f"Initialized {len(self._tools)} MCP tools")
    
    def _create_tool_definition(self, name: str, metadata: Dict[str, Any]) -> MCPTool:
        """Create MCP tool definition from command metadata.
        
        Args:
            name: Command name
            metadata: Command metadata
            
        Returns:
            MCPTool definition
        """
        # Build input schema
        properties = {
            "target_host": {
                "type": "string",
                "description": "Optional target Cassandra node IP address"
            }
        }
        
        required = []
        
        # Add required arguments
        if metadata.get("requires_args") and "required_args" in metadata:
            for arg in metadata["required_args"]:
                properties[arg] = {
                    "type": "string",
                    "description": f"Required argument: {arg}"
                }
                required.append(arg)

        # Add optional arguments
        if "optional_args" in metadata:
            for arg in metadata["optional_args"]:
                properties[arg] = {
                    "type": "string",
                    "description": f"Optional argument: {arg}"
                }
        
        input_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        description = metadata.get("description", f"Execute nodetool {name} command")
        
        return MCPTool(
            name=f"cassandra_{name}",
            description=description,
            input_schema=input_schema
        )
    
    async def handle_list_tools(self) -> List[Tool]:
        """Handle list_tools MCP request.
        
        Returns:
            List of available tools in MCP format
        """
        self.logger.info("Handling list_tools request")
        
        tools = []
        for mcp_tool in self._tools:
            tool_dict = mcp_tool.to_mcp_format()
            tools.append(Tool(
                name=tool_dict["name"],
                description=tool_dict["description"],
                inputSchema=tool_dict["inputSchema"]
            ))
        
        return tools

    async def handle_call_tool(
        self, 
        name: str, 
        arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle call_tool MCP request.
        
        Args:
            name: Tool name to execute
            arguments: Tool arguments including optional api_key and target_host
            
        Returns:
            List of TextContent with execution results
        """
        self.logger.info(f"Handling call_tool request: {name}")
        
        # Extract API key from arguments
        api_key = arguments.get("api_key")
        client_ip = arguments.get("client_ip", "unknown")
        
        # Authenticate request
        auth_status = self.auth_manager.get_http_status_code(api_key)
        self.auth_manager.log_auth_attempt(api_key or "", auth_status == 200, client_ip)
        
        if auth_status == 401:
            error = ErrorResponse(
                error_code="UNAUTHORIZED",
                message="API key is required",
                timestamp=datetime.now()
            )
            return [TextContent(
                type="text",
                text=json.dumps(error.to_dict(), indent=2)
            )]
        
        if auth_status == 403:
            error = ErrorResponse(
                error_code="FORBIDDEN",
                message="Invalid API key",
                timestamp=datetime.now()
            )
            return [TextContent(
                type="text",
                text=json.dumps(error.to_dict(), indent=2)
            )]

        # Extract command name (remove "cassandra_" prefix)
        if name.startswith("cassandra_"):
            command_name = name[len("cassandra_"):]
        else:
            error = ErrorResponse(
                error_code="INVALID_TOOL",
                message=f"Unknown tool: {name}",
                timestamp=datetime.now()
            )
            return [TextContent(
                type="text",
                text=json.dumps(error.to_dict(), indent=2)
            )]
        
        # Remove api_key and client_ip from arguments before passing to command
        command_args = {k: v for k, v in arguments.items() 
                       if k not in ["api_key", "client_ip"]}
        
        try:
            # Execute command through registry
            result = await self.command_registry.execute_command(
                command_name, 
                command_args
            )
            
            # Format response
            response = result.to_dict()
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            self.logger.error(f"Error executing tool {name}: {e}", exc_info=True)
            error = ErrorResponse(
                error_code="EXECUTION_ERROR",
                message=f"Error executing command: {str(e)}",
                timestamp=datetime.now()
            )
            return [TextContent(
                type="text",
                text=json.dumps(error.to_dict(), indent=2)
            )]

    async def run(self) -> None:
        """Run the MCP server with stdio transport.
        
        This method starts the server and handles MCP protocol communication
        via standard input/output (stdio).
        """
        self.logger.info("Starting Cassandra MCP Server")
        
        async with stdio_server() as (read_stream, write_stream):
            self.logger.info("MCP Server running on stdio transport")
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
    
    def get_tool_count(self) -> int:
        """Get the number of registered tools.
        
        Returns:
            Number of tools
        """
        return len(self._tools)
    
    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names.
        
        Returns:
            List of tool names
        """
        return [tool.name for tool in self._tools]
