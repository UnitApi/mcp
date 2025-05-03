#!/usr/bin/env python3
"""
Base Hardware Device Module for UnitMCP

This module defines the base classes for hardware devices in UnitMCP.
It provides a consistent interface that all hardware device implementations must follow.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable, Tuple, Union

from ..utils.env_loader import EnvLoader

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env = EnvLoader()


class DeviceType(Enum):
    """Enumeration of supported device types."""
    LED = "led"
    BUTTON = "button"
    SWITCH = "switch"
    RELAY = "relay"
    SENSOR = "sensor"
    DISPLAY = "display"
    MOTOR = "motor"
    SERVO = "servo"
    STEPPER = "stepper"
    TRAFFIC_LIGHT = "traffic_light"
    BUZZER = "buzzer"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_str(cls, value: str) -> 'DeviceType':
        """Convert a string to a DeviceType enum value.
        
        Args:
            value: String representation of the device type
            
        Returns:
            Corresponding DeviceType enum value, or UNKNOWN if not found
        """
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(f"Unknown device type: {value}")
            return cls.UNKNOWN


class DeviceState(Enum):
    """Enumeration of common device states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class DeviceMode(Enum):
    """Enumeration of device operation modes."""
    HARDWARE = "hardware"  # Real hardware mode
    SIMULATION = "simulation"  # Simulated hardware mode
    REMOTE = "remote"  # Remote hardware mode (via network)
    MOCK = "mock"  # Mock mode for testing


class DeviceError(Exception):
    """Base exception for device errors."""
    pass


class DeviceInitError(DeviceError):
    """Exception raised when device initialization fails."""
    pass


class DeviceCommandError(DeviceError):
    """Exception raised when a device command fails."""
    pass


class DeviceTimeoutError(DeviceError):
    """Exception raised when a device operation times out."""
    pass


class Device(ABC):
    """
    Abstract base class for hardware devices.
    
    This class defines the interface that all hardware device implementations must follow.
    It provides common functionality for device initialization, cleanup, and command execution.
    """
    
    def __init__(
        self, 
        device_id: str,
        device_type: Union[DeviceType, str] = DeviceType.UNKNOWN,
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ):
        """
        Initialize a hardware device.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Additional device parameters
        """
        self.device_id = device_id
        
        # Convert string device type to enum if needed
        if isinstance(device_type, str):
            self.device_type = DeviceType.from_str(device_type)
        else:
            self.device_type = device_type
        
        # Determine operation mode
        if mode is None:
            # Use simulation mode if specified in environment
            if env.get_bool("SIMULATION_MODE", False):
                self.mode = DeviceMode.SIMULATION
            else:
                self.mode = DeviceMode.HARDWARE
        elif isinstance(mode, str):
            try:
                self.mode = DeviceMode(mode.lower())
            except ValueError:
                logger.warning(f"Unknown device mode: {mode}, defaulting to hardware mode")
                self.mode = DeviceMode.HARDWARE
        else:
            self.mode = mode
        
        # Device state
        self.state = DeviceState.UNINITIALIZED
        
        # Store additional parameters
        self.params = kwargs
        
        # Event callbacks
        self.event_callbacks = {}
        
        # Last error
        self.last_error = None
        
        logger.debug(f"Created {self.device_type.value} device '{self.device_id}' in {self.mode.value} mode")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the device.
        
        Returns:
            True if initialization was successful, False otherwise
        
        Raises:
            DeviceInitError: If initialization fails
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Clean up device resources.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the device.
        
        Args:
            command: Command to execute
            params: Command parameters
            
        Returns:
            Command result
            
        Raises:
            DeviceCommandError: If the command fails
            DeviceTimeoutError: If the command times out
        """
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the device.
        
        Returns:
            Dictionary containing device status information
        """
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "state": self.state.value,
            "mode": self.mode.value,
            "error": str(self.last_error) if self.last_error else None
        }
    
    def register_event_callback(self, event_type: str, callback: Callable[..., Awaitable[None]]) -> None:
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event to register for
            callback: Async callback function to call when the event occurs
        """
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        
        self.event_callbacks[event_type].append(callback)
        logger.debug(f"Registered callback for event '{event_type}' on device '{self.device_id}'")
    
    def unregister_event_callback(self, event_type: str, callback: Callable[..., Awaitable[None]]) -> bool:
        """
        Unregister a callback for a specific event type.
        
        Args:
            event_type: Type of event to unregister for
            callback: Callback function to unregister
            
        Returns:
            True if the callback was unregistered, False otherwise
        """
        if event_type not in self.event_callbacks:
            return False
        
        try:
            self.event_callbacks[event_type].remove(callback)
            logger.debug(f"Unregistered callback for event '{event_type}' on device '{self.device_id}'")
            return True
        except ValueError:
            return False
    
    async def trigger_event(self, event_type: str, **event_data) -> None:
        """
        Trigger an event and call all registered callbacks.
        
        Args:
            event_type: Type of event to trigger
            **event_data: Event data to pass to callbacks
        """
        if event_type not in self.event_callbacks:
            return
        
        event_data["device_id"] = self.device_id
        event_data["device_type"] = self.device_type.value
        event_data["timestamp"] = asyncio.get_event_loop().time()
        
        for callback in self.event_callbacks[event_type]:
            try:
                await callback(event_type=event_type, **event_data)
            except Exception as e:
                logger.error(f"Error in event callback for '{event_type}' on device '{self.device_id}': {e}")
    
    def __str__(self) -> str:
        """Return a string representation of the device."""
        return f"{self.device_type.value}('{self.device_id}', {self.state.value})"
    
    def __repr__(self) -> str:
        """Return a detailed string representation of the device."""
        return f"{self.__class__.__name__}(device_id='{self.device_id}', device_type={self.device_type}, mode={self.mode}, state={self.state})"


class OutputDevice(Device):
    """
    Base class for output devices.
    
    Output devices are devices that can produce some kind of output,
    such as LEDs, displays, motors, etc.
    """
    
    def __init__(
        self, 
        device_id: str,
        device_type: Union[DeviceType, str] = DeviceType.UNKNOWN,
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ):
        """
        Initialize an output device.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, device_type, mode, **kwargs)
        self.is_active = False
    
    @abstractmethod
    async def activate(self) -> bool:
        """
        Activate the output device.
        
        Returns:
            True if activation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """
        Deactivate the output device.
        
        Returns:
            True if deactivation was successful, False otherwise
        """
        pass
    
    async def toggle(self) -> bool:
        """
        Toggle the output device state.
        
        Returns:
            True if the toggle was successful, False otherwise
        """
        if self.is_active:
            return await self.deactivate()
        else:
            return await self.activate()
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the output device.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        status["is_active"] = self.is_active
        return status


class InputDevice(Device):
    """
    Base class for input devices.
    
    Input devices are devices that can receive some kind of input,
    such as buttons, switches, sensors, etc.
    """
    
    def __init__(
        self, 
        device_id: str,
        device_type: Union[DeviceType, str] = DeviceType.UNKNOWN,
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ):
        """
        Initialize an input device.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, device_type, mode, **kwargs)
        self.last_value = None
        self.value_timestamp = None
    
    @abstractmethod
    async def read_value(self) -> Any:
        """
        Read the current value from the input device.
        
        Returns:
            Current value from the device
        """
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the input device.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        status["last_value"] = self.last_value
        status["value_timestamp"] = self.value_timestamp
        return status


class CompositeDevice(Device):
    """
    Base class for composite devices.
    
    Composite devices are devices that consist of multiple sub-devices,
    such as traffic lights, robot arms, etc.
    """
    
    def __init__(
        self, 
        device_id: str,
        device_type: Union[DeviceType, str] = DeviceType.UNKNOWN,
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ):
        """
        Initialize a composite device.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, device_type, mode, **kwargs)
        self.sub_devices = {}
    
    def add_sub_device(self, device: Device) -> None:
        """
        Add a sub-device to the composite device.
        
        Args:
            device: Sub-device to add
        """
        self.sub_devices[device.device_id] = device
        logger.debug(f"Added sub-device '{device.device_id}' to composite device '{self.device_id}'")
    
    def remove_sub_device(self, device_id: str) -> Optional[Device]:
        """
        Remove a sub-device from the composite device.
        
        Args:
            device_id: ID of the sub-device to remove
            
        Returns:
            Removed sub-device, or None if not found
        """
        if device_id in self.sub_devices:
            device = self.sub_devices.pop(device_id)
            logger.debug(f"Removed sub-device '{device_id}' from composite device '{self.device_id}'")
            return device
        return None
    
    def get_sub_device(self, device_id: str) -> Optional[Device]:
        """
        Get a sub-device by ID.
        
        Args:
            device_id: ID of the sub-device to get
            
        Returns:
            Sub-device, or None if not found
        """
        return self.sub_devices.get(device_id)
    
    async def initialize(self) -> bool:
        """
        Initialize the composite device and all sub-devices.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        self.state = DeviceState.INITIALIZING
        
        try:
            # Initialize all sub-devices
            for device_id, device in self.sub_devices.items():
                if not await device.initialize():
                    logger.error(f"Failed to initialize sub-device '{device_id}' of composite device '{self.device_id}'")
                    self.state = DeviceState.ERROR
                    self.last_error = f"Failed to initialize sub-device '{device_id}'"
                    return False
            
            self.state = DeviceState.READY
            logger.info(f"Initialized composite device '{self.device_id}' with {len(self.sub_devices)} sub-devices")
            return True
            
        except Exception as e:
            self.state = DeviceState.ERROR
            self.last_error = str(e)
            logger.error(f"Error initializing composite device '{self.device_id}': {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Clean up the composite device and all sub-devices.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        success = True
        
        # Clean up all sub-devices
        for device_id, device in self.sub_devices.items():
            try:
                if not await device.cleanup():
                    logger.error(f"Failed to clean up sub-device '{device_id}' of composite device '{self.device_id}'")
                    success = False
            except Exception as e:
                logger.error(f"Error cleaning up sub-device '{device_id}' of composite device '{self.device_id}': {e}")
                success = False
        
        self.state = DeviceState.UNINITIALIZED
        logger.info(f"Cleaned up composite device '{self.device_id}'")
        return success
    
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the composite device.
        
        Args:
            command: Command to execute
            params: Command parameters
            
        Returns:
            Command result
        """
        params = params or {}
        
        # Check if the command is for a specific sub-device
        if "device_id" in params:
            device_id = params.pop("device_id")
            device = self.get_sub_device(device_id)
            
            if device is None:
                return {"success": False, "error": f"Sub-device '{device_id}' not found"}
            
            return await device.execute_command(command, params)
        
        # Otherwise, execute the command on the composite device itself
        return {"success": False, "error": "Command not supported for this composite device"}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the composite device and all sub-devices.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        
        # Add sub-device statuses
        sub_device_statuses = {}
        for device_id, device in self.sub_devices.items():
            try:
                sub_device_statuses[device_id] = await device.get_status()
            except Exception as e:
                logger.error(f"Error getting status of sub-device '{device_id}': {e}")
                sub_device_statuses[device_id] = {"error": str(e)}
        
        status["sub_devices"] = sub_device_statuses
        return status
