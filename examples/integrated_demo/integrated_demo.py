"""
integrated_demo.py
"""

"""Integrated demonstration of Shell CLI and Pipeline features."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient, MCPShell
    from unitmcp.pipeline.pipeline import Pipeline, PipelineManager, PipelineStep, Expectation, ExpectationType
    from unitmcp.utils import EnvLoader
except ImportError:
    print("Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient, MCPShell
        from unitmcp.pipeline.pipeline import Pipeline, PipelineManager, PipelineStep, Expectation, ExpectationType
        from unitmcp.utils import EnvLoader
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()


async def integrated_demo():
    """Demonstrate integrated use of shell and pipelines."""
    print("MCP Hardware Integrated Demo")
    print("=" * 50)

    # Create a pipeline for LED control
    led_pipeline = create_led_control_pipeline()

    # Create a pipeline for automation
    automation_pipeline = create_automation_pipeline()

    # Initialize pipeline manager
    manager = PipelineManager()
    manager.add_pipeline(led_pipeline)
    manager.add_pipeline(automation_pipeline)

    # Create shell instance
    shell = MCPShell()

    print("\n1. Executing LED control pipeline...")
    async with MCPHardwareClient() as client:
        result = await manager.execute_pipeline("led_control", client)
        print(f"LED pipeline result: {result.success}")

    print("\n2. Demonstrating shell commands...")
    shell_demo_commands = [
        "status",
        "set led_pin 17",
        "get led_pin",
        "pipeline_list",
        "vars"
    ]

    for cmd in shell_demo_commands:
        print(f"mcp> {cmd}")
        shell.onecmd(cmd)

    print("\n3. Creating and running a custom pipeline through shell...")
    custom_commands = [
        "pipeline_create custom_demo",
        "pipeline_add custom_demo type Hello from custom pipeline!",
        "pipeline_add custom_demo move 100 100",
        "pipeline_add custom_demo click left",
        "pipeline_run custom_demo"
    ]

    for cmd in custom_commands:
        print(f"mcp> {cmd}")
        shell.onecmd(cmd)

    print("\n4. Saving pipelines...")
    save_dir = Path("integrated_demo_pipelines")
    manager.save_all(save_dir)
    print(f"Pipelines saved to {save_dir}")


def create_led_control_pipeline():
    """Create a comprehensive LED control pipeline."""
    steps = [
        PipelineStep(
            command="setup_led",
            method="gpio.setupLED",
            params={"device_id": "demo_led", "pin": env.get_int("LED_PIN", 17)},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="status",
                    value="success",
                    message="LED setup failed"
                )
            ],
            description="Setup LED on pin 17"
        ),
        PipelineStep(
            command="pattern_1",
            method="gpio.controlLED",
            params={
                "device_id": "demo_led",
                "action": "blink",
                "on_time": env.get_float("FAST_BLINK", 0.1),
                "off_time": env.get_float("FAST_BLINK", 0.1)
            },
            retry_count=2,
            description="Fast blink pattern"
        ),
        PipelineStep(
            command="wait_1",
            method="system.sleep",
            params={"duration": 2},
            description="Wait between patterns"
        ),
        PipelineStep(
            command="pattern_2",
            method="gpio.controlLED",
            params={
                "device_id": "demo_led",
                "action": "blink",
                "on_time": env.get_float("SLOW_BLINK", 0.5),
                "off_time": env.get_float("SLOW_BLINK", 0.5)
            },
            description="Slow blink pattern"
        ),
        PipelineStep(
            command="wait_2",
            method="system.sleep",
            params={"duration": 2},
            description="Wait before cleanup"
        ),
        PipelineStep(
            command="cleanup",
            method="gpio.controlLED",
            params={"device_id": "demo_led", "action": "off"},
            description="Turn off LED"
        )
    ]

    pipeline = Pipeline(
        name="led_control",
        steps=steps,
        description="Comprehensive LED control demonstration"
    )

    return pipeline


def create_automation_pipeline():
    """Create an automation pipeline with error handling."""
    steps = [
        PipelineStep(
            command="check_mouse",
            method="input.getMousePosition",
            params={},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="status",
                    value="success"
                )
            ],
            on_failure="error_handler",
            description="Check mouse accessibility"
        ),
        PipelineStep(
            command="take_screenshot",
            method="input.screenshot",
            params={},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="status",
                    value="success"
                )
            ],
            on_failure="error_handler",
            description="Take initial screenshot"
        ),
        PipelineStep(
            command="automation_sequence",
            method="input.typeText",
            params={"text": "Automation test: ${timestamp}"},
            description="Type test message"
        ),
        PipelineStep(
            command="move_mouse",
            method="input.moveMouse",
            params={"x": 500, "y": 300, "relative": False},
            retry_count=1,
            description="Move mouse to center"
        ),
        PipelineStep(
            command="success_log",
            method="system.log",
            params={"message": "Automation completed successfully"},
            on_success="cleanup",
            description="Log success"
        ),
        PipelineStep(
            command="error_handler",
            method="system.logError",
            params={"message": "Automation failed: ${error_message}"},
            on_success="cleanup",
            description="Handle errors"
        ),
        PipelineStep(
            command="cleanup",
            method="system.cleanup",
            params={},
            description="Clean up resources"
        )
    ]

    pipeline = Pipeline(
        name="automation",
        steps=steps,
        description="Automation pipeline with error handling"
    )

    return pipeline


def create_interactive_shell_script():
    """Create a shell script file for batch operations."""
    script_content = """#!/bin/bash
# Interactive shell script for UnitMCP integrated demo

echo "Starting UnitMCP Interactive Shell"
echo "=================================="

# Set up an LED
echo "Setting up LED on pin 17..."
echo "setup_led demo_led 17" | nc localhost 8080

# Control the LED
echo "Turning LED on..."
echo "control_led demo_led on" | nc localhost 8080
sleep 2

echo "Blinking LED..."
echo "control_led demo_led blink 0.2 0.2" | nc localhost 8080
sleep 5

echo "Turning LED off..."
echo "control_led demo_led off" | nc localhost 8080

echo "Demo complete!"
"""

    with open("interactive_demo.sh", "w") as f:
        f.write(script_content)
    
    os.chmod("interactive_demo.sh", 0o755)
    print("Created interactive shell script: interactive_demo.sh")


async def main():
    """Main entry point for integrated demo."""
    print("UnitMCP Integrated Demo")
    print("======================")
    print("\nThis demo showcases the integration of various UnitMCP features:")
    print("1. Pipeline execution")
    print("2. Shell command interface")
    print("3. Hardware control")
    print("4. Automation capabilities")
    
    # Create the interactive shell script
    create_interactive_shell_script()
    
    try:
        # Run the integrated demo
        await integrated_demo()
        
        print("\nDemo completed successfully!")
        print("\nYou can also try the interactive shell script:")
        print("  ./interactive_demo.sh")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demo: {e}")
    
    print("\nThank you for exploring UnitMCP!")


if __name__ == "__main__":
    asyncio.run(main())