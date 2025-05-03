#!/usr/bin/env python3
"""
LED Device Module for UnitMCP

This module provides classes for controlling LED devices in UnitMCP.
It includes implementations for both hardware and simulated LEDs.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import OutputDevice, DeviceType, DeviceState, DeviceMode, DeviceCommandError
from ..utils.env_loader import EnvLoader

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env = EnvLoader()


class LEDDevice(OutputDevice):
    """
    LED device implementation.
    
    This class provides functionality for controlling LED devices.
    It supports both hardware and simulation modes.
    """
    
    def __init__(
        self,
        device_id: str,
        pin: int = None,
        mode: Union[DeviceMode, str] = None,
        active_high: bool = True,
        **kwargs
    ):
        """
        Initialize an LED device.
        
        Args:
            device_id: Unique identifier for the device
            pin: GPIO pin number for the LED
            mode: Operation mode (hardware, simulation, remote, mock)
            active_high: Whether the LED is active high (True) or active low (False)
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, DeviceType.LED, mode, **kwargs)
        
        # Use the provided pin or get from environment
        self.pin = pin or env.get_int('LED_PIN', kwargs.get('default_pin', 17))
        
        # LED configuration
        self.active_high = active_high
        
        # LED state
        self.is_active = False
        self.brightness = 0.0  # 0.0 to 1.0
        
        # Blinking state
        self.is_blinking = False
        self.blink_task = None
        self.blink_params = {
            'on_time': 0.5,
            'off_time': 0.5,
            'count': 0  # 0 means blink indefinitely
        }
        
        # PWM state (for brightness control)
        self.pwm_enabled = kwargs.get('pwm_enabled', False)
        self.pwm_frequency = kwargs.get('pwm_frequency', 100)  # Hz
        
        # Hardware-specific attributes
        self._gpio = None  # Will be set during initialization if in hardware mode
        
        logger.debug(f"Created LED device '{device_id}' on pin {self.pin} (mode: {self.mode.value})")
    
    async def initialize(self) -> bool:
        """
        Initialize the LED device.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        self.state = DeviceState.INITIALIZING
        
        try:
            if self.mode == DeviceMode.HARDWARE:
                # Initialize hardware GPIO
                await self._initialize_hardware()
            elif self.mode == DeviceMode.SIMULATION:
                # No hardware initialization needed for simulation
                logger.info(f"Initialized LED device '{self.device_id}' in simulation mode")
            elif self.mode == DeviceMode.REMOTE:
                # Initialize remote connection
                await self._initialize_remote()
            elif self.mode == DeviceMode.MOCK:
                # No initialization needed for mock mode
                logger.info(f"Initialized LED device '{self.device_id}' in mock mode")
            
            self.state = DeviceState.READY
            return True
            
        except Exception as e:
            self.state = DeviceState.ERROR
            self.last_error = str(e)
            logger.error(f"Error initializing LED device '{self.device_id}': {e}")
            return False
    
    async def _initialize_hardware(self) -> None:
        """
        Initialize the hardware GPIO for the LED.
        
        Raises:
            DeviceInitError: If hardware initialization fails
        """
        try:
            # Import GPIO library (RPi.GPIO or equivalent)
            # This is imported here to avoid requiring the library in simulation mode
            try:
                import RPi.GPIO as GPIO
                self._gpio = GPIO
                
                # Set up GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.pin, GPIO.OUT)
                
                # Set up PWM if enabled
                if self.pwm_enabled:
                    self._pwm = GPIO.PWM(self.pin, self.pwm_frequency)
                    self._pwm.start(0)  # Start with 0% duty cycle
                
                logger.info(f"Initialized LED device '{self.device_id}' on pin {self.pin} (hardware mode)")
                
            except ImportError:
                logger.warning("RPi.GPIO library not found, falling back to simulation mode")
                self.mode = DeviceMode.SIMULATION
                
        except Exception as e:
            logger.error(f"Error initializing LED hardware: {e}")
            raise
    
    async def _initialize_remote(self) -> None:
        """
        Initialize the remote connection for the LED.
        
        Raises:
            DeviceInitError: If remote initialization fails
        """
        # Implementation for remote mode would go here
        # This could involve setting up a connection to a remote server
        # that controls the actual hardware
        raise NotImplementedError("Remote mode not implemented yet")
    
    async def cleanup(self) -> bool:
        """
        Clean up LED device resources.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            # Stop any ongoing blink task
            await self._stop_blinking()
            
            # Turn off the LED
            await self.deactivate()
            
            if self.mode == DeviceMode.HARDWARE and self._gpio:
                # Clean up GPIO
                if self.pwm_enabled and hasattr(self, '_pwm'):
                    self._pwm.stop()
                
                # Don't call GPIO.cleanup() here as it would affect all pins
                # Just set the pin as input to avoid leaving it in an active state
                self._gpio.setup(self.pin, self._gpio.IN)
            
            self.state = DeviceState.UNINITIALIZED
            logger.info(f"Cleaned up LED device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error cleaning up LED device '{self.device_id}': {e}")
            return False
    
    async def activate(self) -> bool:
        """
        Turn on the LED.
        
        Returns:
            True if activation was successful, False otherwise
        """
        try:
            # Stop any ongoing blink task
            await self._stop_blinking()
            
            if self.mode == DeviceMode.HARDWARE and self._gpio:
                if self.pwm_enabled and hasattr(self, '_pwm'):
                    # Set to 100% brightness
                    self._pwm.ChangeDutyCycle(100 if self.active_high else 0)
                else:
                    # Set pin to active state
                    self._gpio.output(self.pin, self.active_high)
            
            self.is_active = True
            self.brightness = 1.0
            
            # Trigger event
            await self.trigger_event("activated")
            
            logger.debug(f"Activated LED device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error activating LED device '{self.device_id}': {e}")
            return False
    
    async def deactivate(self) -> bool:
        """
        Turn off the LED.
        
        Returns:
            True if deactivation was successful, False otherwise
        """
        try:
            # Stop any ongoing blink task
            await self._stop_blinking()
            
            if self.mode == DeviceMode.HARDWARE and self._gpio:
                if self.pwm_enabled and hasattr(self, '_pwm'):
                    # Set to 0% brightness
                    self._pwm.ChangeDutyCycle(0 if self.active_high else 100)
                else:
                    # Set pin to inactive state
                    self._gpio.output(self.pin, not self.active_high)
            
            self.is_active = False
            self.brightness = 0.0
            
            # Trigger event
            await self.trigger_event("deactivated")
            
            logger.debug(f"Deactivated LED device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error deactivating LED device '{self.device_id}': {e}")
            return False
    
    async def set_brightness(self, brightness: float) -> bool:
        """
        Set the LED brightness.
        
        Args:
            brightness: Brightness value from 0.0 to 1.0
            
        Returns:
            True if setting brightness was successful, False otherwise
        """
        try:
            # Ensure brightness is between 0.0 and 1.0
            brightness = max(0.0, min(1.0, brightness))
            
            # Stop any ongoing blink task
            await self._stop_blinking()
            
            if self.mode == DeviceMode.HARDWARE and self._gpio:
                if self.pwm_enabled and hasattr(self, '_pwm'):
                    # Convert brightness to duty cycle (0-100)
                    duty_cycle = brightness * 100
                    if not self.active_high:
                        duty_cycle = 100 - duty_cycle
                    
                    self._pwm.ChangeDutyCycle(duty_cycle)
                else:
                    # For non-PWM, just turn on or off based on threshold
                    self._gpio.output(self.pin, (brightness > 0.5) == self.active_high)
            
            self.brightness = brightness
            self.is_active = brightness > 0.0
            
            # Trigger event
            await self.trigger_event("brightness_changed", brightness=brightness)
            
            logger.debug(f"Set LED device '{self.device_id}' brightness to {brightness:.2f}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error setting LED device '{self.device_id}' brightness: {e}")
            return False
    
    async def blink(self, on_time: float = 0.5, off_time: float = 0.5, count: int = 0) -> bool:
        """
        Make the LED blink.
        
        Args:
            on_time: Time in seconds the LED should be on during each cycle
            off_time: Time in seconds the LED should be off during each cycle
            count: Number of blink cycles (0 means blink indefinitely)
            
        Returns:
            True if starting blinking was successful, False otherwise
        """
        try:
            # Stop any ongoing blink task
            await self._stop_blinking()
            
            # Update blink parameters
            self.blink_params = {
                'on_time': on_time,
                'off_time': off_time,
                'count': count
            }
            
            # Start a new blink task
            self.is_blinking = True
            self.blink_task = asyncio.create_task(self._blink_loop())
            
            # Trigger event
            await self.trigger_event("blinking_started", **self.blink_params)
            
            logger.debug(f"Started blinking LED device '{self.device_id}' (on: {on_time}s, off: {off_time}s, count: {count})")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error starting LED device '{self.device_id}' blinking: {e}")
            return False
    
    async def _stop_blinking(self) -> None:
        """Stop any ongoing blink task."""
        if self.is_blinking and self.blink_task and not self.blink_task.done():
            self.blink_task.cancel()
            try:
                await self.blink_task
            except asyncio.CancelledError:
                pass
            
            self.is_blinking = False
            self.blink_task = None
            
            # Trigger event
            await self.trigger_event("blinking_stopped")
            
            logger.debug(f"Stopped blinking LED device '{self.device_id}'")
    
    async def _blink_loop(self) -> None:
        """Blink the LED according to the current blink parameters."""
        count = self.blink_params['count']
        cycles = 0
        
        try:
            while count == 0 or cycles < count:
                # Turn on
                await self.activate()
                await asyncio.sleep(self.blink_params['on_time'])
                
                # Turn off
                await self.deactivate()
                await asyncio.sleep(self.blink_params['off_time'])
                
                cycles += 1
            
            # Blinking completed
            self.is_blinking = False
            self.blink_task = None
            
            # Trigger event
            await self.trigger_event("blinking_completed", cycles=cycles)
            
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            self.is_blinking = False
            raise
    
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the LED device.
        
        Args:
            command: Command to execute (on, off, toggle, blink, set_brightness)
            params: Command parameters
            
        Returns:
            Command result
            
        Raises:
            DeviceCommandError: If the command fails
        """
        params = params or {}
        
        if not self.state == DeviceState.READY:
            return {"success": False, "error": f"Device not ready (state: {self.state.value})"}
        
        try:
            if command == "on":
                success = await self.activate()
                return {"success": success, "state": "on" if self.is_active else "off"}
            
            elif command == "off":
                success = await self.deactivate()
                return {"success": success, "state": "on" if self.is_active else "off"}
            
            elif command == "toggle":
                success = await self.toggle()
                return {"success": success, "state": "on" if self.is_active else "off"}
            
            elif command == "blink":
                on_time = params.get("on_time", 0.5)
                off_time = params.get("off_time", 0.5)
                count = params.get("count", 0)
                
                success = await self.blink(on_time, off_time, count)
                return {"success": success, "blinking": self.is_blinking}
            
            elif command == "set_brightness":
                brightness = params.get("brightness", 1.0)
                
                success = await self.set_brightness(brightness)
                return {"success": success, "brightness": self.brightness}
            
            elif command == "stop_blinking":
                await self._stop_blinking()
                return {"success": True, "blinking": False}
            
            elif command == "status":
                return {
                    "success": True,
                    "state": "on" if self.is_active else "off",
                    "brightness": self.brightness,
                    "blinking": self.is_blinking,
                    "blink_params": self.blink_params if self.is_blinking else None
                }
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error executing command '{command}' on LED device '{self.device_id}': {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the LED device.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        status.update({
            "pin": self.pin,
            "state": "on" if self.is_active else "off",
            "brightness": self.brightness,
            "blinking": self.is_blinking,
            "blink_params": self.blink_params if self.is_blinking else None,
            "pwm_enabled": self.pwm_enabled,
            "active_high": self.active_high
        })
        return status


class RGBLEDDevice(OutputDevice):
    """
    RGB LED device implementation.
    
    This class provides functionality for controlling RGB LED devices.
    It supports both hardware and simulation modes.
    """
    
    def __init__(
        self,
        device_id: str,
        red_pin: int = None,
        green_pin: int = None,
        blue_pin: int = None,
        mode: Union[DeviceMode, str] = None,
        common_anode: bool = True,
        **kwargs
    ):
        """
        Initialize an RGB LED device.
        
        Args:
            device_id: Unique identifier for the device
            red_pin: GPIO pin number for the red channel
            green_pin: GPIO pin number for the green channel
            blue_pin: GPIO pin number for the blue channel
            mode: Operation mode (hardware, simulation, remote, mock)
            common_anode: Whether the RGB LED has a common anode (True) or common cathode (False)
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, DeviceType.LED, mode, **kwargs)
        
        # Use the provided pins or get from environment
        self.red_pin = red_pin or env.get_int('RGB_RED_PIN', kwargs.get('default_red_pin', 17))
        self.green_pin = green_pin or env.get_int('RGB_GREEN_PIN', kwargs.get('default_green_pin', 18))
        self.blue_pin = blue_pin or env.get_int('RGB_BLUE_PIN', kwargs.get('default_blue_pin', 27))
        
        # RGB LED configuration
        self.common_anode = common_anode
        
        # RGB LED state
        self.is_active = False
        self.color = (0, 0, 0)  # RGB values (0-255)
        
        # Individual LED devices for each channel
        self.leds = {}
        
        logger.debug(f"Created RGB LED device '{device_id}' on pins R:{self.red_pin}, G:{self.green_pin}, B:{self.blue_pin} (mode: {self.mode.value})")
    
    async def initialize(self) -> bool:
        """
        Initialize the RGB LED device.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        self.state = DeviceState.INITIALIZING
        
        try:
            # Create individual LED devices for each channel
            self.leds = {
                'red': LEDDevice(
                    f"{self.device_id}_red",
                    self.red_pin,
                    self.mode,
                    not self.common_anode,  # Invert active_high for common anode
                    pwm_enabled=True
                ),
                'green': LEDDevice(
                    f"{self.device_id}_green",
                    self.green_pin,
                    self.mode,
                    not self.common_anode,  # Invert active_high for common anode
                    pwm_enabled=True
                ),
                'blue': LEDDevice(
                    f"{self.device_id}_blue",
                    self.blue_pin,
                    self.mode,
                    not self.common_anode,  # Invert active_high for common anode
                    pwm_enabled=True
                )
            }
            
            # Initialize each LED
            for color, led in self.leds.items():
                if not await led.initialize():
                    self.state = DeviceState.ERROR
                    self.last_error = f"Failed to initialize {color} channel"
                    logger.error(f"Failed to initialize {color} channel of RGB LED device '{self.device_id}'")
                    return False
            
            self.state = DeviceState.READY
            logger.info(f"Initialized RGB LED device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.state = DeviceState.ERROR
            self.last_error = str(e)
            logger.error(f"Error initializing RGB LED device '{self.device_id}': {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Clean up RGB LED device resources.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        success = True
        
        # Clean up each LED
        for color, led in self.leds.items():
            try:
                if not await led.cleanup():
                    logger.error(f"Failed to clean up {color} channel of RGB LED device '{self.device_id}'")
                    success = False
            except Exception as e:
                logger.error(f"Error cleaning up {color} channel of RGB LED device '{self.device_id}': {e}")
                success = False
        
        self.state = DeviceState.UNINITIALIZED
        logger.info(f"Cleaned up RGB LED device '{self.device_id}'")
        return success
    
    async def activate(self) -> bool:
        """
        Turn on the RGB LED with the current color.
        
        Returns:
            True if activation was successful, False otherwise
        """
        try:
            # Set the current color
            success = await self.set_color(*self.color)
            
            if success:
                self.is_active = True
                
                # Trigger event
                await self.trigger_event("activated", color=self.color)
                
                logger.debug(f"Activated RGB LED device '{self.device_id}' with color {self.color}")
            
            return success
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error activating RGB LED device '{self.device_id}': {e}")
            return False
    
    async def deactivate(self) -> bool:
        """
        Turn off the RGB LED.
        
        Returns:
            True if deactivation was successful, False otherwise
        """
        try:
            # Turn off all channels
            for led in self.leds.values():
                await led.deactivate()
            
            self.is_active = False
            
            # Trigger event
            await self.trigger_event("deactivated")
            
            logger.debug(f"Deactivated RGB LED device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error deactivating RGB LED device '{self.device_id}': {e}")
            return False
    
    async def set_color(self, red: int, green: int, blue: int) -> bool:
        """
        Set the RGB LED color.
        
        Args:
            red: Red value (0-255)
            green: Green value (0-255)
            blue: Blue value (0-255)
            
        Returns:
            True if setting color was successful, False otherwise
        """
        try:
            # Ensure values are between 0 and 255
            red = max(0, min(255, red))
            green = max(0, min(255, green))
            blue = max(0, min(255, blue))
            
            # Set brightness for each channel
            await self.leds['red'].set_brightness(red / 255.0)
            await self.leds['green'].set_brightness(green / 255.0)
            await self.leds['blue'].set_brightness(blue / 255.0)
            
            self.color = (red, green, blue)
            self.is_active = any(c > 0 for c in self.color)
            
            # Trigger event
            await self.trigger_event("color_changed", color=self.color)
            
            logger.debug(f"Set RGB LED device '{self.device_id}' color to {self.color}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error setting RGB LED device '{self.device_id}' color: {e}")
            return False
    
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the RGB LED device.
        
        Args:
            command: Command to execute (on, off, toggle, set_color)
            params: Command parameters
            
        Returns:
            Command result
            
        Raises:
            DeviceCommandError: If the command fails
        """
        params = params or {}
        
        if not self.state == DeviceState.READY:
            return {"success": False, "error": f"Device not ready (state: {self.state.value})"}
        
        try:
            if command == "on":
                success = await self.activate()
                return {"success": success, "state": "on" if self.is_active else "off", "color": self.color}
            
            elif command == "off":
                success = await self.deactivate()
                return {"success": success, "state": "on" if self.is_active else "off"}
            
            elif command == "toggle":
                success = await self.toggle()
                return {"success": success, "state": "on" if self.is_active else "off", "color": self.color}
            
            elif command == "set_color":
                red = params.get("red", 0)
                green = params.get("green", 0)
                blue = params.get("blue", 0)
                
                success = await self.set_color(red, green, blue)
                return {"success": success, "color": self.color}
            
            elif command == "status":
                return {
                    "success": True,
                    "state": "on" if self.is_active else "off",
                    "color": self.color
                }
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error executing command '{command}' on RGB LED device '{self.device_id}': {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the RGB LED device.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        status.update({
            "pins": {
                "red": self.red_pin,
                "green": self.green_pin,
                "blue": self.blue_pin
            },
            "state": "on" if self.is_active else "off",
            "color": self.color,
            "common_anode": self.common_anode
        })
        return status
