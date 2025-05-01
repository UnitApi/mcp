"""Security system with motion detection example."""

import asyncio
from datetime import datetime
from unitmcp import MCPHardwareClient, Pipeline
from unitmcp.pipeline.pipeline import PipelineStep, Expectation, ExpectationType


async def simple_security_system():
    """Basic security system with motion sensor."""
    async with MCPHardwareClient() as client:
        # Setup components
        print("Setting up security system...")
        await client.send_request("gpio.setupMotionSensor", {
            "device_id": "motion1",
            "pin": 23
        })
        await client.setup_led("alarm_led", pin=17)
        await client.send_request("gpio.setupBuzzer", {
            "device_id": "alarm_buzzer",
            "pin": 18
        })

        print("Security system active (Ctrl+C to stop)")

        try:
            while True:
                # Check motion sensor
                result = await client.send_request("gpio.readMotionSensor", {
                    "device_id": "motion1"
                })

                if result.get("motion_detected"):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"ALERT: Motion detected at {timestamp}")

                    # Activate alarm
                    await client.control_led("alarm_led", "blink",
                                           on_time=0.2, off_time=0.2)
                    await client.send_request("gpio.controlBuzzer", {
                        "device_id": "alarm_buzzer",
                        "action": "beep",
                        "count": 3,
                        "on_time": 0.5,
                        "off_time": 0.2
                    })

                    # Wait before resetting
                    await asyncio.sleep(5)
                    await client.control_led("alarm_led", "off")

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("\nDisarming security system...")
            await client.control_led("alarm_led", "off")


async def advanced_security_pipeline():
    """Advanced security system using pipelines."""
    # Create security monitoring pipeline
    steps = [
        PipelineStep(
            command="setup_sensors",
            method="system.batch",
            params={
                "commands": [
                    {"method": "gpio.setupMotionSensor",
                     "params": {"device_id": "motion1", "pin": 23}},
                    {"method": "gpio.setupLED",
                     "params": {"device_id": "alarm_led", "pin": 17}},
                    {"method": "gpio.setupBuzzer",
                     "params": {"device_id": "alarm", "pin": 18}},
                    {"method": "camera.openCamera",
                     "params": {"camera_id": 0, "device_name": "security_cam"}}
                ]
            },
            description="Setup all security devices"
        ),
        PipelineStep(
            command="monitor_motion",
            method="gpio.readMotionSensor",
            params={"device_id": "motion1"},
            expectations=[
                Expectation(
                    type=ExpectationType.VALUE_EQUALS,
                    field="motion_detected",
                    value=True
                )
            ],
            on_success="trigger_alarm",
            on_failure="monitor_motion",  # Loop if no motion
            retry_count=1000,
            retry_delay=0.1,
            description="Monitor for motion"
        ),
        PipelineStep(
            command="trigger_alarm",
            method="system.parallel",
            params={
                "commands": [
                    {"method": "gpio.controlLED",
                     "params": {"device_id": "alarm_led", "action": "blink"}},
                    {"method": "gpio.controlBuzzer",
                     "params": {"device_id": "alarm", "action": "beep"}},
                    {"method": "camera.captureImage",
                     "params": {"device_name": "security_cam"}}
                ]
            },
            on_success="log_event",
            description="Trigger alarm and capture image"
        ),
        PipelineStep(
            command="log_event",
            method="system.log",
            params={"message": "Security breach detected at ${timestamp}"},
            on_success="reset_system",
            description="Log security event"
        ),
        PipelineStep(
            command="reset_system",
            method="system.sleep",
            params={"duration": 10},
            on_success="monitor_motion",  # Go back to monitoring
            description="Wait before resetting"
        )
    ]

    pipeline = Pipeline(
        name="advanced_security",
        steps=steps,
        description="Advanced security monitoring system"
    )

    # Set timestamp variable
    pipeline.set_variable("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    async with MCPHardwareClient() as client:
        print("Starting advanced security system...")
        result = await pipeline.execute(client)
        print(f"Security pipeline status: {result.success}")


async def camera_surveillance():
    """Camera-based surveillance system."""
    async with MCPHardwareClient() as client:
        print("Setting up camera surveillance...")

        # Open camera
        await client.send_request("camera.openCamera", {
            "camera_id": 0,
            "device_name": "surveillance_cam"
        })

        # Setup alert LED
        await client.setup_led("alert_led", pin=17)

        print("Camera surveillance active (Ctrl+C to stop)")

        try:
            frame_count = 0
            while True:
                # Detect motion in camera feed
                result = await client.send_request("camera.detectMotion", {
                    "device_name": "surveillance_cam",
                    "threshold": 25,
                    "min_area": 500
                })

                if result.get("motion_detected"):
                    motion_areas = result.get("motion_areas", [])
                    print(f"Motion detected! Areas: {len(motion_areas)}")

                    # Flash alert LED
                    await client.control_led("alert_led", "on")

                    # Capture image with motion highlighted
                    image_result = await client.send_request("camera.detectMotion", {
                        "device_name": "surveillance_cam",
                        "mark_motion": True
                    })

                    # Save image (in real implementation)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    print(f"Saved motion image: motion_{timestamp}.jpg")

                    await asyncio.sleep(2)
                    await client.control_led("alert_led", "off")

                frame_count += 1
                if frame_count % 100 == 0:
                    print(f"Processed {frame_count} frames")

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopping surveillance...")
            await client.send_request("camera.closeCamera", {
                "device_name": "surveillance_cam"
            })
            await client.control_led("alert_led", "off")


if __name__ == "__main__":
    print("Security System Examples")
    print("1. Simple motion detection")
    print("2. Advanced security pipeline")
    print("3. Camera surveillance")

    choice = input("Select demo (1-3): ")

    if choice == "1":
        asyncio.run(simple_security_system())
    elif choice == "2":
        asyncio.run(advanced_security_pipeline())
    elif choice == "3":
        asyncio.run(camera_surveillance())
    else:
        print("Invalid choice")