"""
DSL Integration for UnitMCP

This module provides integration between the DSL system and
the existing UnitMCP hardware abstraction layer.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
import os
import yaml

from .compiler import DslCompiler
from .converters.to_devices import DeviceConverter
from .converters.mock_factory import MockDeviceFactory
from unitmcp import MCPHardwareClient

logger = logging.getLogger(__name__)

class DslHardwareIntegration:
    """
    Integration between DSL and the UnitMCP hardware abstraction layer.
    
    This class provides methods for creating and controlling hardware devices
    using DSL configurations.
    """
    
    def __init__(self, device_factory=None, simulation=False):
        """
        Initialize the DSL hardware integration.
        
        Args:
            device_factory: Optional device factory instance.
                           If not provided, it will be imported from the hardware module.
            simulation: Whether to run in simulation mode
        """
        self.compiler = DslCompiler()
        
        # Use mock factory if in simulation mode or if no factory is provided
        if simulation or device_factory is None:
            device_factory = MockDeviceFactory()
            
        self.device_converter = DeviceConverter(device_factory)
        self.devices = {}
        self.simulation = simulation
    
    async def load_config_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and process a DSL configuration file.
        
        Args:
            file_path: Path to the configuration file
        
        Returns:
            A dictionary containing the created devices
        
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file cannot be parsed or the configuration is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Determine the format based on file extension
        format_type = None
        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
            format_type = 'yaml'
        elif file_path.endswith('.json'):
            format_type = 'json'
        
        # Compile the DSL content
        return await self.load_config(content, format_type)
    
    async def load_config(self, content: str, format_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Load and process a DSL configuration string.
        
        Args:
            content: The DSL configuration content
            format_type: Optional format type ('yaml', 'json', 'text')
        
        Returns:
            A dictionary containing the created devices
        
        Raises:
            ValueError: If the content cannot be parsed or the configuration is invalid
        """
        # Compile the DSL content
        config = self.compiler.compile(content, format_type)
        
        # Create devices from the configuration
        if 'devices' in config:
            devices = await self.device_converter.convert_to_devices(config)
            self.devices.update(devices)
        
        return {
            'devices': self.devices,
            'config': config
        }
    
    async def initialize_devices(self) -> Dict[str, bool]:
        """
        Initialize all created devices.
        
        Returns:
            A dictionary mapping device IDs to initialization status
        """
        results = {}
        
        for device_id, device in self.devices.items():
            try:
                success = await device.initialize()
                results[device_id] = success
            except Exception as e:
                logger.error(f"Failed to initialize device '{device_id}': {e}")
                results[device_id] = False
        
        return results
    
    async def cleanup_devices(self) -> Dict[str, bool]:
        """
        Clean up all created devices.
        
        Returns:
            A dictionary mapping device IDs to cleanup status
        """
        results = {}
        
        for device_id, device in self.devices.items():
            try:
                if hasattr(device, 'cleanup'):
                    success = await device.cleanup()
                    results[device_id] = success
                else:
                    results[device_id] = True
            except Exception as e:
                logger.error(f"Failed to clean up device '{device_id}': {e}")
                results[device_id] = False
        
        return results
    
    def get_device(self, device_id: str) -> Any:
        """
        Get a device by ID.
        
        Args:
            device_id: The device ID
        
        Returns:
            The device instance
        
        Raises:
            KeyError: If the device does not exist
        """
        if device_id not in self.devices:
            raise KeyError(f"Device '{device_id}' not found")
        
        return self.devices[device_id]
    
    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on a device.
        
        Args:
            command: The command dictionary
        
        Returns:
            The command result
        
        Raises:
            ValueError: If the command is invalid
            KeyError: If the device does not exist
        """
        if 'device' not in command:
            raise ValueError("Command must specify a device")
        
        if 'action' not in command:
            raise ValueError("Command must specify an action")
        
        device_id = command['device']
        action = command['action']
        params = command.get('parameters', {})
        
        device = self.get_device(device_id)
        
        # Execute the action on the device
        if hasattr(device, action):
            method = getattr(device, action)
            result = await method(**params)
            return {
                'status': 'success',
                'device': device_id,
                'action': action,
                'result': result
            }
        else:
            raise ValueError(f"Device '{device_id}' does not support action '{action}'")
