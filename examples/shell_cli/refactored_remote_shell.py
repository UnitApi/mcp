#!/usr/bin/env python3
"""
Refactored Remote Shell Example

This example demonstrates a refactored version of the simple_remote_shell.py
that uses the standardized utilities for error handling, resource management,
and logging.

Features:
- Connect to remote devices over SSH or TCP
- Execute commands on remote devices
- Interactive shell interface
- Simulation mode for testing without hardware
- Process monitoring and management for concurrent operations
- Proper resource management and error handling

Usage:
    python refactored_remote_shell.py [--host HOSTNAME] [--port PORT] [--ssh]
"""

import argparse
import cmd
import os
import socket
import subprocess
import sys
import time
import threading
import json
import select
import signal
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

# Import the process manager
try:
    from process_manager import get_instance as get_process_manager
    PROCESS_MANAGER_AVAILABLE = True
except ImportError:
    PROCESS_MANAGER_AVAILABLE = False
    print("Process manager not available. Concurrent process monitoring disabled.")
    print("Install process_manager.py in the same directory for enhanced stability.")

# Check if paramiko is installed for SSH support
try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False
    print("SSH support not available. Install paramiko for SSH functionality.")
    print("pip install paramiko")

# Import UnitMCP utilities if available
try:
    from unitmcp.utils import (
        UnitMCPError, NetworkError, ResourceError, RemoteError,
        ResourceManager, configure_logging, get_standardized_logger, log_exception
    )
    UNITMCP_AVAILABLE = True
except ImportError:
    UNITMCP_AVAILABLE = False
    print("UnitMCP utilities not available. Using simplified error handling.")
    
    # Define simplified versions of the utilities
    class UnitMCPError(Exception):
        """Base exception for all errors."""
        pass
    
    class NetworkError(UnitMCPError):
        """Network-related error."""
        pass
    
    class ResourceError(UnitMCPError):
        """Error related to resource management."""
        pass
    
    class RemoteError(UnitMCPError):
        """Error related to remote operations."""
        pass
    
    class ResourceManager:
        """Simplified resource manager."""
        
        def __init__(self):
            self._resources = []
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.cleanup_all()
        
        def register(self, resource, cleanup_func=None, name=None):
            self._resources.append((resource, cleanup_func, name))
            return resource
        
        def cleanup_all(self):
            for resource, cleanup_func, name in reversed(self._resources):
                try:
                    if cleanup_func:
                        cleanup_func()
                    elif hasattr(resource, 'close'):
                        resource.close()
                except Exception as e:
                    print(f"Error cleaning up resource {name}: {e}")
            self._resources = []
    
    def configure_logging(level="INFO", log_file=None, console=True):
        """Simplified logging configuration."""
        import logging
        logging.basicConfig(
            level=getattr(logging, level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filename=log_file
        )
    
    def get_standardized_logger(name):
        """Get a logger with standardized settings."""
        import logging
        return logging.getLogger(name)
    
    def log_exception(logger, exception, message="An exception occurred", level="ERROR"):
        """Log an exception with appropriate level."""
        import traceback
        log_method = getattr(logger, level.lower(), logger.error)
        log_method(f"{message}: {exception}\n{traceback.format_exc()}")

# Configure logging
configure_logging(level="INFO", console=True)
logger = get_standardized_logger(__name__)


class ConnectionManager:
    """
    Manager for remote connections.
    
    This class handles SSH and TCP connections to remote devices,
    providing a unified interface for executing commands.
    """
    
    def __init__(self, resource_manager: Optional[ResourceManager] = None):
        """
        Initialize the connection manager.
        
        Args:
            resource_manager: Optional resource manager for tracking resources
        """
        self.ssh_client = None
        self.tcp_socket = None
        self.connected = False
        self.host = None
        self.port = None
        self.use_ssh = False
        self.username = None
        self.resource_manager = resource_manager or ResourceManager()
    
    def connect_ssh(
        self,
        host: str,
        port: int = 22,
        username: str = "pi",
        password: Optional[str] = None,
        key_path: Optional[str] = None
    ) -> bool:
        """
        Connect to a remote device using SSH.
        
        Args:
            host: Hostname or IP address
            port: SSH port
            username: SSH username
            password: SSH password
            key_path: Path to SSH key file
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            NetworkError: If connection fails
        """
        if not SSH_AVAILABLE:
            raise NetworkError("SSH support not available. Install paramiko.")
        
        try:
            # Close existing connection if any
            self.disconnect()
            
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Register with resource manager
            self.ssh_client = self.resource_manager.register(
                ssh_client,
                cleanup_func=ssh_client.close,
                name=f"SSH connection to {host}:{port}"
            )
            
            # Connect to remote device
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": 10
            }
            
            if password:
                connect_kwargs["password"] = password
            
            if key_path:
                key_path = os.path.expanduser(key_path)
                if os.path.exists(key_path):
                    connect_kwargs["key_filename"] = key_path
                else:
                    logger.warning(f"SSH key file not found: {key_path}")
            
            self.ssh_client.connect(**connect_kwargs)
            
            # Update connection state
            self.connected = True
            self.host = host
            self.port = port
            self.use_ssh = True
            self.username = username
            
            logger.info(f"Connected to {host}:{port} via SSH")
            return True
            
        except paramiko.AuthenticationException as e:
            raise NetworkError(f"SSH authentication failed: {e}")
        except paramiko.SSHException as e:
            raise NetworkError(f"SSH connection error: {e}")
        except Exception as e:
            raise NetworkError(f"Failed to connect via SSH: {e}")
    
    def connect_tcp(self, host: str, port: int) -> bool:
        """
        Connect to a remote device using TCP.
        
        Args:
            host: Hostname or IP address
            port: TCP port
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            NetworkError: If connection fails
        """
        try:
            # Close existing connection if any
            self.disconnect()
            
            # Create TCP socket
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.settimeout(10)
            
            # Register with resource manager
            self.tcp_socket = self.resource_manager.register(
                tcp_socket,
                cleanup_func=tcp_socket.close,
                name=f"TCP connection to {host}:{port}"
            )
            
            # Connect to remote device
            self.tcp_socket.connect((host, port))
            
            # Update connection state
            self.connected = True
            self.host = host
            self.port = port
            self.use_ssh = False
            
            logger.info(f"Connected to {host}:{port} via TCP")
            return True
            
        except socket.timeout:
            raise NetworkError(f"Connection to {host}:{port} timed out")
        except socket.error as e:
            raise NetworkError(f"Socket error: {e}")
        except Exception as e:
            raise NetworkError(f"Failed to connect via TCP: {e}")
    
    def disconnect(self) -> None:
        """
        Disconnect from the remote device.
        
        This method is safe to call even if not connected.
        """
        # Resources will be cleaned up by the resource manager
        self.connected = False
        self.ssh_client = None
        self.tcp_socket = None
    
    def execute_command(
        self,
        command: str,
        timeout: int = 30,
        get_output: bool = True
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """
        Execute a command on the remote device.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            get_output: Whether to capture and return command output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
            
        Raises:
            RemoteError: If command execution fails
        """
        if not self.connected:
            raise RemoteError("Not connected to a remote device")
        
        try:
            if self.use_ssh and self.ssh_client:
                return self._execute_ssh_command(command, timeout, get_output)
            elif self.tcp_socket:
                return self._execute_tcp_command(command, timeout, get_output)
            else:
                raise RemoteError("No valid connection available")
                
        except Exception as e:
            raise RemoteError(f"Failed to execute command: {e}")
    
    def _execute_ssh_command(
        self,
        command: str,
        timeout: int,
        get_output: bool
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """Execute a command via SSH."""
        if not self.ssh_client:
            raise RemoteError("SSH client not available")
        
        try:
            # Execute command
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            
            if get_output:
                # Get command output
                stdout_data = stdout.read().decode('utf-8')
                stderr_data = stderr.read().decode('utf-8')
                exit_status = stdout.channel.recv_exit_status()
                
                return exit_status, stdout_data, stderr_data
            else:
                # Just get exit status
                exit_status = stdout.channel.recv_exit_status()
                return exit_status, None, None
                
        except socket.timeout:
            raise RemoteError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise RemoteError(f"SSH command execution failed: {e}")
    
    def _execute_tcp_command(
        self,
        command: str,
        timeout: int,
        get_output: bool
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """Execute a command via TCP."""
        if not self.tcp_socket:
            raise RemoteError("TCP socket not available")
        
        try:
            # Send command
            self.tcp_socket.sendall(f"{command}\n".encode('utf-8'))
            
            if not get_output:
                return 0, None, None
            
            # Get command output
            output = b""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if data is available
                readable, _, _ = select.select([self.tcp_socket], [], [], 1.0)
                
                if readable:
                    # Read data
                    data = self.tcp_socket.recv(4096)
                    
                    if not data:
                        # Connection closed
                        break
                    
                    output += data
                    
                    # Check if command is complete
                    if b"$" in data or b"#" in data or b">" in data:
                        break
            
            # Parse output (simplified)
            output_str = output.decode('utf-8', errors='replace')
            
            # Assume success if we got output
            return 0, output_str, ""
            
        except socket.timeout:
            raise RemoteError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise RemoteError(f"TCP command execution failed: {e}")


class CommandParser:
    """
    Parser for shell commands.
    
    This class provides utilities for parsing command arguments
    with support for positional and named arguments.
    """
    
    @staticmethod
    def parse_args(arg_string: str) -> Tuple[List[str], Dict[str, str]]:
        """
        Parse command arguments.
        
        Args:
            arg_string: Command argument string
            
        Returns:
            Tuple of (positional_args, named_args)
        """
        args = arg_string.split()
        positional_args = []
        named_args = {}
        
        i = 0
        while i < len(args):
            if args[i].startswith('--'):
                # Named argument
                arg_name = args[i][2:]
                
                if i + 1 < len(args) and not args[i + 1].startswith('--'):
                    # Argument has a value
                    named_args[arg_name] = args[i + 1]
                    i += 2
                else:
                    # Flag argument
                    named_args[arg_name] = 'true'
                    i += 1
            else:
                # Positional argument
                positional_args.append(args[i])
                i += 1
        
        return positional_args, named_args


class RemoteShell(cmd.Cmd):
    """Interactive shell for remote device control."""
    
    intro = "Remote Device Control Shell. Type help or ? to list commands.\n"
    prompt = "(remote) "
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 22,
        use_ssh: bool = False,
        simulation: bool = False,
        username: str = "pi",
        key_path: Optional[str] = None
    ):
        """
        Initialize the remote shell.
        
        Args:
            host: Hostname or IP address
            port: Port number
            use_ssh: Whether to use SSH
            simulation: Whether to run in simulation mode
            username: SSH username
            key_path: Path to SSH key file
        """
        super().__init__()
        self.host = host
        self.port = port
        self.use_ssh = use_ssh
        self.simulation = simulation
        self.username = username
        self.key_path = key_path
        self.variables = {}
        
        # Create resource manager
        self.resource_manager = ResourceManager()
        
        # Create connection manager
        self.connection_manager = ConnectionManager(self.resource_manager)
        
        # Process monitoring
        self.process_manager = get_process_manager() if PROCESS_MANAGER_AVAILABLE else None
        self.monitor_thread = None
        self.monitoring_active = False
        
        # Set simulation mode from environment variable if present
        if os.environ.get("SIMULATION") == "1":
            self.simulation = True
            logger.info("Running in simulation mode")
        
        # Start the process monitoring thread if process manager is available
        if self.process_manager:
            self.start_monitoring()
    
    def start_monitoring(self) -> None:
        """Start the process monitoring thread."""
        if self.process_manager and not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_processes,
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("Process monitoring active")
    
    def stop_monitoring(self) -> None:
        """Stop the process monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _monitor_processes(self) -> None:
        """Monitor processes for anomalies."""
        anomaly_count = 0
        last_check_time = time.time()
        
        while self.monitoring_active:
            if self.process_manager:
                current_time = time.time()
                check_interval = 5  # Normal check interval in seconds
                
                # Adjust check interval based on system load
                if anomaly_count > 5:
                    # More frequent checks if we've seen anomalies recently
                    check_interval = 2
                
                # Only check if enough time has passed
                if current_time - last_check_time >= check_interval:
                    last_check_time = current_time
                    
                    # Check for anomalies
                    fixed, remaining = self.process_manager.handle_anomalies(auto_fix=True)
                    
                    # Reset anomaly count if no issues found
                    if not fixed and not remaining:
                        anomaly_count = max(0, anomaly_count - 1)
                    else:
                        anomaly_count += len(fixed) + len(remaining)
                    
                    # Log any fixed anomalies
                    for anomaly in fixed:
                        anomaly_type = anomaly.get('type', 'unknown')
                        if anomaly_type == 'timeout' or anomaly_type == 'long_running':
                            print(f"\nWARNING: Terminated process {anomaly.get('pid')} due to {anomaly_type} condition")
                            # Restore prompt after printing warning
                            print(f"\n{self.prompt}", end='', flush=True)
                        elif anomaly_type == 'resource_contention_fixed':
                            print(f"\nWARNING: Resolved resource contention on {anomaly.get('resource')} by terminating process {anomaly.get('terminated_pid')}")
                            print(f"\n{self.prompt}", end='', flush=True)
                    
                    # Report any remaining anomalies
                    for anomaly in remaining:
                        anomaly_type = anomaly.get('type', 'unknown')
                        if anomaly_type == 'resource_contention':
                            print(f"\nWARNING: Resource contention detected on {anomaly.get('resource')} between processes {anomaly.get('pids')}")
                            print(f"\n{self.prompt}", end='', flush=True)
            
            # Sleep to avoid high CPU usage
            time.sleep(1)
    
    def emptyline(self) -> None:
        """Do nothing on empty line."""
        pass
    
    def do_connect(self, arg: str) -> None:
        """
        Connect to a remote device.
        
        Usage: connect [host] [port] [--ssh] [--username USERNAME] [--key-path KEY_PATH] [--password PASSWORD]
        """
        # Parse arguments
        positional_args, named_args = CommandParser.parse_args(arg)
        
        # Get host and port from positional arguments
        if len(positional_args) > 0:
            self.host = positional_args[0]
        
        if len(positional_args) > 1:
            try:
                self.port = int(positional_args[1])
            except ValueError:
                print(f"Invalid port: {positional_args[1]}")
                return
        
        # Get named arguments
        self.use_ssh = 'ssh' in named_args or self.use_ssh
        self.username = named_args.get('username', self.username)
        self.key_path = named_args.get('key-path', self.key_path)
        password = named_args.get('password')
        
        # Connect to the remote device
        try:
            if self.simulation:
                print(f"Simulation: Connecting to {self.host}:{self.port}")
                print("Simulation: Connection successful")
                self.prompt = f"(sim:{self.host}) "
                return
            
            if self.use_ssh:
                if not SSH_AVAILABLE:
                    print("SSH support not available. Install paramiko.")
                    return
                
                print(f"Connecting to {self.host}:{self.port} via SSH...")
                self.connection_manager.connect_ssh(
                    self.host,
                    self.port,
                    self.username,
                    password,
                    self.key_path
                )
                self.prompt = f"(ssh:{self.host}) "
            else:
                print(f"Connecting to {self.host}:{self.port} via TCP...")
                self.connection_manager.connect_tcp(self.host, self.port)
                self.prompt = f"(tcp:{self.host}) "
            
            print("Connection successful")
            
        except NetworkError as e:
            print(f"Connection failed: {e}")
            log_exception(logger, e, "Connection failed")
        except Exception as e:
            print(f"Unexpected error: {e}")
            log_exception(logger, e, "Unexpected error during connection")
    
    def do_disconnect(self, arg: str) -> None:
        """
        Disconnect from the remote device.
        
        Usage: disconnect
        """
        try:
            if self.simulation:
                print("Simulation: Disconnected")
                self.prompt = "(remote) "
                return
            
            self.connection_manager.disconnect()
            print("Disconnected")
            self.prompt = "(remote) "
            
        except Exception as e:
            print(f"Error disconnecting: {e}")
            log_exception(logger, e, "Error disconnecting")
    
    def do_exec(self, arg: str) -> None:
        """
        Execute a command on the remote device.
        
        Usage: exec <command>
        """
        if not arg:
            print("No command specified")
            return
        
        try:
            if self.simulation:
                print(f"Simulation: Executing command: {arg}")
                print("Simulation: Command output would appear here")
                return
            
            if not self.connection_manager.connected:
                print("Not connected to a remote device")
                return
            
            # Execute command
            exit_code, stdout, stderr = self.connection_manager.execute_command(arg)
            
            # Print output
            if stdout:
                print(stdout)
            
            if stderr:
                print(f"Error output: {stderr}")
            
            print(f"Command exited with code: {exit_code}")
            
        except RemoteError as e:
            print(f"Command execution failed: {e}")
            log_exception(logger, e, "Command execution failed")
        except Exception as e:
            print(f"Unexpected error: {e}")
            log_exception(logger, e, "Unexpected error during command execution")
    
    def do_set(self, arg: str) -> None:
        """
        Set a variable.
        
        Usage: set <name> <value>
        """
        args = arg.split(maxsplit=1)
        if len(args) != 2:
            print("Usage: set <name> <value>")
            return
        
        name, value = args
        self.variables[name] = value
        print(f"Variable {name} set to: {value}")
    
    def do_get(self, arg: str) -> None:
        """
        Get a variable value.
        
        Usage: get <name>
        """
        if not arg:
            print("Usage: get <name>")
            return
        
        if arg in self.variables:
            print(f"{arg} = {self.variables[arg]}")
        else:
            print(f"Variable {arg} not found")
    
    def do_list(self, arg: str) -> None:
        """
        List all variables.
        
        Usage: list
        """
        if not self.variables:
            print("No variables defined")
            return
        
        print("Variables:")
        for name, value in self.variables.items():
            print(f"  {name} = {value}")
    
    def do_clear(self, arg: str) -> None:
        """
        Clear the screen.
        
        Usage: clear
        """
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_exit(self, arg: str) -> bool:
        """
        Exit the shell.
        
        Usage: exit
        """
        if self.connection_manager.connected:
            print("Disconnecting...")
            self.connection_manager.disconnect()
        
        self.stop_monitoring()
        print("Goodbye!")
        return True
    
    def do_quit(self, arg: str) -> bool:
        """
        Exit the shell.
        
        Usage: quit
        """
        return self.do_exit(arg)
    
    def do_help(self, arg: str) -> None:
        """
        Show help for commands.
        
        Usage: help [command]
        """
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help
            print("Available commands:")
            print("  connect    - Connect to a remote device")
            print("  disconnect - Disconnect from the remote device")
            print("  exec       - Execute a command on the remote device")
            print("  set        - Set a variable")
            print("  get        - Get a variable value")
            print("  list       - List all variables")
            print("  clear      - Clear the screen")
            print("  exit/quit  - Exit the shell")
            print("  help       - Show this help message")
            print("\nType 'help <command>' for more information on a specific command.")


def main() -> None:
    """Main entry point for the remote shell."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Remote Device Control Shell")
    parser.add_argument("--host", default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=22, help="Port to use")
    parser.add_argument("--ssh", action="store_true", help="Use SSH for connection")
    parser.add_argument("--username", default="pi", help="SSH username")
    parser.add_argument("--key-path", help="Path to SSH key file")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    parser.add_argument("--log-file", help="Path to log file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(
        level=args.log_level,
        log_file=args.log_file,
        console=True
    )
    
    # Create and run the shell
    shell = RemoteShell(
        host=args.host,
        port=args.port,
        use_ssh=args.ssh,
        simulation=args.simulation,
        username=args.username,
        key_path=args.key_path
    )
    
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        log_exception(logger, e, "Unexpected error in shell")
        sys.exit(1)


if __name__ == "__main__":
    main()
