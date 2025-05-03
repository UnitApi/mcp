#!/usr/bin/env python3
"""
Button Demo for UnitMCP.

This example demonstrates how to set up and use buttons with the UnitMCP library.
It shows how to read button states, wait for button presses, and implement
button-triggered actions.
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
logger = logging.getLogger("ButtonDemo")


class ButtonDemo:
    """Button demo for UnitMCP."""

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the button demo.
        
        Args:
            host: Host address of the Raspberry Pi
            port: Port number for the MCP server
        """
        self.host = host or env.get('RPI_HOST', 'localhost')
        self.port = port or env.get_int('RPI_PORT', 8080)
        self.client = MCPHardwareClient(self.host, self.port)
        self.logger = logging.getLogger("ButtonDemo")
        
        # Button configuration
        self.button_id = "demo_button"
        self.button_pin = env.get_int('BUTTON_PIN', 27)
        
        # LED configuration for feedback
        self.led_id = "feedback_led"
        self.led_pin = env.get_int('LED_PIN', 17)
        
        # Demo configuration
        self.poll_interval = env.get_float('POLL_INTERVAL', 0.1)  # seconds
        self.demo_duration = env.get_int('DEMO_DURATION', 30)  # seconds

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

    async def setup_button(self) -> bool:
        """
        Set up the button with the configured pin.
        
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            self.logger.info(f"Setting up button {self.button_id} on pin {self.button_pin}")
            
            result = await self.client.setup_button(
                self.button_id,
                self.button_pin
            )
            
            if result.get('success', False):
                self.logger.info("Button setup successful")
                return True
            else:
                self.logger.error(f"Button setup failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up button: {e}")
            return False

    async def setup_led(self) -> bool:
        """
        Set up the LED for visual feedback.
        
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

    async def read_button(self) -> Optional[int]:
        """
        Read the current button state.
        
        Returns:
            1 if button is pressed, 0 if not pressed, None if error
        """
        try:
            result = await self.client.read_button(self.button_id)
            
            if result.get('success', False):
                value = result.get('value', 0)
                return value
            else:
                self.logger.error(f"Failed to read button: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading button: {e}")
            return None

    async def control_led(self, state: str, **kwargs) -> bool:
        """
        Control the feedback LED.
        
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

    async def wait_for_button_press(self, timeout: float = None) -> bool:
        """
        Wait for a button press event.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if button was pressed, False if timeout or error
        """
        try:
            self.logger.info(f"Waiting for button press" + 
                           (f" (timeout: {timeout}s)" if timeout else ""))
            
            start_time = time.time()
            
            while True:
                # Check for timeout
                if timeout is not None and (time.time() - start_time) > timeout:
                    self.logger.info("Timeout waiting for button press")
                    return False
                
                # Read button state
                value = await self.read_button()
                
                if value == 1:
                    self.logger.info("Button press detected")
                    return True
                
                # Small delay to avoid hammering the server
                await asyncio.sleep(self.poll_interval)
                
        except Exception as e:
            self.logger.error(f"Error waiting for button press: {e}")
            return False

    async def count_button_presses(self, duration: float) -> int:
        """
        Count the number of button presses within a time period.
        
        Args:
            duration: Time period in seconds
            
        Returns:
            Number of button presses detected
        """
        try:
            self.logger.info(f"Counting button presses for {duration} seconds")
            
            count = 0
            last_state = 0
            end_time = time.time() + duration
            
            while time.time() < end_time:
                current_state = await self.read_button()
                
                # Detect rising edge (button press)
                if current_state == 1 and last_state == 0:
                    count += 1
                    self.logger.info(f"Button press detected (count: {count})")
                    
                    # Blink LED for visual feedback
                    await self.control_led('on')
                    await asyncio.sleep(0.1)
                    await self.control_led('off')
                
                last_state = current_state
                await asyncio.sleep(self.poll_interval)
            
            self.logger.info(f"Counted {count} button presses in {duration} seconds")
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting button presses: {e}")
            return 0

    async def run_button_led_demo(self) -> bool:
        """
        Run a demo where button presses control the LED.
        
        Returns:
            True if demo completed successfully, False otherwise
        """
        try:
            self.logger.info("Running button-controlled LED demo")
            self.logger.info("Press the button to toggle the LED")
            
            led_state = False
            last_button_state = 0
            
            # Run for the configured demo duration
            end_time = time.time() + self.demo_duration
            
            while time.time() < end_time:
                # Read current button state
                current_button_state = await self.read_button()
                
                # Detect rising edge (button press)
                if current_button_state == 1 and last_button_state == 0:
                    # Toggle LED state
                    led_state = not led_state
                    
                    if led_state:
                        self.logger.info("Button pressed: Turning LED on")
                        await self.control_led('on')
                    else:
                        self.logger.info("Button pressed: Turning LED off")
                        await self.control_led('off')
                
                last_button_state = current_button_state
                await asyncio.sleep(self.poll_interval)
            
            # Turn off LED at the end
            await self.control_led('off')
            
            self.logger.info("Button-controlled LED demo completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error running button-LED demo: {e}")
            return False

    async def run_demo(self) -> Tuple[bool, str]:
        """
        Run the complete button demo.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Connect to the server
            if not await self.connect():
                return False, "Failed to connect to MCP server"
                
            # Set up the button and LED
            if not await self.setup_button():
                return False, "Failed to set up button"
                
            if not await self.setup_led():
                return False, "Failed to set up LED"
            
            # Demo 1: Wait for a single button press
            self.logger.info("Demo 1: Press the button once")
            await self.control_led('blink', on_time=0.1, off_time=0.1, blink_count=5)
            
            if not await self.wait_for_button_press(timeout=10):
                return False, "Timeout waiting for button press"
                
            # Visual feedback for successful press
            await self.control_led('on')
            await asyncio.sleep(1)
            await self.control_led('off')
            
            # Demo 2: Count button presses
            self.logger.info("Demo 2: Press the button as many times as you can in 5 seconds")
            await self.control_led('blink', on_time=0.2, off_time=0.2, blink_count=3)
            await asyncio.sleep(1)
            
            count = await self.count_button_presses(5)
            self.logger.info(f"You pressed the button {count} times")
            
            # Visual feedback based on count
            for _ in range(min(count, 10)):
                await self.control_led('on')
                await asyncio.sleep(0.2)
                await self.control_led('off')
                await asyncio.sleep(0.2)
            
            # Demo 3: Button-controlled LED
            self.logger.info("Demo 3: Press the button to toggle the LED")
            await self.control_led('blink', on_time=0.3, off_time=0.3, blink_count=3)
            await asyncio.sleep(1)
            
            if not await self.run_button_led_demo():
                return False, "Error running button-LED demo"
            
            return True, "Button demo completed successfully"
            
        except Exception as e:
            self.logger.error(f"Error running button demo: {e}")
            return False, f"Error: {str(e)}"
        finally:
            # Always disconnect
            await self.disconnect()


async def main():
    """Main entry point for the button demo."""
    print("UnitMCP Button Demo")
    print("==================")
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Button Demo")
    parser.add_argument("--host", type=str, help="Raspberry Pi host address")
    parser.add_argument("--port", type=int, help="MCP server port")
    parser.add_argument("--duration", type=int, help="Demo duration in seconds")
    
    args = parser.parse_args()
    
    # Create and run the demo
    demo = ButtonDemo(
        host=args.host,
        port=args.port
    )
    
    if args.duration:
        demo.demo_duration = args.duration
    
    try:
        success, message = await demo.run_demo()
        
        if success:
            print(f"Demo completed successfully: {message}")
        else:
            print(f"Demo failed: {message}")
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
