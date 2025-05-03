#!/usr/bin/env python3
"""
Button Device Module for UnitMCP

This module provides classes for controlling button devices in UnitMCP.
It includes implementations for both hardware and simulated buttons.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union

from .base import InputDevice, DeviceType, DeviceState, DeviceMode, DeviceCommandError
from ..utils.env_loader import EnvLoader

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env = EnvLoader()


class ButtonDevice(InputDevice):
    """
    Button device implementation.
    
    This class provides functionality for controlling button devices.
    It supports both hardware and simulation modes.
    """
    
    def __init__(
        self,
        device_id: str,
        pin: int = None,
        mode: Union[DeviceMode, str] = None,
        pull_up: bool = True,
        debounce_ms: int = 50,
        **kwargs
    ):
        """
        Initialize a button device.
        
        Args:
            device_id: Unique identifier for the device
            pin: GPIO pin number for the button
            mode: Operation mode (hardware, simulation, remote, mock)
            pull_up: Whether the button uses a pull-up resistor (True) or pull-down (False)
            debounce_ms: Debounce time in milliseconds
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, DeviceType.BUTTON, mode, **kwargs)
        
        # Use the provided pin or get from environment
        self.pin = pin or env.get_int('BUTTON_PIN', kwargs.get('default_pin', 27))
        
        # Button configuration
        self.pull_up = pull_up
        self.debounce_ms = debounce_ms
        
        # Button state
        self.is_pressed = False
        self.press_time = None
        self.release_time = None
        self.press_count = 0
        self.last_value = 0
        
        # Polling configuration
        self.polling_enabled = kwargs.get('polling_enabled', False)
        self.polling_interval = kwargs.get('polling_interval', 0.05)  # seconds
        self.polling_task = None
        
        # Event detection
        self.event_detection_enabled = kwargs.get('event_detection_enabled', True)
        
        # Hardware-specific attributes
        self._gpio = None  # Will be set during initialization if in hardware mode
        
        logger.debug(f"Created button device '{device_id}' on pin {self.pin} (mode: {self.mode.value})")
    
    async def initialize(self) -> bool:
        """
        Initialize the button device.
        
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
                logger.info(f"Initialized button device '{self.device_id}' in simulation mode")
            elif self.mode == DeviceMode.REMOTE:
                # Initialize remote connection
                await self._initialize_remote()
            elif self.mode == DeviceMode.MOCK:
                # No initialization needed for mock mode
                logger.info(f"Initialized button device '{self.device_id}' in mock mode")
            
            # Start polling if enabled
            if self.polling_enabled:
                await self._start_polling()
            
            self.state = DeviceState.READY
            return True
            
        except Exception as e:
            self.state = DeviceState.ERROR
            self.last_error = str(e)
            logger.error(f"Error initializing button device '{self.device_id}': {e}")
            return False
    
    async def _initialize_hardware(self) -> None:
        """
        Initialize the hardware GPIO for the button.
        
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
                
                # Set up the pin as input with pull-up or pull-down
                if self.pull_up:
                    GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                else:
                    GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                
                # Set up event detection if enabled
                if self.event_detection_enabled:
                    # Add event detection for both rising and falling edges
                    GPIO.add_event_detect(
                        self.pin,
                        GPIO.BOTH,
                        callback=self._gpio_callback,
                        bouncetime=self.debounce_ms
                    )
                
                logger.info(f"Initialized button device '{self.device_id}' on pin {self.pin} (hardware mode)")
                
            except ImportError:
                logger.warning("RPi.GPIO library not found, falling back to simulation mode")
                self.mode = DeviceMode.SIMULATION
                
        except Exception as e:
            logger.error(f"Error initializing button hardware: {e}")
            raise
    
    def _gpio_callback(self, channel):
        """
        Callback function for GPIO events.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        # This runs in a separate thread, so we need to be careful
        # We'll just update the state and let the polling task handle events
        try:
            # Read the current value
            value = self._gpio.input(channel)
            
            # Determine if the button is pressed based on pull-up/down configuration
            is_pressed = (value == 0) if self.pull_up else (value == 1)
            
            # Update state
            if is_pressed != self.is_pressed:
                self.is_pressed = is_pressed
                
                if is_pressed:
                    self.press_time = time.time()
                    self.press_count += 1
                    
                    # Schedule press event
                    asyncio.run_coroutine_threadsafe(
                        self.trigger_event("pressed", timestamp=self.press_time),
                        asyncio.get_event_loop()
                    )
                else:
                    self.release_time = time.time()
                    
                    # Calculate press duration
                    duration = self.release_time - self.press_time if self.press_time else 0
                    
                    # Schedule release event
                    asyncio.run_coroutine_threadsafe(
                        self.trigger_event("released", timestamp=self.release_time, duration=duration),
                        asyncio.get_event_loop()
                    )
            
            # Update last value
            self.last_value = value
            self.value_timestamp = time.time()
            
        except Exception as e:
            logger.error(f"Error in GPIO callback for button device '{self.device_id}': {e}")
    
    async def _initialize_remote(self) -> None:
        """
        Initialize the remote connection for the button.
        
        Raises:
            DeviceInitError: If remote initialization fails
        """
        # Implementation for remote mode would go here
        # This could involve setting up a connection to a remote server
        # that controls the actual hardware
        raise NotImplementedError("Remote mode not implemented yet")
    
    async def cleanup(self) -> bool:
        """
        Clean up button device resources.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            # Stop polling if enabled
            await self._stop_polling()
            
            if self.mode == DeviceMode.HARDWARE and self._gpio:
                # Remove event detection if enabled
                if self.event_detection_enabled:
                    try:
                        self._gpio.remove_event_detect(self.pin)
                    except Exception as e:
                        logger.warning(f"Error removing event detection: {e}")
                
                # Don't call GPIO.cleanup() here as it would affect all pins
                # Just leave the pin as input
            
            self.state = DeviceState.UNINITIALIZED
            logger.info(f"Cleaned up button device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error cleaning up button device '{self.device_id}': {e}")
            return False
    
    async def read_value(self) -> int:
        """
        Read the current value from the button.
        
        Returns:
            1 if the button is pressed, 0 if not pressed
        """
        try:
            if self.mode == DeviceMode.HARDWARE and self._gpio:
                # Read the value from the GPIO pin
                value = self._gpio.input(self.pin)
                
                # Determine if the button is pressed based on pull-up/down configuration
                self.is_pressed = (value == 0) if self.pull_up else (value == 1)
                
                # Update last value and timestamp
                self.last_value = value
                self.value_timestamp = time.time()
                
                return 1 if self.is_pressed else 0
                
            elif self.mode == DeviceMode.SIMULATION:
                # In simulation mode, just return the current state
                return 1 if self.is_pressed else 0
                
            else:
                logger.warning(f"Reading button value not implemented for mode: {self.mode.value}")
                return 0
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error reading button device '{self.device_id}' value: {e}")
            return 0
    
    async def wait_for_press(self, timeout: float = None) -> bool:
        """
        Wait for the button to be pressed.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if the button was pressed, False if timeout occurred
        """
        try:
            logger.debug(f"Waiting for button '{self.device_id}' press" + 
                        (f" (timeout: {timeout}s)" if timeout else ""))
            
            # If the button is already pressed, return immediately
            if self.is_pressed:
                return True
            
            # Create a future to wait for the press event
            press_future = asyncio.get_event_loop().create_future()
            
            # Register a callback for the press event
            async def press_callback(event_type, **kwargs):
                if not press_future.done():
                    press_future.set_result(True)
            
            self.register_event_callback("pressed", press_callback)
            
            try:
                # Wait for the press event or timeout
                if timeout is not None:
                    await asyncio.wait_for(press_future, timeout)
                else:
                    await press_future
                
                logger.debug(f"Button '{self.device_id}' press detected")
                return True
                
            except asyncio.TimeoutError:
                logger.debug(f"Timeout waiting for button '{self.device_id}' press")
                return False
                
            finally:
                # Unregister the callback
                self.unregister_event_callback("pressed", press_callback)
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error waiting for button device '{self.device_id}' press: {e}")
            return False
    
    async def wait_for_release(self, timeout: float = None) -> bool:
        """
        Wait for the button to be released.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if the button was released, False if timeout occurred
        """
        try:
            logger.debug(f"Waiting for button '{self.device_id}' release" + 
                        (f" (timeout: {timeout}s)" if timeout else ""))
            
            # If the button is already released, return immediately
            if not self.is_pressed:
                return True
            
            # Create a future to wait for the release event
            release_future = asyncio.get_event_loop().create_future()
            
            # Register a callback for the release event
            async def release_callback(event_type, **kwargs):
                if not release_future.done():
                    release_future.set_result(True)
            
            self.register_event_callback("released", release_callback)
            
            try:
                # Wait for the release event or timeout
                if timeout is not None:
                    await asyncio.wait_for(release_future, timeout)
                else:
                    await release_future
                
                logger.debug(f"Button '{self.device_id}' release detected")
                return True
                
            except asyncio.TimeoutError:
                logger.debug(f"Timeout waiting for button '{self.device_id}' release")
                return False
                
            finally:
                # Unregister the callback
                self.unregister_event_callback("released", release_callback)
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error waiting for button device '{self.device_id}' release: {e}")
            return False
    
    async def simulate_press(self, duration: float = 0.1) -> bool:
        """
        Simulate a button press.
        
        Args:
            duration: Duration of the press in seconds
            
        Returns:
            True if simulation was successful, False otherwise
        """
        try:
            if self.mode != DeviceMode.SIMULATION and self.mode != DeviceMode.MOCK:
                logger.warning(f"Button press simulation only available in simulation or mock mode")
                return False
            
            # Simulate press
            self.is_pressed = True
            self.press_time = time.time()
            self.press_count += 1
            
            # Trigger press event
            await self.trigger_event("pressed", timestamp=self.press_time)
            
            # Wait for the specified duration
            await asyncio.sleep(duration)
            
            # Simulate release
            self.is_pressed = False
            self.release_time = time.time()
            
            # Calculate press duration
            press_duration = self.release_time - self.press_time
            
            # Trigger release event
            await self.trigger_event("released", timestamp=self.release_time, duration=press_duration)
            
            logger.debug(f"Simulated button '{self.device_id}' press (duration: {duration}s)")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error simulating button device '{self.device_id}' press: {e}")
            return False
    
    async def _start_polling(self) -> None:
        """Start polling the button state."""
        if self.polling_task is None or self.polling_task.done():
            self.polling_task = asyncio.create_task(self._polling_loop())
            logger.debug(f"Started polling button device '{self.device_id}' (interval: {self.polling_interval}s)")
    
    async def _stop_polling(self) -> None:
        """Stop polling the button state."""
        if self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
            
            self.polling_task = None
            logger.debug(f"Stopped polling button device '{self.device_id}'")
    
    async def _polling_loop(self) -> None:
        """Poll the button state at regular intervals."""
        prev_value = None
        
        try:
            while True:
                # Read the current value
                value = await self.read_value()
                
                # Check if the value has changed
                if prev_value is not None and value != prev_value:
                    # Button state has changed
                    if value == 1:
                        # Button pressed
                        self.is_pressed = True
                        self.press_time = time.time()
                        self.press_count += 1
                        
                        # Trigger press event
                        await self.trigger_event("pressed", timestamp=self.press_time)
                    else:
                        # Button released
                        self.is_pressed = False
                        self.release_time = time.time()
                        
                        # Calculate press duration
                        duration = self.release_time - self.press_time if self.press_time else 0
                        
                        # Trigger release event
                        await self.trigger_event("released", timestamp=self.release_time, duration=duration)
                
                # Update previous value
                prev_value = value
                
                # Wait for the next polling interval
                await asyncio.sleep(self.polling_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.debug(f"Button polling task cancelled for device '{self.device_id}'")
            raise
    
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the button device.
        
        Args:
            command: Command to execute (read, wait_for_press, wait_for_release, simulate_press)
            params: Command parameters
            
        Returns:
            Command result
            
        Raises:
            DeviceCommandError: If the command fails
        """
        params = params or {}
        
        if not self.state == DeviceState.READY and command != "status":
            return {"success": False, "error": f"Device not ready (state: {self.state.value})"}
        
        try:
            if command == "read":
                value = await self.read_value()
                return {"success": True, "value": value, "is_pressed": self.is_pressed}
            
            elif command == "wait_for_press":
                timeout = params.get("timeout")
                
                success = await self.wait_for_press(timeout)
                return {"success": success, "is_pressed": self.is_pressed}
            
            elif command == "wait_for_release":
                timeout = params.get("timeout")
                
                success = await self.wait_for_release(timeout)
                return {"success": success, "is_pressed": self.is_pressed}
            
            elif command == "simulate_press":
                if self.mode != DeviceMode.SIMULATION and self.mode != DeviceMode.MOCK:
                    return {"success": False, "error": "Button press simulation only available in simulation or mock mode"}
                
                duration = params.get("duration", 0.1)
                
                success = await self.simulate_press(duration)
                return {"success": success, "is_pressed": self.is_pressed}
            
            elif command == "status":
                return {
                    "success": True,
                    "is_pressed": self.is_pressed,
                    "press_count": self.press_count,
                    "last_press_time": self.press_time,
                    "last_release_time": self.release_time
                }
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error executing command '{command}' on button device '{self.device_id}': {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the button device.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        status.update({
            "pin": self.pin,
            "is_pressed": self.is_pressed,
            "press_count": self.press_count,
            "last_press_time": self.press_time,
            "last_release_time": self.release_time,
            "pull_up": self.pull_up,
            "debounce_ms": self.debounce_ms,
            "polling_enabled": self.polling_enabled,
            "polling_interval": self.polling_interval,
            "event_detection_enabled": self.event_detection_enabled
        })
        return status
