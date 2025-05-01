"""
integrated_demo.py
"""

"""Integrated demonstration of Shell CLI and Pipeline features."""

import asyncio
import json
from pathlib import Path

from mcp_hardware import MCPHardwareClient, MCPShell, Pipeline, PipelineManager
from mcp_hardware.pipeline.pipeline import PipelineStep, Expectation, ExpectationType


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
            params={"device_id": "demo_led", "pin": 17},
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
                "on_time": 0.1,
                "off_time": 0.1
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
                "on_time": 0.5,
                "off_time": 0.5
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
        name="automation_demo",
        steps=steps,
        description="Automation demonstration with error handling"
    )

    # Set timestamp variable
    import datetime
    pipeline.set_variable("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return pipeline


def create_interactive_shell_script():
    """Create a shell script file for batch operations."""
    script_content = """# MCP Hardware Shell Script
# This script can be run through the shell

# Setup variables
set led_pin 17
set led_id test_led
set blink_count 3

# Create a pipeline
pipeline_create led_test
pipeline_add led_test led_setup ${led_id} ${led_pin}
pipeline_add led_test led ${led_id} on
pipeline_add led_test sleep 1
pipeline_add led_test led ${led_id} off

# Create automation pipeline
pipeline_create auto_test
pipeline_add auto_test type Testing automation at $(date)
pipeline_add auto_test move 100 100
pipeline_add auto_test click left

# List all pipelines
pipeline_list

# Run the LED test
pipeline_run led_test

# Save pipelines
pipeline_save led_test led_test.json
pipeline_save auto_test auto_test.json

# Show results
result
vars
"""

    script_file = Path("interactive_demo.mcp")
    with open(script_file, "w") as f:
        f.write(script_content)

    print(f"Created shell script: {script_file}")


def main():
    """Main entry point for integrated demo."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Hardware Integrated Demo")
    parser.add_argument("--shell", action="store_true", help="Start interactive shell")
    parser.add_argument("--pipeline", action="store_true", help="Run pipeline demo")
    parser.add_argument("--script", action="store_true", help="Create shell script")

    args = parser.parse_args()

    if args.shell:
        # Start interactive shell
        print("Starting MCP Hardware Shell...")
        shell = MCPShell()
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
    elif args.pipeline:
        # Run pipeline demo
        asyncio.run(integrated_demo())
    elif args.script:
        # Create shell script
        create_interactive_shell_script()
    else:
        # Show options
        print("MCP Hardware Integrated Demo")
        print("=" * 50)
        print("Options:")
        print("  --shell    : Start interactive shell")
        print("  --pipeline : Run pipeline demonstration")
        print("  --script   : Create example shell script")
        print("\nRun with one of the options above")


if __name__ == "__main__":
    main()