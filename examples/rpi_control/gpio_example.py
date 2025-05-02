#!/usr/bin/env python3
"""
Basic GPIO Control Example for UnitMCP

This example demonstrates how to:
1. Connect to a Raspberry Pi (or simulate connection)
2. Set up an LED on a GPIO pin
3. Turn the LED on and off
4. Implement a simple blinking pattern

This example uses the UnitMCP hardware client to control GPIO pins.
"""

import asyncio
import argparse
import platform
import time
from typing import Optional

from unitmcp import MCPHardwareClient

# Check if we're on a Raspberry Pi
IS_RPI = platform.machine() in ["armv7l", "aarch64"]


class GPIOExample:
    """Basic GPIO control example class."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8888, pin: int = 17):
        """Initialize the GPIO example.
        
        Args:
            host: The hostname or IP address of the MCP server
            port: The port of the MCP server
            pin: The GPIO pin number to use for the LED
        """
        self.host = host
        self.port = port
        self.pin = pin
        self.client: Optional[MCPHardwareClient] = None
        self.device_id = f"led_{pin}"
        
    async def connect(self):
        """Connect to the MCP server."""
        print(f"Connecting to MCP server at {self.host}:{self.port}...")
        self.client = MCPHardwareClient(self.host, self.port)
        await self.client.connect()
        print("Connected to MCP server")
        
    async def setup_led(self):
        """Set up the LED on the specified GPIO pin."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Setting up LED on GPIO pin {self.pin}...")
        result = await self.client.setup_led(self.device_id, self.pin)
        print(f"LED setup complete: {result}")
        
    async def turn_on(self):
        """Turn the LED on."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print("Turning LED on...")
        result = await self.client.control_led(self.device_id, "on")
        print(f"LED turned on: {result}")
        
    async def turn_off(self):
        """Turn the LED off."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print("Turning LED off...")
        result = await self.client.control_led(self.device_id, "off")
        print(f"LED turned off: {result}")
        
    async def blink(self, count: int = 5, on_time: float = 0.5, off_time: float = 0.5):
        """Blink the LED a specified number of times.
        
        Args:
            count: Number of times to blink
            on_time: Time in seconds to keep the LED on
            off_time: Time in seconds to keep the LED off
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Blinking LED {count} times...")
        for i in range(count):
            print(f"Blink {i+1}/{count}")
            await self.turn_on()
            await asyncio.sleep(on_time)
            await self.turn_off()
            await asyncio.sleep(off_time)
        print("Blinking complete")
        
    async def pattern_blink(self, duration: float = 5.0, on_time: float = 0.2, off_time: float = 0.2):
        """Use the built-in blink pattern functionality.
        
        Args:
            duration: Total duration to run the pattern
            on_time: Time in seconds to keep the LED on
            off_time: Time in seconds to keep the LED off
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Starting blink pattern (on: {on_time}s, off: {off_time}s) for {duration}s...")
        result = await self.client.control_led(self.device_id, "blink", on_time=on_time, off_time=off_time)
        print(f"Blink pattern started: {result}")
        
        # Wait for the specified duration
        await asyncio.sleep(duration)
        
        # Stop the blinking
        await self.turn_off()
        print("Blink pattern stopped")
        
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.turn_off()
            await self.client.disconnect()
            print("Disconnected from MCP server")
            
    async def run_demo(self):
        """Run the complete GPIO demo."""
        try:
            await self.connect()
            await self.setup_led()
            
            # Simple on/off
            await self.turn_on()
            await asyncio.sleep(1)
            await self.turn_off()
            await asyncio.sleep(1)
            
            # Manual blinking
            await self.blink(count=3)
            await asyncio.sleep(1)
            
            # Pattern blinking
            await self.pattern_blink(duration=5.0)
            
        finally:
            await self.cleanup()


async def main():
    """Main function to run the GPIO example."""
    parser = argparse.ArgumentParser(description="UnitMCP GPIO Control Example")
    parser.add_argument("--host", default="127.0.0.1", help="MCP server hostname or IP")
    parser.add_argument("--port", type=int, default=8888, help="MCP server port")
    parser.add_argument("--pin", type=int, default=17, help="GPIO pin number for LED")
    args = parser.parse_args()
    
    if not IS_RPI:
        print("Not running on a Raspberry Pi. Using simulation mode.")
    
    example = GPIOExample(host=args.host, port=args.port, pin=args.pin)
    await example.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
