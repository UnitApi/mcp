#!/usr/bin/env python3
"""
UnitMCP Hardware Client Example

This example demonstrates how to connect to a UnitMCP server and control hardware remotely.
It shows basic GPIO operations, LED control, and button input handling.
"""

import asyncio
import argparse
import logging
import os
import sys
from typing import Optional, Dict, Any

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

class HardwareClientExample:
    """Example class for demonstrating hardware client functionality."""
    
    def __init__(self, host: str = None, port: int = None):
        """Initialize the hardware client example.
        
        Args:
            host: The hostname or IP address of the MCP server
            port: The port of the MCP server
        """
        self.host = host or get_rpi_host()
        self.port = port or get_rpi_port()
        self.client: Optional[MCPHardwareClient] = None
        self.led_pin = env.get_int('LED_PIN', 18)
        self.button_pin = env.get_int('BUTTON_PIN', 17)
        self.led_device_id = f"led_{self.led_pin}"
        self.button_device_id = f"button_{self.button_pin}"
        self.running = False
        
    async def connect(self):
        """Connect to the MCP server."""
        logger = logging.getLogger("HardwareClient")
        logger.info(f"Connecting to MCP server at {self.host}:{self.port}")
        
        self.client = MCPHardwareClient(self.host, self.port)
        await self.client.connect()
        logger.info("Connected to MCP server")
        
    async def setup_hardware(self):
        """Set up the hardware devices."""
        logger = logging.getLogger("HardwareClient")
        
        # Set up LED
        logger.info(f"Setting up LED on pin {self.led_pin}")
        await self.client.setup_led(self.led_device_id, self.led_pin)
        
        # Set up button
        logger.info(f"Setting up button on pin {self.button_pin}")
        await self.client.setup_button(self.button_device_id, self.button_pin)
        
        # Register button callback
        await self.client.register_button_callback(
            self.button_device_id, 
            self.on_button_press
        )
        
    async def on_button_press(self, state: bool):
        """Handle button press events.
        
        Args:
            state: True if button is pressed, False if released
        """
        logger = logging.getLogger("HardwareClient")
        if state:
            logger.info("Button pressed - turning LED on")
            await self.client.led_on(self.led_device_id)
        else:
            logger.info("Button released - turning LED off")
            await self.client.led_off(self.led_device_id)
    
    async def run_led_demo(self, duration: float = 10.0):
        """Run a demo of LED control.
        
        Args:
            duration: Duration to run the demo in seconds
        """
        logger = logging.getLogger("HardwareClient")
        logger.info(f"Running LED demo for {duration} seconds")
        
        # Blink the LED
        logger.info("Blinking LED")
        await self.client.led_blink(self.led_device_id, 0.5, 0.5)
        await asyncio.sleep(5)
        
        # Turn LED on
        logger.info("Turning LED on")
        await self.client.led_on(self.led_device_id)
        await asyncio.sleep(2)
        
        # Turn LED off
        logger.info("Turning LED off")
        await self.client.led_off(self.led_device_id)
        await asyncio.sleep(2)
        
        # Pulse the LED
        logger.info("Pulsing LED")
        await self.client.led_pulse(self.led_device_id, 2.0)
        await asyncio.sleep(duration - 9)  # Remaining time
        
        # Turn LED off at the end
        await self.client.led_off(self.led_device_id)
    
    async def run_button_demo(self, duration: float = 10.0):
        """Run a demo of button input.
        
        Args:
            duration: Duration to run the demo in seconds
        """
        logger = logging.getLogger("HardwareClient")
        logger.info(f"Running button demo for {duration} seconds")
        logger.info("Press the button to control the LED")
        
        # Just wait for button presses
        await asyncio.sleep(duration)
    
    async def run_demo(self, demo_type: str = "all", duration: float = 30.0):
        """Run the hardware client demo.
        
        Args:
            demo_type: Type of demo to run ('led', 'button', or 'all')
            duration: Duration to run the demo in seconds
        """
        logger = logging.getLogger("HardwareClient")
        
        try:
            # Connect to server
            await self.connect()
            
            # Set up hardware
            await self.setup_hardware()
            
            self.running = True
            
            # Run the selected demo
            if demo_type == "led":
                await self.run_led_demo(duration)
            elif demo_type == "button":
                await self.run_button_demo(duration)
            else:  # "all"
                # Split the time between demos
                led_duration = duration / 2
                button_duration = duration / 2
                
                await self.run_led_demo(led_duration)
                await self.run_button_demo(button_duration)
                
        except Exception as e:
            logger.error(f"Error in hardware client demo: {e}")
        finally:
            self.running = False
            
            # Clean up
            if self.client:
                await self.client.disconnect()
                logger.info("Disconnected from MCP server")

async def main():
    """Main function to run the hardware client example."""
    # Get the environment loader instance
    env_loader = env
    
    # Configure logging
    log_level = env_loader.get('LOG_LEVEL', 'INFO').upper()
    log_file = env_loader.get('LOG_FILE', 'hardware_client.log')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("HardwareClient")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UnitMCP Hardware Client Example")
    parser.add_argument("--host", type=str, default=None,
                        help="MCP server hostname or IP address")
    parser.add_argument("--port", type=int, default=None,
                        help="MCP server port")
    parser.add_argument("--demo", type=str, choices=["led", "button", "all"], default="all",
                        help="Type of demo to run")
    parser.add_argument("--duration", type=float, default=env_loader.get_float('DEMO_DURATION', 30.0),
                        help="Duration to run the demo in seconds")
    parser.add_argument("--env-file", type=str, default=None,
                        help="Path to .env file")
    
    args = parser.parse_args()
    
    # Load custom environment file if specified
    if args.env_file:
        env_loader = EnvLoader(args.env_file)
    
    # Log startup information
    logger.info("Starting UnitMCP Hardware Client Example")
    logger.info(f"Server: {args.host or get_rpi_host()}:{args.port or get_rpi_port()}")
    logger.info(f"Demo: {args.demo}")
    logger.info(f"Duration: {args.duration} seconds")
    
    # Create and run the hardware client example
    example = HardwareClientExample(
        host=args.host,
        port=args.port
    )
    
    try:
        await example.run_demo(args.demo, args.duration)
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error running demo: {e}")
    finally:
        if example.running:
            if example.client:
                await example.client.disconnect()
            logger.info("Demo completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
