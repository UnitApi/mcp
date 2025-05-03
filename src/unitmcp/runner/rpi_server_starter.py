"""
Raspberry Pi MCP Server Starter

This module provides a specialized runner that can SSH into a Raspberry Pi,
check if the MCP server is running, and start it if needed.
"""

import os
import sys
import time
import asyncio
import logging
import argparse
import subprocess
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class RPiServerStarter:
    """
    A specialized runner that manages the MCP server on a Raspberry Pi.
    
    This class can:
    1. SSH into a Raspberry Pi
    2. Check if the MCP server is running
    3. Start the MCP server if it's not running
    4. Verify the server is listening on the correct port
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the RPi Server Starter.
        
        Args:
            config: Configuration dictionary with the following keys:
                - host: The IP address of the Raspberry Pi
                - port: The port to run the MCP server on
                - ssh_username: SSH username for the Raspberry Pi
                - ssh_password: SSH password (optional, use ssh_key_path instead if possible)
                - ssh_key_path: Path to the SSH private key file (optional)
                - server_path: Path to the MCP server on the Raspberry Pi (default: ~/UnitApi/mcp)
                - simulation: Whether to run in simulation mode (default: False)
                - verbose: Whether to enable verbose logging (default: False)
        """
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.ssh_username = config.get('ssh_username', 'pi')
        self.ssh_password = config.get('ssh_password', None)
        self.ssh_key_path = config.get('ssh_key_path', None)
        self.server_path = config.get('server_path', '~/UnitApi/mcp')
        self.simulation = config.get('simulation', False)
        self.verbose = config.get('verbose', False)
        self.server_running = False
        self.logger = logging.getLogger("RPiServerStarter")
        
        # Set up logging
        if self.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    
    async def initialize(self) -> bool:
        """
        Initialize the RPi Server Starter.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing RPi Server Starter for {self.host}:{self.port}")
            
            # Check SSH connection
            if not await self._check_ssh_connection():
                self.logger.error(f"Failed to establish SSH connection to {self.host}")
                return False
            
            self.logger.info(f"Successfully connected to {self.host} via SSH")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing RPi Server Starter: {e}")
            return False
    
    async def start_server(self) -> bool:
        """
        Start the MCP server on the Raspberry Pi.
        
        This method will:
        1. Check if the server is already running
        2. Start the server if it's not running
        3. Verify the server is listening on the correct port
        
        Returns:
            True if the server was started successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting MCP server on {self.host}:{self.port}")
            
            # Check if the server is already running
            is_running, pid = await self._check_server_running()
            
            if is_running:
                self.logger.info(f"MCP server is already running on {self.host}:{self.port} (PID: {pid})")
                self.server_running = True
                return True
            
            # Start the server
            if not await self._start_server():
                self.logger.error(f"Failed to start MCP server on {self.host}:{self.port}")
                return False
            
            # Wait for the server to start
            self.logger.info("Waiting for server to start...")
            for _ in range(10):  # Try for 10 seconds
                is_running, pid = await self._check_server_running()
                if is_running:
                    self.logger.info(f"MCP server started successfully on {self.host}:{self.port} (PID: {pid})")
                    self.server_running = True
                    
                    # Verify the server is listening on the correct port
                    if await self._verify_server_port():
                        self.logger.info(f"Verified server is listening on port {self.port}")
                        return True
                    else:
                        self.logger.error(f"Server is running but not listening on port {self.port}")
                        return False
                
                await asyncio.sleep(1)
            
            self.logger.error(f"Timed out waiting for MCP server to start on {self.host}:{self.port}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error starting MCP server: {e}")
            return False
    
    async def stop_server(self) -> bool:
        """
        Stop the MCP server on the Raspberry Pi.
        
        Returns:
            True if the server was stopped successfully, False otherwise
        """
        try:
            self.logger.info(f"Stopping MCP server on {self.host}:{self.port}")
            
            # Check if the server is running
            is_running, pid = await self._check_server_running()
            
            if not is_running:
                self.logger.info(f"MCP server is not running on {self.host}:{self.port}")
                self.server_running = False
                return True
            
            # Stop the server
            if not await self._stop_server(pid):
                self.logger.error(f"Failed to stop MCP server on {self.host}:{self.port}")
                return False
            
            self.logger.info(f"MCP server stopped successfully on {self.host}:{self.port}")
            self.server_running = False
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping MCP server: {e}")
            return False
    
    async def _check_ssh_connection(self) -> bool:
        """
        Check if we can connect to the Raspberry Pi via SSH.
        
        Returns:
            True if the connection was successful, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add a simple command to test the connection
            test_cmd = "echo 'SSH connection successful'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{test_cmd}'"
            
            self.logger.debug(f"Testing SSH connection with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"SSH connection failed: {stderr.decode()}")
                return False
            
            output = stdout.decode().strip()
            if "SSH connection successful" in output:
                return True
            else:
                self.logger.error(f"Unexpected SSH test output: {output}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error checking SSH connection: {e}")
            return False
    
    async def _check_server_running(self) -> Tuple[bool, Optional[int]]:
        """
        Check if the MCP server is running on the Raspberry Pi.
        
        Returns:
            A tuple (is_running, pid) where:
                - is_running: True if the server is running, False otherwise
                - pid: The process ID of the server if it's running, None otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the command to check if the server is running
            check_cmd = f"pgrep -f 'python.*unitmcp.server.server_main.*--port {self.port}'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{check_cmd}'"
            
            self.logger.debug(f"Checking if server is running with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # If the command returns a non-zero exit code, the server is not running
            if process.returncode != 0:
                return False, None
            
            # Get the PID from the output
            pid_str = stdout.decode().strip()
            if pid_str:
                try:
                    pid = int(pid_str)
                    return True, pid
                except ValueError:
                    self.logger.warning(f"Failed to parse PID: {pid_str}")
                    return True, None
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"Error checking if server is running: {e}")
            return False, None
    
    async def _start_server(self) -> bool:
        """
        Start the MCP server on the Raspberry Pi.
        
        Returns:
            True if the server was started successfully, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the command to start the server
            server_cmd = f"cd {self.server_path} && python -m unitmcp.server.server_main --host 0.0.0.0 --port {self.port}"
            
            if self.simulation:
                server_cmd += " --simulation"
                
            if self.verbose:
                server_cmd += " --verbose"
            
            # Start the server in the background and redirect output to a log file
            log_file = f"~/mcp_server_{self.port}.log"
            server_cmd = f"nohup {server_cmd} > {log_file} 2>&1 &"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{server_cmd}'"
            
            self.logger.info(f"Starting server with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Failed to start server: {stderr.decode()}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            return False
    
    async def _stop_server(self, pid: Optional[int] = None) -> bool:
        """
        Stop the MCP server on the Raspberry Pi.
        
        Args:
            pid: The process ID of the server to stop (optional)
            
        Returns:
            True if the server was stopped successfully, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the command to stop the server
            if pid:
                stop_cmd = f"kill {pid}"
            else:
                stop_cmd = f"pkill -f 'python.*unitmcp.server.server_main.*--port {self.port}'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{stop_cmd}'"
            
            self.logger.info(f"Stopping server with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # pkill might return non-zero if no process is found, which is fine
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
            return False
    
    async def _verify_server_port(self) -> bool:
        """
        Verify that the server is listening on the correct port.
        
        Returns:
            True if the server is listening on the correct port, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the command to check if the port is open
            check_cmd = f"netstat -tuln | grep ':{self.port}'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{check_cmd}'"
            
            self.logger.debug(f"Checking if port {self.port} is open with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # If the command returns a non-zero exit code, the port is not open
            if process.returncode != 0:
                return False
            
            # Check if the port is in the output
            output = stdout.decode().strip()
            if f":{self.port}" in output:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying server port: {e}")
            return False
    
    def _build_ssh_command(self) -> str:
        """
        Build the SSH command to connect to the Raspberry Pi.
        
        Returns:
            The SSH command string
        """
        ssh_cmd = f"ssh"
        
        # Add options
        ssh_cmd += f" -o StrictHostKeyChecking=no -o ConnectTimeout=10"
        
        # Add key file if provided
        if self.ssh_key_path:
            ssh_cmd += f" -i {self.ssh_key_path}"
        
        # Add username and host
        ssh_cmd += f" {self.ssh_username}@{self.host}"
        
        return ssh_cmd

async def main():
    """
    Main entry point for the RPi Server Starter.
    """
    parser = argparse.ArgumentParser(description="Start the MCP server on a Raspberry Pi")
    parser.add_argument("--host", required=True, help="The IP address of the Raspberry Pi")
    parser.add_argument("--port", type=int, default=8080, help="The port to run the MCP server on")
    parser.add_argument("--ssh-username", default="pi", help="SSH username for the Raspberry Pi")
    parser.add_argument("--ssh-password", help="SSH password (optional)")
    parser.add_argument("--ssh-key-path", help="Path to the SSH private key file (optional)")
    parser.add_argument("--server-path", default="~/UnitApi/mcp", help="Path to the MCP server on the Raspberry Pi")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Create the config dictionary
    config = {
        "host": args.host,
        "port": args.port,
        "ssh_username": args.ssh_username,
        "ssh_password": args.ssh_password,
        "ssh_key_path": args.ssh_key_path,
        "server_path": args.server_path,
        "simulation": args.simulation,
        "verbose": args.verbose
    }
    
    # Create the RPi Server Starter
    starter = RPiServerStarter(config)
    
    # Initialize
    if not await starter.initialize():
        logger.error("Failed to initialize RPi Server Starter")
        sys.exit(1)
    
    # Start the server
    if not await starter.start_server():
        logger.error("Failed to start MCP server")
        sys.exit(1)
    
    logger.info(f"MCP server started successfully on {args.host}:{args.port}")
    
    # Keep the script running to maintain the SSH connection
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping MCP server...")
        await starter.stop_server()
        logger.info("MCP server stopped")

if __name__ == "__main__":
    asyncio.run(main())
