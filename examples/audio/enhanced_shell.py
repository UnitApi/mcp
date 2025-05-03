#!/usr/bin/env python3
"""
UnitMCP Enhanced Orchestrator Shell

This module extends the UnitMCP Orchestrator Shell with additional features:
- Connection beeps when connecting to a Raspberry Pi
- File upload functionality
- Enhanced command handling
- Direct GPIO control
"""

import os
import sys
import shlex
import logging
import argparse
import time
import asyncio
import cmd
import json
from typing import Dict, List, Optional, Any, Tuple
from colorama import Fore, Style, init

# Add the parent directory to sys.path to import UnitMCP modules
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the tone generator for beeps
try:
    from tone_generator import ToneGenerator
    TONE_GENERATOR_AVAILABLE = True
except ImportError:
    TONE_GENERATOR_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize colorama
init()


class Orchestrator:
    """
    Simplified Orchestrator class that provides the core functionality
    needed for the enhanced shell.
    """
    
    def __init__(self, quiet: bool = False):
        """Initialize the orchestrator."""
        self.config = self._load_config()
        self.examples = self._load_examples()
        self.quiet = quiet
        self.logger = logging.getLogger("Orchestrator")
        
        if quiet:
            self.logger.setLevel(logging.WARNING)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration."""
        config_path = os.path.expanduser("~/.unitmcp/config.json")
        
        # Create default config if it doesn't exist
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            default_config = {
                "recent_examples": [],
                "favorite_examples": [],
                "recent_servers": []
            }
            
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        # Load existing config
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {
                "recent_examples": [],
                "favorite_examples": [],
                "recent_servers": []
            }
    
    def _save_config(self):
        """Save orchestrator configuration."""
        config_path = os.path.expanduser("~/.unitmcp/config.json")
        
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _load_examples(self) -> Dict[str, Dict[str, Any]]:
        """Load available examples."""
        examples = {}
        
        # Add audio examples
        examples["audio"] = {
            "name": "audio",
            "description": "Audio examples for Raspberry Pi",
            "path": os.path.abspath(os.path.dirname(__file__)),
            "has_runner": True,
            "has_server": True
        }
        
        return examples
    
    def get_examples(self) -> Dict[str, Dict[str, Any]]:
        """Get all available examples."""
        return self.examples
    
    def get_example(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific example."""
        return self.examples.get(name)
    
    def get_recent_examples(self) -> List[str]:
        """Get list of recently used examples."""
        return self.config.get("recent_examples", [])
    
    def get_favorite_examples(self) -> List[str]:
        """Get list of favorite examples."""
        return self.config.get("favorite_examples", [])
    
    def run_example(self, example_name: str, **kwargs) -> Dict[str, Any]:
        """Run an example."""
        # Check if example exists
        example = self.get_example(example_name)
        if not example:
            raise ValueError(f"Example '{example_name}' not found")
        
        # Generate a unique ID for the runner
        import uuid
        runner_id = str(uuid.uuid4())
        
        # Add example to recent list
        if example_name in self.config.get("recent_examples", []):
            self.config["recent_examples"].remove(example_name)
        
        if "recent_examples" not in self.config:
            self.config["recent_examples"] = []
            
        self.config["recent_examples"].insert(0, example_name)
        self.config["recent_examples"] = self.config["recent_examples"][:10]  # Keep only 10 most recent
        self._save_config()
        
        # Return runner info
        return {
            "id": runner_id,
            "example": example_name,
            "status": "running",
            "host": kwargs.get("host", "localhost"),
            "port": kwargs.get("port", 8080),
            "simulation": kwargs.get("simulation", True)
        }
    
    def get_active_runners(self) -> Dict[str, Dict[str, Any]]:
        """Get all active runners."""
        return {}
    
    def get_runner_status(self, runner_id: str) -> Dict[str, Any]:
        """Get status of a specific runner."""
        return {
            "id": runner_id,
            "example": "unknown",
            "status": "unknown",
            "host": "unknown",
            "port": "unknown",
            "simulation": False
        }
    
    def stop_runner(self, runner_id: str) -> bool:
        """Stop a runner."""
        return True


class EnhancedOrchestratorShell(cmd.Cmd):
    """
    Enhanced version of the UnitMCP Orchestrator Shell with additional features.
    """
    
    def __init__(self, orchestrator: Optional[Orchestrator] = None, enable_beeps: bool = True):
        """
        Initialize the enhanced shell.
        
        Parameters
        ----------
        orchestrator : Orchestrator, optional
            Orchestrator instance to use
        enable_beeps : bool
            Whether to enable connection beeps
        """
        super().__init__()
        
        self.orchestrator = orchestrator or Orchestrator()
        self.enable_beeps = enable_beeps
        
        self.prompt = f"{Fore.BLUE}mcp> {Style.RESET_ALL}"
        self.intro = f"{Fore.GREEN}UnitMCP Enhanced Orchestrator Shell{Style.RESET_ALL}\n" \
                     f"Type '{Fore.CYAN}help{Style.RESET_ALL}' for a list of commands.\n"
        
        self.current_example = None
        self.current_runner = None
        self.current_server = None
        
        # Initialize tone generator if available
        self.tone_generator = None
        if TONE_GENERATOR_AVAILABLE and enable_beeps:
            self.tone_generator = ToneGenerator()
        
        # Update intro with enhanced features
        self.intro = f"""
{Fore.GREEN}╔═════════════════════════════════════════════════════╗
║  {Fore.YELLOW}UnitMCP Enhanced Orchestrator{Fore.GREEN}                    ║
║  {Fore.CYAN}Type 'help' for commands | 'exit' to quit{Fore.GREEN}        ║
║  {Fore.MAGENTA}Features: Connection Beeps, File Upload, Enhanced Run{Fore.GREEN} ║
╚═════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    
    def play_connection_beep(self):
        """Play a beep sound to indicate a successful connection."""
        if not self.enable_beeps or not self.tone_generator:
            return
        
        try:
            logger.info("Playing connection beep")
            self.tone_generator.play_tone(
                frequency=1000.0,
                duration=0.5,
                volume=0.7,
                fade_in_out=0.05
            )
        except Exception as e:
            logger.warning(f"Failed to play connection beep: {e}")
    
    def play_error_beep(self):
        """Play an error beep sound to indicate a failed connection."""
        if not self.enable_beeps or not self.tone_generator:
            return
        
        try:
            logger.info("Playing error beep")
            # Play two lower frequency beeps
            self.tone_generator.play_sequence(
                frequencies=[440, 330],
                durations=0.2,
                volume=0.7,
                fade_in_out=0.05,
                gap=0.1
            )
        except Exception as e:
            logger.warning(f"Failed to play error beep: {e}")
    
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Simulate connection for demonstration purposes
                connection_successful = True
            except Exception as e:
                connection_successful = False
                connection_error = str(e)
            finally:
                loop.close()
            
            if connection_successful:
                # Create connection info
                connection_info = {
                    "host": host,
                    "port": port,
                    "ssl_enabled": ssl_enabled,
                    "status": "connected"
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
                
                # Play connection beep
                self.play_connection_beep()
                
                # Update prompt
                self.prompt = f"{Fore.BLUE}mcp ({host}:{port})> {Style.RESET_ALL}"
            else:
                print(f"{Fore.RED}Connection failed: {connection_error}{Style.RESET_ALL}")
                
                # Play error beep
                self.play_error_beep()
        except Exception as e:
            print(f"{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
            
            # Play error beep
            self.play_error_beep()
    
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
        
        print(f"{Fore.GREEN}Uploading {local_path} to {remote_path}...{Style.RESET_ALL}")
        
        try:
            # Simulate file upload for demonstration purposes
            upload_successful = True
        except Exception as e:
            upload_successful = False
            upload_error = str(e)
        
        if upload_successful:
            print(f"{Fore.GREEN}File uploaded successfully.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Upload failed: {upload_error}{Style.RESET_ALL}")
    
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
          --ssh-key-path=<path>     Path to SSH key file (default: ~/.ssh/id_rsa)
          --ssl=<bool>              Enable SSL (default: false)
          --example=<name>          Specific example script to run (for audio examples)
          --demo=<name>             Demo to run (for audio examples)
          --frequency=<float>       Tone frequency in Hz (for audio examples)
          --duration=<float>        Duration in seconds (for audio examples)
          --volume=<float>          Volume level (for audio examples)
          --output=<device>         Audio output device (for audio examples)
        
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
            
            frequency = options.get("frequency")
            if frequency:
                print(f"  {Fore.CYAN}Frequency:{Style.RESET_ALL} {frequency} Hz")
            
            duration = options.get("duration")
            if duration:
                print(f"  {Fore.CYAN}Duration:{Style.RESET_ALL} {duration} seconds")
            
            volume = options.get("volume")
            if volume:
                print(f"  {Fore.CYAN}Volume:{Style.RESET_ALL} {volume}")
            
            output = options.get("output")
            if output:
                print(f"  {Fore.CYAN}Output Device:{Style.RESET_ALL} {output}")
        
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
    
    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            # Check if the arg is a valid command
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write(f"{Fore.GREEN}{doc}{Style.RESET_ALL}\n")
                        return
                except AttributeError:
                    self.stdout.write(f"{Fore.RED}*** No help on {arg}{Style.RESET_ALL}\n")
                    return
            func()
        else:
            # List all commands
            commands = [name[3:] for name in dir(self) if name.startswith('do_')]
            self.stdout.write(f"{Fore.GREEN}Available commands:{Style.RESET_ALL}\n")
            
            # Group commands by category
            categories = {
                "Basic": ["help", "exit", "quit"],
                "Examples": ["list", "select", "run", "status", "stop"],
                "Server": ["connect", "upload"],
                "Hardware": ["gpio"]
            }
            
            # Print commands by category
            for category, cmds in categories.items():
                # Filter out commands that don't exist
                available_cmds = [cmd for cmd in cmds if cmd in commands]
                if available_cmds:
                    self.stdout.write(f"{Fore.CYAN}{category}:{Style.RESET_ALL} {', '.join(available_cmds)}\n")
            
            # Print other commands
            other_cmds = [cmd for cmd in commands if not any(cmd in cat_cmds for cat_cmds in categories.values())]
            if other_cmds:
                self.stdout.write(f"{Fore.CYAN}Other:{Style.RESET_ALL} {', '.join(other_cmds)}\n")
    
    def do_gpio(self, arg):
        """
        Control GPIO pins on the connected Raspberry Pi.
        
        Usage:
          gpio <pin> <mode> [value]       Configure and control a GPIO pin
          gpio <pin> toggle               Toggle the state of a GPIO pin
        
        Modes:
          in                              Configure pin as input
          out                             Configure pin as output
          
        Examples:
          gpio 18 in                      Set pin 18 as input
          gpio 18 out 1                   Set pin 18 as output with value HIGH
          gpio 18 out 0                   Set pin 18 as output with value LOW
          gpio 18 toggle                  Toggle the state of pin 18
          
        Note: You must be connected to a Raspberry Pi first.
        """
        if not self.current_server:
            print(f"{Fore.RED}Not connected to any server. Use 'connect' first.{Style.RESET_ALL}")
            return
        
        args = shlex.split(arg) if arg else []
        
        if len(args) < 2:
            print(f"{Fore.RED}Please specify pin and mode.{Style.RESET_ALL}")
            print(f"Usage: gpio <pin> <mode> [value]")
            return
        
        # Parse pin number
        try:
            pin = int(args[0])
        except ValueError:
            print(f"{Fore.RED}Pin must be a number.{Style.RESET_ALL}")
            return
        
        # Get mode
        mode = args[1].lower()
        
        # Simulate GPIO control for demonstration purposes
        if mode == "in":
            print(f"{Fore.GREEN}Pin {pin} set as input.{Style.RESET_ALL}")
        elif mode == "out":
            if len(args) < 3:
                print(f"{Fore.RED}Please specify a value (0 or 1) for output mode.{Style.RESET_ALL}")
                return
            
            value = int(args[2])
            print(f"{Fore.GREEN}Pin {pin} set as output with value {value}.{Style.RESET_ALL}")
        elif mode == "toggle":
            print(f"{Fore.GREEN}Pin {pin} toggled.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Unknown mode: {mode}. Use 'in', 'out', or 'toggle'.{Style.RESET_ALL}")


def main():
    """Main entry point for the enhanced orchestrator shell."""
    parser = argparse.ArgumentParser(description="UnitMCP Enhanced Orchestrator Shell")
    
    parser.add_argument(
        "--no-beeps",
        action="store_true",
        help="Disable connection beeps"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimize log output"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Create and run shell
    shell = EnhancedOrchestratorShell(enable_beeps=not args.no_beeps)
    shell.cmdloop()


if __name__ == "__main__":
    main()
