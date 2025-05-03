#!/usr/bin/env python3
"""
Traffic light system example.

This example demonstrates how to create a traffic light system using LEDs
and the UnitMCP library. It uses environment variables for configuration
and demonstrates proper error handling.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader, get_simulation_mode, get_rpi_host, get_rpi_port
except ImportError:
    print("Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient
        from unitmcp.utils import EnvLoader, get_simulation_mode, get_rpi_host, get_rpi_port
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()


async def traffic_light_system():
    """Simulate a traffic light system with LEDs."""
    # Get configuration from environment variables
    red_pin = env.get_int('RED_LED_PIN', 17)
    yellow_pin = env.get_int('YELLOW_LED_PIN', 27)
    green_pin = env.get_int('GREEN_LED_PIN', 22)
    red_time = env.get_float('RED_LIGHT_TIME', 5.0)
    yellow_time = env.get_float('YELLOW_LIGHT_TIME', 2.0)
    green_time = env.get_float('GREEN_LIGHT_TIME', 5.0)
    host = get_rpi_host()
    port = get_rpi_port()
    
    print(f"Connecting to MCP server at {host}:{port}")
    print(f"Using LED pins: Red={red_pin}, Yellow={yellow_pin}, Green={green_pin}")
    print(f"Timing: Red={red_time}s, Yellow={yellow_time}s, Green={green_time}s")
    
    async with MCPHardwareClient(host, port) as client:
        # Setup LEDs for traffic light
        print("Setting up traffic light system...")
        try:
            await client.setup_led("red", pin=red_pin)
            await client.setup_led("yellow", pin=yellow_pin)
            await client.setup_led("green", pin=green_pin)

            print("Traffic light running (Ctrl+C to stop)")

            try:
                while True:
                    # Red light
                    print("RED")
                    await client.control_led("red", "on")
                    await client.control_led("yellow", "off")
                    await client.control_led("green", "off")
                    await asyncio.sleep(red_time)

                    # Red + Yellow (prepare to go)
                    print("RED + YELLOW")
                    await client.control_led("yellow", "on")
                    await asyncio.sleep(yellow_time)

                    # Green light
                    print("GREEN")
                    await client.control_led("red", "off")
                    await client.control_led("yellow", "off")
                    await client.control_led("green", "on")
                    await asyncio.sleep(green_time)

                    # Yellow light
                    print("YELLOW")
                    await client.control_led("green", "off")
                    await client.control_led("yellow", "on")
                    await asyncio.sleep(yellow_time)

            except KeyboardInterrupt:
                print("\nStopping traffic light...")
            except Exception as e:
                print(f"\nError during traffic light operation: {e}")
            finally:
                # Turn off all LEDs
                for led in ["red", "yellow", "green"]:
                    try:
                        await client.control_led(led, "off")
                    except Exception as e:
                        print(f"Error turning off {led} LED: {e}")
                print("Traffic light stopped")
        except Exception as e:
            print(f"Error setting up traffic light: {e}")


async def pedestrian_crossing():
    """Traffic light with pedestrian crossing button."""
    # Get configuration from environment variables
    car_red_pin = env.get_int('CAR_RED_PIN', 17)
    car_green_pin = env.get_int('CAR_GREEN_PIN', 22)
    ped_red_pin = env.get_int('PED_RED_PIN', 23)
    ped_green_pin = env.get_int('PED_GREEN_PIN', 24)
    button_pin = env.get_int('BUTTON_PIN', 25)
    crossing_time = env.get_float('CROSSING_TIME', 10.0)
    transition_time = env.get_float('TRANSITION_TIME', 3.0)
    flash_count = env.get_int('FLASH_COUNT', 3)
    host = get_rpi_host()
    port = get_rpi_port()
    
    print(f"Connecting to MCP server at {host}:{port}")
    print(f"Using car traffic lights: Red={car_red_pin}, Green={car_green_pin}")
    print(f"Using pedestrian lights: Red={ped_red_pin}, Green={ped_green_pin}")
    print(f"Button on pin {button_pin}, crossing time: {crossing_time}s")
    
    async with MCPHardwareClient(host, port) as client:
        try:
            # Setup traffic lights
            await client.setup_led("car_red", pin=car_red_pin)
            await client.setup_led("car_green", pin=car_green_pin)
            await client.setup_led("ped_red", pin=ped_red_pin)
            await client.setup_led("ped_green", pin=ped_green_pin)

            # Setup button for pedestrian crossing
            await client.send_request("gpio.setupButton", {
                "device_id": "ped_button",
                "pin": button_pin
            })

            print("Pedestrian crossing system running...")

            # Start with cars green, pedestrians red
            await client.control_led("car_green", "on")
            await client.control_led("car_red", "off")
            await client.control_led("ped_red", "on")
            await client.control_led("ped_green", "off")

            try:
                while True:
                    # Check for button press
                    result = await client.send_request("gpio.readButton", {
                        "device_id": "ped_button"
                    })

                    if result.get("is_pressed"):
                        print("Pedestrian crossing requested")

                        # Change to yellow for cars
                        await client.control_led("car_green", "off")
                        await client.control_led("car_red", "on")
                        await asyncio.sleep(transition_time)

                        # Allow pedestrians to cross
                        await client.control_led("ped_red", "off")
                        await client.control_led("ped_green", "on")
                        await asyncio.sleep(crossing_time)

                        # Flash pedestrian green
                        for _ in range(flash_count):
                            await client.control_led("ped_green", "off")
                            await asyncio.sleep(0.5)
                            await client.control_led("ped_green", "on")
                            await asyncio.sleep(0.5)

                        # Back to normal
                        await client.control_led("ped_green", "off")
                        await client.control_led("ped_red", "on")
                        await asyncio.sleep(transition_time)
                        await client.control_led("car_red", "off")
                        await client.control_led("car_green", "on")

                    await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                print("\nStopping pedestrian crossing...")
            except Exception as e:
                print(f"\nError during pedestrian crossing operation: {e}")
            finally:
                # Turn off all LEDs
                for led in ["car_red", "car_green", "ped_red", "ped_green"]:
                    try:
                        await client.control_led(led, "off")
                    except Exception as e:
                        print(f"Error turning off {led} LED: {e}")
                print("Pedestrian crossing stopped")
        except Exception as e:
            print(f"Error setting up pedestrian crossing: {e}")


if __name__ == "__main__":
    # Check if simulation mode is enabled
    simulation = get_simulation_mode()
    if simulation:
        print("Running in simulation mode - no actual hardware will be controlled")
    
    print("Traffic Light Examples")
    print("1. Basic traffic light")
    print("2. Pedestrian crossing")

    choice = input("Select demo (1-2): ")

    if choice == "1":
        asyncio.run(traffic_light_system())
    elif choice == "2":
        asyncio.run(pedestrian_crossing())
    else:
        print("Invalid choice")