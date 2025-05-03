"""
Mock Device Factory for UnitMCP Testing

This module provides a mock implementation of the DeviceFactory for testing purposes.
"""

import logging
from typing import Dict, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class MockDevice:
    """Mock device implementation for testing."""
    
    def __init__(self, device_id, device_type=None, **kwargs):
        self.device_id = device_id
        self.device_type = device_type
        self.config = kwargs
        self.status = "initialized"
        logger.info(f"MockDevice {device_id} created with type: {device_type}, config: {kwargs}")
    
    async def initialize(self):
        logger.info(f"Initializing MockDevice {self.device_id}")
        return True
    
    async def cleanup(self):
        logger.info(f"Cleaning up MockDevice {self.device_id}")
        return True
    
    async def on(self, **kwargs):
        logger.info(f"Turning ON MockDevice {self.device_id}")
        return True
    
    async def off(self, **kwargs):
        logger.info(f"Turning OFF MockDevice {self.device_id}")
        return True
    
    async def toggle(self, **kwargs):
        logger.info(f"Toggling MockDevice {self.device_id}")
        return True
    
    async def blink(self, **kwargs):
        logger.info(f"Blinking MockDevice {self.device_id}")
        return True

class MockDeviceFactory:
    """
    Mock implementation of DeviceFactory for testing.
    """
    
    async def create_device(self, device_id, device_type, mode=None, **kwargs):
        """
        Create a mock device for testing.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device to create
            mode: Operation mode (ignored in mock)
            **kwargs: Device parameters
            
        Returns:
            A mock device instance
        """
        logger.info(f"Creating mock device {device_id} of type {device_type}")
        return MockDevice(device_id, device_type=device_type, **kwargs)
    
    async def create_led(self, device_id, **kwargs):
        """Create a mock LED device."""
        return await self.create_device(device_id, "led", **kwargs)
    
    async def create_button(self, device_id, **kwargs):
        """Create a mock button device."""
        return await self.create_device(device_id, "button", **kwargs)
    
    async def create_traffic_light(self, device_id, **kwargs):
        """Create a mock traffic light device."""
        return await self.create_device(device_id, "traffic_light", **kwargs)
    
    async def create_display(self, device_id, **kwargs):
        """Create a mock display device."""
        return await self.create_device(device_id, "display", **kwargs)
