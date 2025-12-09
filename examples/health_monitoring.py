#!/usr/bin/env python3
"""
Health Monitoring Example for Cassandra MCP Server

This example demonstrates:
- Continuous health monitoring
- Node status tracking
- Alert generation
- Health metrics collection
"""

import json
import subprocess
import sys
import os
import time
from datetime import datetime
from collections import defaultdict


def send_mcp_request(server_process, request):
    """Send a request to the MCP server and get response."""
    request_json = json.dumps(request) + "\n"
    server_process.stdin.write(request_json.encode())
    server_process.stdin.flush()
    
    response_line = server_process.stdout.readline().decode()
    return json.loads(response_line)


def parse_cluster_status(status_output):
    """Parse cluster status output to extract node information."""
    nodes = []
    lines = status_output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('Datacenter') and not line.startswith('Status') and not line.startswith('--') and not line.startswith('|/'):
            parts = line.split()
            if len(parts) >= 6:
                status_state = parts[0]
                address = parts[1]
                load = parts[2] + ' ' + parts[3] if len(parts) > 3 else parts[2]
                
                node_info = {
                    'status': status_state[0],  # U=Up, D=Down
                    'state': status_state[1] if len(status_state) > 1 else 'N',  # N=Normal, L=Leaving, J=Joining, M=Moving
                    'address': address,
                    'load': load,
                    'is_up': status_state[0] == 'U',
                    'is_normal': status_state[1] == 'N' if len(status_state) > 1 else True
                }
                nodes.append(node_info)
    
    return nodes


def check_cluster_health(server_process, api_key):
    """Check cluster health and return status."""
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
        status_output = response["result"]["content"][0]["text"]
        nodes = parse_cluster_status(status_output)
        
        total_nodes = len(nodes)
        up_nodes = sum(1 for n in nodes if n['is_up'])
        down_nodes = total_nodes - up_nodes
        
        health_status = {
            'healthy': down_nodes == 0,
            'total_nodes': total_nodes,
            'up_nodes': up_nodes,
            'down_nodes': down_nodes,
            'nodes': nodes,
            'timestamp': datetime.now()
        }
        
        return health_status
    else:
        return {
            'healthy': False,
            'error': response['error']['message'],
            'timestamp': datetime.now()
        }


def display_health_status(health_status):
    """Display health status in a readable format."""
    timestamp = health_status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\n[{timestamp}] Cluster Health Check")
    print("=" * 60)
    
    if 'error' in health_status:
        print(f"✗ Health check failed: {health_status['error']}")
        return
    
    if health_status['healthy']:
        print("✓ Cluster is HEALTHY")
    else:
        print("⚠ Cluster has ISSUES")
    
    print(f"\nNodes: {health_status['up_nodes']}/{health_status['total_nodes']} UP")
    
    if health_status['down_nodes'] > 0:
        print(f"⚠ {health_status['down_nodes']} node(s) DOWN")
    
    # Display node details
    print("\nNode Status:")
    print("-" * 60)
    for node in health_status['nodes']:
        status_icon = "✓" if node['is_up'] else "✗"
        state_text = "Normal" if node['is_normal'] else "Not Normal"
        print(f"{status_icon} {node['address']:<15} | {node['load']:<10} | {state_text}")


def generate_alert(health_status, previous_status):
    """Generate alerts based on health status changes."""
    alerts = []
    
    # Check if cluster health changed
    if previous_status and previous_status['healthy'] != health_status['healthy']:
        if health_status['healthy']:
            alerts.append("✓ ALERT: Cluster recovered to healthy state")
        else:
            alerts.append("⚠ ALERT: Cluster health degraded")
    
    # Check for new down nodes
    if previous_status and 'nodes' in health_status and 'nodes' in previous_status:
        current_down = {n['address'] for n in health_status['nodes'] if not n['is_up']}
        previous_down = {n['address'] for n in previous_status['nodes'] if not n['is_up']}
        
        new_down = current_down - previous_down
        recovered = previous_down - current_down
        
        for node in new_down:
            alerts.append(f"⚠ ALERT: Node {node} went DOWN")
        
        for node in recovered:
            alerts.append(f"✓ ALERT: Node {node} recovered")
    
    return alerts


def monitor_health(server_process, api_key, interval=30, duration=None):
    """Continuously monitor cluster health."""
    print("=" * 60)
    print("Cassandra Cluster Health Monitoring")
    print("=" * 60)
    print(f"Check interval: {interval} seconds")
    if duration:
        print(f"Duration: {duration} seconds")
    else:
        print("Duration: Continuous (press Ctrl+C to stop)")
    print()
    
    previous_status = None
    start_time = time.time()
    check_count = 0
    alert_count = 0
    
    try:
        while True:
            # Check if duration exceeded
            if duration and (time.time() - start_time) > duration:
                break
            
            # Perform health check
            health_status = check_cluster_health(server_process, api_key)
            check_count += 1
            
            # Display status
            display_health_status(health_status)
            
            # Generate and display alerts
            alerts = generate_alert(health_status, previous_status)
            if alerts:
                print("\n" + "!" * 60)
                for alert in alerts:
                    print(alert)
                    alert_count += 1
                print("!" * 60)
            
            # Store for next comparison
            previous_status = health_status
            
            # Wait for next check
            print(f"\nNext check in {interval} seconds...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    
    # Summary
    print("\n" + "=" * 60)
    print("Monitoring Summary")
    print("=" * 60)
    print(f"Total checks: {check_count}")
    print(f"Alerts generated: {alert_count}")
    print(f"Duration: {int(time.time() - start_time)} seconds")


def get_node_metrics(server_process, api_key, node_address):
    """Get detailed metrics for a specific node."""
    print(f"\nGetting metrics for node: {node_address}")
    
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
        "method": "tools/call",
        "params": {
            "name": "cassandra_info",
            "arguments": {
                "api_key": api_key,
                "target_host": node_address
            }
        }
    }
    
    response = send_mcp_request(server_process, request)
    
    if "result" in response:
        info_output = response["result"]["content"][0]["text"]
        print(f"\nNode Metrics for {node_address}:")
        print("-" * 60)
        print(info_output)
        return True
    else:
        print(f"✗ Failed to get metrics: {response['error']['message']}")
        return False


def main():
    """Main function for health monitoring."""
    # Configuration
    api_key = os.getenv("CASSANDRA_MCP_API_KEY", "your-api-key-here")
    
    if api_key == "your-api-key-here":
        print("Warning: Using default API key. Set CASSANDRA_MCP_API_KEY environment variable.")
    
    # Monitoring interval (seconds)
    interval = int(os.getenv("MONITOR_INTERVAL", "30"))
    
    # Duration (None for continuous)
    duration = None
    if len(sys.argv) > 1:
        duration = int(sys.argv[1])
    
    print("Cassandra MCP Server - Health Monitoring")
    print("=" * 60)
    print(f"API Key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
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
        
        # Start monitoring
        monitor_health(server_process, api_key, interval, duration)
        
        print("\n" + "=" * 60)
        print("Health Monitoring Completed")
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
