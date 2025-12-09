#!/usr/bin/env python3
"""
Basic Usage Example for Cassandra MCP Server

This example demonstrates:
- Connecting to the MCP server
- Checking cluster status
- Getting node information
- Basic error handling
"""

import json
import subprocess
import sys
import os


def send_mcp_request(server_process, request):
    """Send a request to the MCP server and get response."""
    # Send request
    request_json = json.dumps(request) + "\n"
    server_process.stdin.write(request_json.encode())
    server_process.stdin.flush()
    
    # Read response
    response_line = server_process.stdout.readline().decode()
    return json.loads(response_line)


def check_cluster_status(server_process, api_key):
    """Check the status of the Cassandra cluster."""
    print("=" * 60)
    print("Checking Cluster Status")
    print("=" * 60)
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "cassandra_status",
            "arguments": {
                "api_key": api_key
            }
        }
    }
    
    response = send_mcp_request(server_process, request)
    
    if "result" in response:
        status_output = response["result"]["content"][0]["text"]
        print("\nCluster Status:")
        print(status_output)
        return True
    else:
        print(f"\nError: {response['error']['message']}")
        return False


def get_node_info(server_process, api_key, target_host=None):
    """Get detailed information about a node."""
    print("\n" + "=" * 60)
    print(f"Getting Node Information{' for ' + target_host if target_host else ''}")
    print("=" * 60)
    
    arguments = {"api_key": api_key}
    if target_host:
        arguments["target_host"] = target_host
    
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "cassandra_info",
            "arguments": arguments
        }
    }
    
    response = send_mcp_request(server_process, request)
    
    if "result" in response:
        info_output = response["result"]["content"][0]["text"]
        print("\nNode Information:")
        print(info_output)
        return True
    else:
        print(f"\nError: {response['error']['message']}")
        return False


def get_ring_info(server_process, api_key):
    """Get token ring information."""
    print("\n" + "=" * 60)
    print("Getting Ring Information")
    print("=" * 60)
    
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "cassandra_ring",
            "arguments": {
                "api_key": api_key
            }
        }
    }
    
    response = send_mcp_request(server_process, request)
    
    if "result" in response:
        ring_output = response["result"]["content"][0]["text"]
        print("\nRing Information:")
        print(ring_output)
        return True
    else:
        print(f"\nError: {response['error']['message']}")
        return False


def main():
    """Main function to demonstrate basic usage."""
    # Get API key from environment or use default
    api_key = os.getenv("CASSANDRA_MCP_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        print("Warning: Using default API key. Set CASSANDRA_MCP_API_KEY environment variable.")
    
    # Get server path
    server_path = os.getenv("CASSANDRA_MCP_SERVER_PATH", "../src/main.py")
    
    print("Starting Cassandra MCP Server...")
    print(f"Server path: {server_path}")
    print(f"API key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
    print()
    
    try:
        # Start the MCP server
        server_process = subprocess.Popen(
            ["python", "-m", "src.main"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Wait for server to initialize
        import time
        time.sleep(2)
        
        # Check cluster status
        if not check_cluster_status(server_process, api_key):
            print("\nFailed to get cluster status. Check your configuration.")
            return 1
        
        # Get node information
        if not get_node_info(server_process, api_key):
            print("\nFailed to get node information.")
            return 1
        
        # Get ring information
        if not get_ring_info(server_process, api_key):
            print("\nFailed to get ring information.")
            return 1
        
        print("\n" + "=" * 60)
        print("Basic Usage Example Completed Successfully!")
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
        if 'server_process' in locals():
            server_process.terminate()
            server_process.wait(timeout=5)


if __name__ == "__main__":
    sys.exit(main())
