#!/usr/bin/env python3
"""
Simple LED control example.

This example demonstrates how to control LEDs using the UnitMCP library.
It uses environment variables for configuration and shows proper error handling.
"""

import asyncio
import os
import sys

# Add project root to Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader, get_simulation_mode
except ImportError:
    print("Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient
        from unitmcp.utils import EnvLoader, get_simulation_mode
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()


async def blink_led():
    """Blink an LED 5 times."""
    # Get configuration from environment variables
    led_pin = env.get_int('LED_PIN', 17)
    led_id = env.get('LED_ID', 'led1')
    blink_count = env.get_int('BLINK_COUNT', 5)
    blink_duration = env.get_float('BLINK_DURATION', 0.5)
    host = env.get('RPI_HOST', 'localhost')
    port = env.get_int('RPI_PORT', 8080)
    
    print(f"Connecting to MCP server at {host}:{port}")
    print(f"Using LED on pin {led_pin} with ID '{led_id}'")
    
    async with MCPHardwareClient(host, port) as client:
        try:
            # Setup LED on GPIO pin from environment
            await client.setup_led(led_id, pin=led_pin)
            print("LED setup complete")

            # Blink LED the specified number of times
            for i in range(blink_count):
                print(f"Blink {i+1}")
                await client.control_led(led_id, "on")
                await asyncio.sleep(blink_duration)
                await client.control_led(led_id, "off")
                await asyncio.sleep(blink_duration)

            print("LED blinking complete")
        except Exception as e:
            print(f"Error during LED control: {e}")
            # Ensure LED is turned off in case of error
            try:
                await client.control_led(led_id, "off")
            except:
                pass


async def led_patterns():
    """Demonstrate different LED patterns."""
    # Get configuration from environment variables
    led_pin = env.get_int('LED_PIN', 17)
    led_id = env.get('LED_ID', 'led1')
    fast_blink = env.get_float('FAST_BLINK', 0.1)
    slow_blink = env.get_float('SLOW_BLINK', 0.5)
    pattern_duration = env.get_float('PATTERN_DURATION', 3.0)
    host = env.get('RPI_HOST', 'localhost')
    port = env.get_int('RPI_PORT', 8080)
    
    print(f"Connecting to MCP server at {host}:{port}")
    print(f"Using LED on pin {led_pin} with ID '{led_id}'")
    
    async with MCPHardwareClient(host, port) as client:
        try:
            # Setup LED
            await client.setup_led(led_id, pin=led_pin)

            # Pattern 1: Fast blink
            print("Fast blink pattern")
            await client.control_led(led_id, "blink", on_time=fast_blink, off_time=fast_blink)
            await asyncio.sleep(pattern_duration)

            # Pattern 2: Slow blink
            print("Slow blink pattern")
            await client.control_led(led_id, "blink", on_time=slow_blink, off_time=slow_blink)
            await asyncio.sleep(pattern_duration)

            # Turn off
            await client.control_led(led_id, "off")
            print("LED patterns complete")
        except Exception as e:
            print(f"Error during LED pattern demonstration: {e}")
            # Ensure LED is turned off in case of error
            try:
                await client.control_led(led_id, "off")
            except:
                pass


if __name__ == "__main__":
    # Check if simulation mode is enabled
    simulation = get_simulation_mode()
    if simulation:
        print("Running in simulation mode - no actual hardware will be controlled")
    
    print("LED Control Demo")
    print("1. Simple blink")
    print("2. LED patterns")

    choice = input("Select demo (1-2): ")

    if choice == "1":
        asyncio.run(blink_led())
    elif choice == "2":
        asyncio.run(led_patterns())
    else:
        print("Invalid choice")