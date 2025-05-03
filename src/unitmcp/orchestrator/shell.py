"""Interactive shell for the UnitMCP Orchestrator."""

import os
import sys
import cmd
import time
import logging
import argparse
import shlex
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from tabulate import tabulate
from colorama import Fore, Style, init

from .orchestrator import Orchestrator
from ..hardware.gpio import HELP_DOCUMENTATION as GPIO_HELP_DOCS

# Initialize colorama
init()

logger = logging.getLogger(__name__)

class OrchestratorShell(cmd.Cmd):
    """
    Interactive shell for managing UnitMCP examples and servers.
    
    This shell provides commands to:
    - List available examples
    - Run examples with different configurations
    - Monitor running examples
    - Connect to servers
    - Manage simulation vs. real hardware modes
    """
    
    intro = f"""
{Fore.GREEN}╔═════════════════════════════════════════════╗
║  {Fore.YELLOW}UnitMCP Orchestrator{Fore.GREEN}                       ║
║  {Fore.CYAN}Type 'help' for commands | 'exit' to quit{Fore.GREEN}  ║
╚═════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    prompt = f"{Fore.BLUE}mcp> {Style.RESET_ALL}"
    
    def __init__(self, orchestrator: Optional[Orchestrator] = None):
        """
        Initialize the shell.
        
        Args:
            orchestrator: Orchestrator instance or None to create a new one
        """
        super().__init__()
        self.orchestrator = orchestrator or Orchestrator()
        self.current_example = None
        self.current_server = None
        self.current_runner = None
    
    def emptyline(self):
        """Do nothing on empty line."""
        pass
    
    def do_exit(self, arg):
        """Exit the shell."""
        print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
        return True
    
    def do_quit(self, arg):
        """Exit the shell."""
        return self.do_exit(arg)
    
    def do_EOF(self, arg):
        """Exit on EOF (Ctrl+D)."""
        print()  # Add newline
        return self.do_exit(arg)
    
    def do_list(self, arg):
        """
        List available examples.
        
        Usage: list [category]
        Categories:
          all         - List all examples (default)
          recent      - List recently used examples
          favorite    - List favorite examples
          running     - List running examples
          with-runner - List examples with runner component
        """
        args = shlex.split(arg) if arg else []
        category = args[0] if args else "all"
        
        if category == "all":
            examples = self.orchestrator.get_examples()
            if not examples:
                print(f"{Fore.YELLOW}No examples found.{Style.RESET_ALL}")
                return
            
            table_data = []
            for name, info in examples.items():
                description = info.get("description", "")
                if len(description) > 60:
                    description = description[:57] + "..."
                
                has_runner = "✓" if info.get("has_runner") else ""
                has_server = "✓" if info.get("has_server") else ""
                
                table_data.append([
                    name,
                    description,
                    has_runner,
                    has_server
                ])
            
            print(f"\n{Fore.GREEN}Available Examples:{Style.RESET_ALL}")
            print(tabulate(
                table_data,
                headers=["Name", "Description", "Runner", "Server"],
                tablefmt="pretty"
            ))
            
        elif category == "recent":
            recent = self.orchestrator.get_recent_examples()
            if not recent:
                print(f"{Fore.YELLOW}No recent examples.{Style.RESET_ALL}")
                return
            
            table_data = []
            for name in recent:
                info = self.orchestrator.get_example(name)
                if info:
                    description = info.get("description", "")
                    if len(description) > 60:
                        description = description[:57] + "..."
                    
                    table_data.append([name, description])
            
            print(f"\n{Fore.GREEN}Recent Examples:{Style.RESET_ALL}")
            print(tabulate(
                table_data,
                headers=["Name", "Description"],
                tablefmt="pretty"
            ))
            
        elif category == "favorite":
            favorites = self.orchestrator.get_favorite_examples()
            if not favorites:
                print(f"{Fore.YELLOW}No favorite examples.{Style.RESET_ALL}")
                return
            
            table_data = []
            for name in favorites:
                info = self.orchestrator.get_example(name)
                if info:
                    description = info.get("description", "")
                    if len(description) > 60:
                        description = description[:57] + "..."
                    
                    table_data.append([name, description])
            
            print(f"\n{Fore.GREEN}Favorite Examples:{Style.RESET_ALL}")
            print(tabulate(
                table_data,
                headers=["Name", "Description"],
                tablefmt="pretty"
            ))
            
        elif category == "running":
            runners = self.orchestrator.get_active_runners()
            if not runners:
                print(f"{Fore.YELLOW}No running examples.{Style.RESET_ALL}")
                return
            
            table_data = []
            for runner_id, info in runners.items():
                status = info.get("status", "unknown")
                status_color = Fore.GREEN if status == "running" else Fore.RED
                
                table_data.append([
                    runner_id[:8] + "...",  # Truncate ID
                    info.get("example", ""),
                    f"{status_color}{status}{Style.RESET_ALL}",
                    info.get("host", ""),
                    info.get("port", ""),
                    "Yes" if info.get("simulation") else "No"
                ])
            
            print(f"\n{Fore.GREEN}Running Examples:{Style.RESET_ALL}")
            print(tabulate(
                table_data,
                headers=["ID", "Example", "Status", "Host", "Port", "Simulation"],
                tablefmt="pretty"
            ))
            
        elif category == "with-runner":
            examples = self.orchestrator.get_examples()
            if not examples:
                print(f"{Fore.YELLOW}No examples found.{Style.RESET_ALL}")
                return
            
            # Filter examples that have a runner
            examples_with_runner = {name: info for name, info in examples.items() if info.get("has_runner")}
            
            if not examples_with_runner:
                print(f"{Fore.YELLOW}No examples with runner component found.{Style.RESET_ALL}")
                return
            
            table_data = []
            for name, info in examples_with_runner.items():
                description = info.get("description", "")
                if len(description) > 60:
                    description = description[:57] + "..."
                
                has_server = "✓" if info.get("has_server") else ""
                
                table_data.append([
                    name,
                    description,
                    has_server
                ])
            
            print(f"\n{Fore.GREEN}Examples with Runner Component:{Style.RESET_ALL}")
            print(tabulate(
                table_data,
                headers=["Name", "Description", "Server"],
                tablefmt="pretty"
            ))
        else:
            print(f"{Fore.RED}Unknown category: {category}{Style.RESET_ALL}")
            print(f"Use one of: all, recent, favorite, running, with-runner")
    
    def do_info(self, arg):
        """
        Show detailed information about an example.
        
        Usage: info <example_name>
        """
        if not arg:
            print(f"{Fore.RED}Please specify an example name.{Style.RESET_ALL}")
            return
        
        example_name = arg.strip()
        example = self.orchestrator.get_example(example_name)
        
        if not example:
            print(f"{Fore.RED}Example '{example_name}' not found.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}Example Information:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Name:{Style.RESET_ALL} {example_name}")
        print(f"  {Fore.CYAN}Path:{Style.RESET_ALL} {example['path']}")
        print(f"  {Fore.CYAN}Description:{Style.RESET_ALL} {example.get('description', '')}")
        print(f"  {Fore.CYAN}Has Runner:{Style.RESET_ALL} {'Yes' if example.get('has_runner') else 'No'}")
        print(f"  {Fore.CYAN}Has Server:{Style.RESET_ALL} {'Yes' if example.get('has_server') else 'No'}")
        print(f"  {Fore.CYAN}Has .env:{Style.RESET_ALL} {'Yes' if example.get('env_file') else 'No'}")
        print(f"  {Fore.CYAN}Has .env.example:{Style.RESET_ALL} {'Yes' if example.get('env_example') else 'No'}")
        
        # Check if example is in favorites
        favorites = self.orchestrator.get_favorite_examples()
        is_favorite = example_name in favorites
        print(f"  {Fore.CYAN}Favorite:{Style.RESET_ALL} {'Yes' if is_favorite else 'No'}")
        
        # Show README if available
        readme_path = os.path.join(example['path'], "README.md")
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r') as f:
                    readme_content = f.read()
                    
                print(f"\n{Fore.GREEN}README:{Style.RESET_ALL}")
                print(f"{readme_content[:500]}...")
                print(f"{Fore.YELLOW}(Truncated, see full README at {readme_path}){Style.RESET_ALL}")
            except Exception as e:
                logger.warning(f"Failed to read README for {example_name}: {e}")
    
    def do_select(self, arg):
        """
        Select an example as the current working example.
        
        Usage: select <example_name>
        """
        if not arg:
            print(f"{Fore.RED}Please specify an example name.{Style.RESET_ALL}")
            return
        
        example_name = arg.strip()
        example = self.orchestrator.get_example(example_name)
        
        if not example:
            print(f"{Fore.RED}Example '{example_name}' not found.{Style.RESET_ALL}")
            return
        
        self.current_example = example_name
        print(f"{Fore.GREEN}Selected example: {example_name}{Style.RESET_ALL}")
        
        # Update prompt
        self.prompt = f"{Fore.BLUE}mcp ({example_name})> {Style.RESET_ALL}"
    
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
        
        Examples:
          run basic
          run rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi
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
        
        try:
            runner_info = self.orchestrator.run_example(
                example_name,
                simulation=simulation,
                host=host,
                port=port,
                ssh_username=ssh_username,
                ssh_key_path=ssh_key_path,
                ssl_enabled=ssl_enabled
            )
            
            self.current_runner = runner_info["id"]
            
            print(f"{Fore.GREEN}Runner started with ID: {self.current_runner}{Style.RESET_ALL}")
            print(f"Use 'status {self.current_runner}' to check status")
            
        except Exception as e:
            print(f"{Fore.RED}Failed to run example: {e}{Style.RESET_ALL}")
    
    def do_status(self, arg):
        """
        Check status of a running example.
        
        Usage: status [runner_id]
        
        If runner_id is not provided, uses the currently selected runner.
        """
        runner_id = arg.strip() if arg else self.current_runner
        
        if not runner_id:
            print(f"{Fore.RED}Please specify a runner ID or run an example first.{Style.RESET_ALL}")
            return
        
        try:
            status = self.orchestrator.get_runner_status(runner_id)
            
            print(f"\n{Fore.GREEN}Runner Status:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}ID:{Style.RESET_ALL} {runner_id}")
            print(f"  {Fore.CYAN}Example:{Style.RESET_ALL} {status.get('example', '')}")
            print(f"  {Fore.CYAN}Status:{Style.RESET_ALL} {status.get('status', '')}")
            print(f"  {Fore.CYAN}Host:{Style.RESET_ALL} {status.get('host', '')}")
            print(f"  {Fore.CYAN}Port:{Style.RESET_ALL} {status.get('port', '')}")
            print(f"  {Fore.CYAN}Simulation:{Style.RESET_ALL} {'Yes' if status.get('simulation') else 'No'}")
            
            if status.get("stdout"):
                print(f"\n{Fore.GREEN}Output:{Style.RESET_ALL}")
                print(status["stdout"])
            
            if status.get("stderr"):
                print(f"\n{Fore.RED}Errors:{Style.RESET_ALL}")
                print(status["stderr"])
                
        except Exception as e:
            print(f"{Fore.RED}Failed to get status: {e}{Style.RESET_ALL}")
    
    def do_stop(self, arg):
        """
        Stop a running example.
        
        Usage: stop [runner_id]
        
        If runner_id is not provided, uses the currently selected runner.
        """
        runner_id = arg.strip() if arg else self.current_runner
        
        if not runner_id:
            print(f"{Fore.RED}Please specify a runner ID or run an example first.{Style.RESET_ALL}")
            return
        
        try:
            success = self.orchestrator.stop_runner(runner_id)
            
            if success:
                print(f"{Fore.GREEN}Runner {runner_id} stopped successfully.{Style.RESET_ALL}")
                
                # Clear current runner if it was stopped
                if self.current_runner == runner_id:
                    self.current_runner = None
            else:
                print(f"{Fore.RED}Failed to stop runner {runner_id}.{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Failed to stop runner: {e}{Style.RESET_ALL}")
    
    def do_connect(self, arg):
        """
        Connect to a server.
        
        Usage: connect <host> <port> [--retry=<count>] [--timeout=<seconds>] [--discover]
        
        Examples:
          connect localhost 8080
          connect 192.168.1.100 9515 --retry=5 --timeout=3
          connect 192.168.1.100 9515 --discover
        """
        args = shlex.split(arg) if arg else []
        
        if len(args) < 2:
            print(f"{Fore.RED}Please specify a host and port.{Style.RESET_ALL}")
            print(f"Usage: connect <host> <port> [--retry=<count>] [--timeout=<seconds>] [--discover]")
            return
        
        host = args[0]
        
        try:
            port = int(args[1])
        except ValueError:
            print(f"{Fore.RED}Invalid port number: {args[1]}{Style.RESET_ALL}")
            return
        
        # Parse retry count and timeout from arguments
        retry_count = 3  # default retry count
        timeout = 2.0    # default timeout in seconds (smaller for faster scanning)
        use_discovery = False
        
        for arg in args[2:]:
            if arg.startswith("--retry="):
                try:
                    retry_count = int(arg.split("=")[1])
                except (ValueError, IndexError):
                    print(f"{Fore.YELLOW}Invalid retry count, using default {retry_count}{Style.RESET_ALL}")
            elif arg.startswith("--timeout="):
                try:
                    timeout = float(arg.split("=")[1])
                except (ValueError, IndexError):
                    print(f"{Fore.YELLOW}Invalid timeout value, using default {timeout}s{Style.RESET_ALL}")
            elif arg == "--discover":
                use_discovery = True
        
        print(f"Connecting to {host}:{port} ...")
        print(f"Using {retry_count} connection attempts with {timeout}s timeout...")
        
        # Check if the port is open before attempting to connect
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            print(f"{Fore.YELLOW}Warning: Initial port check indicates {host}:{port} may not be open (error code: {result}){Style.RESET_ALL}")
            if use_discovery:
                print(f"{Fore.GREEN}Port discovery enabled. Will scan for available MCP servers if connection fails.{Style.RESET_ALL}")
            else:
                print(f"Attempting connection anyway with retry logic...")
        
        try:
            if use_discovery:
                self.orchestrator.connect_to_server(host, port, retry_count=retry_count, timeout=timeout, use_discovery=True)
            else:
                self.orchestrator.connect_to_server(host, port, retry_count=retry_count, timeout=timeout)
                
            print(f"{Fore.GREEN}Connected to {host}:{port}{Style.RESET_ALL}")
            self._update_prompt()
            
        except Exception as e:
            print(f"{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
            print(f"\nTroubleshooting suggestions:")
            print(f"1. Verify the server is running on {host}")
            print(f"2. Check if port {port} is the correct port (try 'test_connection {host} {port}')")
            print(f"3. If you just started the server, it might need more time to initialize")
            print(f"4. Check for any firewall rules that might be blocking the connection")
            print(f"5. Try increasing the retry count: connect {host} {port} --retry=5 --timeout=3")
            print(f"6. Try the port discovery feature: connect {host} {port} --discover")
    
    def do_disconnect(self, arg):
        """Disconnect from the current server."""
        if not self.current_server:
            print(f"{Fore.YELLOW}Not connected to any server.{Style.RESET_ALL}")
            return
        
        try:
            client = self.current_server.get("client")
            if client:
                client.disconnect()
            
            host = self.current_server.get("host", "")
            port = self.current_server.get("port", "")
            
            print(f"{Fore.GREEN}Disconnected from {host}:{port}.{Style.RESET_ALL}")
            
            # Reset current server and prompt
            self.current_server = None
            
            # Update prompt based on current example
            if self.current_example:
                self.prompt = f"{Fore.BLUE}mcp ({self.current_example})> {Style.RESET_ALL}"
            else:
                self.prompt = f"{Fore.BLUE}mcp> {Style.RESET_ALL}"
                
        except Exception as e:
            print(f"{Fore.RED}Failed to disconnect: {e}{Style.RESET_ALL}")
    
    def do_favorite(self, arg):
        """
        Add or remove an example from favorites.
        
        Usage: favorite <example_name>
        
        If the example is already a favorite, it will be removed.
        If not, it will be added.
        """
        if not arg:
            print(f"{Fore.RED}Please specify an example name.{Style.RESET_ALL}")
            return
        
        example_name = arg.strip()
        example = self.orchestrator.get_example(example_name)
        
        if not example:
            print(f"{Fore.RED}Example '{example_name}' not found.{Style.RESET_ALL}")
            return
        
        favorites = self.orchestrator.get_favorite_examples()
        
        if example_name in favorites:
            self.orchestrator.remove_favorite_example(example_name)
            print(f"{Fore.GREEN}Removed '{example_name}' from favorites.{Style.RESET_ALL}")
        else:
            self.orchestrator.add_favorite_example(example_name)
            print(f"{Fore.GREEN}Added '{example_name}' to favorites.{Style.RESET_ALL}")
    
    def do_env(self, arg):
        """
        Create or update .env file for an example.
        
        Usage: env [example_name] [options]
        
        If example_name is not provided, uses the currently selected example.
        
        Options:
          --simulation=<bool>       Run in simulation mode (default: true)
          --host=<host>             Host to connect to (default: localhost)
          --port=<port>             Port to use (default: 8080)
          --ssh-username=<username> SSH username (default: pi)
          --ssh-key-path=<path>     Path to SSH key (default: ~/.ssh/id_rsa)
          --ssl=<bool>              Enable SSL (default: false)
        
        Examples:
          env basic
          env rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi
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
        
        ssl_enabled = options.get("ssl")
        if isinstance(ssl_enabled, str):
            ssl_enabled = ssl_enabled.lower() == "true"
        
        # Create .env file
        try:
            env_file = self.orchestrator.create_env_file(
                example_name,
                simulation=simulation,
                host=host,
                port=port,
                ssh_username=ssh_username,
                ssh_key_path=ssh_key_path,
                ssl_enabled=ssl_enabled
            )
            
            if env_file:
                print(f"{Fore.GREEN}.env file created: {env_file}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to create .env file.{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Failed to create .env file: {e}{Style.RESET_ALL}")
    
    def do_servers(self, arg):
        """
        List recent servers.
        
        Usage: servers
        """
        recent_servers = self.orchestrator.get_recent_servers()
        
        if not recent_servers:
            print(f"{Fore.YELLOW}No recent servers.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}Recent Servers:{Style.RESET_ALL}")
        
        for i, server in enumerate(recent_servers, 1):
            print(f"  {i}. {server}")
    
    def do_runners(self, arg):
        """
        List active runners.
        
        Usage: runners
        """
        runners = self.orchestrator.get_active_runners()
        
        if not runners:
            print(f"{Fore.YELLOW}No active runners.{Style.RESET_ALL}")
            return
        
        table_data = []
        for runner_id, info in runners.items():
            status = info.get("status", "unknown")
            status_color = Fore.GREEN if status == "running" else Fore.RED
            
            table_data.append([
                runner_id[:8] + "...",  # Truncate ID
                info.get("example", ""),
                f"{status_color}{status}{Style.RESET_ALL}",
                info.get("host", ""),
                info.get("port", ""),
                "Yes" if info.get("simulation") else "No"
            ])
        
        print(f"\n{Fore.GREEN}Active Runners:{Style.RESET_ALL}")
        print(tabulate(
            table_data,
            headers=["ID", "Example", "Status", "Host", "Port", "Simulation"],
            tablefmt="pretty"
        ))
    
    def do_refresh(self, arg):
        """
        Refresh the list of examples.
        
        Usage: refresh
        """
        self.orchestrator._discover_examples()
        print(f"{Fore.GREEN}Examples refreshed.{Style.RESET_ALL}")
    
    def do_gpio(self, arg):
        """
        Control GPIO pins.
        
        Usage:
          gpio setup <pin> <mode>   Setup a GPIO pin (mode: in, out)
          gpio write <pin> <value>  Write to a GPIO pin (value: 1/0, high/low, true/false, on/off)
          gpio read <pin>           Read from a GPIO pin
          
        Examples:
          gpio setup 18 out         Setup pin 18 as output
          gpio write 18 1           Set pin 18 high
          gpio write 18 high        Set pin 18 high
          gpio read 18              Read the state of pin 18
        """
        if not self.current_server:
            print(f"{Fore.RED}Not connected to a server. Use 'connect <host> <port>' first.{Style.RESET_ALL}")
            return
        
        # Check if client is available and connected
        client = self.current_server.get("client")
        if not client or not hasattr(client, "is_connected") or not client.is_connected():
            print(f"{Fore.RED}Connection to server lost. Please reconnect using 'connect <host> <port>'.{Style.RESET_ALL}")
            return
            
        args = shlex.split(arg) if arg else []
        
        if not args:
            print(f"{Fore.RED}No GPIO command specified. Use 'help gpio' for usage.{Style.RESET_ALL}")
            return
        
        command = args[0].lower()
        command_args = args[1:]
        
        if command not in ["setup", "write", "read"]:
            print(f"{Fore.RED}Unknown GPIO command: {command}. Use 'help gpio' for usage.{Style.RESET_ALL}")
            return
        
        # Check for required arguments
        if command == "setup" and len(command_args) < 2:
            print(f"{Fore.RED}Usage: {GPIO_HELP_DOCS['commands']['setup']['usage']}{Style.RESET_ALL}")
            return
        elif command == "write" and len(command_args) < 2:
            print(f"{Fore.RED}Usage: {GPIO_HELP_DOCS['commands']['write']['usage']}{Style.RESET_ALL}")
            return
        elif command == "read" and len(command_args) < 1:
            print(f"{Fore.RED}Usage: {GPIO_HELP_DOCS['commands']['read']['usage']}{Style.RESET_ALL}")
            return
        
        # Execute GPIO command
        try:
            # Run the async command in the event loop
            result = asyncio.run(self.orchestrator.handle_gpio_command(command, command_args))
            
            if "error" in result:
                print(f"{Fore.RED}Error: {result['error']}{Style.RESET_ALL}")
                
                # If connection error, update current_server status
                if "connect" in str(result['error']).lower():
                    print(f"{Fore.YELLOW}Connection to server may be lost. Try reconnecting with 'connect <host> <port>'.{Style.RESET_ALL}")
                    if self.current_server and "client" in self.current_server:
                        # Mark as disconnected
                        self.current_server["status"] = "disconnected"
                return
            
            # Display result
            if command == "setup":
                print(f"{Fore.GREEN}Pin {result.get('pin')} setup as {result.get('mode')}.{Style.RESET_ALL}")
            elif command == "write":
                value_str = "HIGH" if result.get('value') else "LOW"
                print(f"{Fore.GREEN}Pin {result.get('pin')} set to {value_str}.{Style.RESET_ALL}")
            elif command == "read":
                value_str = "HIGH" if result.get('value') else "LOW"
                print(f"{Fore.GREEN}Pin {result.get('pin')} is {value_str}.{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Failed to execute GPIO command: {e}{Style.RESET_ALL}")
            
            # If connection error, update current_server status
            if "connect" in str(e).lower():
                print(f"{Fore.YELLOW}Connection to server may be lost. Try reconnecting with 'connect <host> <port>'.{Style.RESET_ALL}")
                if self.current_server and "client" in self.current_server:
                    # Mark as disconnected
                    self.current_server["status"] = "disconnected"
    
    def help_gpio(self):
        """Detailed help for GPIO commands."""
        print(f"\n{Fore.GREEN}GPIO Commands:{Style.RESET_ALL}")
        
        # Print the long help documentation from the GPIO module
        print(GPIO_HELP_DOCS['long'])
        
        # Print detailed help for each command
        for cmd_name, cmd_info in GPIO_HELP_DOCS['commands'].items():
            print(f"\n{Fore.CYAN}{cmd_info['usage']}{Style.RESET_ALL}")
            print(f"  {cmd_info['description']}")
            
            # Print arguments
            for arg in cmd_info['args']:
                print(f"  {arg['name']}: {arg['description']}")
            
            # Print examples
            if cmd_info['examples']:
                print(f"  Examples:")
                for example in cmd_info['examples']:
                    print(f"    {example}")
    
    def do_discover_servers(self, arg):
        """
        Scan for available MCP servers on the network.
        
        Usage: discover_servers <host> [--ports=<port-range>] [--timeout=<seconds>]
        
        Examples:
          discover_servers 192.168.188.154
          discover_servers 192.168.188.154 --ports=8000-10000 --timeout=0.5
        """
        import socket
        import concurrent.futures
        import time
        
        args = shlex.split(arg) if arg else []
        
        if len(args) < 1:
            print(f"{Fore.RED}Please specify a host to scan.{Style.RESET_ALL}")
            print(f"Usage: discover_servers <host> [--ports=<port-range>] [--timeout=<seconds>]")
            return
        
        host = args[0]
        
        # Parse port range
        port_range = "8000-10000"  # default range
        for arg in args[1:]:
            if arg.startswith("--ports="):
                port_range = arg.split("=")[1]
        
        try:
            if "-" in port_range:
                start_port, end_port = map(int, port_range.split("-"))
            else:
                start_port = int(port_range)
                end_port = start_port + 100
                
            if end_port - start_port > 2000:
                print(f"{Fore.YELLOW}Warning: Large port range specified. Limiting to 2000 ports to avoid excessive scanning time.{Style.RESET_ALL}")
                end_port = start_port + 2000
        except ValueError:
            print(f"{Fore.RED}Invalid port range. Using default range 8000-10000.{Style.RESET_ALL}")
            start_port, end_port = 8000, 10000
        
        # Parse timeout
        timeout = 0.2  # default timeout in seconds (smaller for faster scanning)
        for arg in args[1:]:
            if arg.startswith("--timeout="):
                try:
                    timeout = float(arg.split("=")[1])
                except (ValueError, IndexError):
                    print(f"{Fore.YELLOW}Invalid timeout value, using default {timeout}s{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Scanning {host} for open ports in range {start_port}-{end_port} (timeout: {timeout}s)...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}This may take some time. Please wait...{Style.RESET_ALL}")
        
        start_time = time.time()
        open_ports = []
        
        # Function to check a single port
        def check_port(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return port
            return None
        
        # Use ThreadPoolExecutor for parallel port scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(check_port, port) for port in range(start_port, end_port + 1)]
            
            # Show progress
            total_ports = end_port - start_port + 1
            completed = 0
            
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                if completed % 100 == 0 or completed == total_ports:
                    progress = (completed / total_ports) * 100
                    elapsed = time.time() - start_time
                    print(f"\r{Fore.CYAN}Progress: {completed}/{total_ports} ports checked ({progress:.1f}%) - Elapsed: {elapsed:.1f}s{Style.RESET_ALL}", end="")
                
                port = future.result()
                if port is not None:
                    open_ports.append(port)
                    print(f"\n{Fore.GREEN}Found open port: {port}{Style.RESET_ALL}")
        
        print("\n")
        elapsed = time.time() - start_time
        
        if open_ports:
            print(f"{Fore.GREEN}Scan complete in {elapsed:.1f}s. Found {len(open_ports)} open ports on {host}:{Style.RESET_ALL}")
            
            # Sort open ports
            open_ports.sort()
            
            # Group ports for display
            groups = []
            current_group = [open_ports[0]]
            
            for i in range(1, len(open_ports)):
                if open_ports[i] == open_ports[i-1] + 1:
                    current_group.append(open_ports[i])
                else:
                    groups.append(current_group)
                    current_group = [open_ports[i]]
            
            groups.append(current_group)
            
            # Display grouped ports
            for group in groups:
                if len(group) == 1:
                    print(f"  {Fore.CYAN}Port {group[0]}{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.CYAN}Ports {group[0]}-{group[-1]} ({len(group)} ports){Style.RESET_ALL}")
            
            print(f"\n{Fore.GREEN}Try connecting to one of these ports:{Style.RESET_ALL}")
            for port in open_ports:
                print(f"  connect {host} {port}")
        else:
            print(f"{Fore.YELLOW}Scan complete in {elapsed:.1f}s. No open ports found on {host} in range {start_port}-{end_port}.{Style.RESET_ALL}")
            print(f"Please check that the server is running and accessible.")
            print(f"You can try scanning a different port range: discover_servers {host} --ports=1000-8000")
    
    def do_test_connection(self, arg):
        """
        Test connectivity to a server with detailed diagnostics.
        
        Usage: test_connection <host> <port> [--timeout=<seconds>]
        
        Examples:
          test_connection localhost 8080
          test_connection 192.168.1.100 9515 --timeout=5
        """
        import socket
        import subprocess
        import platform
        
        args = shlex.split(arg) if arg else []
        
        if len(args) < 2:
            print(f"{Fore.RED}Please specify host and port.{Style.RESET_ALL}")
            print(f"Usage: test_connection <host> <port> [--timeout=<seconds>]")
            return
        
        host = args[0]
        
        try:
            port = int(args[1])
        except ValueError:
            print(f"{Fore.RED}Port must be a number.{Style.RESET_ALL}")
            return
        
        # Parse timeout option
        timeout = 2  # default timeout in seconds
        for arg in args[2:]:
            if arg.startswith("--timeout="):
                try:
                    timeout = float(arg.split("=")[1])
                except (ValueError, IndexError):
                    print(f"{Fore.YELLOW}Invalid timeout value, using default {timeout}s{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Testing connectivity to {host}:{port}...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Step 1: Checking if host is reachable{Style.RESET_ALL}")
        
        # Try to ping the host
        ping_param = "-n" if platform.system().lower() == "windows" else "-c"
        ping_cmd = ["ping", ping_param, "4", host]
        try:
            print(f"Running: {' '.join(ping_cmd)}")
            ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=timeout*2)
            if ping_result.returncode == 0:
                print(f"{Fore.GREEN}Host {host} is reachable (ping successful){Style.RESET_ALL}")
                print(f"Ping statistics: {ping_result.stdout.splitlines()[-2:]}")
            else:
                print(f"{Fore.YELLOW}Warning: Host {host} did not respond to ping{Style.RESET_ALL}")
                print(f"This might be normal if the host blocks ICMP packets")
                print(f"Error: {ping_result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"{Fore.YELLOW}Warning: Ping to {host} timed out{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not ping {host}: {e}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Step 2: Checking DNS resolution{Style.RESET_ALL}")
        try:
            print(f"Resolving {host}...")
            addr_info = socket.getaddrinfo(host, port, family=socket.AF_INET)
            resolved_ip = addr_info[0][4][0]
            print(f"{Fore.GREEN}Successfully resolved {host} to IP: {resolved_ip}{Style.RESET_ALL}")
        except socket.gaierror as e:
            print(f"{Fore.RED}Failed to resolve hostname {host}: {e}{Style.RESET_ALL}")
            if not all(c.isdigit() or c == '.' for c in host):
                print(f"{Fore.YELLOW}This appears to be a hostname that cannot be resolved.{Style.RESET_ALL}")
                print(f"Please check if the hostname is correct or try using an IP address directly.")
        
        print(f"\n{Fore.CYAN}Step 3: Testing TCP connection to port {port}{Style.RESET_ALL}")
        try:
            print(f"Attempting to connect to {host}:{port} (timeout: {timeout}s)...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"{Fore.GREEN}Success! Port {port} on {host} is open and accepting connections{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to connect to {host}:{port} (error code: {result}){Style.RESET_ALL}")
                
                # Provide more specific error information
                if result == 111:  # Connection refused
                    print(f"{Fore.YELLOW}Error 111: Connection refused{Style.RESET_ALL}")
                    print(f"This typically means the server is not running or is not listening on port {port}.")
                    print(f"Please check that:")
                    print(f"1. The server application is running on {host}")
                    print(f"2. The server is configured to listen on port {port}")
                    print(f"3. There are no firewall rules blocking the connection")
                elif result == 110:  # Connection timed out
                    print(f"{Fore.YELLOW}Error 110: Connection timed out{Style.RESET_ALL}")
                    print(f"This typically means the host is unreachable or a firewall is blocking the connection.")
                elif result == 113:  # No route to host
                    print(f"{Fore.YELLOW}Error 113: No route to host{Style.RESET_ALL}")
                    print(f"This typically means there's a network routing issue reaching {host}.")
                else:
                    print(f"{Fore.YELLOW}Socket error code {result}{Style.RESET_ALL}")
                    print(f"Please check your network connection and server configuration.")
        except Exception as e:
            print(f"{Fore.RED}Error testing connection: {e}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Step 4: Checking for common issues{Style.RESET_ALL}")
        
        # Check if localhost but trying to connect to a non-local IP
        if host in ["localhost", "127.0.0.1"] and port != 8080:
            print(f"{Fore.YELLOW}Note: You're connecting to localhost but using a non-standard port ({port}).{Style.RESET_ALL}")
            print(f"Make sure the server is actually configured to listen on this port.")
        
        # Check if trying to connect to a common remote port but server might be on a different port
        if port in [80, 443, 8080, 8888] and result != 0:
            print(f"{Fore.YELLOW}Note: Port {port} is a common port, but the server might be using a different port.{Style.RESET_ALL}")
            print(f"Double-check the port number in your server configuration.")
        
        print(f"\n{Fore.GREEN}Connection diagnostics complete.{Style.RESET_ALL}")
    
    def do_server_status(self, arg):
        """
        Check if the MCP server is running and which ports are open.
        
        Usage: server_status <host> [--ports=<port-list>] [--timeout=<seconds>]
        
        Examples:
          server_status 192.168.188.154
          server_status 192.168.188.154 --ports=8000,9515,9517,9518
        """
        import socket
        import subprocess
        import shlex
        import time
        
        args = shlex.split(arg) if arg else []
        
        if len(args) < 1:
            print(f"{Fore.RED}Please specify a host to check.{Style.RESET_ALL}")
            print(f"Usage: server_status <host> [--ports=<port-list>] [--timeout=<seconds>]")
            return
        
        host = args[0]
        
        # Parse ports to check
        ports_to_check = [8000, 8080, 9515, 9517, 9518]  # Default ports to check
        for arg in args[1:]:
            if arg.startswith("--ports="):
                try:
                    ports_str = arg.split("=")[1]
                    if "," in ports_str:
                        ports_to_check = [int(p) for p in ports_str.split(",")]
                    else:
                        ports_to_check = [int(ports_str)]
                except (ValueError, IndexError):
                    print(f"{Fore.YELLOW}Invalid port list, using default ports{Style.RESET_ALL}")
        
        # Parse timeout
        timeout = 1.0  # default timeout in seconds
        for arg in args[1:]:
            if arg.startswith("--timeout="):
                try:
                    timeout = float(arg.split("=")[1])
                except (ValueError, IndexError):
                    print(f"{Fore.YELLOW}Invalid timeout value, using default {timeout}s{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Checking server status for {host}...{Style.RESET_ALL}")
        
        # Step 1: Check if host is reachable
        print(f"\n{Fore.CYAN}Step 1: Checking if host is reachable{Style.RESET_ALL}")
        try:
            # Use subprocess to run ping command
            ping_cmd = f"ping -c 2 -W 2 {host}"
            print(f"Running: {ping_cmd}")
            
            result = subprocess.run(
                ping_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"{Fore.GREEN}Host {host} is reachable (ping successful){Style.RESET_ALL}")
                # Extract ping statistics
                stats_lines = [line for line in result.stdout.splitlines() if "packets transmitted" in line or "min/avg/max" in line]
                for line in stats_lines:
                    print(f"Ping statistics: {line}")
            else:
                print(f"{Fore.RED}Host {host} is not responding to ping{Style.RESET_ALL}")
                print(f"Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"{Fore.RED}Ping command timed out{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error checking host reachability: {e}{Style.RESET_ALL}")
        
        # Step 2: Check for open ports
        print(f"\n{Fore.CYAN}Step 2: Checking for open ports{Style.RESET_ALL}")
        print(f"Checking ports: {', '.join(map(str, ports_to_check))}")
        
        open_ports = []
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            print(f"Checking port {port}... ", end="", flush=True)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"{Fore.GREEN}OPEN{Style.RESET_ALL}")
                open_ports.append(port)
            else:
                print(f"{Fore.RED}CLOSED (error code: {result}){Style.RESET_ALL}")
        
        # Step 3: Check for running MCP server processes on the host
        print(f"\n{Fore.CYAN}Step 3: Checking for running MCP server processes{Style.RESET_ALL}")
        try:
            # This would typically require SSH access to the remote host
            print(f"{Fore.YELLOW}Note: This check requires SSH access to the remote host.{Style.RESET_ALL}")
            print(f"To check for running MCP server processes on {host}, you would need to:")
            print(f"1. SSH into the host: ssh user@{host}")
            print(f"2. Run: ps aux | grep -i mcp")
            print(f"3. Look for processes listening on ports: netstat -tuln | grep -E ':{','.join(map(str, ports_to_check))}'")
        except Exception as e:
            print(f"{Fore.RED}Error checking for running processes: {e}{Style.RESET_ALL}")
        
        # Summary
        print(f"\n{Fore.GREEN}Server Status Summary for {host}:{Style.RESET_ALL}")
        if open_ports:
            print(f"{Fore.GREEN}Found {len(open_ports)} open ports:{Style.RESET_ALL}")
            for port in open_ports:
                print(f"  - Port {port} is OPEN")
            
            print(f"\n{Fore.GREEN}Try connecting to one of these ports:{Style.RESET_ALL}")
            for port in open_ports:
                print(f"  connect {host} {port}")
        else:
            print(f"{Fore.YELLOW}No open ports found on {host} from the checked list.{Style.RESET_ALL}")
            print(f"This could mean:")
            print(f"1. The server is not running")
            print(f"2. The server is running on a different port")
            print(f"3. A firewall is blocking the connections")
            print(f"\nTry scanning for all open ports with: discover_servers {host}")
    
    def do_start_remote_server(self, arg):
        """
        Start the MCP server on a remote Raspberry Pi via SSH.
        
        Usage: start_remote_server <host> [--port=<port>] [--ssh-username=<username>] [--ssh-key-path=<path>] [--simulation] [--verbose]
        
        Examples:
          start_remote_server 192.168.188.154
          start_remote_server 192.168.188.154 --port=8080 --ssh-username=pi
        """
        import asyncio
        import shlex
        import sys
        from pathlib import Path
        
        # Import the RPiServerStarter
        try:
            from unitmcp.runner.rpi_server_starter import RPiServerStarter
        except ImportError:
            print(f"{Fore.RED}RPiServerStarter not found. Make sure you have the latest version of UnitMCP.{Style.RESET_ALL}")
            return
        
        args = shlex.split(arg) if arg else []
        
        if len(args) < 1:
            print(f"{Fore.RED}Please specify a host to connect to.{Style.RESET_ALL}")
            print(f"Usage: start_remote_server <host> [--port=<port>] [--ssh-username=<username>] [--ssh-key-path=<path>] [--simulation] [--verbose]")
            return
        
        host = args[0]
        
        # Default configuration
        config = {
            "host": host,
            "port": 8080,
            "ssh_username": "pi",
            "ssh_password": None,
            "ssh_key_path": None,
            "server_path": "~/UnitApi/mcp",
            "simulation": False,
            "verbose": False
        }
        
        # Parse arguments
        for arg in args[1:]:
            if arg.startswith("--port="):
                try:
                    config["port"] = int(arg.split("=")[1])
                except (ValueError, IndexError):
                    print(f"{Fore.YELLOW}Invalid port, using default port 8080{Style.RESET_ALL}")
            elif arg.startswith("--ssh-username="):
                config["ssh_username"] = arg.split("=")[1]
            elif arg.startswith("--ssh-key-path="):
                config["ssh_key_path"] = arg.split("=")[1]
            elif arg == "--simulation":
                config["simulation"] = True
            elif arg == "--verbose":
                config["verbose"] = True
        
        print(f"{Fore.CYAN}Starting MCP server on {host}:{config['port']} via SSH...{Style.RESET_ALL}")
        
        # Create and run the RPiServerStarter in a separate thread to avoid blocking the shell
        async def start_server():
            starter = RPiServerStarter(config)
            
            # Initialize
            if not await starter.initialize():
                print(f"{Fore.RED}Failed to initialize RPiServerStarter{Style.RESET_ALL}")
                return
            
            # Start the server
            if not await starter.start_server():
                print(f"{Fore.RED}Failed to start MCP server{Style.RESET_ALL}")
                return
            
            print(f"{Fore.GREEN}MCP server started successfully on {host}:{config['port']}{Style.RESET_ALL}")
            print(f"You can now connect to the server using: connect {host} {config['port']}")
        
        # Run the async function in a separate thread
        import threading
        def run_async_in_thread():
            asyncio.run(start_server())
        
        thread = threading.Thread(target=run_async_in_thread)
        thread.daemon = True  # This ensures the thread will exit when the main program exits
        thread.start()
    
    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            # Show help for specific command
            try:
                func = getattr(self, 'help_' + arg)
                func()
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        print(doc)
                    else:
                        print(f"{Fore.RED}No help available for {arg}{Style.RESET_ALL}")
                except AttributeError:
                    print(f"{Fore.RED}Unknown command: {arg}{Style.RESET_ALL}")
        else:
            # Show general help
            print(f"\n{Fore.GREEN}UnitMCP Orchestrator Shell{Style.RESET_ALL}")
            print(f"Type 'help <command>' for detailed help on a command.\n")
            
            commands = [
                ("list [category]", "List available examples"),
                ("info <example>", "Show detailed information about an example"),
                ("select <example>", "Select an example as the current working example"),
                ("run [example] [options]", "Run an example"),
                ("status [runner_id]", "Check status of a running example"),
                ("stop [runner_id]", "Stop a running example"),
                ("connect <host> <port>", "Connect to a server"),
                ("test_connection <host> <port>", "Test connectivity to a server with detailed diagnostics"),
                ("server_status <host>", "Check if the MCP server is running and which ports are open"),
                ("disconnect", "Disconnect from the current server"),
                ("servers", "List recent servers"),
                ("runners", "List active runners"),
                ("refresh", "Refresh the list of examples"),
                ("gpio <command>", "Control GPIO pins"),
                ("discover_servers <host>", "Scan for available MCP servers on the network"),
                ("start_remote_server <host>", "Start the MCP server on a remote Raspberry Pi via SSH"),
                ("help [command]", "Show help for a specific command"),
                ("exit, quit", "Exit the shell")
            ]
            
            for cmd, desc in commands:
                print(f"  {Fore.CYAN}{cmd.ljust(25)}{Style.RESET_ALL}{desc}")
            
            print("\nFor detailed help on a specific command, type 'help <command>'")
    
def main():
    """Main entry point for the orchestrator shell."""
    parser = argparse.ArgumentParser(description="UnitMCP Orchestrator Shell")
    parser.add_argument("--examples-dir", help="Path to examples directory")
    parser.add_argument("--config-file", help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Set the logging level")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create orchestrator
    orchestrator = Orchestrator(
        examples_dir=args.examples_dir,
        config_file=args.config_file
    )
    
    # Create and start shell
    shell = OrchestratorShell(orchestrator)
    
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Error in shell: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
