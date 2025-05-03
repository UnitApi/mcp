"""Interactive shell for the UnitMCP Orchestrator."""

import os
import sys
import cmd
import time
import logging
import argparse
import shlex
from typing import Dict, List, Optional, Any, Tuple
from tabulate import tabulate
from colorama import Fore, Style, init

from .orchestrator import Orchestrator

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
          all       - List all examples (default)
          recent    - List recently used examples
          favorite  - List favorite examples
          running   - List running examples
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
            
        else:
            print(f"{Fore.RED}Unknown category: {category}{Style.RESET_ALL}")
            print(f"Use one of: all, recent, favorite, running")
    
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
            connection_info = self.orchestrator.connect_to_server(host, port, ssl_enabled)
            
            if connection_info["status"] == "connected":
                print(f"{Fore.GREEN}Connected successfully!{Style.RESET_ALL}")
                self.current_server = connection_info
                
                # Update prompt
                self.prompt = f"{Fore.BLUE}mcp ({host}:{port})> {Style.RESET_ALL}"
            else:
                print(f"{Fore.RED}Connection failed: {connection_info.get('error', 'Unknown error')}{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
    
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
        print(f"{Fore.GREEN}Examples refreshed. Found {len(self.orchestrator.examples)} examples.{Style.RESET_ALL}")
    
    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help
            print(f"\n{Fore.GREEN}Available Commands:{Style.RESET_ALL}")
            
            commands = [
                ("list [category]", "List available examples (categories: all, recent, favorite, running)"),
                ("info <example>", "Show detailed information about an example"),
                ("select <example>", "Select an example as the current working example"),
                ("run [example] [options]", "Run an example"),
                ("status [runner_id]", "Check status of a running example"),
                ("stop [runner_id]", "Stop a running example"),
                ("connect <host> <port> [--ssl]", "Connect to a server"),
                ("disconnect", "Disconnect from the current server"),
                ("favorite <example>", "Add or remove an example from favorites"),
                ("env [example] [options]", "Create or update .env file for an example"),
                ("servers", "List recent servers"),
                ("runners", "List active runners"),
                ("refresh", "Refresh the list of examples"),
                ("help [command]", "Show help for a specific command"),
                ("exit, quit", "Exit the shell")
            ]
            
            for cmd, desc in commands:
                print(f"  {Fore.CYAN}{cmd.ljust(30)}{Style.RESET_ALL} {desc}")
            
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
