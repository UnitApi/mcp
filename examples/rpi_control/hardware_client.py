#!/usr/bin/env python3
"""
Raspberry Pi hardware client example for UnitMCP.

This example demonstrates how to create a client that connects to a Raspberry Pi
running the UnitMCP server and control hardware devices.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

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
logger = logging.getLogger("RPiHardwareClient")


class RPiHardwareClient:
    """Client for controlling Raspberry Pi hardware through UnitMCP."""

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the Raspberry Pi hardware client.
        
        Args:
            host: Host address of the Raspberry Pi
            port: Port number for the MCP server
        """
        self.host = host or env.get('RPI_HOST', 'localhost')
        self.port = port or env.get_int('RPI_PORT', 8080)
        self.client = MCPHardwareClient(self.host, self.port)
        self.logger = logging.getLogger("RPiHardwareClient")
        self.logger.info(f"Initialized RPi Hardware Client for {self.host}:{self.port}")
        self.devices = {}

    async def connect(self) -> bool:
        """
        Connect to the Raspberry Pi MCP server.
        
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
        Disconnect from the Raspberry Pi MCP server.
        
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

    async def setup_led(self, device_id: str, pin: int) -> Dict[str, Any]:
        """
        Set up an LED connected to a GPIO pin.
        
        Args:
            device_id: Unique identifier for the LED device
            pin: GPIO pin number the LED is connected to
            
        Returns:
            Dictionary with setup result
        """
        try:
            self.logger.info(f"Setting up LED {device_id} on pin {pin}")
            result = await self.client.setup_led(device_id, pin)
            
            if result.get("status") == "success":
                self.devices[device_id] = {"type": "led", "pin": pin}
                self.logger.info(f"LED {device_id} setup successful")
            else:
                self.logger.error(f"LED {device_id} setup failed: {result}")
                
            return result
        except Exception as e:
            self.logger.error(f"Error setting up LED {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def control_led(
            self, 
            device_id: str, 
            action: str, 
            on_time: float = None, 
            off_time: float = None,
            blink_count: int = None
    ) -> Dict[str, Any]:
        """
        Control an LED device.
        
        Args:
            device_id: Identifier for the LED device
            action: Action to perform (on, off, blink)
            on_time: Time in seconds for LED to stay on during blink
            off_time: Time in seconds for LED to stay off during blink
            blink_count: Number of times to blink (None for infinite)
            
        Returns:
            Dictionary with control result
        """
        try:
            if device_id not in self.devices:
                self.logger.error(f"Device {device_id} not found")
                return {"status": "error", "message": f"Device {device_id} not found"}
                
            params = {"device_id": device_id, "action": action}
            if on_time is not None:
                params["on_time"] = on_time
            if off_time is not None:
                params["off_time"] = off_time
            if blink_count is not None:
                params["blink_count"] = blink_count
                
            self.logger.info(f"Controlling LED {device_id}: {action}")
            result = await self.client.control_led(**params)
            
            if result.get("status") == "success":
                self.logger.info(f"LED {device_id} control successful")
            else:
                self.logger.error(f"LED {device_id} control failed: {result}")
                
            return result
        except Exception as e:
            self.logger.error(f"Error controlling LED {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def setup_button(self, device_id: str, pin: int) -> Dict[str, Any]:
        """
        Set up a button connected to a GPIO pin.
        
        Args:
            device_id: Unique identifier for the button device
            pin: GPIO pin number the button is connected to
            
        Returns:
            Dictionary with setup result
        """
        try:
            self.logger.info(f"Setting up button {device_id} on pin {pin}")
            result = await self.client.setup_button(device_id, pin)
            
            if result.get("status") == "success":
                self.devices[device_id] = {"type": "button", "pin": pin}
                self.logger.info(f"Button {device_id} setup successful")
            else:
                self.logger.error(f"Button {device_id} setup failed: {result}")
                
            return result
        except Exception as e:
            self.logger.error(f"Error setting up button {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def read_button(self, device_id: str) -> Dict[str, Any]:
        """
        Read the state of a button.
        
        Args:
            device_id: Identifier for the button device
            
        Returns:
            Dictionary with button state
        """
        try:
            if device_id not in self.devices:
                self.logger.error(f"Device {device_id} not found")
                return {"status": "error", "message": f"Device {device_id} not found"}
                
            self.logger.info(f"Reading button {device_id}")
            result = await self.client.read_button(device_id)
            
            if result.get("status") == "success":
                self.logger.info(f"Button {device_id} read: {result.get('value')}")
            else:
                self.logger.error(f"Button {device_id} read failed: {result}")
                
            return result
        except Exception as e:
            self.logger.error(f"Error reading button {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def setup_traffic_light(
            self, 
            device_id: str, 
            red_pin: int, 
            yellow_pin: int, 
            green_pin: int
    ) -> Dict[str, Any]:
        """
        Set up a traffic light with three LEDs.
        
        Args:
            device_id: Unique identifier for the traffic light
            red_pin: GPIO pin number for the red LED
            yellow_pin: GPIO pin number for the yellow LED
            green_pin: GPIO pin number for the green LED
            
        Returns:
            Dictionary with setup result
        """
        try:
            self.logger.info(f"Setting up traffic light {device_id}")
            result = await self.client.setup_traffic_light(
                device_id, red_pin, yellow_pin, green_pin
            )
            
            if result.get("status") == "success":
                self.devices[device_id] = {
                    "type": "traffic_light",
                    "pins": {
                        "red": red_pin,
                        "yellow": yellow_pin,
                        "green": green_pin
                    }
                }
                self.logger.info(f"Traffic light {device_id} setup successful")
            else:
                self.logger.error(f"Traffic light {device_id} setup failed: {result}")
                
            return result
        except Exception as e:
            self.logger.error(f"Error setting up traffic light {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def control_traffic_light(
            self, 
            device_id: str, 
            state: str, 
            duration: float = None
    ) -> Dict[str, Any]:
        """
        Control a traffic light device.
        
        Args:
            device_id: Identifier for the traffic light device
            state: State to set (red, yellow, green, off, cycle)
            duration: Duration in seconds for temporary states
            
        Returns:
            Dictionary with control result
        """
        try:
            if device_id not in self.devices:
                self.logger.error(f"Device {device_id} not found")
                return {"status": "error", "message": f"Device {device_id} not found"}
                
            params = {"device_id": device_id, "state": state}
            if duration is not None:
                params["duration"] = duration
                
            self.logger.info(f"Controlling traffic light {device_id}: {state}")
            result = await self.client.control_traffic_light(**params)
            
            if result.get("status") == "success":
                self.logger.info(f"Traffic light {device_id} control successful")
            else:
                self.logger.error(f"Traffic light {device_id} control failed: {result}")
                
            return result
        except Exception as e:
            self.logger.error(f"Error controlling traffic light {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def run_demo(self, demo_type: str = "led") -> Dict[str, Any]:
        """
        Run a demonstration of hardware control.
        
        Args:
            demo_type: Type of demo to run (led, button, traffic_light)
            
        Returns:
            Dictionary with demo result
        """
        try:
            self.logger.info(f"Running {demo_type} demo")
            
            if demo_type == "led":
                return await self._run_led_demo()
            elif demo_type == "button":
                return await self._run_button_demo()
            elif demo_type == "traffic_light":
                return await self._run_traffic_light_demo()
            else:
                self.logger.error(f"Unknown demo type: {demo_type}")
                return {"status": "error", "message": f"Unknown demo type: {demo_type}"}
        except Exception as e:
            self.logger.error(f"Error running {demo_type} demo: {e}")
            return {"status": "error", "message": str(e)}

    async def _run_led_demo(self) -> Dict[str, Any]:
        """Run LED demonstration."""
        device_id = "demo_led"
        pin = env.get_int("LED_PIN", 17)
        
        try:
            # Setup LED
            await self.setup_led(device_id, pin)
            
            # Turn on
            self.logger.info("Turning LED on")
            await self.control_led(device_id, "on")
            await asyncio.sleep(1)
            
            # Blink fast
            self.logger.info("Blinking LED fast")
            await self.control_led(
                device_id, 
                "blink", 
                on_time=env.get_float("FAST_BLINK", 0.1), 
                off_time=env.get_float("FAST_BLINK", 0.1),
                blink_count=5
            )
            await asyncio.sleep(2)
            
            # Blink slow
            self.logger.info("Blinking LED slow")
            await self.control_led(
                device_id, 
                "blink", 
                on_time=env.get_float("SLOW_BLINK", 0.5), 
                off_time=env.get_float("SLOW_BLINK", 0.5),
                blink_count=3
            )
            await asyncio.sleep(3)
            
            # Turn off
            self.logger.info("Turning LED off")
            await self.control_led(device_id, "off")
            
            return {"status": "success", "message": "LED demo completed successfully"}
        except Exception as e:
            self.logger.error(f"Error in LED demo: {e}")
            # Try to turn off LED
            try:
                await self.control_led(device_id, "off")
            except:
                pass
            return {"status": "error", "message": str(e)}

    async def _run_button_demo(self) -> Dict[str, Any]:
        """Run button demonstration."""
        device_id = "demo_button"
        pin = env.get_int("BUTTON_PIN", 27)
        led_id = "demo_led"
        led_pin = env.get_int("LED_PIN", 17)
        
        try:
            # Setup button and LED
            await self.setup_button(device_id, pin)
            await self.setup_led(led_id, led_pin)
            
            self.logger.info("Press the button to toggle the LED (5 times)")
            
            for i in range(5):
                self.logger.info(f"Waiting for button press {i+1}/5...")
                
                # Wait for button press
                while True:
                    result = await self.read_button(device_id)
                    if result.get("value") == 1:
                        break
                    await asyncio.sleep(0.1)
                
                # Toggle LED
                self.logger.info("Button pressed, turning LED on")
                await self.control_led(led_id, "on")
                await asyncio.sleep(0.5)
                
                # Wait for button release
                while True:
                    result = await self.read_button(device_id)
                    if result.get("value") == 0:
                        break
                    await asyncio.sleep(0.1)
                
                self.logger.info("Button released, turning LED off")
                await self.control_led(led_id, "off")
            
            return {"status": "success", "message": "Button demo completed successfully"}
        except Exception as e:
            self.logger.error(f"Error in button demo: {e}")
            # Try to turn off LED
            try:
                await self.control_led(led_id, "off")
            except:
                pass
            return {"status": "error", "message": str(e)}

    async def _run_traffic_light_demo(self) -> Dict[str, Any]:
        """Run traffic light demonstration."""
        device_id = "demo_traffic"
        red_pin = env.get_int("RED_PIN", 17)
        yellow_pin = env.get_int("YELLOW_PIN", 27)
        green_pin = env.get_int("GREEN_PIN", 22)
        
        try:
            # Setup traffic light
            await self.setup_traffic_light(device_id, red_pin, yellow_pin, green_pin)
            
            # Run through states
            self.logger.info("Traffic light demo: Red")
            await self.control_traffic_light(device_id, "red")
            await asyncio.sleep(2)
            
            self.logger.info("Traffic light demo: Yellow")
            await self.control_traffic_light(device_id, "yellow")
            await asyncio.sleep(2)
            
            self.logger.info("Traffic light demo: Green")
            await self.control_traffic_light(device_id, "green")
            await asyncio.sleep(2)
            
            self.logger.info("Traffic light demo: Cycle")
            await self.control_traffic_light(device_id, "cycle", duration=10)
            
            self.logger.info("Traffic light demo: Off")
            await self.control_traffic_light(device_id, "off")
            
            return {"status": "success", "message": "Traffic light demo completed successfully"}
        except Exception as e:
            self.logger.error(f"Error in traffic light demo: {e}")
            # Try to turn off traffic light
            try:
                await self.control_traffic_light(device_id, "off")
            except:
                pass
            return {"status": "error", "message": str(e)}


async def main():
    """Main entry point for the Raspberry Pi hardware client example."""
    print("UnitMCP Raspberry Pi Hardware Client Example")
    print("===========================================")
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Raspberry Pi Hardware Client Example")
    parser.add_argument("--host", type=str, help="Raspberry Pi host address")
    parser.add_argument("--port", type=int, help="MCP server port")
    parser.add_argument("--demo", choices=["led", "button", "traffic_light"], 
                      default="led", help="Demo type to run")
    
    args = parser.parse_args()
    
    # Create client
    client = RPiHardwareClient(host=args.host, port=args.port)
    
    try:
        # Connect to server
        connected = await client.connect()
        if not connected:
            print("Failed to connect to MCP server. Exiting.")
            return
        
        # Run demo
        print(f"Running {args.demo} demo...")
        result = await client.run_demo(args.demo)
        
        if result.get("status") == "success":
            print(f"Demo completed successfully: {result.get('message')}")
        else:
            print(f"Demo failed: {result.get('message')}")
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect
        await client.disconnect()
        print("Disconnected from MCP server")


if __name__ == "__main__":
    asyncio.run(main())
