#!/usr/bin/env python3
"""
Device Factory Module for UnitMCP

This module implements the Factory Pattern for hardware device creation in UnitMCP.
It provides a unified interface for creating different types of hardware devices
and concrete factory implementations for specific device types.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class Device(ABC):
    """
    Abstract base class for hardware devices.
    
    This class defines the interface that all hardware device implementations must follow.
    """
    
    def __init__(self, device_id: str):
        """
        Initialize a hardware device.
        
        Parameters
        ----------
        device_id : str
            Unique identifier for the device
        """
        self.device_id = device_id
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the device.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Clean up device resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the device.
        
        Parameters
        ----------
        command : str
            Command to execute
        params : Dict[str, Any]
            Command parameters
            
        Returns
        -------
        Dict[str, Any]
            Command result
        """
        pass


class LEDDevice(Device):
    """
    LED device implementation.
    
    This class provides functionality for controlling LED devices.
    """
    
    def __init__(self, device_id: str, pin: int):
        """
        Initialize an LED device.
        
        Parameters
        ----------
        device_id : str
            Unique identifier for the device
        pin : int
            GPIO pin number for the LED
        """
        super().__init__(device_id)
        self.pin = pin
        self.state = False
        self.blink_task = None
    
    async def initialize(self) -> bool:
        """
        Initialize the LED device.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # In a real implementation, this would set up the GPIO pin
            # For now, we'll just mark it as initialized
            self.is_initialized = True
            logger.info(f"Initialized LED device {self.device_id} on pin {self.pin}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LED device {self.device_id}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Clean up LED device resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        try:
            # Stop any ongoing blink task
            if self.blink_task and not self.blink_task.done():
                self.blink_task.cancel()
            
            # Turn off the LED
            self.state = False
            
            # In a real implementation, this would clean up the GPIO pin
            self.is_initialized = False
            logger.info(f"Cleaned up LED device {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clean up LED device {self.device_id}: {e}")
            return False
    
    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the LED device.
        
        Parameters
        ----------
        command : str
            Command to execute (on, off, blink, toggle)
        params : Dict[str, Any]
            Command parameters
            
        Returns
        -------
        Dict[str, Any]
            Command result
        """
        import asyncio
        
        if not self.is_initialized:
            return {"success": False, "error": "Device not initialized"}
        
        try:
            if command == "on":
                self.state = True
                # Stop any ongoing blink task
                if self.blink_task and not self.blink_task.done():
                    self.blink_task.cancel()
                return {"success": True, "state": self.state}
            
            elif command == "off":
                self.state = False
                # Stop any ongoing blink task
                if self.blink_task and not self.blink_task.done():
                    self.blink_task.cancel()
                return {"success": True, "state": self.state}
            
            elif command == "toggle":
                self.state = not self.state
                # Stop any ongoing blink task
                if self.blink_task and not self.blink_task.done():
                    self.blink_task.cancel()
                return {"success": True, "state": self.state}
            
            elif command == "blink":
                # Get blink parameters
                on_time = params.get("on_time", 0.5)
                off_time = params.get("off_time", 0.5)
                count = params.get("count", 0)  # 0 means blink indefinitely
                
                # Stop any ongoing blink task
                if self.blink_task and not self.blink_task.done():
                    self.blink_task.cancel()
                
                # Start a new blink task
                self.blink_task = asyncio.create_task(self._blink(on_time, off_time, count))
                
                return {
                    "success": True,
                    "on_time": on_time,
                    "off_time": off_time,
                    "count": count
                }
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
        
        except Exception as e:
            logger.error(f"Error executing command {command} on LED device {self.device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _blink(self, on_time: float, off_time: float, count: int = 0):
        """
        Blink the LED.
        
        Parameters
        ----------
        on_time : float
            Time in seconds that the LED should be on
        off_time : float
            Time in seconds that the LED should be off
        count : int, optional
            Number of blink cycles (0 means blink indefinitely), by default 0
        """
        import asyncio
        
        try:
            blink_count = 0
            while count == 0 or blink_count < count:
                # Turn on
                self.state = True
                await asyncio.sleep(on_time)
                
                # Turn off
                self.state = False
                await asyncio.sleep(off_time)
                
                blink_count += 1
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            logger.error(f"Error in blink task for LED device {self.device_id}: {e}")


class ButtonDevice(Device):
    """
    Button device implementation.
    
    This class provides functionality for controlling button devices.
    """
    
    def __init__(self, device_id: str, pin: int):
        """
        Initialize a button device.
        
        Parameters
        ----------
        device_id : str
            Unique identifier for the device
        pin : int
            GPIO pin number for the button
        """
        super().__init__(device_id)
        self.pin = pin
        self.is_pressed = False
        self.press_callbacks = []
    
    async def initialize(self) -> bool:
        """
        Initialize the button device.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # In a real implementation, this would set up the GPIO pin
            # For now, we'll just mark it as initialized
            self.is_initialized = True
            logger.info(f"Initialized button device {self.device_id} on pin {self.pin}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize button device {self.device_id}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Clean up button device resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        try:
            # In a real implementation, this would clean up the GPIO pin
            self.is_initialized = False
            logger.info(f"Cleaned up button device {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clean up button device {self.device_id}: {e}")
            return False
    
    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the button device.
        
        Parameters
        ----------
        command : str
            Command to execute (read, register_callback, simulate_press)
        params : Dict[str, Any]
            Command parameters
            
        Returns
        -------
        Dict[str, Any]
            Command result
        """
        if not self.is_initialized:
            return {"success": False, "error": "Device not initialized"}
        
        try:
            if command == "read":
                return {"success": True, "is_pressed": self.is_pressed}
            
            elif command == "register_callback":
                callback = params.get("callback")
                if callback and callable(callback):
                    self.press_callbacks.append(callback)
                    return {"success": True, "message": "Callback registered"}
                else:
                    return {"success": False, "error": "Invalid callback"}
            
            elif command == "simulate_press":
                # For testing purposes
                self.is_pressed = True
                # Notify callbacks
                for callback in self.press_callbacks:
                    try:
                        callback(self.device_id, True)
                    except Exception as e:
                        logger.error(f"Error in button press callback: {e}")
                
                # Reset after a short delay
                import asyncio
                asyncio.create_task(self._reset_after_delay(0.1))
                
                return {"success": True, "message": "Press simulated"}
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
        
        except Exception as e:
            logger.error(f"Error executing command {command} on button device {self.device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _reset_after_delay(self, delay: float):
        """
        Reset the button state after a delay.
        
        Parameters
        ----------
        delay : float
            Delay in seconds before resetting
        """
        import asyncio
        
        await asyncio.sleep(delay)
        self.is_pressed = False
        
        # Notify callbacks
        for callback in self.press_callbacks:
            try:
                callback(self.device_id, False)
            except Exception as e:
                logger.error(f"Error in button release callback: {e}")


class DeviceFactory(ABC):
    """
    Abstract base class for device factories.
    
    This class defines the interface that all device factory implementations must follow.
    """
    
    @abstractmethod
    def create_device(self, device_id: str, device_type: str, **kwargs) -> Optional[Device]:
        """
        Create a device of the specified type.
        
        Parameters
        ----------
        device_id : str
            Unique identifier for the device
        device_type : str
            Type of device to create
        **kwargs
            Device parameters
            
        Returns
        -------
        Optional[Device]
            An instance of the appropriate device class, or None if creation failed
        """
        pass


class GPIODeviceFactory(DeviceFactory):
    """
    Factory for GPIO devices.
    
    This class provides functionality for creating GPIO devices like LEDs and buttons.
    """
    
    def create_device(self, device_id: str, device_type: str, **kwargs) -> Optional[Device]:
        """
        Create a GPIO device of the specified type.
        
        Parameters
        ----------
        device_id : str
            Unique identifier for the device
        device_type : str
            Type of device to create (led, button)
        **kwargs
            Device parameters
            
        Returns
        -------
        Optional[Device]
            An instance of the appropriate device class, or None if creation failed
        """
        if device_type == "led":
            pin = kwargs.get("pin")
            if pin is None:
                logger.error("LED device requires a pin parameter")
                return None
            
            return LEDDevice(device_id, pin)
        
        elif device_type == "button":
            pin = kwargs.get("pin")
            if pin is None:
                logger.error("Button device requires a pin parameter")
                return None
            
            return ButtonDevice(device_id, pin)
        
        else:
            logger.error(f"Unknown GPIO device type: {device_type}")
            return None


# Factory registry
device_factories = {
    "gpio": GPIODeviceFactory()
}


def get_device_factory(factory_type: str) -> Optional[DeviceFactory]:
    """
    Get a device factory of the specified type.
    
    Parameters
    ----------
    factory_type : str
        Type of factory to get
        
    Returns
    -------
    Optional[DeviceFactory]
        An instance of the appropriate factory class, or None if not found
    """
    return device_factories.get(factory_type)


def register_device_factory(factory_type: str, factory: DeviceFactory):
    """
    Register a device factory.
    
    Parameters
    ----------
    factory_type : str
        Type of factory to register
    factory : DeviceFactory
        Factory instance to register
    """
    device_factories[factory_type] = factory


def create_device(factory_type: str, device_id: str, device_type: str, **kwargs) -> Optional[Device]:
    """
    Create a device using the specified factory.
    
    Parameters
    ----------
    factory_type : str
        Type of factory to use
    device_id : str
        Unique identifier for the device
    device_type : str
        Type of device to create
    **kwargs
        Device parameters
        
    Returns
    -------
    Optional[Device]
        An instance of the appropriate device class, or None if creation failed
    """
    factory = get_device_factory(factory_type)
    if factory is None:
        logger.error(f"Unknown factory type: {factory_type}")
        return None
    
    return factory.create_device(device_id, device_type, **kwargs)
