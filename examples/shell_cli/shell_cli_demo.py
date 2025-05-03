"""
shell_cli_demo.py
"""

"""Example usage of the MCP Hardware Shell CLI."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

try:
    from unitmcp.client.shell import MCPShell
except ImportError:
    print("Error: Could not import unitmcp module.")
    print("Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print("Try installing the package with: pip install -e /path/to/UnitApi/mcp")
    sys.exit(1)


def demonstrate_shell_features():
    """Demonstrate various shell features."""
    print("MCP Hardware Shell Demo")
    print("-" * 50)
    print("This demo shows shell features. Run interactively for full experience.")
    print()

    # Example commands to demonstrate
    demo_commands = [
        # Connection
        ("connect localhost 8888", "Connect to MCP server"),
        ("status", "Check connection status"),

        # GPIO control
        ("gpio_setup 17 OUT", "Setup GPIO pin 17 as output"),
        ("led_setup led1 17", "Setup LED on pin 17"),
        ("led led1 on", "Turn on the LED"),
        ("led led1 blink on_time 0.5 off_time 0.5", "Blink LED"),
        ("led led1 off", "Turn off the LED"),

        # Keyboard/Mouse control
        ("type Hello World!", "Type text"),
        ("move 500 300", "Move mouse to position"),
        ("click left", "Left click"),
        ("screenshot", "Take screenshot"),

        # Variables
        ("set led_pin 17", "Set a variable"),
        ("get led_pin", "Get variable value"),
        ("vars", "List all variables"),

        # Pipelines
        ("pipeline_create blink_test", "Create a pipeline"),
        ("pipeline_add blink_test led_setup led1 ${led_pin}", "Add step with variable"),
        ("pipeline_add blink_test led led1 on", "Add LED on step"),
        ("pipeline_add blink_test sleep 1", "Add sleep step"),
        ("pipeline_add blink_test led led1 off", "Add LED off step"),
        ("pipeline_list blink_test", "Show pipeline steps"),
        ("pipeline_run blink_test", "Run the pipeline"),
        ("pipeline_save blink_test blink_test.json", "Save pipeline to file"),

        # Results
        ("result", "Show last command result"),
        ("help", "Show help"),
    ]

    print("Example Shell Commands:")
    print("-" * 50)
    for cmd, desc in demo_commands:
        print(f"mcp> {cmd:<40} # {desc}")
    print()


def create_example_pipelines():
    """Create example pipeline files."""
    examples_dir = Path("pipeline_examples")
    examples_dir.mkdir(exist_ok=True)

    # LED Blink Pipeline
    led_pipeline = {
        "name": "led_blink_sequence",
        "description": "Blink LED in a pattern",
        "steps": [
            {
                "command": "setup",
                "method": "gpio.setupLED",
                "params": {"device_id": "led1", "pin": 17},
                "expectations": [
                    {
                        "type": "equals",
                        "field": "status",
                        "value": "success",
                        "message": "LED setup failed"
                    }
                ],
                "description": "Setup LED on pin 17"
            },
            {
                "command": "blink_fast",
                "method": "gpio.controlLED",
                "params": {
                    "device_id": "led1",
                    "action": "blink",
                    "on_time": 0.1,
                    "off_time": 0.1
                },
                "description": "Fast blink"
            },
            {
                "command": "wait",
                "method": "system.sleep",
                "params": {"duration": 2},
                "description": "Wait 2 seconds"
            },
            {
                "command": "blink_slow",
                "method": "gpio.controlLED",
                "params": {
                    "device_id": "led1",
                    "action": "blink",
                    "on_time": 0.5,
                    "off_time": 0.5
                },
                "description": "Slow blink"
            },
            {
                "command": "off",
                "method": "gpio.controlLED",
                "params": {"device_id": "led1", "action": "off"},
                "description": "Turn off LED"
            }
        ],
        "variables": {
            "led_pin": 17,
            "device_id": "led1"
        }
    }

    # Save LED pipeline
    import json
    with open(examples_dir / "led_blink_sequence.json", "w") as f:
        json.dump(led_pipeline, f, indent=2)

    # Automation Pipeline
    automation_pipeline = {
        "name": "automation_test",
        "description": "Test automation features",
        "steps": [
            {
                "command": "open_notepad",
                "method": "input.hotkey",
                "params": {"keys": ["win", "r"]},
                "description": "Open Run dialog"
            },
            {
                "command": "type_notepad",
                "method": "input.typeText",
                "params": {"text": "notepad"},
                "description": "Type notepad"
            },
            {
                "command": "launch",
                "method": "input.pressKey",
                "params": {"key": "enter"},
                "description": "Press Enter"
            },
            {
                "command": "wait_for_notepad",
                "method": "system.sleep",
                "params": {"duration": 2},
                "description": "Wait for Notepad to open"
            },
            {
                "command": "type_message",
                "method": "input.typeText",
                "params": {"text": "Hello from MCP Hardware Automation!"},
                "description": "Type message"
            },
            {
                "command": "save_dialog",
                "method": "input.hotkey",
                "params": {"keys": ["ctrl", "s"]},
                "description": "Open save dialog"
            }
        ]
    }

    # Save automation pipeline
    with open(examples_dir / "automation_test.json", "w") as f:
        json.dump(automation_pipeline, f, indent=2)

    print(f"Created example pipelines in {examples_dir}")


def main():
    """Main entry point for shell demo."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Hardware Shell Demo")
    parser.add_argument("--interactive", action="store_true", help="Start interactive shell")
    parser.add_argument("--examples", action="store_true", help="Create example pipelines")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8888, help="Server port")

    args = parser.parse_args()

    if args.examples:
        create_example_pipelines()
    elif args.interactive:
        # Start interactive shell
        shell = MCPShell(args.host, args.port)
        print("Starting MCP Hardware Shell...")
        print("Type 'help' for commands, 'exit' to quit")
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        # Show demo commands
        demonstrate_shell_features()
        print("\nTo start interactive shell, run with --interactive")
        print("To create example pipelines, run with --examples")


if __name__ == "__main__":
    main()