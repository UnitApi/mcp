#!/usr/bin/env python3
"""
Start MCP Server on Raspberry Pi

This script connects to a Raspberry Pi via SSH and starts the MCP server
using the updated repository structure.
"""

import os
import sys
import time
import asyncio
import logging
import argparse
import subprocess
from typing import Dict, Any, Optional, List, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("RPiServerStarter")

class RPiServerStarter:
    """
    A utility class to start the MCP server on a Raspberry Pi.
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
        
    async def start_server(self) -> bool:
        """
        Start the MCP server on the Raspberry Pi.
        
        Returns:
            True if the server was started successfully, False otherwise
        """
        try:
            # Connect to the Raspberry Pi via SSH
            if not await self._check_ssh_connection():
                logger.error(f"Failed to connect to {self.host} via SSH")
                return False
            
            logger.info(f"Successfully connected to {self.host} via SSH")
            
            # Check if the server is already running
            if await self._is_server_running():
                logger.info(f"MCP server is already running on {self.host}:{self.port}")
                self.server_running = True
                return True
            
            # Start the server
            logger.info(f"Starting MCP server on {self.host}:{self.port}")
            if not await self._start_server():
                logger.error(f"Failed to start MCP server on {self.host}:{self.port}")
                return False
            
            # Wait for the server to start
            logger.info("Waiting for server to start...")
            if not await self._wait_for_server():
                logger.error(f"Server did not start within the expected time")
                return False
            
            logger.info(f"MCP server started successfully on {self.host}:{self.port}")
            self.server_running = True
            return True
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    async def stop_server(self) -> bool:
        """
        Stop the MCP server on the Raspberry Pi.
        
        Returns:
            True if the server was stopped successfully, False otherwise
        """
        try:
            # Check if the server is running
            if not await self._is_server_running():
                logger.info(f"MCP server is not running on {self.host}:{self.port}")
                self.server_running = False
                return True
            
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Find the process ID of the server
            find_pid_cmd = f"lsof -i :{self.port} -t"
            full_find_pid_cmd = f"{ssh_cmd} '{find_pid_cmd}'"
            
            logger.info(f"Finding server process ID: {full_find_pid_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_find_pid_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            pid = stdout.decode().strip()
            
            if not pid:
                logger.warning(f"No process found listening on port {self.port}")
                self.server_running = False
                return True
            
            # Kill the process
            kill_cmd = f"kill {pid}"
            full_kill_cmd = f"{ssh_cmd} '{kill_cmd}'"
            
            logger.info(f"Stopping server with command: {full_kill_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_kill_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to stop server: {stderr.decode()}")
                return False
            
            # Wait for the server to stop
            for _ in range(5):
                if not await self._is_server_running():
                    logger.info(f"MCP server stopped successfully on {self.host}:{self.port}")
                    self.server_running = False
                    return True
                
                await asyncio.sleep(1)
            
            logger.error(f"Server did not stop within the expected time")
            return False
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            return False
    
    async def _check_ssh_connection(self) -> bool:
        """
        Check if the SSH connection to the Raspberry Pi is working.
        
        Returns:
            True if the connection is working, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add a simple command to test the connection
            test_cmd = "echo 'SSH connection successful'"
            full_cmd = f"{ssh_cmd} '{test_cmd}'"
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"SSH connection failed: {stderr.decode()}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking SSH connection: {e}")
            return False
    
    async def _is_server_running(self) -> bool:
        """
        Check if the MCP server is running on the Raspberry Pi.
        
        Returns:
            True if the server is running, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add a command to check if the server is running
            check_cmd = f"lsof -i :{self.port}"
            full_cmd = f"{ssh_cmd} '{check_cmd}'"
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Check if the command was successful and if there is any output
            if process.returncode != 0 or not stdout:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if server is running: {e}")
            return False
    
    async def _start_server(self) -> bool:
        """
        Start the MCP server on the Raspberry Pi.
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # First, check if Python and the required modules are available
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
            
            # Check if server_main.py exists
            server_main_path = f"{self.server_path}/src/unitmcp/server/server_main.py"
            check_server_main_cmd = f"test -f {server_main_path} && echo 'File exists' || echo 'File does not exist'"
            full_check_server_main_cmd = f"{ssh_cmd} '{check_server_main_cmd}'"
            
            logger.info(f"Checking if server_main.py exists: {full_check_server_main_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_check_server_main_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode().strip()
            
            if "File exists" in output:
                logger.info(f"server_main.py found at {server_main_path}")
                
                # Check if virtual environment exists
                check_venv_cmd = f"test -d {self.server_path}/venv && echo 'venv exists' || echo 'venv does not exist'"
                full_check_venv_cmd = f"{ssh_cmd} '{check_venv_cmd}'"
                
                logger.info(f"Checking if virtual environment exists: {full_check_venv_cmd}")
                process = await asyncio.create_subprocess_shell(
                    full_check_venv_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                venv_output = stdout.decode().strip()
                
                if "venv does not exist" in venv_output:
                    logger.info("Creating virtual environment and installing dependencies")
                    venv_cmd = f"cd {self.server_path} && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
                    full_venv_cmd = f"{ssh_cmd} '{venv_cmd}'"
                    
                    process = await asyncio.create_subprocess_shell(
                        full_venv_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    if process.returncode != 0:
                        logger.warning(f"Error creating virtual environment: {stderr.decode()}")
                        logger.warning("Will try to start server without virtual environment")
                    else:
                        logger.info("Virtual environment created successfully")
                else:
                    logger.info("Virtual environment already exists")
                
                # Start the server using server_main.py with virtual environment
                server_cmd = f"cd {self.server_path} && source venv/bin/activate && python -m src.unitmcp.server.server_main --host 0.0.0.0 --port {self.port}"
                
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
                    
                    # Check for errors in the log
                    if "Error" in log_content or "Exception" in log_content:
                        logger.warning("Found errors in server log")
                        return False
                else:
                    logger.warning("Server log is empty")
                
                if stderr:
                    logger.warning(f"Server log stderr: {stderr.decode()}")
                
                # Check if the server is running
                if await self._is_server_running():
                    logger.info(f"Server started successfully with server_main.py")
                    return True
                
                logger.warning(f"Server not running after starting with server_main.py")
                return False
            else:
                logger.warning(f"server_main.py not found at {server_main_path}")
                
                # Try to find server files as fallback
                server_files = await self._find_server_files()
                
                if not server_files:
                    logger.error("Could not find server entry points")
                    return False
                
                logger.info(f"Found server entry points: {server_files}")
                
                # Try each server entry point until one works
                for server_file, is_module in server_files:
                    if await self._try_start_server(server_file, is_module):
                        return True
                
                logger.error("All server entry points failed")
                return False
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    async def _find_server_files(self) -> List[Tuple[str, bool]]:
        """
        Find potential server entry points in the repository.
        
        Returns:
            A list of tuples containing (file_path, is_module) for each potential server entry point
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Find potential server files
            find_cmd = f"find {self.server_path} -name '*server*.py' | grep -v test"
            full_find_cmd = f"{ssh_cmd} '{find_cmd}'"
            
            logger.info(f"Finding server files: {full_find_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_find_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            server_files = stdout.decode().strip().split('\n')
            
            # Filter out empty lines
            server_files = [f for f in server_files if f]
            
            # Check if each file contains a main function or is executable
            result = []
            for file_path in server_files:
                # Check if the file contains a main function or if __name__ == "__main__"
                check_main_cmd = f"grep -E 'def main|if __name__ == \"__main__\"' {file_path}"
                full_check_main_cmd = f"{ssh_cmd} '{check_main_cmd}'"
                
                process = await asyncio.create_subprocess_shell(
                    full_check_main_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if stdout:
                    # This file might be a server entry point
                    # Check if it's a module or a script
                    rel_path = file_path.replace(f"{self.server_path}/", "")
                    module_path = rel_path.replace("/", ".").replace(".py", "")
                    
                    result.append((file_path, True))  # As a module
                    result.append((file_path, False))  # As a script
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding server files: {e}")
            return []
    
    async def _try_start_server(self, server_file: str, as_module: bool) -> bool:
        """
        Try to start the server using the given entry point.
        
        Args:
            server_file: The path to the server file
            as_module: Whether to run the file as a module or as a script
            
        Returns:
            True if the server was started successfully, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Prepare the server command
            if as_module:
                # Convert file path to module path
                rel_path = server_file.replace(f"{self.server_path}/", "")
                module_path = rel_path.replace("/", ".").replace(".py", "")
                server_cmd = f"cd {self.server_path} && python -m {module_path} --host 0.0.0.0 --port {self.port}"
            else:
                server_cmd = f"cd {os.path.dirname(server_file)} && python {os.path.basename(server_file)} --host 0.0.0.0 --port {self.port}"
            
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
                
                # Check for errors in the log
                if "Error" in log_content or "Exception" in log_content:
                    logger.warning("Found errors in server log")
                    return False
            else:
                logger.warning("Server log is empty")
            
            if stderr:
                logger.warning(f"Server log stderr: {stderr.decode()}")
            
            # Check if the server is running
            if await self._is_server_running():
                logger.info(f"Server started successfully with {server_file} {'as module' if as_module else 'as script'}")
                return True
            
            logger.warning(f"Server not running after starting with {server_file} {'as module' if as_module else 'as script'}")
            return False
            
        except Exception as e:
            logger.error(f"Error trying to start server: {e}")
            return False
    
    async def _wait_for_server(self, timeout: int = 30) -> bool:
        """
        Wait for the server to start.
        
        Args:
            timeout: The maximum time to wait in seconds
            
        Returns:
            True if the server started within the timeout, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self._is_server_running():
                return True
            
            await asyncio.sleep(1)
        
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
    
    # Create the RPiServerStarter
    starter = RPiServerStarter(config)
    
    # Start the server
    if not await starter.start_server():
        logger.error("Failed to start server")
        sys.exit(1)
    
    logger.info("Server started successfully")

if __name__ == "__main__":
    asyncio.run(main())
