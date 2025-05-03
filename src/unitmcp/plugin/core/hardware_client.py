"""
Hardware client integration for UnitMCP Claude Plugin.

This module provides a client for connecting to UnitMCP hardware
from the Claude plugin, with support for simulation mode.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

from unitmcp.plugin.nl.parser import NLCommandParser
from unitmcp.plugin.core.error_handling import NLErrorHandler

logger = logging.getLogger(__name__)

class PluginHardwareClient:
    """
    Client for connecting to UnitMCP hardware from the Claude plugin.
    
    This client provides methods for executing hardware commands
    parsed from natural language input.
    """
    
    def __init__(self, host="localhost", port=8888, simulation_mode=True):
        """
        Initialize the hardware client.
        
        Args:
            host: Hostname or IP address of the UnitMCP server
            port: Port number of the UnitMCP server
            simulation_mode: Whether to run in simulation mode
        """
        # In a real implementation, this would import the actual client
        # self.client = MCPHardwareClient(host, port, simulation_mode)
        self.host = host
        self.port = port
        self.simulation_mode = simulation_mode
        
        # Use our MockDeviceFactory for testing in simulation mode
        if simulation_mode:
            try:
                from unitmcp.dsl.converters.mock_factory import MockDeviceFactory
                self.device_factory = MockDeviceFactory()
                logger.info("Using MockDeviceFactory for simulation mode")
            except ImportError:
                logger.warning("MockDeviceFactory not available, using simulation fallback")
                self.device_factory = None
        else:
            try:
                from unitmcp.hardware.factory import DeviceFactory
                self.device_factory = DeviceFactory()
                logger.info("Using DeviceFactory for hardware mode")
            except ImportError:
                logger.warning("DeviceFactory not available")
                self.device_factory = None
        
        self.nl_parser = NLCommandParser()
        self.error_handler = NLErrorHandler()
        self.devices = {}
        
    async def connect(self):
        """Establish connection to the UnitMCP hardware server."""
        logger.info(f"Connecting to UnitMCP server at {self.host}:{self.port}")
        
        # In a real implementation, this would connect to the server
        # await self.client.connect()
        
        # For simulation, we'll just create a mock connection
        if self.simulation_mode:
            logger.info("Running in simulation mode, no actual connection needed")
            await asyncio.sleep(0.1)  # Simulate connection time
            return True
        
        # For now, we'll just simulate a successful connection
        logger.info("Connected to UnitMCP server")
        return True
        
    async def execute_nl_command(self, nl_command: str) -> Dict[str, Any]:
        """
        Execute a natural language hardware command.
        
        Args:
            nl_command: The natural language command from the user
            
        Returns:
            A dictionary containing the result of the command execution
        """
        try:
            # Parse the natural language command
            parsed_command = await self.nl_parser.parse_command(nl_command)
            
            if parsed_command.get("status") == "error":
                return parsed_command
            
            # Execute the parsed command
            result = await self.execute_command(
                parsed_command["device_type"],
                parsed_command["device_id"],
                parsed_command["action"],
                parsed_command["parameters"]
            )
            
            return {
                "status": "success",
                "result": result,
                "nl_command": nl_command,
                "parsed_command": parsed_command
            }
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return self.error_handler.handle_command_error(e, nl_command)
    
    async def execute_command(self, device_type: str, device_id: str, 
                             action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a parsed hardware command.
        
        Args:
            device_type: Type of device (e.g., "led", "button")
            device_id: Identifier for the device
            action: Action to perform (e.g., "on", "off")
            parameters: Parameters for the action
            
        Returns:
            A dictionary containing the result of the command execution
        """
        logger.info(f"Executing command: {device_type}.{device_id}.{action}({parameters})")
        
        # Get or create the device
        device = await self._get_or_create_device(device_type, device_id)
        
        if not device:
            raise ValueError(f"Could not create device of type {device_type} with ID {device_id}")
        
        # Execute the action on the device
        if self.simulation_mode:
            # In simulation mode, we'll just log the action
            logger.info(f"Simulation: {device_type}.{device_id}.{action}({parameters})")
            result = await self._simulate_action(device, action, parameters)
        else:
            # In real mode, we'd execute the action on the actual device
            # result = await device.execute(action, **parameters)
            result = {"status": "success", "message": f"Executed {action} on {device_type} {device_id}"}
        
        return result
    
    async def _get_or_create_device(self, device_type: str, device_id: str) -> Any:
        """Get an existing device or create a new one."""
        device_key = f"{device_type}:{device_id}"
        
        if device_key in self.devices:
            return self.devices[device_key]
        
        # Create a new device
        if self.device_factory:
            try:
                # Create the device using the factory
                device_config = self._create_device_config(device_type, device_id)
                device = await self.device_factory.create_device(device_config)
                self.devices[device_key] = device
                return device
            except Exception as e:
                logger.error(f"Error creating device: {str(e)}")
                return None
        
        # If no factory is available, return a mock device
        return self._create_mock_device(device_type, device_id)
    
    def _create_device_config(self, device_type: str, device_id: str) -> Dict[str, Any]:
        """Create a device configuration for the factory."""
        # Basic configuration for different device types
        configs = {
            "led": {
                "type": "led",
                "pin": 17,  # Default pin
                "name": device_id
            },
            "button": {
                "type": "button",
                "pin": 27,  # Default pin
                "name": device_id,
                "pull_up": True
            },
            "display": {
                "type": "display",
                "name": device_id,
                "width": 128,
                "height": 64
            },
            "traffic_light": {
                "type": "traffic_light",
                "name": device_id,
                "red_pin": 17,
                "yellow_pin": 27,
                "green_pin": 22
            }
        }
        
        return configs.get(device_type, {"type": device_type, "name": device_id})
    
    def _create_mock_device(self, device_type: str, device_id: str) -> Any:
        """Create a mock device for simulation."""
        # This is a very simple mock implementation
        class MockDevice:
            def __init__(self, device_type, device_id):
                self.device_type = device_type
                self.device_id = device_id
                self.state = {}
            
            async def execute(self, action, **parameters):
                logger.info(f"Mock device {self.device_type}.{self.device_id} executing {action}({parameters})")
                return {"status": "success", "action": action, "parameters": parameters}
        
        device = MockDevice(device_type, device_id)
        self.devices[f"{device_type}:{device_id}"] = device
        return device
    
    async def _simulate_action(self, device: Any, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate an action on a device."""
        # If the device has an execute method, use it
        if hasattr(device, "execute"):
            try:
                return await device.execute(action, **parameters)
            except Exception as e:
                logger.error(f"Error executing action on device: {str(e)}")
                return {"status": "error", "error": str(e)}
        
        # Otherwise, just return a simulated result
        return {
            "status": "success",
            "message": f"Simulated {action} on {device.device_type} {device.device_id}",
            "parameters": parameters
        }
