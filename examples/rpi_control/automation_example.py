#!/usr/bin/env python3
"""
Simple Automation Example for UnitMCP

This example demonstrates how to:
1. Set up a basic automation sequence
2. Use triggers (time-based or GPIO input)
3. Execute a series of actions in response
4. Log the execution progress

This example uses the UnitMCP hardware client to create simple automations.
"""

import asyncio
import argparse
import platform
import time
import datetime
import logging
import os
from typing import Optional, List, Dict, Any, Callable, Awaitable

from unitmcp import MCPHardwareClient

# Check if we're on a Raspberry Pi
IS_RPI = platform.machine() in ["armv7l", "aarch64"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("automation.log")
    ]
)
logger = logging.getLogger("UnitMCP-Automation")


class Trigger:
    """Base class for automation triggers."""
    
    def __init__(self, name: str):
        """Initialize the trigger.
        
        Args:
            name: Trigger name
        """
        self.name = name
        self.callbacks = []
        
    def add_callback(self, callback: Callable[[], Awaitable[None]]):
        """Add a callback to be executed when the trigger fires.
        
        Args:
            callback: Async function to call when triggered
        """
        self.callbacks.append(callback)
        
    async def fire(self):
        """Fire the trigger and execute all callbacks."""
        logger.info(f"Trigger '{self.name}' fired")
        for callback in self.callbacks:
            await callback()
            
    async def start(self):
        """Start monitoring for trigger conditions."""
        pass
        
    async def stop(self):
        """Stop monitoring for trigger conditions."""
        pass


class TimeTrigger(Trigger):
    """Time-based trigger that fires at specified intervals."""
    
    def __init__(self, name: str, interval: float, max_count: int = None):
        """Initialize the time trigger.
        
        Args:
            name: Trigger name
            interval: Time interval in seconds
            max_count: Maximum number of times to trigger (None for unlimited)
        """
        super().__init__(name)
        self.interval = interval
        self.max_count = max_count
        self.count = 0
        self.running = False
        self.task = None
        
    async def _monitor(self):
        """Monitor for time intervals."""
        self.running = True
        while self.running:
            await asyncio.sleep(self.interval)
            if not self.running:
                break
                
            self.count += 1
            logger.debug(f"Time trigger '{self.name}' count: {self.count}")
            
            await self.fire()
            
            if self.max_count is not None and self.count >= self.max_count:
                logger.info(f"Time trigger '{self.name}' reached max count {self.max_count}")
                self.running = False
                break
                
    async def start(self):
        """Start the time trigger."""
        logger.info(f"Starting time trigger '{self.name}' with interval {self.interval}s")
        self.task = asyncio.create_task(self._monitor())
        
    async def stop(self):
        """Stop the time trigger."""
        if self.running:
            logger.info(f"Stopping time trigger '{self.name}'")
            self.running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                self.task = None


class GPIOTrigger(Trigger):
    """GPIO-based trigger that fires when a pin changes state."""
    
    def __init__(self, name: str, client: MCPHardwareClient, pin: int, 
                 edge: str = "rising", debounce: float = 0.2):
        """Initialize the GPIO trigger.
        
        Args:
            name: Trigger name
            client: MCP hardware client
            pin: GPIO pin number
            edge: Trigger edge ('rising', 'falling', or 'both')
            debounce: Debounce time in seconds
        """
        super().__init__(name)
        self.client = client
        self.pin = pin
        self.edge = edge
        self.debounce = debounce
        self.running = False
        self.task = None
        self.last_trigger_time = 0
        self.device_id = f"button_{pin}"
        
    async def setup(self):
        """Set up the GPIO pin as a button."""
        logger.info(f"Setting up GPIO trigger on pin {self.pin}")
        await self.client.send_request("gpio.setupButton", {
            "device_id": self.device_id,
            "pin": self.pin
        })
        
    async def _monitor(self):
        """Monitor for GPIO state changes."""
        self.running = True
        last_state = False
        
        while self.running:
            try:
                # Read button state
                result = await self.client.send_request("gpio.readButton", {
                    "device_id": self.device_id
                })
                
                current_state = result.get("pressed", False)
                
                # Check for state change based on edge type
                if (self.edge == "rising" and not last_state and current_state) or \
                   (self.edge == "falling" and last_state and not current_state) or \
                   (self.edge == "both" and last_state != current_state):
                    
                    # Apply debounce
                    current_time = time.time()
                    if current_time - self.last_trigger_time > self.debounce:
                        self.last_trigger_time = current_time
                        logger.debug(f"GPIO trigger '{self.name}' detected edge: {self.edge}")
                        await self.fire()
                        
                last_state = current_state
                
                # Small delay to prevent excessive polling
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error in GPIO trigger monitoring: {e}")
                await asyncio.sleep(1)
                
    async def start(self):
        """Start the GPIO trigger."""
        logger.info(f"Starting GPIO trigger '{self.name}' on pin {self.pin}")
        await self.setup()
        self.task = asyncio.create_task(self._monitor())
        
    async def stop(self):
        """Stop the GPIO trigger."""
        if self.running:
            logger.info(f"Stopping GPIO trigger '{self.name}'")
            self.running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                self.task = None


class Action:
    """Base class for automation actions."""
    
    def __init__(self, name: str):
        """Initialize the action.
        
        Args:
            name: Action name
        """
        self.name = name
        
    async def execute(self):
        """Execute the action."""
        logger.info(f"Executing action '{self.name}'")


class LEDAction(Action):
    """Action to control an LED."""
    
    def __init__(self, name: str, client: MCPHardwareClient, device_id: str, action: str, **kwargs):
        """Initialize the LED action.
        
        Args:
            name: Action name
            client: MCP hardware client
            device_id: LED device ID
            action: LED action ('on', 'off', 'toggle', 'blink')
            **kwargs: Additional parameters for the LED action
        """
        super().__init__(name)
        self.client = client
        self.device_id = device_id
        self.action = action
        self.kwargs = kwargs
        
    async def execute(self):
        """Execute the LED action."""
        logger.info(f"Executing LED action '{self.name}': {self.action}")
        try:
            result = await self.client.control_led(self.device_id, self.action, **self.kwargs)
            logger.debug(f"LED action result: {result}")
        except Exception as e:
            logger.error(f"Error executing LED action: {e}")


class AudioAction(Action):
    """Action to play audio or speak text."""
    
    def __init__(self, name: str, client: MCPHardwareClient, action_type: str, **kwargs):
        """Initialize the audio action.
        
        Args:
            name: Action name
            client: MCP hardware client
            action_type: Type of audio action ('play', 'speak')
            **kwargs: Additional parameters for the audio action
        """
        super().__init__(name)
        self.client = client
        self.action_type = action_type
        self.kwargs = kwargs
        
    async def execute(self):
        """Execute the audio action."""
        logger.info(f"Executing audio action '{self.name}': {self.action_type}")
        try:
            if self.action_type == "speak":
                text = self.kwargs.get("text", "")
                rate = self.kwargs.get("rate", 150)
                volume = self.kwargs.get("volume", 1.0)
                
                result = await self.client.send_request("audio.textToSpeech", {
                    "text": text,
                    "rate": rate,
                    "volume": volume
                })
                logger.debug(f"Text-to-speech result: {result}")
                
            elif self.action_type == "play":
                audio_file = self.kwargs.get("file")
                if audio_file and os.path.exists(audio_file):
                    with open(audio_file, "rb") as f:
                        audio_data = f.read()
                    import base64
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    
                    result = await self.client.send_request("audio.playAudio", {
                        "audio_data": audio_base64,
                        "format": "wav" if audio_file.lower().endswith(".wav") else "raw"
                    })
                    logger.debug(f"Audio playback result: {result}")
                else:
                    logger.error(f"Audio file not found: {audio_file}")
                    
        except Exception as e:
            logger.error(f"Error executing audio action: {e}")


class DelayAction(Action):
    """Action to introduce a delay."""
    
    def __init__(self, name: str, delay: float):
        """Initialize the delay action.
        
        Args:
            name: Action name
            delay: Delay time in seconds
        """
        super().__init__(name)
        self.delay = delay
        
    async def execute(self):
        """Execute the delay action."""
        logger.info(f"Executing delay action '{self.name}': {self.delay}s")
        await asyncio.sleep(self.delay)


class LogAction(Action):
    """Action to log a message."""
    
    def __init__(self, name: str, message: str, level: str = "info"):
        """Initialize the log action.
        
        Args:
            name: Action name
            message: Message to log
            level: Log level ('debug', 'info', 'warning', 'error')
        """
        super().__init__(name)
        self.message = message
        self.level = level.lower()
        
    async def execute(self):
        """Execute the log action."""
        if self.level == "debug":
            logger.debug(self.message)
        elif self.level == "info":
            logger.info(self.message)
        elif self.level == "warning":
            logger.warning(self.message)
        elif self.level == "error":
            logger.error(self.message)
        else:
            logger.info(self.message)


class Sequence:
    """A sequence of actions to be executed in order."""
    
    def __init__(self, name: str, actions: List[Action] = None):
        """Initialize the sequence.
        
        Args:
            name: Sequence name
            actions: List of actions to execute
        """
        self.name = name
        self.actions = actions or []
        
    def add_action(self, action: Action):
        """Add an action to the sequence.
        
        Args:
            action: Action to add
        """
        self.actions.append(action)
        
    async def execute(self):
        """Execute all actions in the sequence."""
        logger.info(f"Executing sequence '{self.name}' with {len(self.actions)} actions")
        for action in self.actions:
            await action.execute()


class AutomationExample:
    """Simple automation example class."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        """Initialize the automation example.
        
        Args:
            host: The hostname or IP address of the MCP server
            port: The port of the MCP server
        """
        self.host = host
        self.port = port
        self.client: Optional[MCPHardwareClient] = None
        self.triggers: List[Trigger] = []
        self.running = False
        
    async def connect(self):
        """Connect to the MCP server."""
        logger.info(f"Connecting to MCP server at {self.host}:{self.port}...")
        self.client = MCPHardwareClient(self.host, self.port)
        await self.client.connect()
        logger.info("Connected to MCP server")
        
    async def setup_hardware(self):
        """Set up the hardware devices."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        # Set up LED on GPIO pin 17
        logger.info("Setting up LED on GPIO pin 17")
        await self.client.setup_led("led1", 17)
        
        # Set up LED on GPIO pin 18
        logger.info("Setting up LED on GPIO pin 18")
        await self.client.setup_led("led2", 18)
        
    async def create_time_based_automation(self):
        """Create a time-based automation example."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        # Create a time trigger that fires every 5 seconds, up to 5 times
        trigger = TimeTrigger("every_5s", interval=5.0, max_count=5)
        
        # Create a sequence of actions
        sequence = Sequence("blink_sequence")
        sequence.add_action(LogAction("log_start", "Starting blink sequence"))
        sequence.add_action(LEDAction("led_on", self.client, "led1", "on"))
        sequence.add_action(DelayAction("delay_1", 0.5))
        sequence.add_action(LEDAction("led_off", self.client, "led1", "off"))
        sequence.add_action(DelayAction("delay_2", 0.5))
        sequence.add_action(AudioAction("speak", self.client, "speak", text="Blink complete"))
        sequence.add_action(LogAction("log_end", "Blink sequence completed"))
        
        # Connect the trigger to the sequence
        trigger.add_callback(sequence.execute)
        
        # Add the trigger to our list
        self.triggers.append(trigger)
        
        # Start the trigger
        await trigger.start()
        
    async def create_button_based_automation(self):
        """Create a button-based automation example."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        # Create a GPIO trigger for a button on pin 23
        trigger = GPIOTrigger("button_press", self.client, 23, edge="rising")
        
        # Create a sequence of actions
        sequence = Sequence("button_sequence")
        sequence.add_action(LogAction("log_button", "Button pressed"))
        sequence.add_action(AudioAction("speak", self.client, "speak", text="Button pressed"))
        sequence.add_action(LEDAction("led_blink", self.client, "led2", "blink", on_time=0.2, off_time=0.2))
        sequence.add_action(DelayAction("delay", 3.0))
        sequence.add_action(LEDAction("led_off", self.client, "led2", "off"))
        
        # Connect the trigger to the sequence
        trigger.add_callback(sequence.execute)
        
        # Add the trigger to our list
        self.triggers.append(trigger)
        
        # Start the trigger
        await trigger.start()
        
    async def cleanup(self):
        """Clean up resources."""
        # Stop all triggers
        for trigger in self.triggers:
            await trigger.stop()
            
        # Turn off LEDs
        if self.client:
            try:
                await self.client.control_led("led1", "off")
                await self.client.control_led("led2", "off")
            except:
                pass
                
            await self.client.disconnect()
            logger.info("Disconnected from MCP server")
            
    async def run_demo(self, duration: float = 30.0):
        """Run the complete automation demo.
        
        Args:
            duration: Duration to run the demo in seconds
        """
        self.running = True
        try:
            await self.connect()
            await self.setup_hardware()
            
            # Create automations
            await self.create_time_based_automation()
            await self.create_button_based_automation()
            
            # Run for specified duration
            logger.info(f"Running automation demo for {duration} seconds")
            await asyncio.sleep(duration)
            
        finally:
            self.running = False
            await self.cleanup()


async def main():
    """Main function to run the automation example."""
    parser = argparse.ArgumentParser(description="UnitMCP Simple Automation Example")
    parser.add_argument("--host", default="127.0.0.1", help="MCP server hostname or IP")
    parser.add_argument("--port", type=int, default=8888, help="MCP server port")
    parser.add_argument("--duration", type=float, default=30.0, 
                      help="Duration to run the demo in seconds")
    args = parser.parse_args()
    
    if not IS_RPI:
        logger.info("Not running on a Raspberry Pi. Using simulation mode.")
    
    example = AutomationExample(host=args.host, port=args.port)
    await example.run_demo(duration=args.duration)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Automation example interrupted by user")
    except Exception as e:
        logger.error(f"Error in automation example: {e}", exc_info=True)
