#!/usr/bin/env python3
"""
Traffic Light Demo for UnitMCP.

This example demonstrates how to control a traffic light system using the UnitMCP library.
It shows how to set up and control multiple LEDs in a traffic light pattern.
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
logger = logging.getLogger("TrafficLightDemo")


class TrafficLightDemo:
    """Traffic light demo for UnitMCP."""

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the traffic light demo.
        
        Args:
            host: Host address of the Raspberry Pi
            port: Port number for the MCP server
        """
        self.host = host or env.get('RPI_HOST', 'localhost')
        self.port = port or env.get_int('RPI_PORT', 8080)
        self.client = MCPHardwareClient(self.host, self.port)
        self.logger = logging.getLogger("TrafficLightDemo")
        
        # Traffic light configuration
        self.traffic_light_id = "demo_traffic_light"
        self.red_pin = env.get_int('RED_PIN', 17)
        self.yellow_pin = env.get_int('YELLOW_PIN', 27)
        self.green_pin = env.get_int('GREEN_PIN', 22)
        
        # Timing configuration (in seconds)
        self.red_duration = env.get_float('RED_DURATION', 3.0)
        self.yellow_duration = env.get_float('YELLOW_DURATION', 1.0)
        self.green_duration = env.get_float('GREEN_DURATION', 3.0)

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

    async def setup_traffic_light(self) -> bool:
        """
        Set up the traffic light with the configured pins.
        
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            self.logger.info(f"Setting up traffic light {self.traffic_light_id} with pins: "
                            f"Red={self.red_pin}, Yellow={self.yellow_pin}, Green={self.green_pin}")
            
            result = await self.client.setup_traffic_light(
                self.traffic_light_id,
                self.red_pin,
                self.yellow_pin,
                self.green_pin
            )
            
            if result.get('success', False):
                self.logger.info("Traffic light setup successful")
                return True
            else:
                self.logger.error(f"Traffic light setup failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up traffic light: {e}")
            return False

    async def control_traffic_light(self, state: str, duration: float = None) -> bool:
        """
        Control the traffic light state.
        
        Args:
            state: The state to set ('red', 'yellow', 'green', 'off', 'cycle')
            duration: Optional duration for the state (in seconds)
            
        Returns:
            True if control was successful, False otherwise
        """
        try:
            self.logger.info(f"Setting traffic light to {state}" + 
                           (f" for {duration} seconds" if duration else ""))
            
            result = await self.client.control_traffic_light(
                self.traffic_light_id,
                state,
                duration=duration
            )
            
            if result.get('success', False):
                self.logger.info(f"Traffic light control successful: {state}")
                return True
            else:
                self.logger.error(f"Traffic light control failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error controlling traffic light: {e}")
            return False

    async def run_traffic_cycle(self, cycles: int = 1) -> bool:
        """
        Run a complete traffic light cycle.
        
        Args:
            cycles: Number of cycles to run
            
        Returns:
            True if all cycles completed successfully, False otherwise
        """
        try:
            self.logger.info(f"Running {cycles} traffic light cycle(s)")
            
            for i in range(cycles):
                self.logger.info(f"Cycle {i+1}/{cycles}")
                
                # Red light
                if not await self.control_traffic_light('red', self.red_duration):
                    return False
                await asyncio.sleep(self.red_duration)
                
                # Green light
                if not await self.control_traffic_light('green', self.green_duration):
                    return False
                await asyncio.sleep(self.green_duration)
                
                # Yellow light
                if not await self.control_traffic_light('yellow', self.yellow_duration):
                    return False
                await asyncio.sleep(self.yellow_duration)
            
            # Turn off all lights at the end
            await self.control_traffic_light('off')
            
            self.logger.info(f"Completed {cycles} traffic light cycle(s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error running traffic light cycle: {e}")
            return False

    async def run_demo(self) -> Tuple[bool, str]:
        """
        Run the complete traffic light demo.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Connect to the server
            if not await self.connect():
                return False, "Failed to connect to MCP server"
                
            # Set up the traffic light
            if not await self.setup_traffic_light():
                return False, "Failed to set up traffic light"
                
            # Run a normal cycle
            self.logger.info("Running normal traffic light cycle")
            if not await self.run_traffic_cycle(2):
                return False, "Failed to run normal traffic cycle"
                
            # Run a custom pattern
            self.logger.info("Running custom traffic light pattern")
            
            # Blink red light
            for _ in range(3):
                await self.control_traffic_light('red')
                await asyncio.sleep(0.5)
                await self.control_traffic_light('off')
                await asyncio.sleep(0.5)
                
            # Blink yellow light
            for _ in range(3):
                await self.control_traffic_light('yellow')
                await asyncio.sleep(0.3)
                await self.control_traffic_light('off')
                await asyncio.sleep(0.3)
                
            # Blink green light
            for _ in range(3):
                await self.control_traffic_light('green')
                await asyncio.sleep(0.2)
                await self.control_traffic_light('off')
                await asyncio.sleep(0.2)
                
            # Run one more normal cycle
            self.logger.info("Running final traffic light cycle")
            if not await self.run_traffic_cycle(1):
                return False, "Failed to run final traffic cycle"
                
            # Turn off all lights
            await self.control_traffic_light('off')
            
            return True, "Traffic light demo completed successfully"
            
        except Exception as e:
            self.logger.error(f"Error running traffic light demo: {e}")
            return False, f"Error: {str(e)}"
        finally:
            # Always disconnect
            await self.disconnect()


async def main():
    """Main entry point for the traffic light demo."""
    print("UnitMCP Traffic Light Demo")
    print("==========================")
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Traffic Light Demo")
    parser.add_argument("--host", type=str, help="Raspberry Pi host address")
    parser.add_argument("--port", type=int, help="MCP server port")
    parser.add_argument("--cycles", type=int, default=2, help="Number of traffic light cycles to run")
    
    args = parser.parse_args()
    
    # Create and run the demo
    demo = TrafficLightDemo(
        host=args.host,
        port=args.port
    )
    
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
