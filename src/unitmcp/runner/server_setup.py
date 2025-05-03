"""
UnitMCP Runner Server Setup

This module provides functionality for setting up and managing the UnitMCP server
in the UnitMCP Runner environment.
"""

import os
import sys
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ServerSetup:
    """
    Server setup for UnitMCP Runner.
    
    This class handles the setup and management of the UnitMCP server
    in the UnitMCP Runner environment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the server setup.
        
        Args:
            config: Configuration dictionary for the server
        """
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8888)
        self.simulation = config.get('simulation', False)
        self.verbose = config.get('verbose', False)
        self.auto_setup = config.get('auto_setup', True)
        self.server_process = None
        self.is_remote = config.get('is_remote', False)
        self.remote_host = config.get('remote_host', None)
        self.remote_user = config.get('remote_user', None)
        self.remote_key = config.get('remote_key', None)
        self.server_running = False
        self.logger = logging.getLogger("ServerSetup")
        
    async def initialize(self) -> bool:
        """
        Initialize the server setup.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing server setup on {self.host}:{self.port}")
            
            # If auto_setup is enabled, prepare the environment
            if self.auto_setup:
                if not await self.prepare_environment():
                    self.logger.error("Failed to prepare server environment")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing server setup: {e}")
            return False
            
    async def prepare_environment(self) -> bool:
        """
        Prepare the server environment.
        
        Returns:
            True if preparation was successful, False otherwise
        """
        try:
            self.logger.info("Preparing server environment")
            
            # If this is a remote server, we need to set up SSH access
            if self.is_remote:
                if not self.remote_host or not self.remote_user:
                    self.logger.error("Remote host and user must be specified for remote server")
                    return False
                    
                # Check SSH connection
                if not await self._check_ssh_connection():
                    self.logger.error("Failed to establish SSH connection to remote server")
                    return False
                    
                # Check if UnitMCP is installed on the remote server
                if not await self._check_remote_unitmcp():
                    self.logger.error("UnitMCP is not installed on the remote server")
                    return False
                    
            # If this is a local server, check if UnitMCP is installed
            else:
                try:
                    import unitmcp
                    self.logger.info(f"Found UnitMCP version {unitmcp.__version__}")
                except ImportError:
                    self.logger.error("UnitMCP is not installed")
                    return False
                    
            # Check if we're running on a Raspberry Pi
            is_rpi = await self._check_if_rpi()
            
            # If we're on a Raspberry Pi, optimize for it
            if is_rpi and self.config.get('optimize_rpi', True):
                await self._optimize_for_rpi()
                
            self.logger.info("Server environment prepared successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error preparing server environment: {e}")
            return False
            
    async def start(self) -> bool:
        """
        Start the UnitMCP server.
        
        Returns:
            True if start was successful, False otherwise
        """
        try:
            self.logger.info(f"Starting UnitMCP server on {self.host}:{self.port}")
            
            # If the server is already running, don't start it again
            if self.server_running:
                self.logger.info("Server is already running")
                return True
                
            # If this is a remote server, start it via SSH
            if self.is_remote:
                return await self._start_remote_server()
                
            # Otherwise, start the server locally
            return await self._start_local_server()
            
        except Exception as e:
            self.logger.error(f"Error starting UnitMCP server: {e}")
            return False
            
    async def stop(self) -> bool:
        """
        Stop the UnitMCP server.
        
        Returns:
            True if stop was successful, False otherwise
        """
        try:
            self.logger.info("Stopping UnitMCP server")
            
            # If the server is not running, don't stop it
            if not self.server_running:
                self.logger.info("Server is not running")
                return True
                
            # If this is a remote server, stop it via SSH
            if self.is_remote:
                return await self._stop_remote_server()
                
            # Otherwise, stop the server locally
            return await self._stop_local_server()
            
        except Exception as e:
            self.logger.error(f"Error stopping UnitMCP server: {e}")
            return False
            
    async def _start_local_server(self) -> bool:
        """
        Start the UnitMCP server locally.
        
        Returns:
            True if start was successful, False otherwise
        """
        try:
            # Import the server module
            from unitmcp.server.server_main import MCPServer
            
            # Create and start the server
            server = MCPServer(
                host=self.host,
                port=self.port,
                simulation=self.simulation,
                verbose=self.verbose
            )
            
            # Start the server in a separate task
            asyncio.create_task(server.start())
            
            self.server_running = True
            self.logger.info(f"UnitMCP server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting local UnitMCP server: {e}")
            return False
            
    async def _stop_local_server(self) -> bool:
        """
        Stop the UnitMCP server locally.
        
        Returns:
            True if stop was successful, False otherwise
        """
        try:
            # If we have a server process, terminate it
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
                
            self.server_running = False
            self.logger.info("UnitMCP server stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping local UnitMCP server: {e}")
            return False
            
    async def _start_remote_server(self) -> bool:
        """
        Start the UnitMCP server on a remote host via SSH.
        
        Returns:
            True if start was successful, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the server start command
            server_cmd = f"cd ~/UnitApi/mcp && python -m unitmcp.server.server_main --host {self.host} --port {self.port}"
            
            if self.simulation:
                server_cmd += " --simulation"
                
            if self.verbose:
                server_cmd += " --verbose"
                
            # Start the server in the background
            full_cmd = f"{ssh_cmd} '{server_cmd} &'"
            
            # Execute the command
            self.logger.info(f"Starting remote server with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Failed to start remote server: {stderr.decode()}")
                return False
                
            self.server_running = True
            self.logger.info(f"UnitMCP server started on {self.remote_host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting remote UnitMCP server: {e}")
            return False
            
    async def _stop_remote_server(self) -> bool:
        """
        Stop the UnitMCP server on a remote host via SSH.
        
        Returns:
            True if stop was successful, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add the server stop command (kill the Python process running the server)
            server_cmd = f"pkill -f 'python -m unitmcp.server.server_main --host {self.host} --port {self.port}'"
            
            # Execute the command
            full_cmd = f"{ssh_cmd} '{server_cmd}'"
            
            self.logger.info(f"Stopping remote server with command: {full_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # pkill might return non-zero if no process is found, which is fine
            self.server_running = False
            self.logger.info(f"UnitMCP server stopped on {self.remote_host}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping remote UnitMCP server: {e}")
            return False
            
    def _build_ssh_command(self) -> str:
        """
        Build the SSH command for connecting to the remote host.
        
        Returns:
            SSH command string
        """
        ssh_cmd = f"ssh {self.remote_user}@{self.remote_host}"
        
        if self.remote_key:
            ssh_cmd += f" -i {self.remote_key}"
            
        return ssh_cmd
        
    async def _check_ssh_connection(self) -> bool:
        """
        Check if SSH connection to the remote host is possible.
        
        Returns:
            True if connection is possible, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add a simple command to test the connection
            test_cmd = f"{ssh_cmd} 'echo UnitMCP SSH test'"
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                test_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"SSH connection test failed: {stderr.decode()}")
                return False
                
            output = stdout.decode().strip()
            if output != "UnitMCP SSH test":
                self.logger.error(f"SSH connection test returned unexpected output: {output}")
                return False
                
            self.logger.info(f"SSH connection to {self.remote_host} successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking SSH connection: {e}")
            return False
            
    async def _check_remote_unitmcp(self) -> bool:
        """
        Check if UnitMCP is installed on the remote host.
        
        Returns:
            True if UnitMCP is installed, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Add a command to check if UnitMCP is installed
            test_cmd = f"{ssh_cmd} 'python -c \"import unitmcp; print(unitmcp.__version__)\"'"
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                test_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"UnitMCP not found on remote host: {stderr.decode()}")
                return False
                
            version = stdout.decode().strip()
            self.logger.info(f"Found UnitMCP version {version} on remote host")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking remote UnitMCP: {e}")
            return False
            
    async def _check_if_rpi(self) -> bool:
        """
        Check if we're running on a Raspberry Pi.
        
        Returns:
            True if running on a Raspberry Pi, False otherwise
        """
        try:
            # If this is a remote server, check via SSH
            if self.is_remote:
                ssh_cmd = self._build_ssh_command()
                test_cmd = f"{ssh_cmd} 'cat /proc/cpuinfo | grep -i raspberry'"
                
                process = await asyncio.create_subprocess_shell(
                    test_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                return process.returncode == 0 and stdout
                
            # Otherwise, check locally
            else:
                # Check if /proc/cpuinfo contains "Raspberry"
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        return 'Raspberry' in f.read()
                except:
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error checking if running on Raspberry Pi: {e}")
            return False
            
    async def _optimize_for_rpi(self) -> None:
        """
        Optimize the system for running on a Raspberry Pi.
        """
        try:
            self.logger.info("Optimizing system for Raspberry Pi")
            
            # If this is a remote server, optimize via SSH
            if self.is_remote:
                ssh_cmd = self._build_ssh_command()
                
                # Add commands to optimize the system
                optimize_cmds = [
                    "sudo systemctl stop bluetooth.service",  # Stop Bluetooth service
                    "sudo systemctl disable bluetooth.service",  # Disable Bluetooth service
                    "sudo systemctl stop avahi-daemon.service",  # Stop Avahi daemon
                    "sudo systemctl disable avahi-daemon.service",  # Disable Avahi daemon
                ]
                
                for cmd in optimize_cmds:
                    full_cmd = f"{ssh_cmd} '{cmd}'"
                    
                    process = await asyncio.create_subprocess_shell(
                        full_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    await process.communicate()
                    
            # Otherwise, optimize locally
            else:
                # Stop and disable Bluetooth service
                try:
                    await asyncio.create_subprocess_shell(
                        "sudo systemctl stop bluetooth.service",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    await asyncio.create_subprocess_shell(
                        "sudo systemctl disable bluetooth.service",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                except:
                    self.logger.warning("Failed to stop/disable Bluetooth service")
                    
                # Stop and disable Avahi daemon
                try:
                    await asyncio.create_subprocess_shell(
                        "sudo systemctl stop avahi-daemon.service",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    await asyncio.create_subprocess_shell(
                        "sudo systemctl disable avahi-daemon.service",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                except:
                    self.logger.warning("Failed to stop/disable Avahi daemon")
                    
            self.logger.info("System optimized for Raspberry Pi")
            
        except Exception as e:
            self.logger.error(f"Error optimizing system for Raspberry Pi: {e}")
