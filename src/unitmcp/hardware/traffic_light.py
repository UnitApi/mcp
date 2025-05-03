#!/usr/bin/env python3
"""
Traffic Light Device Module for UnitMCP

This module provides a composite device implementation for traffic lights in UnitMCP.
It combines multiple LED devices to create a traffic light system.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Union

from .base import CompositeDevice, DeviceType, DeviceState, DeviceMode, DeviceCommandError
from .led import LEDDevice
from ..utils.env_loader import EnvLoader

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env = EnvLoader()


class TrafficLightState(Enum):
    """Enumeration of traffic light states."""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    RED_YELLOW = "red_yellow"  # Some countries use red+yellow before green
    OFF = "off"
    UNKNOWN = "unknown"


class TrafficLightDevice(CompositeDevice):
    """
    Traffic light device implementation.
    
    This class provides functionality for controlling traffic light devices.
    It combines multiple LED devices to create a traffic light system.
    """
    
    def __init__(
        self,
        device_id: str,
        red_pin: int = None,
        yellow_pin: int = None,
        green_pin: int = None,
        mode: Union[DeviceMode, str] = None,
        **kwargs
    ):
        """
        Initialize a traffic light device.
        
        Args:
            device_id: Unique identifier for the device
            red_pin: GPIO pin number for the red light
            yellow_pin: GPIO pin number for the yellow light
            green_pin: GPIO pin number for the green light
            mode: Operation mode (hardware, simulation, remote, mock)
            **kwargs: Additional device parameters
        """
        super().__init__(device_id, DeviceType.TRAFFIC_LIGHT, mode, **kwargs)
        
        # Use the provided pins or get from environment
        self.red_pin = red_pin or env.get_int('RED_PIN', kwargs.get('default_red_pin', 17))
        self.yellow_pin = yellow_pin or env.get_int('YELLOW_PIN', kwargs.get('default_yellow_pin', 18))
        self.green_pin = green_pin or env.get_int('GREEN_PIN', kwargs.get('default_green_pin', 27))
        
        # Traffic light state
        self.current_state = TrafficLightState.OFF
        
        # Cycle configuration
        self.cycle_task = None
        self.is_cycling = False
        self.cycle_params = {
            'red_time': 5.0,
            'yellow_time': 2.0,
            'green_time': 5.0,
            'red_yellow_time': 1.0,  # Some countries use red+yellow before green
            'use_red_yellow': False,  # Whether to use red+yellow state
            'count': 0  # 0 means cycle indefinitely
        }
        
        logger.debug(f"Created traffic light device '{device_id}' with pins R:{self.red_pin}, Y:{self.yellow_pin}, G:{self.green_pin} (mode: {self.mode.value})")
    
    async def initialize(self) -> bool:
        """
        Initialize the traffic light device.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        self.state = DeviceState.INITIALIZING
        
        try:
            # Create LED devices for each light
            red_led = LEDDevice(
                f"{self.device_id}_red",
                self.red_pin,
                self.mode
            )
            
            yellow_led = LEDDevice(
                f"{self.device_id}_yellow",
                self.yellow_pin,
                self.mode
            )
            
            green_led = LEDDevice(
                f"{self.device_id}_green",
                self.green_pin,
                self.mode
            )
            
            # Add LEDs as sub-devices
            self.add_sub_device(red_led)
            self.add_sub_device(yellow_led)
            self.add_sub_device(green_led)
            
            # Initialize all sub-devices
            if not await super().initialize():
                return False
            
            self.state = DeviceState.READY
            logger.info(f"Initialized traffic light device '{self.device_id}'")
            return True
            
        except Exception as e:
            self.state = DeviceState.ERROR
            self.last_error = str(e)
            logger.error(f"Error initializing traffic light device '{self.device_id}': {e}")
            return False
    
    async def set_state(self, state: Union[TrafficLightState, str]) -> bool:
        """
        Set the traffic light state.
        
        Args:
            state: Traffic light state to set
            
        Returns:
            True if setting state was successful, False otherwise
        """
        try:
            # Stop any ongoing cycle
            await self._stop_cycle()
            
            # Convert string state to enum if needed
            if isinstance(state, str):
                try:
                    state = TrafficLightState(state.lower())
                except ValueError:
                    logger.warning(f"Unknown traffic light state: {state}")
                    state = TrafficLightState.UNKNOWN
            
            # Get LED devices
            red_led = self.get_sub_device(f"{self.device_id}_red")
            yellow_led = self.get_sub_device(f"{self.device_id}_yellow")
            green_led = self.get_sub_device(f"{self.device_id}_green")
            
            if not all([red_led, yellow_led, green_led]):
                logger.error(f"Missing LED devices for traffic light '{self.device_id}'")
                return False
            
            # Set the appropriate LEDs based on the state
            if state == TrafficLightState.RED:
                await red_led.activate()
                await yellow_led.deactivate()
                await green_led.deactivate()
                
            elif state == TrafficLightState.YELLOW:
                await red_led.deactivate()
                await yellow_led.activate()
                await green_led.deactivate()
                
            elif state == TrafficLightState.GREEN:
                await red_led.deactivate()
                await yellow_led.deactivate()
                await green_led.activate()
                
            elif state == TrafficLightState.RED_YELLOW:
                await red_led.activate()
                await yellow_led.activate()
                await green_led.deactivate()
                
            elif state == TrafficLightState.OFF:
                await red_led.deactivate()
                await yellow_led.deactivate()
                await green_led.deactivate()
                
            else:
                logger.warning(f"Unknown traffic light state: {state}")
                return False
            
            self.current_state = state
            
            # Trigger event
            await self.trigger_event("state_changed", state=state.value)
            
            logger.debug(f"Set traffic light '{self.device_id}' state to {state.value}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error setting traffic light '{self.device_id}' state: {e}")
            return False
    
    async def start_cycle(
        self,
        red_time: float = None,
        yellow_time: float = None,
        green_time: float = None,
        red_yellow_time: float = None,
        use_red_yellow: bool = None,
        count: int = None
    ) -> bool:
        """
        Start a traffic light cycle.
        
        Args:
            red_time: Time in seconds for the red light
            yellow_time: Time in seconds for the yellow light
            green_time: Time in seconds for the green light
            red_yellow_time: Time in seconds for the red+yellow light
            use_red_yellow: Whether to use red+yellow state
            count: Number of cycles (0 means cycle indefinitely)
            
        Returns:
            True if starting cycle was successful, False otherwise
        """
        try:
            # Stop any ongoing cycle
            await self._stop_cycle()
            
            # Update cycle parameters with provided values or keep existing ones
            if red_time is not None:
                self.cycle_params['red_time'] = red_time
            
            if yellow_time is not None:
                self.cycle_params['yellow_time'] = yellow_time
            
            if green_time is not None:
                self.cycle_params['green_time'] = green_time
            
            if red_yellow_time is not None:
                self.cycle_params['red_yellow_time'] = red_yellow_time
            
            if use_red_yellow is not None:
                self.cycle_params['use_red_yellow'] = use_red_yellow
            
            if count is not None:
                self.cycle_params['count'] = count
            
            # Start a new cycle task
            self.is_cycling = True
            self.cycle_task = asyncio.create_task(self._cycle_loop())
            
            # Trigger event
            await self.trigger_event("cycle_started", **self.cycle_params)
            
            logger.debug(f"Started traffic light '{self.device_id}' cycle with parameters: {self.cycle_params}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error starting traffic light '{self.device_id}' cycle: {e}")
            return False
    
    async def _stop_cycle(self) -> None:
        """Stop any ongoing traffic light cycle."""
        if self.is_cycling and self.cycle_task and not self.cycle_task.done():
            self.cycle_task.cancel()
            try:
                await self.cycle_task
            except asyncio.CancelledError:
                pass
            
            self.is_cycling = False
            self.cycle_task = None
            
            # Trigger event
            await self.trigger_event("cycle_stopped")
            
            logger.debug(f"Stopped traffic light '{self.device_id}' cycle")
    
    async def _cycle_loop(self) -> None:
        """Run the traffic light cycle according to the current cycle parameters."""
        count = self.cycle_params['count']
        cycles = 0
        
        try:
            while count == 0 or cycles < count:
                # Red light
                await self.set_state(TrafficLightState.RED)
                await asyncio.sleep(self.cycle_params['red_time'])
                
                # Red+Yellow light (if enabled)
                if self.cycle_params['use_red_yellow']:
                    await self.set_state(TrafficLightState.RED_YELLOW)
                    await asyncio.sleep(self.cycle_params['red_yellow_time'])
                
                # Green light
                await self.set_state(TrafficLightState.GREEN)
                await asyncio.sleep(self.cycle_params['green_time'])
                
                # Yellow light
                await self.set_state(TrafficLightState.YELLOW)
                await asyncio.sleep(self.cycle_params['yellow_time'])
                
                cycles += 1
            
            # Cycling completed
            self.is_cycling = False
            self.cycle_task = None
            
            # Trigger event
            await self.trigger_event("cycle_completed", cycles=cycles)
            
            logger.debug(f"Traffic light '{self.device_id}' cycle completed after {cycles} cycles")
            
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            self.is_cycling = False
            raise
    
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the traffic light device.
        
        Args:
            command: Command to execute (set_state, start_cycle, stop_cycle)
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
            if command == "set_state":
                state = params.get("state")
                
                if not state:
                    return {"success": False, "error": "Missing required parameter: state"}
                
                success = await self.set_state(state)
                return {"success": success, "state": self.current_state.value}
            
            elif command == "start_cycle":
                success = await self.start_cycle(
                    red_time=params.get("red_time"),
                    yellow_time=params.get("yellow_time"),
                    green_time=params.get("green_time"),
                    red_yellow_time=params.get("red_yellow_time"),
                    use_red_yellow=params.get("use_red_yellow"),
                    count=params.get("count")
                )
                return {"success": success, "cycling": self.is_cycling, "cycle_params": self.cycle_params}
            
            elif command == "stop_cycle":
                await self._stop_cycle()
                return {"success": True, "cycling": False}
            
            elif command == "status":
                return {
                    "success": True,
                    "state": self.current_state.value,
                    "cycling": self.is_cycling,
                    "cycle_params": self.cycle_params if self.is_cycling else None
                }
            
            else:
                # Try to execute the command on a specific sub-device
                if "device_id" in params:
                    return await super().execute_command(command, params)
                
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error executing command '{command}' on traffic light device '{self.device_id}': {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the traffic light device.
        
        Returns:
            Dictionary containing device status information
        """
        status = await super().get_status()
        status.update({
            "pins": {
                "red": self.red_pin,
                "yellow": self.yellow_pin,
                "green": self.green_pin
            },
            "state": self.current_state.value,
            "cycling": self.is_cycling,
            "cycle_params": self.cycle_params if self.is_cycling else None
        })
        return status
