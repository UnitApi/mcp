"""
GPIO Hardware Module

This module provides GPIO control functionality for UnitMCP.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union

from ..client.client import MCPHardwareClient

logger = logging.getLogger(__name__)

class GPIOController:
    """Controller for GPIO operations."""

    def __init__(self, client: Optional[MCPHardwareClient] = None):
        """
        Initialize the GPIO controller.
        
        Args:
            client: An optional MCPHardwareClient instance
        """
        self.client = client

    def set_client(self, client: MCPHardwareClient):
        """
        Set the client for GPIO operations.
        
        Args:
            client: The MCPHardwareClient instance to use
        """
        self.client = client
        
    def is_connected(self) -> bool:
        """
        Check if the controller is connected to a server.
        
        Returns:
            True if connected, False otherwise
        """
        return self.client is not None and hasattr(self.client, "is_connected") and self.client.is_connected()

    async def setup_pin(self, pin: int, mode: str = "OUT") -> Dict[str, Any]:
        """
        Setup a GPIO pin.
        
        Args:
            pin: The GPIO pin number
            mode: The pin mode ('IN' or 'OUT')
            
        Returns:
            Result of the operation
        """
        if not self.client:
            return {"error": "Not connected to a server. Please connect first."}
            
        if not hasattr(self.client, "is_connected") or not self.client.is_connected():
            return {"error": "Connection to server lost. Please reconnect."}
        
        try:
            result = await self.client.setup_pin(pin, mode)
            return result
        except ConnectionError as e:
            logger.error(f"Connection error setting up GPIO pin: {e}")
            return {"error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error setting up GPIO pin: {e}")
            return {"error": str(e)}

    async def write_pin(self, pin: int, value: bool) -> Dict[str, Any]:
        """
        Write to a GPIO pin.
        
        Args:
            pin: The GPIO pin number
            value: The value to write (True for HIGH, False for LOW)
            
        Returns:
            Result of the operation
        """
        if not self.client:
            return {"error": "Not connected to a server. Please connect first."}
            
        if not hasattr(self.client, "is_connected") or not self.client.is_connected():
            return {"error": "Connection to server lost. Please reconnect."}
        
        try:
            result = await self.client.write_pin(pin, value)
            return result
        except ConnectionError as e:
            logger.error(f"Connection error writing to GPIO pin: {e}")
            return {"error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error writing to GPIO pin: {e}")
            return {"error": str(e)}

    async def read_pin(self, pin: int) -> Dict[str, Any]:
        """
        Read from a GPIO pin.
        
        Args:
            pin: The GPIO pin number
            
        Returns:
            Result of the operation with the pin value
        """
        if not self.client:
            return {"error": "Not connected to a server. Please connect first."}
            
        if not hasattr(self.client, "is_connected") or not self.client.is_connected():
            return {"error": "Connection to server lost. Please reconnect."}
        
        try:
            result = await self.client.read_pin(pin)
            return result
        except ConnectionError as e:
            logger.error(f"Connection error reading from GPIO pin: {e}")
            return {"error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error reading from GPIO pin: {e}")
            return {"error": str(e)}

    async def handle_command(self, command: str, args: List[str]) -> Dict[str, Any]:
        """
        Handle a GPIO command.
        
        Args:
            command: The GPIO command (setup, write, read)
            args: Command arguments
            
        Returns:
            Result of the operation
        """
        if not self.client:
            return {"error": "Not connected to a server. Please connect first."}
            
        if not hasattr(self.client, "is_connected") or not self.client.is_connected():
            return {"error": "Connection to server lost. Please reconnect."}
        
        if command == "setup":
            if len(args) < 2:
                return {"error": "Usage: gpio setup <pin> <mode>"}
            
            try:
                pin = int(args[0])
                mode = args[1].upper()
                if mode not in ["IN", "OUT"]:
                    return {"error": "Mode must be 'in' or 'out'"}
                
                return await self.setup_pin(pin, mode)
            except ValueError:
                return {"error": "Pin must be a number"}
        
        elif command == "write":
            if len(args) < 2:
                return {"error": "Usage: gpio write <pin> <value>"}
            
            try:
                pin = int(args[0])
                value_str = args[1].lower()
                
                if value_str in ["1", "high", "true", "on"]:
                    value = True
                elif value_str in ["0", "low", "false", "off"]:
                    value = False
                else:
                    return {"error": "Value must be 1/0, high/low, true/false, or on/off"}
                
                return await self.write_pin(pin, value)
            except ValueError:
                return {"error": "Pin must be a number"}
        
        elif command == "read":
            if len(args) < 1:
                return {"error": "Usage: gpio read <pin>"}
            
            try:
                pin = int(args[0])
                return await self.read_pin(pin)
            except ValueError:
                return {"error": "Pin must be a number"}
        
        else:
            return {"error": f"Unknown GPIO command: {command}"}

# Help documentation for GPIO commands
HELP_DOCUMENTATION = {
    "short": "Control GPIO pins on the connected hardware",
    "long": """
GPIO Commands:
  gpio setup <pin> <mode>   Setup a GPIO pin (mode: in, out)
  gpio write <pin> <value>  Write to a GPIO pin (value: 1/0, high/low, true/false, on/off)
  gpio read <pin>           Read from a GPIO pin

Examples:
  gpio setup 18 out         Setup pin 18 as output
  gpio write 18 1           Set pin 18 high
  gpio write 18 high        Set pin 18 high
  gpio read 18              Read the state of pin 18
""",
    "commands": {
        "setup": {
            "usage": "gpio setup <pin> <mode>",
            "description": "Setup a GPIO pin",
            "args": [
                {"name": "pin", "description": "GPIO pin number"},
                {"name": "mode", "description": "'in' or 'out'"}
            ],
            "examples": ["gpio setup 18 out"]
        },
        "write": {
            "usage": "gpio write <pin> <value>",
            "description": "Write to a GPIO pin",
            "args": [
                {"name": "pin", "description": "GPIO pin number"},
                {"name": "value", "description": "'1'/'0', 'high'/'low', 'true'/'false', or 'on'/'off'"}
            ],
            "examples": ["gpio write 18 high", "gpio write 18 1"]
        },
        "read": {
            "usage": "gpio read <pin>",
            "description": "Read from a GPIO pin",
            "args": [
                {"name": "pin", "description": "GPIO pin number"}
            ],
            "examples": ["gpio read 18"]
        }
    }
}
