"""NodeTool executor implementation for executing Cassandra nodetool commands."""

import asyncio
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from src.models import CommandResult
from src.interfaces import INodeToolExecutor, IConfigurationManager
from src.logging_config import get_logger


class NodeToolExecutor(INodeToolExecutor):
    """Executor for nodetool commands with error handling and timeout support."""
    
    def __init__(
        self, 
        config_manager: IConfigurationManager,
        timeout: int = 300  # 5 minutes default timeout
    ):
        """Initialize NodeTool executor.
        
        Args:
            config_manager: Configuration manager instance
            timeout: Command execution timeout in seconds
        """
        self.config_manager = config_manager
        self.timeout = timeout
        self.logger = get_logger("nodetool")
    
    async def execute_command(
        self, 
        command: str, 
        target_host: Optional[str] = None
    ) -> CommandResult:
        """Execute a nodetool command with timeout and error handling.
        
        Args:
            command: The nodetool command to execute (e.g., "status", "ring")
            target_host: Optional target host IP address
            
        Returns:
            CommandResult containing execution details
        """
        start_time = time.time()
        timestamp = datetime.now()
        
        # Validate target host IP format if provided
        if target_host:
            if not self._validate_ip_format(target_host):
                error_msg = f"Invalid IP format: {target_host}"
                self.logger.error(error_msg)
                return CommandResult(
                    success=False,
                    command=command,
                    stdout="",
                    stderr=error_msg,
                    execution_time=time.time() - start_time,
                    timestamp=timestamp,
                    target_host=target_host
                )
        
        # Build the full command
        cmd_parts = self.build_command(command, [], target_host)
        cmd_string = " ".join(cmd_parts)
        
        self.logger.info(
            f"Executing nodetool command: {cmd_string}" + 
            (f" on host {target_host}" if target_host else "")
        )
        
        try:
            # Execute command with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_environment()
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                    await process.wait()
                except Exception as kill_error:
                    self.logger.error(f"Error killing timed-out process: {kill_error}")
                
                error_msg = f"Command timed out after {self.timeout} seconds"
                self.logger.error(error_msg)
                
                execution_time = time.time() - start_time
                return CommandResult(
                    success=False,
                    command=command,
                    stdout="",
                    stderr=error_msg,
                    execution_time=execution_time,
                    timestamp=timestamp,
                    target_host=target_host
                )
            
            execution_time = time.time() - start_time
            success = process.returncode == 0
            
            # Log execution result
            if success:
                self.logger.info(
                    f"Command '{command}' completed successfully in {execution_time:.2f}s"
                )
            else:
                self.logger.error(
                    f"Command '{command}' failed with return code {process.returncode}: {stderr}"
                )
            
            result = CommandResult(
                success=success,
                command=command,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                timestamp=timestamp,
                target_host=target_host
            )
            
            # Log command execution details
            self._log_command_execution(result)
            
            return result
            
        except FileNotFoundError as e:
            error_msg = f"nodetool executable not found: {e}"
            self.logger.error(error_msg)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=error_msg,
                execution_time=execution_time,
                timestamp=timestamp,
                target_host=target_host
            )
            
        except Exception as e:
            error_msg = f"Unexpected error executing command: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=error_msg,
                execution_time=execution_time,
                timestamp=timestamp,
                target_host=target_host
            )
    
    def build_command(
        self, 
        base_command: str, 
        args: List[str], 
        host: Optional[str]
    ) -> List[str]:
        """Build a complete nodetool command with arguments and host option.
        
        Args:
            base_command: The base nodetool command (e.g., "status", "ring")
            args: Additional command arguments
            host: Optional target host IP
            
        Returns:
            List of command components for subprocess execution
        """
        cassandra_bin_path = self.config_manager.get_cassandra_bin_path()
        nodetool_path = str(Path(cassandra_bin_path) / "nodetool")
        
        # Start with nodetool executable
        cmd_parts = [nodetool_path]
        
        # Add host option if specified
        if host:
            cmd_parts.extend(["-h", host])
        
        # Add the base command
        cmd_parts.append(base_command)
        
        # Add any additional arguments
        cmd_parts.extend(args)
        
        return cmd_parts
    
    def parse_output(self, command: str, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse command output into structured format.
        
        Args:
            command: The executed command
            stdout: Standard output
            stderr: Standard error
            
        Returns:
            Parsed output as dictionary
        """
        parsed = {
            "command": command,
            "raw_output": stdout,
            "error_output": stderr
        }
        
        # Command-specific parsing
        if command == "status":
            parsed["parsed_data"] = self._parse_status_output(stdout)
        elif command == "ring":
            parsed["parsed_data"] = self._parse_ring_output(stdout)
        elif command == "info":
            parsed["parsed_data"] = self._parse_info_output(stdout)
        elif command == "netstats":
            parsed["parsed_data"] = self._parse_netstats_output(stdout)
        else:
            # For other commands, just return the raw output
            parsed["parsed_data"] = {"output": stdout.strip()}
        
        return parsed
    
    def _validate_ip_format(self, ip: str) -> bool:
        """Validate IP address format (IPv4 or IPv6).
        
        Args:
            ip: IP address string to validate
            
        Returns:
            True if valid IP format, False otherwise
        """
        # IPv4 pattern
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # IPv6 pattern (simplified)
        ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
        
        if re.match(ipv4_pattern, ip):
            # Validate IPv4 octets are in range 0-255
            octets = ip.split('.')
            return all(0 <= int(octet) <= 255 for octet in octets)
        elif re.match(ipv6_pattern, ip):
            return True
        
        return False
    
    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for command execution.
        
        Returns:
            Dictionary of environment variables
        """
        import os
        env = os.environ.copy()
        
        # Set JAVA_HOME from configuration
        java_home = self.config_manager.get_java_home()
        env['JAVA_HOME'] = java_home
        
        # Add Java bin to PATH
        java_bin = str(Path(java_home) / "bin")
        if 'PATH' in env:
            env['PATH'] = f"{java_bin}:{env['PATH']}"
        else:
            env['PATH'] = java_bin
        
        return env
    
    def _log_command_execution(self, result: CommandResult) -> None:
        """Log detailed command execution information.
        
        Args:
            result: CommandResult to log
        """
        log_data = {
            "command": result.command,
            "target_host": result.target_host,
            "execution_time": f"{result.execution_time:.2f}s",
            "timestamp": result.timestamp.isoformat(),
            "success": result.success
        }
        
        if result.success:
            self.logger.info(f"Command execution logged: {log_data}")
        else:
            log_data["error"] = result.stderr
            self.logger.error(f"Command execution failed: {log_data}")
    
    def _parse_status_output(self, output: str) -> Dict[str, Any]:
        """Parse nodetool status output.
        
        Args:
            output: Raw status output
            
        Returns:
            Parsed status data
        """
        lines = output.strip().split('\n')
        nodes = []
        datacenter = None
        
        for line in lines:
            line = line.strip()
            
            # Detect datacenter
            if line.startswith('Datacenter:'):
                datacenter = line.split(':', 1)[1].strip()
                continue
            
            # Parse node lines (start with U, D, N, etc.)
            if line and line[0] in ['U', 'D', 'N']:
                parts = line.split()
                if len(parts) >= 6:
                    nodes.append({
                        "status": parts[0][0],  # U/D
                        "state": parts[0][1] if len(parts[0]) > 1 else "",  # N/L/J/M
                        "address": parts[1],
                        "load": parts[2],
                        "tokens": parts[3],
                        "owns": parts[4] if len(parts) > 4 else "",
                        "host_id": parts[5] if len(parts) > 5 else "",
                        "rack": parts[6] if len(parts) > 6 else "",
                        "datacenter": datacenter
                    })
        
        return {
            "nodes": nodes,
            "total_nodes": len(nodes)
        }
    
    def _parse_ring_output(self, output: str) -> Dict[str, Any]:
        """Parse nodetool ring output.
        
        Args:
            output: Raw ring output
            
        Returns:
            Parsed ring data
        """
        lines = output.strip().split('\n')
        tokens = []
        
        for line in lines:
            line = line.strip()
            # Skip header and empty lines
            if not line or line.startswith('Datacenter:') or line.startswith('Address'):
                continue
            
            parts = line.split()
            if len(parts) >= 6:
                tokens.append({
                    "address": parts[0],
                    "rack": parts[1],
                    "status": parts[2],
                    "state": parts[3],
                    "load": parts[4],
                    "owns": parts[5],
                    "token": parts[6] if len(parts) > 6 else ""
                })
        
        return {
            "tokens": tokens,
            "total_tokens": len(tokens)
        }
    
    def _parse_info_output(self, output: str) -> Dict[str, Any]:
        """Parse nodetool info output.
        
        Args:
            output: Raw info output
            
        Returns:
            Parsed info data
        """
        lines = output.strip().split('\n')
        info = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info
    
    def _parse_netstats_output(self, output: str) -> Dict[str, Any]:
        """Parse nodetool netstats output.
        
        Args:
            output: Raw netstats output
            
        Returns:
            Parsed netstats data
        """
        # For netstats, we'll keep it simple and return sections
        sections = {}
        current_section = None
        section_content = []
        
        for line in output.strip().split('\n'):
            if line and not line.startswith(' '):
                # New section
                if current_section:
                    sections[current_section] = '\n'.join(section_content)
                current_section = line.strip()
                section_content = []
            else:
                section_content.append(line)
        
        # Add last section
        if current_section:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
