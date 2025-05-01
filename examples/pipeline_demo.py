"""
pipeline_demo.py
"""

"""Example usage of the Pipeline system for MCP Hardware control."""

import asyncio
import json
from pathlib import Path

from mcp_hardware import MCPHardwareClient
from mcp_hardware.pipeline.pipeline import (
    Pipeline, PipelineManager, PipelineStep,
    Expectation, ExpectationType
)


async def basic_pipeline_example():
    """Basic pipeline example - LED control."""
    print("\n=== Basic Pipeline Example ===")

    # Create a simple LED control pipeline
    steps = [
        PipelineStep(
            command="setup_led",
            method="gpio.setupLED",
            params={"device_id": "led1", "pin": 17},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="status",
                    value="success",
                    message="LED setup failed"
                )
            ]
        ),
        PipelineStep(
            command="turn_on",
            method="gpio.controlLED",
            params={"device_id": "led1", "action": "on"}
        ),
        PipelineStep(
            command="wait",
            method="system.sleep",
            params={"duration": 2}
        ),
        PipelineStep(
            command="turn_off",
            method="gpio.controlLED",
            params={"device_id": "led1", "action": "off"}
        )
    ]

    pipeline = Pipeline(
        name="basic_led_control",
        steps=steps,
        description="Simple LED on/off control"
    )

    # Execute pipeline
    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)

        print(f"Pipeline executed: {result.success}")
        print(f"Steps completed: {result.steps_executed}/{len(steps)}")
        if result.errors:
            print(f"Errors: {result.errors}")


async def pipeline_with_variables():
    """Pipeline example with variables."""
    print("\n=== Pipeline with Variables ===")

    # Create pipeline with variables
    steps = [
        PipelineStep(
            command="setup_led",
            method="gpio.setupLED",
            params={"device_id": "${led_id}", "pin": "${led_pin}"},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="status",
                    value="success"
                )
            ]
        ),
        PipelineStep(
            command="blink",
            method="gpio.controlLED",
            params={
                "device_id": "${led_id}",
                "action": "blink",
                "on_time": "${blink_speed}",
                "off_time": "${blink_speed}"
            }
        )
    ]

    pipeline = Pipeline(
        name="variable_led_control",
        steps=steps,
        description="LED control with variables"
    )

    # Set variables
    pipeline.set_variable("led_id", "my_led")
    pipeline.set_variable("led_pin", 17)
    pipeline.set_variable("blink_speed", 0.5)

    # Execute pipeline
    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)
        print(f"Pipeline with variables executed: {result.success}")


async def pipeline_with_expectations():
    """Pipeline example with complex expectations."""
    print("\n=== Pipeline with Expectations ===")

    # Create pipeline with various expectation types
    steps = [
        PipelineStep(
            command="check_temperature",
            method="sensor.readTemperature",
            params={"sensor_id": "temp1"},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_RANGE,
                    field="temperature",
                    value=(18.0, 26.0),
                    message="Temperature outside comfortable range"
                )
            ]
        ),
        PipelineStep(
            command="check_motion",
            method="sensor.readMotion",
            params={"sensor_id": "motion1"},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="motion_detected",
                    value=False,
                    message="Motion detected when not expected"
                )
            ]
        ),
        PipelineStep(
            command="verify_system",
            method="system.getStatus",
            params={},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_CONTAINS,
                    field="status_message",
                    value="operational",
                    message="System not operational"
                )
            ]
        )
    ]

    pipeline = Pipeline(
        name="system_check",
        steps=steps,
        description="System status verification"
    )

    # Execute pipeline
    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)

        print(f"System check executed: {result.success}")
        for i, step_result in enumerate(result.results):
            print(f"Step {i + 1}: {'Success' if step_result['success'] else 'Failed'}")


async def pipeline_with_branching():
    """Pipeline example with conditional branching."""
    print("\n=== Pipeline with Branching ===")

    # Create pipeline with conditional execution
    steps = [
        PipelineStep(
            command="check_sensor",
            method="sensor.readTemperature",
            params={"sensor_id": "temp1"},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_GREATER,
                    field="temperature",
                    value=25.0
                )
            ],
            on_success="cooling_procedure",
            on_failure="heating_procedure"
        ),
        PipelineStep(
            command="cooling_procedure",
            method="gpio.controlFan",
            params={"fan_id": "fan1", "action": "on"},
            on_success="end"
        ),
        PipelineStep(
            command="heating_procedure",
            method="gpio.controlHeater",
            params={"heater_id": "heater1", "action": "on"},
            on_success="end"
        ),
        PipelineStep(
            command="end",
            method="system.log",
            params={"message": "Temperature control completed"}
        )
    ]

    pipeline = Pipeline(
        name="temperature_control",
        steps=steps,
        description="Temperature-based control flow"
    )

    # Execute pipeline
    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)

        print(f"Temperature control executed: {result.success}")
        print(f"Path taken: {[s['command'] for s in steps if steps.index(s) < result.steps_executed]}")


async def pipeline_manager_demo():
    """Demonstrate PipelineManager functionality."""
    print("\n=== Pipeline Manager Demo ===")

    manager = PipelineManager()

    # Create pipelines from templates
    led_pipeline = manager.create_from_template(
        "led_blink",
        led_pin=17,
        blink_count=3
    )

    keyboard_pipeline = manager.create_from_template(
        "keyboard_test",
        test_text="Pipeline test message"
    )

    system_check = manager.create_from_template("system_check")

    # Add pipelines to manager
    manager.add_pipeline(led_pipeline)
    manager.add_pipeline(keyboard_pipeline)
    manager.add_pipeline(system_check)

    # List pipelines
    print("Available pipelines:")
    for name in manager.list_pipelines():
        print(f"  - {name}")

    # Execute a pipeline
    async with MCPHardwareClient() as client:
        result = await manager.execute_pipeline("system_check", client)
        print(f"\nSystem check result: {result.success}")

    # Save pipelines
    pipeline_dir = Path("saved_pipelines")
    manager.save_all(pipeline_dir)
    print(f"\nPipelines saved to {pipeline_dir}")


async def custom_pipeline_example():
    """Example of creating a custom pipeline for specific automation."""
    print("\n=== Custom Pipeline Example ===")

    # Create a custom automation pipeline
    steps = [
        # Take screenshot
        PipelineStep(
            command="screenshot",
            method="input.screenshot",
            params={},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="status",
                    value="success"
                )
            ]
        ),

        # Open text editor
        PipelineStep(
            command="open_editor",
            method="input.hotkey",
            params={"keys": ["win", "r"]},
            retry_count=2
        ),
        PipelineStep(
            command="type_notepad",
            method="input.typeText",
            params={"text": "notepad"},
            retry_delay=0.5
        ),
        PipelineStep(
            command="launch",
            method="input.pressKey",
            params={"key": "enter"}
        ),

        # Wait for editor to open
        PipelineStep(
            command="wait",
            method="system.sleep",
            params={"duration": 2}
        ),

        # Type message with timestamp
        PipelineStep(
            command="type_header",
            method="input.typeText",
            params={"text": "Automation Log - ${timestamp}"}
        ),
        PipelineStep(
            command="new_line",
            method="input.pressKey",
            params={"key": "enter"}
        ),
        PipelineStep(
            command="type_message",
            method="input.typeText",
            params={"text": "Pipeline executed successfully!"}
        )
    ]

    pipeline = Pipeline(
        name="automation_demo",
        steps=steps,
        description="Custom automation demonstration"
    )

    # Set timestamp variable
    import datetime
    pipeline.set_variable("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Execute pipeline
    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)

        print(f"Automation pipeline executed: {result.success}")
        print(f"Duration: {result.duration:.2f} seconds")


def create_pipeline_examples():
    """Create example pipeline files."""
    examples_dir = Path("pipeline_examples")
    examples_dir.mkdir(exist_ok=True)

    # Complex automation pipeline
    complex_pipeline = {
        "name": "complex_automation",
        "description": "Complex automation with error handling",
        "steps": [
            {
                "command": "check_system",
                "method": "system.getStatus",
                "params": {},
                "expectations": [
                    {
                        "type": "equals",
                        "field": "status",
                        "value": "ready"
                    }
                ],
                "on_failure": "error_handler"
            },
            {
                "command": "start_process",
                "method": "process.start",
                "params": {"process_id": "main_process"},
                "retry_count": 3,
                "retry_delay": 2.0,
                "timeout": 10.0
            },
            {
                "command": "monitor_process",
                "method": "process.monitor",
                "params": {"process_id": "main_process"},
                "expectations": [
                    {
                        "type": "equals",
                        "field": "state",
                        "value": "running"
                    }
                ],
                "on_success": "complete",
                "on_failure": "error_handler"
            },
            {
                "command": "error_handler",
                "method": "system.logError",
                "params": {"message": "Process failed to start or run"},
                "on_success": "cleanup"
            },
            {
                "command": "complete",
                "method": "system.log",
                "params": {"message": "Process completed successfully"},
                "on_success": "cleanup"
            },
            {
                "command": "cleanup",
                "method": "system.cleanup",
                "params": {}
            }
        ]
    }

    # Save example pipeline
    with open(examples_dir / "complex_automation.json", "w") as f:
        json.dump(complex_pipeline, f, indent=2)

    print(f"Created pipeline examples in {examples_dir}")


async def main():
    """Run all pipeline examples."""
    print("MCP Hardware Pipeline Examples")
    print("=" * 50)

    # Create example files
    create_pipeline_examples()

    # Run examples
    await basic_pipeline_example()
    await pipeline_with_variables()
    await pipeline_with_expectations()
    await pipeline_with_branching()
    await pipeline_manager_demo()
    await custom_pipeline_example()

    print("\nPipeline examples completed!")


if __name__ == "__main__":
    asyncio.run(main())