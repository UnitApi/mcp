"""
Device Converter for UnitMCP

This module provides functionality for converting DSL device configurations
into UnitMCP device objects.
"""

from typing import Dict, Any, List, Optional, Type
import logging
import importlib
import inspect
import os

from .mock_factory import MockDeviceFactory

logger = logging.getLogger(__name__)

class DeviceConverter:
    """
    Converter for DSL device configurations.
    
    This class handles the conversion of DSL device configurations
    into UnitMCP device objects.
    """
    
    def __init__(self, device_factory=None):
        """
        Initialize the device converter.
        
        Args:
            device_factory: Optional device factory instance.
                           If not provided, it will be imported from the hardware module.
        """
        self._device_factory = device_factory
        if not self._device_factory:
            try:
                # Import device factory dynamically
                from unitmcp.hardware.device_factory import DeviceFactory
                self._device_factory = DeviceFactory()
            except ImportError as e:
                logger.error(f"Failed to import DeviceFactory: {e}")
                # Use our mock implementation as fallback
                self._device_factory = MockDeviceFactory()
    
    async def convert_to_devices(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert DSL configuration to UnitMCP devices.
        
        Args:
            config: The DSL configuration dictionary
        
        Returns:
            A dictionary mapping device IDs to device instances
        
        Raises:
            ValueError: If the configuration is invalid or a device cannot be created
        """
        if 'devices' not in config:
            raise ValueError("Configuration must contain a 'devices' section")
        
        devices = {}
        device_configs = config['devices']
        
        # Handle dictionary format
        if isinstance(device_configs, dict):
            for device_id, device_config in device_configs.items():
                device = await self._create_device(device_id, device_config)
                devices[device_id] = device
        
        # Handle list format
        elif isinstance(device_configs, list):
            for device_config in device_configs:
                if 'name' not in device_config:
                    raise ValueError("Device configuration must contain a 'name' field")
                
                device_id = device_config['name']
                device = await self._create_device(device_id, device_config)
                devices[device_id] = device
        
        else:
            raise ValueError("Invalid devices configuration format")
        
        return devices
    
    async def _create_device(self, device_id: str, config: Dict[str, Any]) -> Any:
        """
        Create a device from a configuration.
        
        Args:
            device_id: The device ID
            config: The device configuration
        
        Returns:
            The created device instance
        
        Raises:
            ValueError: If the device cannot be created
        """
        # Determine the device type
        device_type = config.get('type', config.get('platform'))
        if not device_type:
            raise ValueError(f"Device '{device_id}' is missing a type or platform")
        
        # Create the device using the factory
        try:
            # Map DSL device types to factory methods
            if hasattr(self._device_factory, f"create_{device_type}"):
                # Direct method call (e.g., create_led, create_button)
                create_method = getattr(self._device_factory, f"create_{device_type}")
                return await create_method(device_id=device_id, **config)
            elif hasattr(self._device_factory, "create_device"):
                # Generic create_device method
                return await self._device_factory.create_device(
                    device_id=device_id,
                    device_type=device_type,
                    **config
                )
            else:
                # Try to use the create_from_config method if available
                if hasattr(self._device_factory, "create_from_config"):
                    return await self._device_factory.create_from_config(
                        device_id=device_id,
                        config=config
                    )
                else:
                    raise ValueError(
                        f"Device factory does not support creating device type '{device_type}'"
                    )
        except Exception as e:
            logger.error(f"Failed to create device '{device_id}': {e}")
            raise ValueError(f"Failed to create device '{device_id}': {e}")


class ConcreteDeviceConverter(DeviceConverter):
    """
    Concrete implementation of the DeviceConverter.
    """
    
    def create_device(self, device_type: str, config: Dict[str, Any]) -> Any:
        """
        Create a device instance based on the device type and configuration.
        
        Args:
            device_type: The type of device to create
            config: The device configuration
            
        Returns:
            Any: The created device instance
        """
        logger.info(f"Creating device of type {device_type} with config {config}")
        
        # Simulate device creation
        return {
            'type': device_type,
            'config': config,
            'status': 'initialized'
        }


class ConcreteDeviceFactory:
    def create_led(self, device_id: str, **config) -> Any:
        return ConcreteDeviceConverter().create_device('led', config)

    def create_button(self, device_id: str, **config) -> Any:
        return ConcreteDeviceConverter().create_device('button', config)
