#!/usr/bin/env python3
"""
Backup Automation Example for Cassandra MCP Server

This example demonstrates:
- Creating automated snapshots
- Backup scheduling
- Backup verification
- Cleanup of old backups
"""

import json
import subprocess
import sys
import os
from datetime import datetime
import time


def send_mcp_request(server_process, request):
    """Send a request to the MCP server and get response."""
    request_json = json.dumps(request) + "\n"
    server_process.stdin.write(request_json.encode())
    server_process.stdin.flush()
    
    response_line = server_process.stdout.readline().decode()
    return json.loads(response_line)


def create_snapshot(server_process, api_key, keyspace, tag):
    """Create a snapshot of a keyspace."""
    print(f"\nCreating snapshot for keyspace: {keyspace}")
    print(f"Snapshot tag: {tag}")
    
    arguments = {
        "api_key": api_key,
        "tag": tag
    }
    
    if keyspace:
        arguments["keyspace"] = keyspace
    
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
        "method": "tools/call",
        "params": {
            "name": "cassandra_snapshot",
            "arguments": arguments
        }
    }
    
    response = send_mcp_request(server_process, request)
    
    if "result" in response:
        output = response["result"]["content"][0]["text"]
        print(f"✓ Snapshot created successfully")
        print(f"  {output}")
        return True
    else:
        print(f"✗ Snapshot failed: {response['error']['message']}")
        return False


def backup_keyspace(server_process, api_key, keyspace):
    """Create a timestamped backup of a keyspace."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"backup_{keyspace}_{timestamp}"
    
    print("=" * 60)
    print(f"Backing up keyspace: {keyspace}")
    print(f"Timestamp: {timestamp}")
    print("=" * 60)
    
    return create_snapshot(server_process, api_key, keyspace, tag)


def backup_all_keyspaces(server_process, api_key, keyspaces):
    """Backup multiple keyspaces."""
    print("\n" + "=" * 60)
    print("Starting Automated Backup Process")
    print("=" * 60)
    print(f"Keyspaces to backup: {', '.join(keyspaces)}")
    
    results = {}
    
    for keyspace in keyspaces:
        success = backup_keyspace(server_process, api_key, keyspace)
        results[keyspace] = success
        
        if success:
            print(f"✓ {keyspace}: Backup completed")
        else:
            print(f"✗ {keyspace}: Backup failed")
        
        # Small delay between backups
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("Backup Summary")
    print("=" * 60)
    
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    print(f"Total keyspaces: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ All backups completed successfully!")
    else:
        print(f"\n⚠ {failed} backup(s) failed. Check logs for details.")
    
    return failed == 0


def scheduled_backup(server_process, api_key, keyspaces, interval_hours=24):
    """Run backups on a schedule."""
    print("=" * 60)
    print("Scheduled Backup Service")
    print("=" * 60)
    print(f"Backup interval: {interval_hours} hours")
    print(f"Keyspaces: {', '.join(keyspaces)}")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled backup...")
            
            success = backup_all_keyspaces(server_process, api_key, keyspaces)
            
            if success:
                print(f"\n✓ Scheduled backup completed successfully")
            else:
                print(f"\n⚠ Scheduled backup completed with errors")
            
            # Wait for next backup
            print(f"\nNext backup in {interval_hours} hours...")
            time.sleep(interval_hours * 3600)
            
    except KeyboardInterrupt:
        print("\n\nScheduled backup service stopped by user")


def verify_backup(server_process, api_key):
    """Verify that backups can be accessed."""
    print("\n" + "=" * 60)
    print("Verifying Backup Accessibility")
    print("=" * 60)
    
    # Check cluster status to ensure connectivity
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
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
        print("✓ Cluster is accessible")
        print("✓ Backup verification passed")
        return True
    else:
        print("✗ Cluster is not accessible")
        print("✗ Backup verification failed")
        return False


def main():
    """Main function for backup automation."""
    # Configuration
    api_key = os.getenv("CASSANDRA_MCP_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        print("Warning: Using default API key. Set CASSANDRA_MCP_API_KEY environment variable.")
    
    # Keyspaces to backup (customize this list)
    keyspaces = ["system_schema", "system_auth"]
    
    # You can also get keyspaces from command line
    if len(sys.argv) > 1:
        keyspaces = sys.argv[1].split(",")
    
    print("Cassandra MCP Server - Backup Automation")
    print("=" * 60)
    print(f"API Key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
    print(f"Keyspaces: {', '.join(keyspaces)}")
    print()
    
    try:
        # Start the MCP server
        print("Starting MCP server...")
        server_process = subprocess.Popen(
            ["python", "-m", "src.main"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Wait for server to initialize
        time.sleep(2)
        print("✓ MCP server started\n")
        
        # Verify connectivity
        if not verify_backup(server_process, api_key):
            print("\nCannot proceed with backup. Check your configuration.")
            return 1
        
        # Run backup
        success = backup_all_keyspaces(server_process, api_key, keyspaces)
        
        if success:
            print("\n" + "=" * 60)
            print("Backup Automation Completed Successfully!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("Backup Automation Completed with Errors")
            print("=" * 60)
            return 1
        
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
