"""
rpi_control.py
"""

"""Raspberry Pi hardware control examples."""

import asyncio
import time
import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPI_HOST = os.getenv('RPI_HOST', '127.0.0.1')
RPI_PORT = int(os.getenv('RPI_PORT', '8888'))

from mcp_hardware import MCPHardwareClient, MCPServer, PermissionManager
from mcp_hardware.server.gpio import GPIOServer
from mcp_hardware.server.input import InputServer


class RaspberryPiController:
    """Controller for Raspberry Pi hardware demos."""

    def __init__(self, host: str = RPI_HOST, port: int = RPI_PORT):
        self.client = MCPHardwareClient(host, port)

    async def connect(self):
        """Connect to MCP server."""
        await self.client.connect()

    async def led_demo(self):
        """LED control demonstration."""
        print("LED Control Demo")
        print("-" * 30)

        # Setup LED on GPIO 17
        led_pin = 17
        device_id = "led1"

        print(f"Setting up LED on pin {led_pin}")
        await self.client.setup_led(device_id, led_pin)

        # Basic operations
        print("Turning LED on")
        await self.client.control_led(device_id, "on")
        await asyncio.sleep(2)

        print("Turning LED off")
        await self.client.control_led(device_id, "off")
        await asyncio.sleep(1)

        print("Toggling LED")
        await self.client.control_led(device_id, "toggle")
        await asyncio.sleep(1)
        await self.client.control_led(device_id, "toggle")
        await asyncio.sleep(1)

        print("Blinking LED")
        await self.client.control_led(device_id, "blink", on_time=0.5, off_time=0.5)
        await asyncio.sleep(5)

        print("Stopping blink")
        await self.client.control_led(device_id, "off")

    async def button_demo(self):
        """Button input demonstration."""
        print("\nButton Input Demo")
        print("-" * 30)

        button_pin = 27
        led_pin = 17
        button_id = "button1"
        led_id = "led1"

        # Setup button and LED
        print(f"Setting up button on pin {button_pin}")
        await self.client.send_request("gpio.setupButton", {
            "device_id": button_id,
            "pin": button_pin
        })

        print(f"Setting up LED on pin {led_pin}")
        await self.client.setup_led(led_id, led_pin)

        print("Press the button to toggle LED (Ctrl+C to exit)")

        last_state = False
        try:
            while True:
                # Read button state
                result = await self.client.send_request("gpio.readButton", {
                    "device_id": button_id
                })

                is_pressed = result.get("is_pressed", False)

                # Detect state change
                if is_pressed and not last_state:
                    print("Button pressed!")
                    await self.client.control_led(led_id, "toggle")

                last_state = is_pressed
                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopping button demo")
            await self.client.control_led(led_id, "off")

    async def traffic_light_demo(self):
        """Traffic light simulation."""
        print("\nTraffic Light Demo")
        print("-" * 30)

        # Define pins for traffic light
        red_pin = 17
        yellow_pin = 27
        green_pin = 22

        red_id = "red_light"
        yellow_id = "yellow_light"
        green_id = "green_light"

        # Setup LEDs
        print("Setting up traffic lights")
        await self.client.setup_led(red_id, red_pin)
        await self.client.setup_led(yellow_id, yellow_pin)
        await self.client.setup_led(green_id, green_pin)

        print("Running traffic light sequence (Ctrl+C to stop)")

        try:
            while True:
                # Red light
                await self.client.control_led(red_id, "on")
                await self.client.control_led(yellow_id, "off")
                await self.client.control_led(green_id, "off")
                print("Red")
                await asyncio.sleep(5)

                # Red + Yellow (prepare to go)
                await self.client.control_led(yellow_id, "on")
                print("Red + Yellow")
                await asyncio.sleep(2)

                # Green light
                await self.client.control_led(red_id, "off")
                await self.client.control_led(yellow_id, "off")
                await self.client.control_led(green_id, "on")
                print("Green")
                await asyncio.sleep(5)

                # Yellow light
                await self.client.control_led(green_id, "off")
                await self.client.control_led(yellow_id, "on")
                print("Yellow")
                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print("\nStopping traffic light")
            # Turn off all lights
            await self.client.control_led(red_id, "off")
            await self.client.control_led(yellow_id, "off")
            await self.client.control_led(green_id, "off")

    async def sensor_demo(self):
        """Motion sensor demonstration."""
        print("\nMotion Sensor Demo")
        print("-" * 30)

        sensor_pin = 23
        led_pin = 17
        sensor_id = "motion1"
        led_id = "led1"

        # Setup motion sensor and LED
        print(f"Setting up motion sensor on pin {sensor_pin}")
        await self.client.send_request("gpio.setupMotionSensor", {
            "device_id": sensor_id,
            "pin": sensor_pin
        })

        print(f"Setting up LED on pin {led_pin}")
        await self.client.setup_led(led_id, led_pin)

        print("Motion sensor active - LED will light up when motion detected")
        print("Press Ctrl+C to exit")

        try:
            while True:
                # Read motion sensor
                result = await self.client.send_request("gpio.readMotionSensor", {
                    "device_id": sensor_id
                })

                motion_detected = result.get("motion_detected", False)

                if motion_detected:
                    print("Motion detected!")
                    await self.client.control_led(led_id, "on")
                else:
                    await self.client.control_led(led_id, "off")

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopping motion sensor demo")
            await self.client.control_led(led_id, "off")

    async def buzzer_demo(self):
        """Buzzer control demonstration."""
        print("\nBuzzer Demo")
        print("-" * 30)

        buzzer_pin = 24
        buzzer_id = "buzzer1"

        # Setup buzzer
        print(f"Setting up buzzer on pin {buzzer_pin}")
        await self.client.send_request("gpio.setupBuzzer", {
            "device_id": buzzer_id,
            "pin": buzzer_pin
        })

        # Play different patterns
        print("Playing single beep")
        await self.client.send_request("gpio.controlBuzzer", {
            "device_id": buzzer_id,
            "action": "beep"
        })
        await asyncio.sleep(1)

        print("Playing multiple beeps")
        await self.client.send_request("gpio.controlBuzzer", {
            "device_id": buzzer_id,
            "action": "beep",
            "count": 3,
            "on_time": 0.2,
            "off_time": 0.2
        })
        await asyncio.sleep(2)

        print("Playing morse code SOS")
        # S: 3 short beeps
        for _ in range(3):
            await self.client.send_request("gpio.controlBuzzer", {
                "device_id": buzzer_id,
                "action": "beep",
                "on_time": 0.1,
                "off_time": 0.1
            })

        await asyncio.sleep(0.3)

        # O: 3 long beeps
        for _ in range(3):
            await self.client.send_request("gpio.controlBuzzer", {
                "device_id": buzzer_id,
                "action": "beep",
                "on_time": 0.3,
                "off_time": 0.1
            })

        await asyncio.sleep(0.3)

        # S: 3 short beeps
        for _ in range(3):
            await self.client.send_request("gpio.controlBuzzer", {
                "device_id": buzzer_id,
                "action": "beep",
                "on_time": 0.1,
                "off_time": 0.1
            })

    async def cleanup(self):
        """Cleanup GPIO resources."""
        print("\nCleaning up GPIO resources")
        await self.client.send_request("gpio.cleanup", {})
        await self.client.disconnect()


async def run_demo(demo_name: str):
    """Run specific demo."""
    controller = RaspberryPiController()

    try:
        await controller.connect()

        if demo_name == "led":
            await controller.led_demo()
        elif demo_name == "button":
            await controller.button_demo()
        elif demo_name == "traffic":
            await controller.traffic_light_demo()
        elif demo_name == "sensor":
            await controller.sensor_demo()
        elif demo_name == "buzzer":
            await controller.buzzer_demo()
        elif demo_name == "all":
            await controller.led_demo()
            await controller.button_demo()
            await controller.traffic_light_demo()
            await controller.sensor_demo()
            await controller.buzzer_demo()
        else:
            print(f"Unknown demo: {demo_name}")

    finally:
        await controller.cleanup()


async def setup_server():
    """Setup MCP server for Raspberry Pi."""
    # Create permission manager
    permission_manager = PermissionManager()

    # Allow access to GPIO for demo
    permission_manager.grant_permission("client_*", "gpio")

    # Create server
    server = MCPServer(permission_manager=permission_manager)

    # Register GPIO server
    server.register_server("gpio", GPIOServer())

    # Start server
    print("Starting Raspberry Pi MCP server...")
    await server.start()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Raspberry Pi Hardware Control")
    parser.add_argument("--mode", choices=["server", "demo"],
                        default="demo", help="Running mode")
    parser.add_argument("--demo", choices=["led", "button", "traffic", "sensor", "buzzer", "all"],
                        default="led", help="Demo to run")

    args = parser.parse_args()

    if args.mode == "server":
        asyncio.run(setup_server())
    else:
        asyncio.run(run_demo(args.demo))