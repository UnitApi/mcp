#!/usr/bin/env python3
"""
SSH Connection Script with URL-like parameter parsing

This script provides a Python implementation of the ssh_connect.sh bash script,
allowing for SSH connections with simple URL-like format and various authentication methods.
"""

import argparse
import getpass
import os
import sys
import paramiko
import socket
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv


class SSHConnector:
    def __init__(
            self,
            username: str = None,
            server: str = None,
            password: str = None,
            port: int = 22,
            identity_file: str = None,
            verbose: bool = False
    ):
        """
        Initialize SSH connector with connection parameters.

        Args:
            username: SSH username
            server: SSH server address
            password: SSH password (optional)
            port: SSH port (default: 22)
            identity_file: Path to identity file for key-based authentication (optional)
            verbose: Enable verbose output
        """
        # Set default values
        self.username = username or getpass.getuser()
        self.server = server or "localhost"
        self.password = password
        self.port = port
        self.identity_file = identity_file
        self.verbose = verbose
        
        # SSH client
        self.client = None
        
        # Logging
        self.log_level = 1 if verbose else 0
    
    def log(self, message: str, level: int = 0):
        """
        Log a message if the log level is high enough.
        
        Args:
            message: Message to log
            level: Log level (0=always, 1=verbose)
        """
        if level <= self.log_level:
            print(message)
    
    def connect(self) -> bool:
        """
        Establish SSH connection to the server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        self.log(f"Attempting to connect to {self.server} as {self.username}...")
        
        # Create SSH client
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connection options
        connect_kwargs = {
            'hostname': self.server,
            'username': self.username,
            'port': self.port,
            'timeout': 10,
            'allow_agent': False,
            'look_for_keys': False
        }
        
        # Add identity file if provided
        if self.identity_file:
            if os.path.isfile(self.identity_file):
                self.log(f"Using identity file: {self.identity_file}", 1)
                connect_kwargs['key_filename'] = self.identity_file
            else:
                self.log(f"Warning: Identity file {self.identity_file} not found!")
                if not self.password:
                    self.log("No valid authentication method available. Exiting.")
                    return False
        
        # Add password if provided
        if self.password:
            self.log("Using password authentication", 1)
            connect_kwargs['password'] = self.password
        
        try:
            # Connect to server
            self.client.connect(**connect_kwargs)
            self.log(f"Successfully connected to {self.server}")
            return True
        except paramiko.AuthenticationException:
            self.log("Authentication failed. Please check your credentials.")
        except paramiko.SSHException as e:
            self.log(f"SSH error: {str(e)}")
        except socket.error as e:
            self.log(f"Connection error: {str(e)}")
        except Exception as e:
            self.log(f"Error: {str(e)}")
        
        return False
    
    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command on the remote server.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.client:
            self.log("Not connected to any server")
            return -1, "", "Not connected to any server"
        
        try:
            self.log(f"Executing command: {command}", 1)
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            
            return exit_code, stdout_str, stderr_str
        except Exception as e:
            self.log(f"Error executing command: {str(e)}")
            return -1, "", str(e)
    
    def start_interactive_shell(self):
        """
        Start an interactive shell session.
        """
        if not self.client:
            self.log("Not connected to any server")
            return
        
        try:
            self.log("Starting interactive shell session...")
            channel = self.client.invoke_shell()
            
            # Set terminal size
            channel.resize_pty(width=80, height=24)
            
            # Interactive session
            while True:
                if channel.recv_ready():
                    output = channel.recv(1024).decode('utf-8')
                    sys.stdout.write(output)
                    sys.stdout.flush()
                
                if channel.exit_status_ready():
                    break
                
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    input_data = sys.stdin.read(1)
                    channel.send(input_data)
        except Exception as e:
            self.log(f"Error in interactive shell: {str(e)}")
        finally:
            self.disconnect()
    
    def disconnect(self):
        """
        Close the SSH connection.
        """
        if self.client:
            self.client.close()
            self.client = None
            self.log("Disconnected from server")


def parse_connection_string(connection_string: str) -> Tuple[str, str]:
    """
    Parse a connection string in the format username@server.
    
    Args:
        connection_string: Connection string in the format username@server
        
    Returns:
        Tuple of (username, server)
    """
    if '@' in connection_string:
        username, server = connection_string.split('@', 1)
        return username, server
    return None, connection_string


def show_help():
    """
    Display help information.
    """
    print("SSH Connection Script")
    print("=====================")
    print("A Python script to help manage SSH connections with simple URL-like format.")
    print()
    print("Usage: python ssh_connect.py [user@server] [password] [options]")
    print("   or: python ssh_connect.py [options]")
    print()
    print("Connection format:")
    print("  user@server        Simple URL-like format (e.g., pi@192.168.1.100)")
    print("  password           Password for authentication (optional)")
    print()
    print("Options:")
    print("  -h, --help           Show this help message")
    print("  -i, --identity FILE  Specify an identity file for key-based authentication")
    print("  -P, --port PORT      Specify SSH port (default: 22)")
    print("  -v, --verbose        Enable verbose SSH output")
    print("  -c, --command CMD    Execute a command on the remote server")
    print()
    print("Examples:")
    print("  python ssh_connect.py pi@192.168.1.100 raspberry")
    print("  python ssh_connect.py admin@server.local mypassword -P 2222")
    print("  python ssh_connect.py pi@192.168.1.100 -i ~/.ssh/id_rsa")
    print("  python ssh_connect.py pi@192.168.1.100 -c 'ls -la'")
    print()


def main():
    """
    Main function to parse arguments and establish SSH connection.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Default values
    username = os.getenv('SSH_USER', getpass.getuser())
    server = os.getenv('SSH_SERVER', '192.168.1.1')
    password = os.getenv('SSH_PASSWORD', '')
    port = int(os.getenv('SSH_PORT', '22'))
    identity_file = os.getenv('SSH_IDENTITY_FILE', '')
    verbose = os.getenv('SSH_VERBOSE', 'false').lower() == 'true'
    command = None
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='SSH Connection Script', add_help=False)
    parser.add_argument('connection_string', nargs='?', help='Connection string in the format username@server')
    parser.add_argument('password', nargs='?', help='Password for authentication')
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')
    parser.add_argument('-i', '--identity', help='Identity file for key-based authentication')
    parser.add_argument('-P', '--port', type=int, help='SSH port')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-c', '--command', help='Execute a command on the remote server')
    
    # Parse known args first to handle help specially
    args, unknown = parser.parse_known_args()
    
    if args.help:
        show_help()
        return 0
    
    # Parse connection string if provided
    if args.connection_string and '@' in args.connection_string:
        username, server = parse_connection_string(args.connection_string)
    
    # Override with command line arguments
    if args.password:
        password = args.password
    if args.identity:
        identity_file = args.identity
    if args.port:
        port = args.port
    if args.verbose:
        verbose = True
    if args.command:
        command = args.command
    
    # Create SSH connector
    ssh = SSHConnector(
        username=username,
        server=server,
        password=password,
        port=port,
        identity_file=identity_file,
        verbose=verbose
    )
    
    # Connect to server
    if not ssh.connect():
        return 1
    
    # Execute command if provided
    if command:
        exit_code, stdout, stderr = ssh.execute_command(command)
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        ssh.disconnect()
        return exit_code
    
    # Start interactive shell
    try:
        import select
        ssh.start_interactive_shell()
    except ImportError:
        print("Interactive shell requires the 'select' module")
        print("You can still use the -c/--command option to execute commands")
        ssh.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
