#!/usr/bin/env python3
"""
UnitMCP Orchestrator Shell Patch

This module patches the UnitMCP Orchestrator Shell to fix:
1. Connection issues with async client
2. Add file upload functionality
3. Fix run command for audio examples

Usage:
  python shell_patch.py
"""

import os
import sys
import shlex
import logging
import asyncio
import argparse
from typing import Dict, List, Optional, Any
from colorama import Fore, Style, init

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the original shell
from unitmcp.orchestrator.shell import OrchestratorShell
from unitmcp.orchestrator.orchestrator import Orchestrator
from unitmcp.client.client import MCPHardwareClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize colorama
init()


class PatchedOrchestratorShell(OrchestratorShell):
    """
    Patched version of the UnitMCP Orchestrator Shell with fixed functionality.
    """
    
    def do_connect(self, arg):
        """
        Connect to a server.
        
        Usage: connect <host> <port> [--ssl]
        
        Examples:
          connect localhost 8080
          connect 192.168.1.100 8080 --ssl
        """
        args = shlex.split(arg) if arg else []
        
        if len(args) < 2:
            print(f"{Fore.RED}Please specify host and port.{Style.RESET_ALL}")
            print(f"Usage: connect <host> <port> [--ssl]")
            return
        
        host = args[0]
        
        try:
            port = int(args[1])
        except ValueError:
            print(f"{Fore.RED}Port must be a number.{Style.RESET_ALL}")
            return
        
        ssl_enabled = "--ssl" in args
        
        print(f"{Fore.GREEN}Connecting to {host}:{port} {'with SSL' if ssl_enabled else ''}...{Style.RESET_ALL}")
        
        try:
            # Create a client and run connect in an event loop
            client = MCPHardwareClient(host=host, port=port)
            
            # Run the async connect method in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(client.connect())
            finally:
                loop.close()
            
            # Create connection info
            connection_info = {
                "host": host,
                "port": port,
                "ssl_enabled": ssl_enabled,
                "status": "connected",
                "client": client
            }
            
            # Update server in orchestrator config
            server_info = f"{host}:{port}"
            if server_info in self.orchestrator.config.get("recent_servers", []):
                self.orchestrator.config["recent_servers"].remove(server_info)
            
            if "recent_servers" not in self.orchestrator.config:
                self.orchestrator.config["recent_servers"] = []
                
            self.orchestrator.config["recent_servers"].insert(0, server_info)
            self.orchestrator.config["recent_servers"] = self.orchestrator.config["recent_servers"][:10]  # Keep only 10 most recent
            self.orchestrator._save_config()
            
            print(f"{Fore.GREEN}Connected successfully!{Style.RESET_ALL}")
            self.current_server = connection_info
            
            # Update prompt
            self.prompt = f"{Fore.BLUE}mcp ({host}:{port})> {Style.RESET_ALL}"
            
            # Try to play a connection beep if available
            try:
                from examples.audio.connection_beep import play_connection_beep
                play_connection_beep()
            except ImportError:
                pass
                
        except Exception as e:
            print(f"{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
    
    def do_upload(self, arg):
        """
        Upload a file to the connected server.
        
        Usage: upload <local_path> <remote_path>
        
        Examples:
          upload examples/audio/tone_generator.py /home/pi/tone_generator.py
          upload examples/audio/music/ /home/pi/music/
        """
        if not self.current_server:
            print(f"{Fore.RED}Not connected to any server. Use 'connect' first.{Style.RESET_ALL}")
            return
        
        args = shlex.split(arg) if arg else []
        
        if len(args) < 2:
            print(f"{Fore.RED}Please specify local and remote paths.{Style.RESET_ALL}")
            print(f"Usage: upload <local_path> <remote_path>")
            return
        
        local_path = args[0]
        remote_path = args[1]
        
        # Check if local path exists
        if not os.path.exists(local_path):
            print(f"{Fore.RED}Local path '{local_path}' does not exist.{Style.RESET_ALL}")
            return
        
        # Get server connection info
        host = self.current_server.get("host", "")
        ssh_username = "pi"  # Default username
        ssh_password = None
        ssh_key_path = None
        
        print(f"{Fore.GREEN}Uploading {local_path} to {remote_path}...{Style.RESET_ALL}")
        
        try:
            # Check if paramiko is available
            import paramiko
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to server
            try:
                # Try with password if provided
                if ssh_password:
                    client.connect(host, username=ssh_username, password=ssh_password)
                # Try with key if provided
                elif ssh_key_path:
                    client.connect(host, username=ssh_username, key_filename=os.path.expanduser(ssh_key_path))
                # Try default key
                else:
                    client.connect(host, username=ssh_username)
            except Exception as e:
                # If connection fails, try with default password
                try:
                    client.connect(host, username=ssh_username, password="raspberry")
                except Exception as e2:
                    print(f"{Fore.RED}Failed to connect to server: {e2}{Style.RESET_ALL}")
                    return
            
            # Create SFTP client
            sftp = client.open_sftp()
            
            # Check if it's a directory
            if os.path.isdir(local_path):
                # Create remote directory
                try:
                    sftp.mkdir(remote_path)
                except IOError:
                    # Directory might already exist
                    pass
                
                # Upload each file in the directory
                for root, dirs, files in os.walk(local_path):
                    for dir_name in dirs:
                        local_dir = os.path.join(root, dir_name)
                        rel_path = os.path.relpath(local_dir, local_path)
                        remote_dir = os.path.join(remote_path, rel_path)
                        
                        # Create remote directory
                        try:
                            sftp.mkdir(remote_dir)
                        except IOError:
                            # Directory might already exist
                            pass
                    
                    for file_name in files:
                        local_file = os.path.join(root, file_name)
                        rel_path = os.path.relpath(local_file, local_path)
                        remote_file = os.path.join(remote_path, rel_path)
                        
                        # Upload file
                        try:
                            sftp.put(local_file, remote_file)
                            print(f"  Uploaded: {rel_path}")
                        except Exception as e:
                            print(f"{Fore.RED}  Failed to upload {rel_path}: {e}{Style.RESET_ALL}")
                
                print(f"{Fore.GREEN}Directory uploaded successfully.{Style.RESET_ALL}")
            else:
                # Upload single file
                sftp.put(local_path, remote_path)
                print(f"{Fore.GREEN}File uploaded successfully.{Style.RESET_ALL}")
            
            # Close connections
            sftp.close()
            client.close()
            
        except ImportError:
            print(f"{Fore.RED}Paramiko module not found. Please install it with 'pip install paramiko'.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Upload failed: {e}{Style.RESET_ALL}")
    
    def do_run(self, arg):
        """
        Run an example.
        
        Usage: run [example_name] [options]
        
        If example_name is not provided, uses the currently selected example.
        
        Options:
          --simulation=<bool>       Run in simulation mode (default: true)
          --host=<host>             Host to connect to (default: localhost)
          --port=<port>             Port to use (default: 8080)
          --ssh-username=<username> SSH username (default: pi)
          --ssh-key-path=<path>     Path to SSH key (default: ~/.ssh/id_rsa)
          --ssl=<bool>              Enable SSL (default: false)
          --demo=<name>             Demo to run (for audio examples)
          --example=<name>          Specific example to run (for audio examples)
          --frequency=<float>       Tone frequency in Hz (for audio examples)
          --duration=<float>        Duration in seconds (for audio examples)
          --volume=<float>          Volume level (for audio examples)
        
        Examples:
          run basic
          run rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi
          run audio --demo=tone --frequency=1000 --duration=3
        """
        args = shlex.split(arg) if arg else []
        
        # Parse arguments
        example_name = None
        options = {}
        
        for arg in args:
            if arg.startswith("--"):
                # Option
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    
                    # Convert boolean strings
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    
                    options[key] = value
                else:
                    # Flag without value
                    options[arg[2:]] = True
            else:
                # Example name
                example_name = arg
        
        # Use current example if not specified
        if not example_name and self.current_example:
            example_name = self.current_example
        
        if not example_name:
            print(f"{Fore.RED}Please specify an example name or select an example first.{Style.RESET_ALL}")
            return
        
        # Check if example exists
        example = self.orchestrator.get_example(example_name)
        if not example:
            print(f"{Fore.RED}Example '{example_name}' not found.{Style.RESET_ALL}")
            return
        
        # Extract options
        simulation = options.get("simulation")
        if isinstance(simulation, str):
            simulation = simulation.lower() == "true"
            
        host = options.get("host")
        port = options.get("port")
        if port and isinstance(port, str) and port.isdigit():
            port = int(port)
            
        ssh_username = options.get("ssh-username")
        ssh_key_path = options.get("ssh-key-path")
        ssh_password = options.get("ssh-password")
        
        ssl_enabled = options.get("ssl")
        if isinstance(ssl_enabled, str):
            ssl_enabled = ssl_enabled.lower() == "true"
        
        # Run example
        print(f"{Fore.GREEN}Running example: {example_name}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Simulation:{Style.RESET_ALL} {simulation}")
        print(f"  {Fore.CYAN}Host:{Style.RESET_ALL} {host}")
        print(f"  {Fore.CYAN}Port:{Style.RESET_ALL} {port}")
        print(f"  {Fore.CYAN}SSH Username:{Style.RESET_ALL} {ssh_username}")
        print(f"  {Fore.CYAN}SSH Key Path:{Style.RESET_ALL} {ssh_key_path}")
        print(f"  {Fore.CYAN}SSL Enabled:{Style.RESET_ALL} {ssl_enabled}")
        
        # For audio examples, print additional options
        if example_name == "audio":
            demo = options.get("demo")
            if demo:
                print(f"  {Fore.CYAN}Demo:{Style.RESET_ALL} {demo}")
            
            example_opt = options.get("example")
            if example_opt:
                print(f"  {Fore.CYAN}Example:{Style.RESET_ALL} {example_opt}")
            
            frequency = options.get("frequency")
            if frequency:
                print(f"  {Fore.CYAN}Frequency:{Style.RESET_ALL} {frequency} Hz")
            
            duration = options.get("duration")
            if duration:
                print(f"  {Fore.CYAN}Duration:{Style.RESET_ALL} {duration} seconds")
            
            volume = options.get("volume")
            if volume:
                print(f"  {Fore.CYAN}Volume:{Style.RESET_ALL} {volume}")
        
        try:
            # Pass all options to the orchestrator
            runner_info = self.orchestrator.run_example(
                example_name,
                simulation=simulation,
                host=host,
                port=port,
                ssh_username=ssh_username,
                ssh_key_path=ssh_key_path,
                ssl_enabled=ssl_enabled,
                **options  # Pass all other options
            )
            
            self.current_runner = runner_info["id"]
            
            print(f"{Fore.GREEN}Runner started with ID: {self.current_runner}{Style.RESET_ALL}")
            print(f"Use 'status {self.current_runner}' to check status")
            
        except Exception as e:
            print(f"{Fore.RED}Failed to run example: {e}{Style.RESET_ALL}")


def main():
    """Main entry point for the patched orchestrator shell."""
    parser = argparse.ArgumentParser(description="UnitMCP Patched Orchestrator Shell")
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimize log output"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Create orchestrator
    orchestrator = Orchestrator(quiet=args.quiet)
    
    # Create and run shell
    shell = PatchedOrchestratorShell(orchestrator)
    shell.cmdloop()


if __name__ == "__main__":
    main()
