"""
shell.py
"""

"""Interactive shell client for MCP hardware control."""

import asyncio
import cmd
import json
import shlex
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

from .client import MCPHardwareClient
from ..utils.logger import get_logger


class MCPShell(cmd.Cmd):
    """Interactive shell for MCP hardware control."""

    intro = "MCP Hardware Shell - Type 'help' for commands, 'exit' to quit"
    prompt = "mcp> "

    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        super().__init__()
        self.client = MCPHardwareClient(host, port)
        self.logger = get_logger("MCPShell")
        self.connected = False
        self.loop = asyncio.get_event_loop()
        self.pipelines: Dict[str, List[Dict[str, Any]]] = {}
        self.variables: Dict[str, Any] = {}
        self.last_result = None

    def preloop(self):
        """Connect to server before starting shell."""
        try:
            self.loop.run_until_complete(self.client.connect())
            self.connected = True
            print("Connected to MCP server")
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False

    def postloop(self):
        """Disconnect when exiting shell."""
        if self.connected:
            self.loop.run_until_complete(self.client.disconnect())
            print("Disconnected from MCP server")

    def do_exit(self, arg):
        """Exit the shell."""
        return True

    def do_quit(self, arg):
        """Exit the shell."""
        return True

    def do_connect(self, arg):
        """Connect to MCP server: connect [host] [port]"""
        parts = shlex.split(arg)
        host = parts[0] if len(parts) > 0 else "127.0.0.1"
        port = int(parts[1]) if len(parts) > 1 else 8888

        try:
            self.client = MCPHardwareClient(host, port)
            self.loop.run_until_complete(self.client.connect())
            self.connected = True
            print(f"Connected to {host}:{port}")
        except Exception as e:
            print(f"Connection failed: {e}")

    def do_disconnect(self, arg):
        """Disconnect from MCP server."""
        if self.connected:
            self.loop.run_until_complete(self.client.disconnect())
            self.connected = False
            print("Disconnected")
        else:
            print("Not connected")

    def do_status(self, arg):
        """Show connection status."""
        if self.connected:
            print(f"Connected to {self.client.host}:{self.client.port}")
            print(f"Client ID: {self.client.client_id}")
        else:
            print("Not connected")

    # GPIO Commands
    def do_gpio_setup(self, arg):
        """Setup GPIO pin: gpio_setup <pin> [mode]"""
        parts = shlex.split(arg)
        if len(parts) < 1:
            print("Usage: gpio_setup <pin> [mode]")
            return

        pin = int(parts[0])
        mode = parts[1] if len(parts) > 1 else "OUT"

        try:
            result = self.loop.run_until_complete(self.client.setup_pin(pin, mode))
            self.last_result = result
            print(f"Pin {pin} configured as {mode}")
        except Exception as e:
            print(f"Error: {e}")

    def do_gpio_write(self, arg):
        """Write to GPIO pin: gpio_write <pin> <value>"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: gpio_write <pin> <value>")
            return

        pin = int(parts[0])
        value = parts[1].lower() in ["1", "true", "high"]

        try:
            result = self.loop.run_until_complete(self.client.write_pin(pin, value))
            self.last_result = result
            print(f"Pin {pin} set to {value}")
        except Exception as e:
            print(f"Error: {e}")

    def do_gpio_read(self, arg):
        """Read GPIO pin: gpio_read <pin>"""
        parts = shlex.split(arg)
        if len(parts) < 1:
            print("Usage: gpio_read <pin>")
            return

        pin = int(parts[0])

        try:
            result = self.loop.run_until_complete(self.client.read_pin(pin))
            self.last_result = result
            print(f"Pin {pin} value: {result.get('value')}")
        except Exception as e:
            print(f"Error: {e}")

    def do_led_setup(self, arg):
        """Setup LED: led_setup <device_id> <pin>"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: led_setup <device_id> <pin>")
            return

        device_id = parts[0]
        pin = int(parts[1])

        try:
            result = self.loop.run_until_complete(self.client.setup_led(device_id, pin))
            self.last_result = result
            print(f"LED {device_id} setup on pin {pin}")
        except Exception as e:
            print(f"Error: {e}")

    def do_led(self, arg):
        """Control LED: led <device_id> <action> [params]"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: led <device_id> <action> [params]")
            return

        device_id = parts[0]
        action = parts[1]
        params = {}

        # Parse additional parameters
        for i in range(2, len(parts), 2):
            if i + 1 < len(parts):
                params[parts[i]] = float(parts[i + 1])

        try:
            result = self.loop.run_until_complete(
                self.client.control_led(device_id, action, **params)
            )
            self.last_result = result
            print(f"LED {device_id} {action}")
        except Exception as e:
            print(f"Error: {e}")

    # Input Commands
    def do_type(self, arg):
        """Type text: type <text>"""
        if not arg:
            print("Usage: type <text>")
            return

        try:
            result = self.loop.run_until_complete(self.client.type_text(arg))
            self.last_result = result
            print(f"Typed: {arg}")
        except Exception as e:
            print(f"Error: {e}")

    def do_move(self, arg):
        """Move mouse: move <x> <y> [relative]"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: move <x> <y> [relative]")
            return

        x = int(parts[0])
        y = int(parts[1])
        relative = len(parts) > 2 and parts[2].lower() == "relative"

        try:
            result = self.loop.run_until_complete(
                self.client.move_mouse(x, y, relative=relative)
            )
            self.last_result = result
            print(f"Moved to ({x}, {y}){' relative' if relative else ''}")
        except Exception as e:
            print(f"Error: {e}")

    def do_click(self, arg):
        """Click mouse: click [button] [x] [y]"""
        parts = shlex.split(arg)
        button = parts[0] if len(parts) > 0 else "left"
        x = int(parts[1]) if len(parts) > 1 else None
        y = int(parts[2]) if len(parts) > 2 else None

        try:
            result = self.loop.run_until_complete(self.client.click(button, x=x, y=y))
            self.last_result = result
            print(f"Clicked {button}")
        except Exception as e:
            print(f"Error: {e}")

    def do_screenshot(self, arg):
        """Take screenshot: screenshot [region]"""
        parts = shlex.split(arg)
        region = None
        if len(parts) >= 4:
            region = tuple(map(int, parts[:4]))

        try:
            result = self.loop.run_until_complete(self.client.screenshot(region=region))
            self.last_result = result
            print(f"Screenshot taken")
        except Exception as e:
            print(f"Error: {e}")

    # Pipeline Commands
    def do_pipeline_create(self, arg):
        """Create a pipeline: pipeline_create <name>"""
        if not arg:
            print("Usage: pipeline_create <name>")
            return

        self.pipelines[arg] = []
        print(f"Pipeline '{arg}' created")

    def do_pipeline_add(self, arg):
        """Add step to pipeline: pipeline_add <name> <command> [args...]"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: pipeline_add <name> <command> [args...]")
            return

        name = parts[0]
        command = parts[1]
        args = parts[2:] if len(parts) > 2 else []

        if name not in self.pipelines:
            print(f"Pipeline '{name}' not found")
            return

        self.pipelines[name].append({"command": command, "args": args})
        print(f"Added step to pipeline '{name}'")

    def do_pipeline_list(self, arg):
        """List pipelines or show pipeline steps: pipeline_list [name]"""
        if arg:
            if arg in self.pipelines:
                print(f"Pipeline '{arg}':")
                for i, step in enumerate(self.pipelines[arg]):
                    print(f"  {i + 1}. {step['command']} {' '.join(step['args'])}")
            else:
                print(f"Pipeline '{arg}' not found")
        else:
            print("Available pipelines:")
            for name in self.pipelines:
                print(f"  - {name} ({len(self.pipelines[name])} steps)")

    def do_pipeline_run(self, arg):
        """Run a pipeline: pipeline_run <name>"""
        if not arg:
            print("Usage: pipeline_run <name>")
            return

        if arg not in self.pipelines:
            print(f"Pipeline '{arg}' not found")
            return

        print(f"Running pipeline '{arg}'...")
        for i, step in enumerate(self.pipelines[arg]):
            print(f"Step {i + 1}: {step['command']} {' '.join(step['args'])}")
            try:
                # Execute the command
                cmd_line = f"{step['command']} {' '.join(step['args'])}"
                self.onecmd(cmd_line)
            except Exception as e:
                print(f"Error in step {i + 1}: {e}")
                break

        print(f"Pipeline '{arg}' completed")

    def do_pipeline_save(self, arg):
        """Save pipeline to file: pipeline_save <name> <file>"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: pipeline_save <name> <file>")
            return

        name = parts[0]
        filename = parts[1]

        if name not in self.pipelines:
            print(f"Pipeline '{name}' not found")
            return

        try:
            with open(filename, "w") as f:
                json.dump(self.pipelines[name], f, indent=2)
            print(f"Pipeline '{name}' saved to {filename}")
        except Exception as e:
            print(f"Error saving pipeline: {e}")

    def do_pipeline_load(self, arg):
        """Load pipeline from file: pipeline_load <name> <file>"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: pipeline_load <name> <file>")
            return

        name = parts[0]
        filename = parts[1]

        try:
            with open(filename, "r") as f:
                self.pipelines[name] = json.load(f)
            print(f"Pipeline '{name}' loaded from {filename}")
        except Exception as e:
            print(f"Error loading pipeline: {e}")

    # Variable Commands
    def do_set(self, arg):
        """Set a variable: set <name> <value>"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: set <name> <value>")
            return

        name = parts[0]
        value = " ".join(parts[1:])

        # Try to parse as JSON
        try:
            self.variables[name] = json.loads(value)
        except:
            self.variables[name] = value

        print(f"Set {name} = {self.variables[name]}")

    def do_get(self, arg):
        """Get a variable: get <name>"""
        if not arg:
            print("Usage: get <name>")
            return

        if arg in self.variables:
            print(f"{arg} = {self.variables[arg]}")
        else:
            print(f"Variable '{arg}' not found")

    def do_vars(self, arg):
        """List all variables."""
        if self.variables:
            print("Variables:")
            for name, value in self.variables.items():
                print(f"  {name} = {value}")
        else:
            print("No variables defined")

    # Utility Commands
    def do_sleep(self, arg):
        """Sleep for specified seconds: sleep <seconds>"""
        if not arg:
            print("Usage: sleep <seconds>")
            return

        try:
            seconds = float(arg)
            self.loop.run_until_complete(asyncio.sleep(seconds))
            print(f"Slept for {seconds} seconds")
        except ValueError:
            print("Invalid number")

    def do_result(self, arg):
        """Show last command result."""
        if self.last_result:
            print(json.dumps(self.last_result, indent=2))
        else:
            print("No result available")

    def do_help(self, arg):
        """Show help for commands."""
        if arg:
            super().do_help(arg)
        else:
            print("\nAvailable command categories:")
            print("  General:   connect, disconnect, status, exit")
            print("  GPIO:      gpio_setup, gpio_write, gpio_read, led_setup, led")
            print("  Input:     type, move, click, screenshot")
            print("  Pipeline:  pipeline_create, pipeline_add, pipeline_run, etc.")
            print("  Variables: set, get, vars")
            print("  Utility:   sleep, result, help")
            print("\nType 'help <category>' for specific commands")

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def default(self, line):
        """Handle unknown commands."""
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands")


def main():
    """Run the MCP shell."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Hardware Shell")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8888, help="Server port")

    args = parser.parse_args()

    shell = MCPShell(args.host, args.port)

    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
