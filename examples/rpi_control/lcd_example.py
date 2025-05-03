#!/usr/bin/env python3
"""
LCD Display Example for UnitMCP

This example demonstrates how to:
1. Detect and configure an I2C LCD display
2. Display text on multiple lines
3. Update the display with dynamic information
4. Implement scrolling text for longer messages

This example uses the UnitMCP hardware client to control an I2C LCD display.
"""

import asyncio
import argparse
import platform
import time
import datetime
import os
import sys
from typing import Optional, List

# Add the project's src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_simulation_mode
except ImportError:
    print(f"Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient
        from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_simulation_mode
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        print("Please ensure the UnitMCP project is properly installed.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()

# Check if we're on a Raspberry Pi
IS_RPI = platform.machine() in ["armv7l", "aarch64"]


class LCDExample:
    """I2C LCD display example class."""

    def __init__(self, host: str = None, port: int = None, 
                 i2c_address: int = None, width: int = None, height: int = None):
        """Initialize the LCD example.
        
        Args:
            host: The hostname or IP address of the MCP server (overrides env var)
            port: The port of the MCP server (overrides env var)
            i2c_address: The I2C address of the LCD display (usually 0x27 or 0x3F)
            width: The width of the LCD display in characters
            height: The height of the LCD display in characters
        """
        # Use parameters or environment variables with defaults
        self.host = host or get_rpi_host()
        self.port = port or get_rpi_port()
        self.i2c_address = i2c_address or int(env.get("LCD_I2C_ADDR", "0x27"), 16)
        self.width = width or env.get_int("LCD_COLS", 16)
        self.height = height or env.get_int("LCD_ROWS", 2)
        self.client: Optional[MCPHardwareClient] = None
        self.device_id = f"lcd_{hex(self.i2c_address)}"
        self.running = False
        
    async def connect(self):
        """Connect to the MCP server."""
        print(f"Connecting to MCP server at {self.host}:{self.port}...")
        self.client = MCPHardwareClient(self.host, self.port)
        await self.client.connect()
        print("Connected to MCP server")
        
    async def setup_lcd(self):
        """Set up the LCD display."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Setting up LCD display at I2C address {hex(self.i2c_address)}...")
        result = await self.client.send_request("i2c.setupLCD", {
            "device_id": self.device_id,
            "address": self.i2c_address,
            "width": self.width,
            "height": self.height
        })
        print(f"LCD setup complete: {result}")
        
    async def clear_display(self):
        """Clear the LCD display."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print("Clearing LCD display...")
        result = await self.client.send_request("i2c.controlLCD", {
            "device_id": self.device_id,
            "action": "clear"
        })
        print(f"LCD cleared: {result}")
        
    async def display_text(self, text: str, line: int = 0):
        """Display text on a specific line of the LCD.
        
        Args:
            text: The text to display
            line: The line number (0-based)
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        # Truncate or pad the text to fit the display width
        if len(text) > self.width:
            text = text[:self.width]
        else:
            text = text.ljust(self.width)
            
        print(f"Displaying text on line {line}: '{text}'")
        result = await self.client.send_request("i2c.controlLCD", {
            "device_id": self.device_id,
            "action": "write",
            "text": text,
            "line": line
        })
        print(f"Text displayed: {result}")
        
    async def display_multi_line(self, lines: List[str]):
        """Display multiple lines of text on the LCD.
        
        Args:
            lines: List of text lines to display
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        await self.clear_display()
        for i, line in enumerate(lines[:self.height]):
            await self.display_text(line, i)
            
    async def scroll_text(self, text: str, line: int = 0, speed: float = 0.3):
        """Scroll a long text message across the LCD.
        
        Args:
            text: The text to scroll
            line: The line number (0-based)
            speed: Scroll speed in seconds per character
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        if len(text) <= self.width:
            await self.display_text(text, line)
            return
            
        # Add padding at the beginning and end
        padded_text = " " * self.width + text + " " * self.width
        
        for i in range(len(padded_text) - self.width + 1):
            if not self.running:
                break
            segment = padded_text[i:i+self.width]
            await self.display_text(segment, line)
            await asyncio.sleep(speed)
            
    async def display_time(self, duration: float = 10.0, update_interval: float = 1.0):
        """Display the current time on the LCD for a specified duration.
        
        Args:
            duration: Total duration to display the time
            update_interval: How often to update the time
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Displaying time for {duration} seconds...")
        end_time = time.time() + duration
        
        while time.time() < end_time and self.running:
            now = datetime.datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            await self.display_multi_line([date_str, time_str])
            await asyncio.sleep(update_interval)
            
    async def display_status(self, status_messages: List[str], duration: float = 5.0):
        """Display status messages on the LCD.
        
        Args:
            status_messages: List of status messages to display
            duration: Duration to display each message
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Displaying status messages...")
        for message in status_messages:
            if not self.running:
                break
            await self.clear_display()
            if len(message) > self.width:
                await self.scroll_text(message, 0, 0.2)
                await asyncio.sleep(1)
            else:
                await self.display_text(message, 0)
                await asyncio.sleep(duration)
                
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.clear_display()
            await self.client.disconnect()
            print("Disconnected from MCP server")
            
    async def run_demo(self):
        """Run the complete LCD demo."""
        self.running = True
        try:
            await self.connect()
            await self.setup_lcd()
            
            # Display welcome message
            await self.display_multi_line(["UnitMCP", "LCD Example"])
            await asyncio.sleep(2)
            
            # Display time for 10 seconds
            await self.display_time(10.0)
            
            # Display status messages
            status_messages = [
                "System online",
                "All sensors operational",
                "Network connected",
                "This is a very long message that will scroll across the display"
            ]
            await self.display_status(status_messages)
            
            # Scrolling text demo
            long_message = "This is a demonstration of scrolling text on the LCD display"
            await self.scroll_text(long_message, 0, 0.2)
            
            # Final message
            await self.display_multi_line(["Demo complete", "Thank you!"])
            await asyncio.sleep(3)
            
        finally:
            self.running = False
            await self.cleanup()


async def main():
    """Main function to run the LCD example."""
    parser = argparse.ArgumentParser(description="UnitMCP LCD Display Example")
    parser.add_argument("--host", default=None, help="MCP server hostname or IP (overrides env var)")
    parser.add_argument("--port", type=int, default=None, help="MCP server port (overrides env var)")
    parser.add_argument("--address", type=lambda x: int(x, 0), default=None, 
                      help="I2C address of LCD (overrides env var)")
    parser.add_argument("--width", type=int, default=None, help="LCD width in characters (overrides env var)")
    parser.add_argument("--height", type=int, default=None, help="LCD height in characters (overrides env var)")
    parser.add_argument("--env-file", default=None, help="Path to .env file")
    args = parser.parse_args()
    
    # Load environment variables from specified file if provided
    if args.env_file:
        env = EnvLoader(args.env_file)
    
    if not IS_RPI and get_simulation_mode():
        print("Not running on a Raspberry Pi. Using simulation mode.")
    
    example = LCDExample(
        host=args.host, 
        port=args.port, 
        i2c_address=args.address, 
        width=args.width, 
        height=args.height
    )
    await example.run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting LCD example...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
