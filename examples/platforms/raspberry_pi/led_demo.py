#!/usr/bin/env python3
"""
LED Demo for UnitMCP.

This example demonstrates how to control LEDs using the UnitMCP library.
It shows how to set up an LED, turn it on and off, and create blinking patterns.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add project root to Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader
except ImportError:
    print("Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient
        from unitmcp.utils import EnvLoader
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()

# Configure logging
logging.basicConfig(
    level=env.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LEDDemo")


class LEDDemo:
    """LED demo for UnitMCP."""

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the LED demo.
        
        Args:
            host: Host address of the Raspberry Pi
            port: Port number for the MCP server
        """
        self.host = host or env.get('RPI_HOST', 'localhost')
        self.port = port or env.get_int('RPI_PORT', 8080)
        self.client = MCPHardwareClient(self.host, self.port)
        self.logger = logging.getLogger("LEDDemo")
        
        # LED configuration
        self.led_id = "demo_led"
        self.led_pin = env.get_int('LED_PIN', 17)
        
        # Timing configuration
        self.fast_blink = env.get_float('FAST_BLINK', 0.1)  # seconds
        self.slow_blink = env.get_float('SLOW_BLINK', 0.5)  # seconds

    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to MCP server at {self.host}:{self.port}")
            await self.client.connect()
            self.logger.info("Connected to MCP server successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from the MCP server.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            await self.client.disconnect()
            self.logger.info("Disconnected from MCP server")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from MCP server: {e}")
            return False

    async def setup_led(self) -> bool:
        """
        Set up the LED with the configured pin.
        
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            self.logger.info(f"Setting up LED {self.led_id} on pin {self.led_pin}")
            
            result = await self.client.setup_led(
                self.led_id,
                self.led_pin
            )
            
            if result.get('success', False):
                self.logger.info("LED setup successful")
                return True
            else:
                self.logger.error(f"LED setup failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up LED: {e}")
            return False

    async def control_led(self, state: str, **kwargs) -> bool:
        """
        Control the LED state.
        
        Args:
            state: LED state ('on', 'off', 'blink')
            **kwargs: Additional parameters for LED control
            
        Returns:
            True if control was successful, False otherwise
        """
        try:
            self.logger.info(f"Setting LED to {state}")
            
            result = await self.client.control_led(
                self.led_id,
                state,
                **kwargs
            )
            
            if result.get('success', False):
                self.logger.info(f"LED control successful: {state}")
                return True
            else:
                self.logger.error(f"LED control failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error controlling LED: {e}")
            return False

    async def run_blink_pattern(self, pattern: str) -> bool:
        """
        Run a predefined LED blinking pattern.
        
        Args:
            pattern: Pattern name ('sos', 'heartbeat', 'countdown')
            
        Returns:
            True if pattern completed successfully, False otherwise
        """
        try:
            self.logger.info(f"Running LED pattern: {pattern}")
            
            if pattern == 'sos':
                # SOS pattern (... --- ...)
                # Short blinks
                for _ in range(3):
                    await self.control_led('on')
                    await asyncio.sleep(self.fast_blink)
                    await self.control_led('off')
                    await asyncio.sleep(self.fast_blink)
                
                await asyncio.sleep(self.slow_blink)
                
                # Long blinks
                for _ in range(3):
                    await self.control_led('on')
                    await asyncio.sleep(self.slow_blink)
                    await self.control_led('off')
                    await asyncio.sleep(self.slow_blink)
                
                await asyncio.sleep(self.fast_blink)
                
                # Short blinks again
                for _ in range(3):
                    await self.control_led('on')
                    await asyncio.sleep(self.fast_blink)
                    await self.control_led('off')
                    await asyncio.sleep(self.fast_blink)
                    
            elif pattern == 'heartbeat':
                # Heartbeat pattern (two quick pulses followed by a pause)
                for _ in range(5):  # 5 heartbeats
                    # First pulse
                    await self.control_led('on')
                    await asyncio.sleep(0.15)
                    await self.control_led('off')
                    await asyncio.sleep(0.1)
                    
                    # Second pulse
                    await self.control_led('on')
                    await asyncio.sleep(0.15)
                    await self.control_led('off')
                    await asyncio.sleep(0.6)  # Longer pause between heartbeats
                    
            elif pattern == 'countdown':
                # Countdown pattern (gradually increasing blink rate)
                blink_time = 1.0
                
                while blink_time > 0.1:
                    await self.control_led('on')
                    await asyncio.sleep(blink_time)
                    await self.control_led('off')
                    await asyncio.sleep(blink_time)
                    
                    # Decrease blink time
                    blink_time -= 0.1
                
                # Rapid blinks at the end
                await self.control_led('blink', on_time=0.05, off_time=0.05, blink_count=10)
                
            else:
                self.logger.warning(f"Unknown pattern: {pattern}")
                return False
                
            self.logger.info(f"Pattern {pattern} completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error running pattern {pattern}: {e}")
            return False

    async def run_demo(self) -> Tuple[bool, str]:
        """
        Run the complete LED demo.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Connect to the server
            if not await self.connect():
                return False, "Failed to connect to MCP server"
                
            # Set up the LED
            if not await self.setup_led():
                return False, "Failed to set up LED"
                
            # Basic on/off demo
            self.logger.info("Running basic on/off demo")
            
            # Turn on the LED
            if not await self.control_led('on'):
                return False, "Failed to turn on LED"
            await asyncio.sleep(1)
            
            # Turn off the LED
            if not await self.control_led('off'):
                return False, "Failed to turn off LED"
            await asyncio.sleep(1)
            
            # Blinking demo
            self.logger.info("Running blinking demo")
            
            # Fast blinking
            self.logger.info("Blinking LED fast")
            if not await self.control_led('blink', on_time=self.fast_blink, off_time=self.fast_blink, blink_count=10):
                return False, "Failed to blink LED fast"
            
            await asyncio.sleep(2)
            
            # Slow blinking
            self.logger.info("Blinking LED slow")
            if not await self.control_led('blink', on_time=self.slow_blink, off_time=self.slow_blink, blink_count=5):
                return False, "Failed to blink LED slow"
            
            await asyncio.sleep(2)
            
            # Pattern demo
            self.logger.info("Running pattern demo")
            
            # SOS pattern
            if not await self.run_blink_pattern('sos'):
                return False, "Failed to run SOS pattern"
            
            await asyncio.sleep(1)
            
            # Heartbeat pattern
            if not await self.run_blink_pattern('heartbeat'):
                return False, "Failed to run heartbeat pattern"
            
            await asyncio.sleep(1)
            
            # Countdown pattern
            if not await self.run_blink_pattern('countdown'):
                return False, "Failed to run countdown pattern"
            
            # Turn off the LED at the end
            await self.control_led('off')
            
            return True, "LED demo completed successfully"
            
        except Exception as e:
            self.logger.error(f"Error running LED demo: {e}")
            return False, f"Error: {str(e)}"
        finally:
            # Always disconnect
            await self.disconnect()


async def main():
    """Main entry point for the LED demo."""
    print("UnitMCP LED Demo")
    print("===============")
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="LED Demo")
    parser.add_argument("--host", type=str, help="Raspberry Pi host address")
    parser.add_argument("--port", type=int, help="MCP server port")
    parser.add_argument("--pattern", type=str, choices=['sos', 'heartbeat', 'countdown'], 
                        help="Run a specific LED pattern")
    
    args = parser.parse_args()
    
    # Create and run the demo
    demo = LEDDemo(
        host=args.host,
        port=args.port
    )
    
    try:
        if args.pattern:
            # Run a specific pattern
            await demo.connect()
            await demo.setup_led()
            
            print(f"Running LED pattern: {args.pattern}")
            success = await demo.run_blink_pattern(args.pattern)
            
            # Turn off the LED
            await demo.control_led('off')
            await demo.disconnect()
            
            if success:
                print(f"Pattern completed successfully")
            else:
                print(f"Pattern failed")
        else:
            # Run the full demo
            success, message = await demo.run_demo()
            
            if success:
                print(f"Demo completed successfully: {message}")
            else:
                print(f"Demo failed: {message}")
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        # Turn off the LED
        await demo.control_led('off')
        await demo.disconnect()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
