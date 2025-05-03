#!/usr/bin/env python3
"""
Raspberry Pi MCP Server Starter

This script connects to a Raspberry Pi via SSH and starts the MCP server.
"""

import os
import sys
import time
import asyncio
import logging
import argparse
import subprocess
from typing import Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("RPiServerStarter")

class RPiServerStarter:
    """
    A specialized runner that manages the MCP server on a Raspberry Pi.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the RPi Server Starter.
        """
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.ssh_username = config.get('ssh_username', 'pi')
        self.ssh_password = config.get('ssh_password', None)
        self.ssh_key_path = config.get('ssh_key_path', None)
        self.server_path = config.get('server_path', '~/mcp')
        self.simulation = config.get('simulation', False)
        self.verbose = config.get('verbose', False)
        self.server_running = False
        
        # Set up logging
        if self.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    
    async def initialize(self) -> bool:
        """
        Initialize the RPi Server Starter.
        """
        try:
            logger.info(f"Initializing RPi Server Starter for {self.host}:{self.port}")
            
            # Check SSH connection
            if not await self._check_ssh_connection():
                logger.error(f"Failed to establish SSH connection to {self.host}")
                return False
            
            logger.info(f"Successfully connected to {self.host} via SSH")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RPi Server Starter: {e}")
            return False
    
    async def start_server(self) -> bool:
        """
        Start the MCP server on the Raspberry Pi.
        """
        try:
            logger.info(f"Starting MCP server on {self.host}:{self.port}")
            
            # Check if the server is already running
            is_running, pid = await self._check_server_running()
            
            if is_running:
                logger.info(f"MCP server is already running on {self.host}:{self.port} (PID: {pid})")
                self.server_running = True
                return True
            
            # Start the server
            if not await self._start_server():
                logger.error(f"Failed to start MCP server on {self.host}:{self.port}")
                return False
            
            # Wait for the server to start
            logger.info("Waiting for server to start...")
            for _ in range(10):  # Try for 10 seconds
                is_running, pid = await self._check_server_running()
                if is_running:
                    logger.info(f"MCP server started successfully on {self.host}:{self.port} (PID: {pid})")
                    self.server_running = True
                    
                    # Verify the server is listening on the correct port
                    if await self._verify_server_port():
                        logger.info(f"Verified server is listening on port {self.port}")
                        return True
                    else:
                        logger.error(f"Server is running but not listening on port {self.port}")
                        return False
                
                await asyncio.sleep(1)
            
            logger.error(f"Timed out waiting for MCP server to start on {self.host}:{self.port}")
            return False
            
        except Exception as e:
            logger.error(f"Error starting MCP server: {e}")
            return False
    
    async def _check_ssh_connection(self) -> bool:
        """
        Check if we can connect to the Raspberry Pi via SSH.
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add a simple command to test the connection
            test_cmd = "echo 'SSH connection successful'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{test_cmd}'"
            
            logger.debug(f"Testing SSH connection with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"SSH connection failed: {stderr.decode()}")
                return False
            
            output = stdout.decode().strip()
            if "SSH connection successful" in output:
                return True
            else:
                logger.error(f"Unexpected SSH test output: {output}")
                return False
            
        except Exception as e:
            logger.error(f"Error checking SSH connection: {e}")
            return False
    
    async def _check_server_running(self) -> Tuple[bool, Optional[int]]:
        """
        Check if the MCP server is running on the Raspberry Pi.
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the command to check if the server is running
            check_cmd = f"pgrep -f 'python.*unitmcp.server.server_main.*--port {self.port}'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{check_cmd}'"
            
            logger.debug(f"Checking if server is running with command: {full_cmd}")
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
                    logger.warning(f"Failed to parse PID: {pid_str}")
                    return True, None
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking if server is running: {e}")
            return False, None
    
    async def _start_server(self) -> bool:
        """
        Start the MCP server on the Raspberry Pi.
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # First, check if Python and unitmcp are available on the Raspberry Pi
            check_python_cmd = "python --version && python -c \"import sys; print(sys.path)\""
            full_check_cmd = f"{ssh_cmd} '{check_python_cmd}'"
            
            logger.info(f"Checking Python environment: {full_check_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            logger.info(f"Python environment: {stdout.decode()}")
            if stderr:
                logger.warning(f"Python environment stderr: {stderr.decode()}")
            
            # Check if unitmcp module is available
            check_unitmcp_cmd = "python -c \"try: import unitmcp; print('unitmcp found at', unitmcp.__file__); except ImportError as e: print('Error importing unitmcp:', e)\""
            full_check_unitmcp_cmd = f"{ssh_cmd} '{check_unitmcp_cmd}'"
            
            logger.info(f"Checking unitmcp module: {full_check_unitmcp_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_check_unitmcp_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            logger.info(f"unitmcp check: {stdout.decode()}")
            if stderr:
                logger.warning(f"unitmcp check stderr: {stderr.decode()}")
            
            # Check if the server directory exists
            check_dir_cmd = f"ls -la {self.server_path}"
            full_check_dir_cmd = f"{ssh_cmd} '{check_dir_cmd}'"
            
            logger.info(f"Checking server directory: {full_check_dir_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_check_dir_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            logger.info(f"Server directory: {stdout.decode()}")
            if stderr:
                logger.warning(f"Server directory stderr: {stderr.decode()}")
            
            # Check if the server module exists
            check_server_module_cmd = f"ls -la {self.server_path}/src/unitmcp/server"
            full_check_server_module_cmd = f"{ssh_cmd} '{check_server_module_cmd}'"
            
            logger.info(f"Checking server module: {full_check_server_module_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_check_server_module_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            logger.info(f"Server module: {stdout.decode()}")
            if stderr:
                logger.warning(f"Server module stderr: {stderr.decode()}")
            
            # Add the command to start the server
            server_cmd = f"cd {self.server_path} && python -m src.unitmcp.server.server_main --host 0.0.0.0 --port {self.port}"
            
            if self.simulation:
                server_cmd += " --simulation"
                
            if self.verbose:
                server_cmd += " --verbose"
            
            # Start the server in the background and redirect output to a log file
            log_file = f"~/mcp_server_{self.port}.log"
            server_cmd = f"nohup {server_cmd} > {log_file} 2>&1 &"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{server_cmd}'"
            
            logger.info(f"Starting server with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to start server: {stderr.decode()}")
                return False
            
            # Wait a moment for the server to start
            await asyncio.sleep(2)
            
            # Check the log file to see if there are any errors
            check_log_cmd = f"cat {log_file}"
            full_check_log_cmd = f"{ssh_cmd} '{check_log_cmd}'"
            
            logger.info(f"Checking server log: {full_check_log_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_check_log_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            log_content = stdout.decode()
            
            if log_content:
                logger.info(f"Server log content: {log_content}")
            else:
                logger.warning("Server log is empty")
            
            if stderr:
                logger.warning(f"Server log stderr: {stderr.decode()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    async def _verify_server_port(self) -> bool:
        """
        Verify that the server is listening on the correct port.
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the command to check if the port is open
            check_cmd = f"netstat -tuln | grep ':{self.port}'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{check_cmd}'"
            
            logger.debug(f"Checking if port {self.port} is open with command: {full_cmd}")
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
            logger.error(f"Error verifying server port: {e}")
            return False
    
    def _build_ssh_command(self) -> str:
        """
        Build the SSH command to connect to the Raspberry Pi.
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
    parser.add_argument("--host", default="192.168.188.154", help="The IP address of the Raspberry Pi")
    parser.add_argument("--port", type=int, default=8080, help="The port to run the MCP server on")
    parser.add_argument("--ssh-username", default="pi", help="SSH username for the Raspberry Pi")
    parser.add_argument("--ssh-password", help="SSH password (optional)")
    parser.add_argument("--ssh-key-path", help="Path to the SSH private key file (optional)")
    parser.add_argument("--server-path", default="~/mcp", help="Path to the MCP server on the Raspberry Pi")
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
        logger.info("Stopping script")

if __name__ == "__main__":
    asyncio.run(main())
