#!/usr/bin/env python3
"""
Complete MCP Client Example for Cassandra MCP Server

This example demonstrates:
- Full MCP client implementation
- Proper initialization and lifecycle
- Tool discovery and execution
- Error handling and retries
- Resource cleanup
"""

import json
import subprocess
import sys
import os
import time
from typing import Optional, Dict, Any


class CassandraMCPClient:
    """A complete MCP client for Cassandra MCP Server."""
    
    def __init__(self, api_key: str, server_path: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            api_key: API key for authentication
            server_path: Path to the MCP server (default: auto-detect)
        """
        self.api_key = api_key
        self.server_path = server_path or self._find_server_path()
        self.server_process = None
        self.request_id = 0
        self.initialized = False
        self.available_tools = []
    
    def _find_server_path(self) -> str:
        """Find the MCP server path."""
        # Try environment variable first
        env_path = os.getenv("CASSANDRA_MCP_SERVER_PATH")
        if env_path:
            return env_path
        
        # Try relative path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        return os.path.join(parent_dir, "src", "main.py")
    
    def start(self):
        """Start the MCP server."""
        if self.server_process:
            raise RuntimeError("Server already started")
        
        print("Starting Cassandra MCP Server...")
        
        # Get the directory containing src/main.py
        server_dir = os.path.dirname(os.path.dirname(self.server_path))
        
        self.server_process = subprocess.Popen(
            ["python", "-m", "src.main"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_dir
        )
        
        # Wait for server to initialize
        time.sleep(2)
        print("✓ Server started")
    
    def stop(self):
        """Stop the MCP server."""
        if self.server_process:
            print("\nStopping MCP server...")
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
            self.server_process = None
            print("✓ Server stopped")
    
    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the server.
        
        Args:
            method: The JSON-RPC method name
            params: Optional parameters for the method
            
        Returns:
            The JSON-RPC response
        """
        if not self.server_process:
            raise RuntimeError("Server not started")
        
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.server_process.stdin.write(request_json.encode())
        self.server_process.stdin.flush()
        
        # Read response
        response_line = self.server_process.stdout.readline().decode()
        return json.loads(response_line)
    
    def initialize(self) -> bool:
        """
        Initialize the MCP session.
        
        Returns:
            True if initialization successful
        """
        print("Initializing MCP session...")
        
        response = self._send_request("initialize", {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {
                "name": "cassandra-mcp-client",
                "version": "0.1.0"
            }
        })
        
        if "result" in response:
            self.initialized = True
            print("✓ Session initialized")
            return True
        else:
            print(f"✗ Initialization failed: {response.get('error', {}).get('message', 'Unknown error')}")
            return False
    
    def list_tools(self) -> bool:
        """
        List available tools.
        
        Returns:
            True if successful
        """
        print("\nDiscovering available tools...")
        
        response = self._send_request("tools/list")
        
        if "result" in response:
            self.available_tools = response["result"].get("tools", [])
            print(f"✓ Found {len(self.available_tools)} tools:")
            for tool in self.available_tools:
                print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
            return True
        else:
            print(f"✗ Failed to list tools: {response.get('error', {}).get('message', 'Unknown error')}")
            return False
    
    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call a tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool (api_key will be added automatically)
            
        Returns:
            The tool result or error
        """
        if not self.initialized:
            raise RuntimeError("Session not initialized. Call initialize() first.")
        
        # Add API key to arguments
        args = arguments or {}
        args["api_key"] = self.api_key
        
        response = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": args
        })
        
        return response
    
    def get_cluster_status(self, target_host: Optional[str] = None) -> Optional[str]:
        """
        Get cluster status.
        
        Args:
            target_host: Optional target host IP
            
        Returns:
            Status output or None on error
        """
        args = {}
        if target_host:
            args["target_host"] = target_host
        
        response = self.call_tool("cassandra_status", args)
        
        if "result" in response:
            return response["result"]["content"][0]["text"]
        else:
            print(f"Error: {response['error']['message']}")
            return None
    
    def create_snapshot(self, tag: str, keyspace: Optional[str] = None) -> bool:
        """
        Create a snapshot.
        
        Args:
            tag: Snapshot tag
            keyspace: Optional keyspace to snapshot
            
        Returns:
            True if successful
        """
        args = {"tag": tag}
        if keyspace:
            args["keyspace"] = keyspace
        
        response = self.call_tool("cassandra_snapshot", args)
        
        if "result" in response:
            print(f"✓ Snapshot created: {tag}")
            return True
        else:
            print(f"✗ Snapshot failed: {response['error']['message']}")
            return False
    
    def repair_keyspace(self, keyspace: Optional[str] = None, target_host: Optional[str] = None) -> bool:
        """
        Repair a keyspace.
        
        Args:
            keyspace: Optional keyspace to repair
            target_host: Optional target host IP
            
        Returns:
            True if successful
        """
        args = {}
        if keyspace:
            args["keyspace"] = keyspace
        if target_host:
            args["target_host"] = target_host
        
        response = self.call_tool("cassandra_repair", args)
        
        if "result" in response:
            print(f"✓ Repair completed")
            return True
        else:
            print(f"✗ Repair failed: {response['error']['message']}")
            return False


def demo_basic_operations(client: CassandraMCPClient):
    """Demonstrate basic operations."""
    print("\n" + "=" * 60)
    print("Demo: Basic Operations")
    print("=" * 60)
    
    # Get cluster status
    print("\n1. Getting cluster status...")
    status = client.get_cluster_status()
    if status:
        print(status)
    
    # Get node info
    print("\n2. Getting node information...")
    response = client.call_tool("cassandra_info")
    if "result" in response:
        print(response["result"]["content"][0]["text"])


def demo_maintenance(client: CassandraMCPClient):
    """Demonstrate maintenance operations."""
    print("\n" + "=" * 60)
    print("Demo: Maintenance Operations")
    print("=" * 60)
    
    # Create snapshot
    print("\n1. Creating snapshot...")
    from datetime import datetime
    tag = f"demo_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    client.create_snapshot(tag, keyspace="system_schema")
    
    # Note: Repair can take a long time, so we'll skip it in the demo
    print("\n2. Repair operation (skipped in demo - can take a long time)")


def demo_monitoring(client: CassandraMCPClient):
    """Demonstrate monitoring operations."""
    print("\n" + "=" * 60)
    print("Demo: Monitoring Operations")
    print("=" * 60)
    
    # Get compaction throughput
    print("\n1. Getting compaction throughput...")
    response = client.call_tool("cassandra_getcompactionthroughput")
    if "result" in response:
        print(response["result"]["content"][0]["text"])
    
    # Get concurrent compactors
    print("\n2. Getting concurrent compactors...")
    response = client.call_tool("cassandra_getconcurrentcompactors")
    if "result" in response:
        print(response["result"]["content"][0]["text"])


def main():
    """Main function demonstrating complete MCP client usage."""
    # Configuration
    api_key = os.getenv("CASSANDRA_MCP_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        print("Warning: Using default API key. Set CASSANDRA_MCP_API_KEY environment variable.")
    
    print("Cassandra MCP Client - Complete Example")
    print("=" * 60)
    print(f"API Key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
    print()
    
    # Create client
    client = CassandraMCPClient(api_key)
    
    try:
        # Start server
        client.start()
        
        # Initialize session
        if not client.initialize():
            print("Failed to initialize session")
            return 1
        
        # List available tools
        if not client.list_tools():
            print("Failed to list tools")
            return 1
        
        # Run demos
        demo_basic_operations(client)
        demo_maintenance(client)
        demo_monitoring(client)
        
        print("\n" + "=" * 60)
        print("MCP Client Example Completed Successfully!")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        client.stop()


if __name__ == "__main__":
    sys.exit(main())
