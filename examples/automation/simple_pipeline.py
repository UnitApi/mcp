"""Simple pipeline example."""

import asyncio
from unitmcp import MCPHardwareClient, Pipeline
from unitmcp.pipeline.pipeline import PipelineStep, Expectation, ExpectationType


async def basic_pipeline():
    """Basic pipeline for LED control."""
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
            ],
            description="Setup LED on pin 17"
        ),
        PipelineStep(
            command="turn_on",
            method="gpio.controlLED",
            params={"device_id": "led1", "action": "on"},
            description="Turn LED on"
        ),
        PipelineStep(
            command="wait",
            method="system.sleep",
            params={"duration": 2},
            description="Wait 2 seconds"
        ),
        PipelineStep(
            command="turn_off",
            method="gpio.controlLED",
            params={"device_id": "led1", "action": "off"},
            description="Turn LED off"
        )
    ]

    pipeline = Pipeline(
        name="basic_led_control",
        steps=steps,
        description="Simple LED on/off sequence"
    )

    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)

        print(f"Pipeline executed successfully: {result.success}")
        print(f"Steps completed: {result.steps_executed}/{len(steps)}")
        if result.errors:
            print(f"Errors: {result.errors}")


async def pipeline_with_variables():
    """Pipeline using variables."""
    steps = [
        PipelineStep(
            command="type_message",
            method="input.typeText",
            params={"text": "Hello ${name}, the time is ${time}"},
            description="Type personalized message"
        ),
        PipelineStep(
            command="press_enter",
            method="input.pressKey",
            params={"key": "enter"},
            description="Press Enter"
        )
    ]

    pipeline = Pipeline(
        name="message_pipeline",
        steps=steps,
        description="Type a personalized message"
    )

    # Set variables
    import datetime
    pipeline.set_variable("name", "User")
    pipeline.set_variable("time", datetime.datetime.now().strftime("%H:%M"))

    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)
        print(f"Pipeline with variables executed: {result.success}")


async def error_handling_pipeline():
    """Pipeline with error handling."""
    steps = [
        PipelineStep(
            command="check_device",
            method="gpio.checkDevice",
            params={"device_id": "test_device"},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="status",
                    value="available"
                )
            ],
            on_failure="handle_error",
            retry_count=2,
            retry_delay=1.0,
            description="Check if device is available"
        ),
        PipelineStep(
            command="use_device",
            method="gpio.useDevice",
            params={"device_id": "test_device"},
            description="Use the device"
        ),
        PipelineStep(
            command="handle_error",
            method="system.log",
            params={"message": "Device not available, using fallback"},
            description="Error handler"
        )
    ]

    pipeline = Pipeline(
        name="error_handling_demo",
        steps=steps,
        description="Demonstrate error handling"
    )

    async with MCPHardwareClient() as client:
        result = await pipeline.execute(client)
        print(f"Error handling pipeline executed: {result.success}")


if __name__ == "__main__":
    print("Pipeline Examples")
    print("1. Basic pipeline")
    print("2. Pipeline with variables")
    print("3. Error handling pipeline")

    choice = input("Select demo (1-3): ")

    if choice == "1":
        asyncio.run(basic_pipeline())
    elif choice == "2":
        asyncio.run(pipeline_with_variables())
    elif choice == "3":
        asyncio.run(error_handling_pipeline())
    else:
        print("Invalid choice")