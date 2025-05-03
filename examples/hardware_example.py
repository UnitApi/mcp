#!/usr/bin/env python3
"""
Hardware Abstraction Example for UnitMCP

This example demonstrates how to use the hardware abstraction classes in UnitMCP.
It shows how to create and control various hardware devices including LEDs, buttons,
traffic lights, and displays in both hardware and simulation modes.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Dict, List, Any, Callable

# Simple environment loader implementation
class EnvLoader:
    """Simple environment variable loader."""
    
    def __init__(self):
        """Initialize the environment loader."""
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get an environment variable."""
        return os.environ.get(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean environment variable."""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', 'yes', '1', 'y')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer environment variable."""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env = EnvLoader()

# Set simulation mode based on environment or default to True if not on Raspberry Pi
SIMULATION_MODE = env.get_bool('SIMULATION_MODE', True)
DEFAULT_MODE = "SIMULATION" if SIMULATION_MODE else "HARDWARE"

# Define DeviceMode
class DeviceMode:
    """Device mode."""
    SIMULATION = "SIMULATION"
    HARDWARE = "HARDWARE"
    MOCK = "MOCK"

# Define DeviceType
class DeviceType:
    """Device type."""
    LED = "LED"
    BUTTON = "BUTTON"
    TRAFFIC_LIGHT = "TRAFFIC_LIGHT"
    DISPLAY = "DISPLAY"

# Define TrafficLightState
class TrafficLightState:
    """Traffic light state."""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    OFF = "OFF"

# Define DisplayType
class DisplayType:
    """Display type."""
    LCD = "LCD"

# Define base device class
class Device:
    """Base device class."""
    def __init__(self, device_id: str, mode: str):
        """Initialize the device."""
        self.device_id = device_id
        self.mode = mode
        self._event_callbacks = {}
    
    async def initialize(self):
        """Initialize the device."""
        pass
    
    async def cleanup(self):
        """Clean up the device."""
        pass
    
    async def execute_command(self, command: str, data: Dict[str, Any]) -> Any:
        """Execute a command on the device."""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the device status."""
        pass
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register an event callback."""
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)
        logger.info(f"Registered event callback for {event_type} on device {self.device_id}")
    
    async def _trigger_event(self, event_type: str, **kwargs):
        """Trigger an event."""
        if event_type in self._event_callbacks:
            for callback in self._event_callbacks[event_type]:
                await callback(event_type, **kwargs)

# Define LED device class
class LEDDevice(Device):
    """LED device class."""
    def __init__(self, device_id: str, pin: int, mode: str):
        """Initialize the LED device."""
        super().__init__(device_id, mode)
        self.pin = pin
    
    async def initialize(self):
        """Initialize the LED device."""
        logger.info(f"Initializing LED device {self.device_id} on pin {self.pin}")
    
    async def activate(self):
        """Activate the LED."""
        logger.info(f"Activating LED device {self.device_id}")
    
    async def deactivate(self):
        """Deactivate the LED."""
        logger.info(f"Deactivating LED device {self.device_id}")
    
    async def set_brightness(self, brightness: float):
        """Set the LED brightness."""
        logger.info(f"Setting LED device {self.device_id} brightness to {brightness:.2f}")
    
    async def blink(self, on_time: float, off_time: float, count: int):
        """Blink the LED."""
        logger.info(f"Blinking LED device {self.device_id} ({count} times)")
    
    async def execute_command(self, command: str, data: Dict[str, Any]) -> Any:
        """Execute a command on the LED device."""
        if command == "activate":
            await self.activate()
        elif command == "deactivate":
            await self.deactivate()
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the LED device status."""
        return {"status": "OK"}

# Define Button device class
class ButtonDevice(Device):
    """Button device class."""
    def __init__(self, device_id: str, pin: int, mode: str, pull_up: bool = False, debounce_ms: int = 50):
        """Initialize the Button device."""
        super().__init__(device_id, mode)
        self.pin = pin
        self.pull_up = pull_up
        self.debounce_ms = debounce_ms
    
    async def initialize(self):
        """Initialize the Button device."""
        logger.info(f"Initializing Button device {self.device_id} on pin {self.pin}")
    
    async def simulate_press(self, duration: float):
        """Simulate a button press."""
        logger.info(f"Simulating button press on Button device {self.device_id} ({duration:.2f} seconds)")
        await self._trigger_event("pressed", timestamp=time.time())
        await asyncio.sleep(duration)
        await self._trigger_event("released", timestamp=time.time(), duration=duration)
    
    async def execute_command(self, command: str, data: Dict[str, Any]) -> Any:
        """Execute a command on the Button device."""
        if command == "read":
            return True
        return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the Button device status."""
        return {"status": "OK"}

# Define TrafficLight device class
class TrafficLightDevice(Device):
    """TrafficLight device class."""
    def __init__(self, device_id: str, red_pin: int, yellow_pin: int, green_pin: int, mode: str):
        """Initialize the TrafficLight device."""
        super().__init__(device_id, mode)
        self.red_pin = red_pin
        self.yellow_pin = yellow_pin
        self.green_pin = green_pin
        self.is_cycling = False
        self._current_state = TrafficLightState.OFF
    
    async def initialize(self):
        """Initialize the TrafficLight device."""
        logger.info(f"Initializing TrafficLight device {self.device_id} on pins {self.red_pin}, {self.yellow_pin}, {self.green_pin}")
    
    async def set_state(self, state: str):
        """Set the TrafficLight state."""
        logger.info(f"Setting TrafficLight device {self.device_id} state to {state}")
        self._current_state = state
        await self._trigger_event("state_changed", state=state)
    
    async def start_cycle(self, red_time: float, yellow_time: float, green_time: float, use_red_yellow: bool, red_yellow_time: float, count: int):
        """Start a TrafficLight cycle."""
        logger.info(f"Starting TrafficLight cycle on TrafficLight device {self.device_id} ({count} times)")
        self.is_cycling = True
        
        # Simulate cycling in a background task
        asyncio.create_task(self._run_cycle(red_time, yellow_time, green_time, use_red_yellow, red_yellow_time, count))
    
    async def _run_cycle(self, red_time: float, yellow_time: float, green_time: float, use_red_yellow: bool, red_yellow_time: float, count: int):
        """Run the traffic light cycle."""
        cycles_completed = 0
        try:
            while count == 0 or cycles_completed < count:
                # Red
                await self.set_state(TrafficLightState.RED)
                await asyncio.sleep(red_time)
                
                # Red+Yellow (if enabled)
                if use_red_yellow:
                    await self.set_state("RED_YELLOW")
                    await asyncio.sleep(red_yellow_time)
                
                # Green
                await self.set_state(TrafficLightState.GREEN)
                await asyncio.sleep(green_time)
                
                # Yellow
                await self.set_state(TrafficLightState.YELLOW)
                await asyncio.sleep(yellow_time)
                
                cycles_completed += 1
                
            # End with RED
            await self.set_state(TrafficLightState.RED)
        finally:
            self.is_cycling = False
    
    async def execute_command(self, command: str, data: Dict[str, Any]) -> Any:
        """Execute a command on the TrafficLight device."""
        if command == "set_state":
            await self.set_state(data["state"])
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the TrafficLight device status."""
        return {"status": "OK", "state": self._current_state, "is_cycling": self.is_cycling}

# Define Display device class
class DisplayDevice(Device):
    """Display device class."""
    def __init__(self, device_id: str, display_type: str, width: int, height: int, address: int, mode: str):
        """Initialize the Display device."""
        super().__init__(device_id, mode)
        self.display_type = display_type
        self.width = width
        self.height = height
        self.address = address
        self._content = [[' ' for _ in range(width)] for _ in range(height)]
        self._backlight = True
    
    async def initialize(self):
        """Initialize the Display device."""
        logger.info(f"Initializing Display device {self.device_id} ({self.display_type}) on address {self.address}")
    
    async def clear(self):
        """Clear the Display."""
        logger.info(f"Clearing Display device {self.device_id}")
        self._content = [[' ' for _ in range(self.width)] for _ in range(self.height)]
    
    async def write_line(self, text: str, line: int):
        """Write a line to the Display."""
        logger.info(f"Writing line to Display device {self.device_id}: {text}")
        if 0 <= line < self.height:
            text = text[:self.width].ljust(self.width)
            self._content[line] = list(text)
    
    async def write_text(self, text: str, x: int = 0, y: int = 0):
        """Write text to the Display."""
        logger.info(f"Writing text to Display device {self.device_id}: {text} at ({x}, {y})")
        if 0 <= y < self.height:
            for i, char in enumerate(text):
                if x + i < self.width:
                    self._content[y][x + i] = char
    
    async def set_cursor(self, x: int, y: int):
        """Set the cursor position on the Display."""
        logger.info(f"Setting cursor position on Display device {self.device_id} to ({x}, {y})")
    
    async def set_backlight(self, enabled: bool):
        """Set the backlight state on the Display."""
        logger.info(f"Setting backlight on Display device {self.device_id} to {enabled}")
        self._backlight = enabled
    
    async def execute_command(self, command: str, data: Dict[str, Any]) -> Any:
        """Execute a command on the Display device."""
        if command == "write_line":
            await self.write_line(data["text"], data["line"])
        elif command == "simulate":
            display_str = "\n".join([''.join(row) for row in self._content])
            border = '+' + '-' * self.width + '+'
            display_str = f"{border}\n" + '\n'.join([f"|{''.join(row)}|" for row in self._content]) + f"\n{border}"
            if not self._backlight:
                display_str = f"[Backlight OFF]\n{display_str}"
            return {"display": display_str}
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the Display device status."""
        return {"status": "OK", "backlight": self._backlight}

# Define device factory functions
async def create_device(factory_type: str, device_id: str, device_type: str, **kwargs) -> Device:
    """Create a device using the factory."""
    if factory_type == "hardware":
        if device_type == DeviceType.LED:
            return LEDDevice(device_id, kwargs["pin"], DeviceMode.HARDWARE)
        elif device_type == DeviceType.BUTTON:
            return ButtonDevice(device_id, kwargs["pin"], DeviceMode.HARDWARE, kwargs.get("pull_up", False), kwargs.get("debounce_ms", 50))
        elif device_type == DeviceType.TRAFFIC_LIGHT:
            return TrafficLightDevice(device_id, kwargs["red_pin"], kwargs["yellow_pin"], kwargs["green_pin"], DeviceMode.HARDWARE)
        elif device_type == DeviceType.DISPLAY:
            return DisplayDevice(device_id, kwargs["display_type"], kwargs["width"], kwargs["height"], kwargs["address"], DeviceMode.HARDWARE)
    elif factory_type == "simulation":
        if device_type == DeviceType.LED:
            return LEDDevice(device_id, kwargs["pin"], DeviceMode.SIMULATION)
        elif device_type == DeviceType.BUTTON:
            return ButtonDevice(device_id, kwargs["pin"], DeviceMode.SIMULATION, kwargs.get("pull_up", False), kwargs.get("debounce_ms", 50))
        elif device_type == DeviceType.TRAFFIC_LIGHT:
            return TrafficLightDevice(device_id, kwargs["red_pin"], kwargs["yellow_pin"], kwargs["green_pin"], DeviceMode.SIMULATION)
        elif device_type == DeviceType.DISPLAY:
            return DisplayDevice(device_id, kwargs["display_type"], kwargs["width"], kwargs["height"], kwargs["address"], DeviceMode.SIMULATION)
    return None

async def create_devices_from_config(config: Dict[str, Any]) -> Dict[str, Device]:
    """Create devices from a configuration."""
    devices = {}
    for device_config in config["devices"]:
        device = await create_device(device_config["factory"], device_config["id"], device_config["type"], **device_config)
        devices[device_config["id"]] = device
    return devices

# Define example functions
async def led_example():
    """Example demonstrating LED device functionality."""
    logger.info("=== LED Example ===")
    
    # Create an LED device
    led = LEDDevice("example_led", 17, DEFAULT_MODE)
    
    # Initialize the LED
    await led.initialize()
    
    # Basic operations
    logger.info("Turning LED on")
    await led.activate()
    await asyncio.sleep(1)
    
    logger.info("Turning LED off")
    await led.deactivate()
    await asyncio.sleep(1)
    
    # Brightness control (if PWM is supported)
    logger.info("Setting LED brightness to 50%")
    await led.set_brightness(0.5)
    await asyncio.sleep(1)
    
    # Blinking
    logger.info("Blinking LED (3 times)")
    await led.blink(0.2, 0.2, 3)
    await asyncio.sleep(2)  # Wait for blinking to complete
    
    # Command interface
    logger.info("Using command interface")
    result = await led.execute_command("activate", {})
    logger.info(f"Command result: {result}")
    await asyncio.sleep(1)
    
    result = await led.execute_command("deactivate", {})
    logger.info(f"Command result: {result}")
    
    # Get status
    status = await led.get_status()
    logger.info(f"LED status: {status}")
    
    # Clean up
    await led.cleanup()
    logger.info("LED example completed")

async def button_example():
    """Example demonstrating Button device functionality."""
    logger.info("\n=== Button Example ===")
    
    # Create a button device
    button = ButtonDevice("example_button", 27, DEFAULT_MODE, pull_up=True, debounce_ms=50)
    
    # Initialize the button
    await button.initialize()
    
    # Register event callbacks
    async def button_pressed_callback(event_type, **kwargs):
        logger.info(f"Button pressed! Event: {event_type}, Data: {kwargs}")
    
    async def button_released_callback(event_type, **kwargs):
        logger.info(f"Button released! Event: {event_type}, Data: {kwargs}")
        if kwargs.get('duration'):
            logger.info(f"Press duration: {kwargs['duration']:.2f} seconds")
    
    button.register_event_callback("pressed", button_pressed_callback)
    button.register_event_callback("released", button_released_callback)
    
    # Simulate button presses in simulation mode
    if button.mode == DeviceMode.SIMULATION or button.mode == DeviceMode.MOCK:
        logger.info("Simulating button press (short)")
        await button.simulate_press(0.2)
        await asyncio.sleep(0.5)
        
        logger.info("Simulating button press (long)")
        await button.simulate_press(1.0)
        await asyncio.sleep(1.5)
    else:
        # In hardware mode, wait for actual button presses
        logger.info("Waiting for button press (5 seconds)...")
        await asyncio.sleep(5)
    
    # Command interface
    logger.info("Using command interface")
    result = await button.execute_command("read", {})
    logger.info(f"Button state: {result}")
    
    # Get status
    status = await button.get_status()
    logger.info(f"Button status: {status}")
    
    # Clean up
    await button.cleanup()
    logger.info("Button example completed")

async def traffic_light_example():
    """Example demonstrating Traffic Light device functionality."""
    logger.info("\n=== Traffic Light Example ===")
    
    # Create a traffic light device
    traffic_light = TrafficLightDevice("example_traffic_light", 17, 18, 27, DEFAULT_MODE)
    
    # Initialize the traffic light
    await traffic_light.initialize()
    
    # Register event callback
    async def state_changed_callback(event_type, **kwargs):
        logger.info(f"Traffic light state changed to: {kwargs.get('state')}")
    
    traffic_light.register_event_callback("state_changed", state_changed_callback)
    
    # Manual state control
    logger.info("Setting traffic light to RED")
    await traffic_light.set_state(TrafficLightState.RED)
    await asyncio.sleep(2)
    
    logger.info("Setting traffic light to YELLOW")
    await traffic_light.set_state(TrafficLightState.YELLOW)
    await asyncio.sleep(2)
    
    logger.info("Setting traffic light to GREEN")
    await traffic_light.set_state(TrafficLightState.GREEN)
    await asyncio.sleep(2)
    
    # Start a traffic light cycle
    logger.info("Starting traffic light cycle (1 cycle)")
    await traffic_light.start_cycle(3.0, 1.0, 3.0, True, 1.0, 1)
    
    # Wait for the cycle to complete
    while traffic_light.is_cycling:
        await asyncio.sleep(0.5)
    
    # Command interface
    logger.info("Using command interface")
    result = await traffic_light.execute_command("set_state", {"state": "red"})
    logger.info(f"Command result: {result}")
    await asyncio.sleep(1)
    
    # Get status
    status = await traffic_light.get_status()
    logger.info(f"Traffic light status: {status}")
    
    # Clean up
    await traffic_light.cleanup()
    logger.info("Traffic light example completed")

async def display_example():
    """Example demonstrating Display device functionality."""
    logger.info("\n=== Display Example ===")
    
    # Create a display device (LCD)
    display = DisplayDevice("example_display", DisplayType.LCD, 16, 2, 0x27, DEFAULT_MODE)
    
    # Initialize the display
    await display.initialize()
    
    # Write text to the display
    logger.info("Writing text to display")
    await display.clear()
    await display.write_line("Hello, UnitMCP!", 0)
    await display.write_line("Hardware Demo", 1)
    await asyncio.sleep(2)
    
    # Update display content
    logger.info("Updating display content")
    await display.clear()
    await display.write_text("Count: ", 0, 0)
    
    # Simulate a counter
    for i in range(5):
        await display.set_cursor(7, 0)
        await display.write_text(str(i))
        await asyncio.sleep(0.5)
    
    # Toggle backlight
    logger.info("Toggling backlight")
    await display.set_backlight(False)
    await asyncio.sleep(1)
    await display.set_backlight(True)
    await asyncio.sleep(1)
    
    # Command interface
    logger.info("Using command interface")
    result = await display.execute_command("write_line", {"text": "Cmd Interface", "line": 1})
    logger.info(f"Command result: {result}")
    await asyncio.sleep(1)
    
    # Simulate display in console
    if display.mode == DeviceMode.SIMULATION or display.mode == DeviceMode.MOCK:
        result = await display.execute_command("simulate", {})
        logger.info(f"Display simulation:\n{result['display']}")
    
    # Get status
    status = await display.get_status()
    logger.info(f"Display status: {status}")
    
    # Clean up
    await display.cleanup()
    logger.info("Display example completed")

async def factory_example():
    """Example demonstrating Device Factory functionality."""
    logger.info("\n=== Device Factory Example ===")
    
    # Create devices using the factory
    logger.info("Creating devices using factory")
    
    # Create an LED using the factory
    led = await create_device("hardware" if DEFAULT_MODE == DeviceMode.HARDWARE else "simulation", "factory_led", DeviceType.LED, pin=17)
    
    # Create a button using the factory
    button = await create_device("hardware" if DEFAULT_MODE == DeviceMode.HARDWARE else "simulation", "factory_button", DeviceType.BUTTON, pin=27)
    
    # Initialize devices
    await led.initialize()
    await button.initialize()
    
    # Use the devices
    logger.info("Using factory-created devices")
    await led.activate()
    await asyncio.sleep(1)
    await led.deactivate()
    
    # Create devices from configuration
    logger.info("Creating devices from configuration")
    config = {
        "devices": [
            {
                "id": "config_led",
                "type": "LED",
                "factory": "simulation",
                "pin": 22
            },
            {
                "id": "config_button",
                "type": "BUTTON",
                "factory": "simulation",
                "pin": 23,
                "pull_up": True
            },
            {
                "id": "config_traffic_light",
                "type": "TRAFFIC_LIGHT",
                "factory": "simulation",
                "red_pin": 24,
                "yellow_pin": 25,
                "green_pin": 26
            }
        ]
    }
    
    devices = await create_devices_from_config(config)
    
    # Initialize all devices
    for device_id, device in devices.items():
        logger.info(f"Initializing {device_id}")
        await device.initialize()
    
    # Use a device from the config
    if "config_traffic_light" in devices:
        traffic_light = devices["config_traffic_light"]
        await traffic_light.set_state(TrafficLightState.GREEN)
        await asyncio.sleep(1)
        await traffic_light.set_state(TrafficLightState.OFF)
    
    # Clean up all devices
    for device_id, device in devices.items():
        await device.cleanup()
    
    # Clean up factory-created devices
    await led.cleanup()
    await button.cleanup()
    
    logger.info("Factory example completed")

async def main():
    """Main function to run all examples."""
    logger.info(f"Running in {DEFAULT_MODE} mode")
    
    # Run examples
    await led_example()
    await button_example()
    await traffic_light_example()
    await display_example()
    await factory_example()
    
    logger.info("All examples completed successfully!")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
