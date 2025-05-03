#!/usr/bin/env python3
"""
Device Factory Module for UnitMCP

This module implements the Factory Pattern for hardware device creation in UnitMCP.
It provides a unified interface for creating different types of hardware devices
and concrete factory implementations for specific device types.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Type

from .base import Device, DeviceType, DeviceMode
from .led import LEDDevice
from .button import ButtonDevice
from .traffic_light import TrafficLightDevice
from .display import DisplayDevice, DisplayType
from ..utils.env_loader import EnvLoader

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env = EnvLoader()


class DeviceFactory(ABC):
    """
    Abstract base class for device factories.
    
    This class defines the interface that all device factory implementations must follow.
    """
    
    @abstractmethod
    async def create_device(
        self, 
        device_id: str, 
        device_type: Union[DeviceType, str], 
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ) -> Optional[Device]:
        """
        Create a device of the specified type.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device to create
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Device parameters
            
        Returns:
            An instance of the appropriate device class, or None if creation failed
        """
        pass


class HardwareDeviceFactory(DeviceFactory):
    """
    Factory for hardware devices.
    
    This class provides functionality for creating hardware devices like LEDs, buttons,
    traffic lights, and displays.
    """
    
    async def create_device(
        self, 
        device_id: str, 
        device_type: Union[DeviceType, str], 
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ) -> Optional[Device]:
        """
        Create a hardware device of the specified type.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device to create (LED, BUTTON, TRAFFIC_LIGHT, DISPLAY, etc.)
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Device parameters
            
        Returns:
            An instance of the appropriate device class, or None if creation failed
        """
        try:
            # Convert string device type to enum if needed
            if isinstance(device_type, str):
                try:
                    device_type = DeviceType(device_type.upper())
                except ValueError:
                    logger.error(f"Unknown device type: {device_type}")
                    return None
            
            # Convert string mode to enum if needed
            if isinstance(mode, str):
                try:
                    mode = DeviceMode(mode.upper())
                except ValueError:
                    logger.error(f"Unknown device mode: {mode}")
                    return None
            
            # Use default mode if not specified
            if mode is None:
                # Check if we're running on a Raspberry Pi
                try:
                    import RPi.GPIO
                    mode = DeviceMode.HARDWARE
                except ImportError:
                    mode = DeviceMode.SIMULATION
                    logger.warning("RPi.GPIO not available, defaulting to simulation mode")
            
            # Create the appropriate device based on type
            if device_type == DeviceType.LED:
                pin = kwargs.get('pin')
                device = LEDDevice(device_id, pin, mode, **kwargs)
                logger.info(f"Created LED device '{device_id}' on pin {pin} (mode: {mode.value})")
                return device
                
            elif device_type == DeviceType.BUTTON:
                pin = kwargs.get('pin')
                pull_up = kwargs.get('pull_up', True)
                debounce_ms = kwargs.get('debounce_ms', 50)
                device = ButtonDevice(device_id, pin, mode, pull_up, debounce_ms, **kwargs)
                logger.info(f"Created button device '{device_id}' on pin {pin} (mode: {mode.value})")
                return device
                
            elif device_type == DeviceType.TRAFFIC_LIGHT:
                red_pin = kwargs.get('red_pin')
                yellow_pin = kwargs.get('yellow_pin')
                green_pin = kwargs.get('green_pin')
                device = TrafficLightDevice(device_id, red_pin, yellow_pin, green_pin, mode, **kwargs)
                logger.info(f"Created traffic light device '{device_id}' (mode: {mode.value})")
                return device
                
            elif device_type == DeviceType.DISPLAY:
                display_type = kwargs.get('display_type')
                width = kwargs.get('width')
                height = kwargs.get('height')
                address = kwargs.get('address')
                device = DisplayDevice(device_id, display_type, width, height, address, mode, **kwargs)
                logger.info(f"Created display device '{device_id}' of type {display_type} (mode: {mode.value})")
                return device
                
            else:
                logger.error(f"Unsupported device type: {device_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating device '{device_id}' of type {device_type}: {e}")
            return None


class GPIODeviceFactory(HardwareDeviceFactory):
    """
    Factory for GPIO-based hardware devices.
    
    This class provides functionality for creating hardware devices that use GPIO pins,
    such as LEDs, buttons, and traffic lights.
    """
    
    async def create_device(
        self, 
        device_id: str, 
        device_type: Union[DeviceType, str], 
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ) -> Optional[Device]:
        """
        Create a GPIO-based hardware device of the specified type.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device to create (LED, BUTTON, TRAFFIC_LIGHT)
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Device parameters
            
        Returns:
            An instance of the appropriate device class, or None if creation failed
        """
        # Only support GPIO-compatible device types
        if isinstance(device_type, str):
            try:
                device_type = DeviceType(device_type.upper())
            except ValueError:
                logger.error(f"Invalid device type: {device_type}")
                return None
        
        if device_type not in [DeviceType.LED, DeviceType.BUTTON, DeviceType.TRAFFIC_LIGHT]:
            logger.error(f"Device type {device_type} is not compatible with GPIO")
            return None
        
        # Ensure GPIO pin is specified
        if 'pin' not in kwargs and 'pins' not in kwargs:
            logger.error(f"GPIO pin(s) must be specified for device {device_id}")
            return None
        
        # Create the device using the parent class method
        return await super().create_device(device_id, device_type, mode, **kwargs)


class SimulationDeviceFactory(HardwareDeviceFactory):
    """
    Factory for simulation devices.
    
    This class provides functionality for creating simulated devices.
    It extends the HardwareDeviceFactory but forces the mode to be simulation.
    """
    
    async def create_device(
        self, 
        device_id: str, 
        device_type: Union[DeviceType, str], 
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ) -> Optional[Device]:
        """
        Create a simulated device of the specified type.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device to create
            mode: Ignored, always set to simulation
            **kwargs: Device parameters
            
        Returns:
            An instance of the appropriate device class in simulation mode, or None if creation failed
        """
        # Force simulation mode
        return await super().create_device(device_id, device_type, DeviceMode.SIMULATION, **kwargs)


class RemoteDeviceFactory(HardwareDeviceFactory):
    """
    Factory for remote devices.
    
    This class provides functionality for creating remote-controlled devices.
    It extends the HardwareDeviceFactory but forces the mode to be remote.
    """
    
    async def create_device(
        self, 
        device_id: str, 
        device_type: Union[DeviceType, str], 
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ) -> Optional[Device]:
        """
        Create a remote-controlled device of the specified type.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device to create
            mode: Ignored, always set to remote
            **kwargs: Device parameters
            
        Returns:
            An instance of the appropriate device class in remote mode, or None if creation failed
        """
        # Force remote mode
        return await super().create_device(device_id, device_type, DeviceMode.REMOTE, **kwargs)


class MockDeviceFactory(HardwareDeviceFactory):
    """
    Factory for mock devices.
    
    This class provides functionality for creating mock devices for testing.
    It extends the HardwareDeviceFactory but forces the mode to be mock.
    """
    
    async def create_device(
        self, 
        device_id: str, 
        device_type: Union[DeviceType, str], 
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ) -> Optional[Device]:
        """
        Create a mock device of the specified type.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device to create
            mode: Ignored, always set to mock
            **kwargs: Device parameters
            
        Returns:
            An instance of the appropriate device class in mock mode, or None if creation failed
        """
        # Force mock mode
        return await super().create_device(device_id, device_type, DeviceMode.MOCK, **kwargs)


# Factory registry
device_factories = {
    "hardware": HardwareDeviceFactory(),
    "simulation": SimulationDeviceFactory(),
    "remote": RemoteDeviceFactory(),
    "mock": MockDeviceFactory(),
    "gpio": GPIODeviceFactory()
}


async def get_device_factory(factory_type: str) -> Optional[DeviceFactory]:
    """
    Get a device factory of the specified type.
    
    Args:
        factory_type: Type of factory to get
        
    Returns:
        An instance of the appropriate factory class, or None if not found
    """
    factory_type = factory_type.lower()
    if factory_type in device_factories:
        return device_factories[factory_type]
    else:
        logger.error(f"Unknown factory type: {factory_type}")
        return None


def register_device_factory(factory_type: str, factory: DeviceFactory) -> None:
    """
    Register a device factory.
    
    Args:
        factory_type: Type of factory to register
        factory: Factory instance to register
    """
    factory_type = factory_type.lower()
    device_factories[factory_type] = factory
    logger.info(f"Registered device factory: {factory_type}")


async def create_device(
    factory_type: str, 
    device_id: str, 
    device_type: Union[DeviceType, str], 
    **kwargs
) -> Optional[Device]:
    """
    Create a device using the specified factory.
    
    Args:
        factory_type: Type of factory to use
        device_id: Unique identifier for the device
        device_type: Type of device to create
        **kwargs: Device parameters
        
    Returns:
        An instance of the appropriate device class, or None if creation failed
    """
    factory = await get_device_factory(factory_type)
    if factory:
        return await factory.create_device(device_id, device_type, **kwargs)
    else:
        return None


async def create_devices_from_config(config: Dict[str, Any]) -> Dict[str, Device]:
    """
    Create multiple devices from a configuration dictionary.
    
    Args:
        config: Configuration dictionary with device specifications
        
    Returns:
        Dictionary mapping device IDs to device instances
    """
    devices = {}
    
    if "devices" not in config:
        logger.error("No devices specified in configuration")
        return devices
    
    for device_config in config["devices"]:
        device_id = device_config.get("id")
        device_type = device_config.get("type")
        factory_type = device_config.get("factory", "hardware")
        
        if not device_id or not device_type:
            logger.error("Device configuration missing required fields: id, type")
            continue
        
        # Extract device parameters
        params = {k: v for k, v in device_config.items() if k not in ["id", "type", "factory"]}
        
        # Create the device
        device = await create_device(factory_type, device_id, device_type, **params)
        
        if device:
            devices[device_id] = device
    
    return devices
