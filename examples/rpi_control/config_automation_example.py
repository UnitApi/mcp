#!/usr/bin/env python3
"""
Configuration-based Automation Example for UnitMCP

This example demonstrates how to:
1. Load automation configurations from YAML files
2. Create triggers and actions based on configuration
3. Set up automation sequences dynamically
4. Run the automation system without writing code

This example extends the basic automation example with configuration support,
making it more accessible to users without programming experience.
"""

import asyncio
import argparse
import platform
import time
import datetime
import logging
import os
import sys
import yaml
from typing import Optional, List, Dict, Any, Callable, Awaitable

# Add the project's src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_simulation_mode
except ImportError:
    print(f"Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient
        from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_simulation_mode
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        print("Please ensure the UnitMCP project is properly installed.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()

# Check if we're on a Raspberry Pi
IS_RPI = platform.machine() in ["armv7l", "aarch64"]
if not IS_RPI and not get_simulation_mode():
    logger = logging.getLogger("UnitMCP-Automation")
    logger.info("Not running on a Raspberry Pi. Using simulation mode.")

# Configure logging
logging.basicConfig(
    level=env.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(env.get('LOG_FILE', "automation.log"))
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
                logger.info(f"Time trigger '{self.name}' reached max count ({self.max_count})")
                self.running = False
                break
                
    async def start(self):
        """Start the time trigger."""
        if self.task is None or self.task.done():
            logger.info(f"Starting time trigger '{self.name}' (interval: {self.interval}s)")
            self.task = asyncio.create_task(self._monitor())
            
    async def stop(self):
        """Stop the time trigger."""
        if self.task and not self.task.done():
            logger.info(f"Stopping time trigger '{self.name}'")
            self.running = False
            await asyncio.sleep(0.1)  # Give the task a chance to exit cleanly
            if not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass


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
        result = await self.client.send_request("gpio.setupButton", {
            "device_id": self.device_id,
            "pin": self.pin,
            "pull_up": True
        })
        logger.debug(f"Button setup result: {result}")
        
    async def _monitor(self):
        """Monitor for GPIO state changes."""
        await self.setup()
        
        self.running = True
        while self.running:
            try:
                # Poll the button state
                result = await self.client.send_request("gpio.readButton", {
                    "device_id": self.device_id
                })
                
                button_state = result.get("state", False)
                current_time = time.time()
                
                # Check if we should trigger based on edge and debounce
                should_trigger = False
                
                if self.edge == "rising" and button_state:
                    should_trigger = True
                elif self.edge == "falling" and not button_state:
                    should_trigger = True
                elif self.edge == "both":
                    should_trigger = True
                    
                if should_trigger and (current_time - self.last_trigger_time) > self.debounce:
                    self.last_trigger_time = current_time
                    await self.fire()
                    
                # Don't poll too aggressively
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error monitoring GPIO trigger: {e}")
                await asyncio.sleep(1)  # Wait a bit before retrying
                
    async def start(self):
        """Start the GPIO trigger."""
        if self.task is None or self.task.done():
            logger.info(f"Starting GPIO trigger '{self.name}' on pin {self.pin}")
            self.task = asyncio.create_task(self._monitor())
            
    async def stop(self):
        """Stop the GPIO trigger."""
        if self.task and not self.task.done():
            logger.info(f"Stopping GPIO trigger '{self.name}'")
            self.running = False
            await asyncio.sleep(0.1)  # Give the task a chance to exit cleanly
            if not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass


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
            action_type: Type of audio action ('play', 'speak', 'tone')
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
                
                logger.debug(f"Speaking text: '{text}'")
                result = await self.client.text_to_speech(text, rate, volume)
                logger.debug(f"Text-to-speech result: {result}")
                
            elif self.action_type == "play":
                file_path = self.kwargs.get("file_path", "")
                if not file_path:
                    logger.error("No file path specified for audio playback")
                    return
                    
                logger.debug(f"Playing audio file: {file_path}")
                
                # Read the file and convert to base64
                import base64
                with open(file_path, "rb") as f:
                    audio_data = base64.b64encode(f.read()).decode("utf-8")
                    
                format_type = os.path.splitext(file_path)[1].lower()[1:]
                result = await self.client.play_audio(audio_data, format_type)
                logger.debug(f"Audio playback result: {result}")
                
            elif self.action_type == "tone":
                frequency = self.kwargs.get("frequency", 440)
                duration = self.kwargs.get("duration", 1.0)
                
                logger.debug(f"Generating tone: {frequency}Hz for {duration}s")
                result = await self.client.generate_tone(frequency, duration)
                logger.debug(f"Tone generation result: {result}")
                
            else:
                logger.error(f"Unknown audio action type: {self.action_type}")
                
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
            # Default to info level
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
        logger.info(f"Executing sequence '{self.name}'")
        for action in self.actions:
            await action.execute()
        logger.info(f"Sequence '{self.name}' completed")


class ConfigLoader:
    """Loads automation configuration from YAML files."""
    
    def __init__(self, config_file: str):
        """Initialize the configuration loader.
        
        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file
        self.config = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load the configuration from the YAML file.
        
        Returns:
            Dictionary containing the configuration
        """
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
            return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}


class ConfigAutomationExample:
    """Configuration-based automation example class."""
    
    def __init__(self, host: str = None, port: int = None, config_file: str = None):
        """Initialize the automation example.
        
        Args:
            host: The hostname or IP address of the MCP server
            port: The port of the MCP server
            config_file: Path to the YAML configuration file
        """
        self.host = host or get_rpi_host()
        self.port = port or get_rpi_port()
        self.config_file = config_file or env.get(
            'CONFIG_FILE', 
            os.path.join(os.path.dirname(__file__), "automation_config.yaml")
        )
        self.client: Optional[MCPHardwareClient] = None
        self.config_loader = ConfigLoader(self.config_file)
        self.config = {}
        self.triggers: Dict[str, Trigger] = {}
        self.actions: Dict[str, Action] = {}
        self.sequences: Dict[str, Sequence] = {}
        self.running = False
        
    async def connect(self):
        """Connect to the MCP server."""
        logger.info(f"Connecting to MCP server at {self.host}:{self.port}...")
        self.client = MCPHardwareClient(self.host, self.port)
        await self.client.connect()
        logger.info("Connected to MCP server")
        
    def load_configuration(self):
        """Load the automation configuration."""
        self.config = self.config_loader.load_config()
        
        # Configure logging level if specified
        settings = self.config.get("settings", {})
        log_level = settings.get("log_level", "").upper()
        if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.setLevel(getattr(logging, log_level))
            logger.info(f"Set log level to {log_level}")
            
        logger.info(f"Loaded configuration: {settings.get('name', 'Unnamed')}")
        logger.info(f"Description: {settings.get('description', 'No description')}")
        
    async def setup_hardware(self):
        """Set up the hardware devices needed for the automation."""
        if not self.client:
            await self.connect()
            
        # Extract all unique LED device IDs from actions
        led_devices = set()
        for action_name, action_config in self.config.get("actions", {}).items():
            if action_config.get("type") == "led":
                device_id = action_config.get("device_id")
                if device_id:
                    led_devices.add(device_id)
                    
        # Set up each LED device
        for device_id in led_devices:
            # Extract pin number from device_id (assuming format "led_XX")
            try:
                pin = int(device_id.split("_")[1])
                logger.info(f"Setting up LED on pin {pin}")
                await self.client.setup_led(device_id, pin)
            except (IndexError, ValueError):
                logger.error(f"Invalid LED device ID format: {device_id}")
                
    def create_triggers(self):
        """Create triggers based on the configuration."""
        if not self.client:
            logger.error("Client not connected, cannot create triggers")
            return
            
        for trigger_name, trigger_config in self.config.get("triggers", {}).items():
            trigger_type = trigger_config.get("type")
            
            if trigger_type == "time":
                interval = float(trigger_config.get("interval", 10.0))
                max_count = trigger_config.get("max_count")
                if max_count is not None:
                    max_count = int(max_count)
                    
                self.triggers[trigger_name] = TimeTrigger(
                    trigger_name, interval, max_count
                )
                logger.info(f"Created time trigger '{trigger_name}' with interval {interval}s")
                
            elif trigger_type == "gpio":
                pin = int(trigger_config.get("pin", 0))
                edge = trigger_config.get("edge", "rising")
                debounce = float(trigger_config.get("debounce", 0.2))
                
                self.triggers[trigger_name] = GPIOTrigger(
                    trigger_name, self.client, pin, edge, debounce
                )
                logger.info(f"Created GPIO trigger '{trigger_name}' on pin {pin}")
                
            else:
                logger.warning(f"Unknown trigger type: {trigger_type}")
                
    def create_actions(self):
        """Create actions based on the configuration."""
        if not self.client:
            logger.error("Client not connected, cannot create actions")
            return
            
        for action_name, action_config in self.config.get("actions", {}).items():
            action_type = action_config.get("type")
            
            if action_type == "led":
                device_id = action_config.get("device_id", "")
                action = action_config.get("action", "")
                
                # Extract additional parameters
                kwargs = {k: v for k, v in action_config.items() 
                         if k not in ["type", "device_id", "action"]}
                
                self.actions[action_name] = LEDAction(
                    action_name, self.client, device_id, action, **kwargs
                )
                logger.info(f"Created LED action '{action_name}' for {device_id}")
                
            elif action_type == "audio":
                action_subtype = action_config.get("action_type", "")
                
                # Extract additional parameters
                kwargs = {k: v for k, v in action_config.items() 
                         if k not in ["type", "action_type"]}
                
                self.actions[action_name] = AudioAction(
                    action_name, self.client, action_subtype, **kwargs
                )
                logger.info(f"Created audio action '{action_name}' of type {action_subtype}")
                
            elif action_type == "delay":
                delay = float(action_config.get("delay", 1.0))
                
                self.actions[action_name] = DelayAction(action_name, delay)
                logger.info(f"Created delay action '{action_name}' for {delay}s")
                
            elif action_type == "log":
                message = action_config.get("message", "")
                level = action_config.get("level", "info")
                
                self.actions[action_name] = LogAction(action_name, message, level)
                logger.info(f"Created log action '{action_name}'")
                
            else:
                logger.warning(f"Unknown action type: {action_type}")
                
    def create_sequences(self):
        """Create sequences based on the configuration."""
        for seq_name, seq_config in self.config.get("sequences", {}).items():
            trigger_name = seq_config.get("trigger")
            action_names = seq_config.get("actions", [])
            
            if not trigger_name or trigger_name not in self.triggers:
                logger.error(f"Invalid trigger '{trigger_name}' for sequence '{seq_name}'")
                continue
                
            # Create the sequence
            sequence = Sequence(seq_name)
            
            # Add actions to the sequence
            for action_name in action_names:
                if action_name in self.actions:
                    sequence.add_action(self.actions[action_name])
                else:
                    logger.error(f"Invalid action '{action_name}' for sequence '{seq_name}'")
                    
            # Store the sequence
            self.sequences[seq_name] = sequence
            
            # Connect the trigger to the sequence
            trigger = self.triggers[trigger_name]
            trigger.add_callback(sequence.execute)
            
            logger.info(f"Created sequence '{seq_name}' with trigger '{trigger_name}' and {len(action_names)} actions")
            
    async def start_triggers(self):
        """Start all triggers."""
        for trigger_name, trigger in self.triggers.items():
            await trigger.start()
            
    async def stop_triggers(self):
        """Stop all triggers."""
        for trigger_name, trigger in self.triggers.items():
            await trigger.stop()
            
    async def cleanup(self):
        """Clean up resources."""
        await self.stop_triggers()
        
        if self.client:
            # Turn off all LEDs
            for action_name, action in self.actions.items():
                if isinstance(action, LEDAction) and action.action == "on":
                    # Create an "off" version of this action
                    off_action = LEDAction(
                        f"{action_name}_off",
                        self.client,
                        action.device_id,
                        "off"
                    )
                    await off_action.execute()
                    
            await self.client.disconnect()
            logger.info("Disconnected from MCP server")
            
    async def run_demo(self, duration: float = None):
        """Run the complete automation demo."""
        if duration is None:
            duration = env.get_float('DEMO_DURATION', 30.0)
        
        logger.info(f"Running automation demo for {duration} seconds...")
        
        # Load configuration from file
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                
            # Process triggers
            if 'triggers' in config:
                for trigger_id, trigger_config in config['triggers'].items():
                    logger.info(f"Setting up trigger: {trigger_id}")
                    # Here you would set up the actual trigger based on config
                    # For example: self.setup_trigger(trigger_id, trigger_config)
                    
            else:
                logger.warning("No triggers defined in configuration")
                
            # Process actions
            if 'actions' in config:
                for action_id, action_config in config['actions'].items():
                    logger.info(f"Registering action: {action_id}")
                    # Here you would register the action based on config
                    # For example: self.register_action(action_id, action_config)
            else:
                logger.warning("No actions defined in configuration")
                
            # Process sequences
            if 'sequences' in config:
                for sequence_id, sequence_config in config['sequences'].items():
                    logger.info(f"Setting up sequence: {sequence_id}")
                    # Here you would set up the sequence based on config
                    # For example: self.setup_sequence(sequence_id, sequence_config)
            else:
                logger.warning("No sequences defined in configuration")
                
            # Process mappings
            if 'mappings' in config:
                for mapping in config['mappings']:
                    if 'trigger' in mapping and 'sequence' in mapping:
                        logger.info(f"Mapping trigger '{mapping['trigger']}' to sequence '{mapping['sequence']}'")
                        # Here you would set up the mapping
                        # For example: self.map_trigger_to_sequence(mapping['trigger'], mapping['sequence'])
            else:
                logger.warning("No trigger-to-sequence mappings defined")
                
            # Start the automation system
            logger.info("Starting automation system...")
            
            # Simulate running for the specified duration
            await asyncio.sleep(duration)
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
        except Exception as e:
            logger.error(f"Error running automation demo: {e}")
            
        logger.info("Automation demo completed")

async def main():
    """Main function to run the configuration-based automation example."""
    # Get the environment loader instance
    env_loader = env
    
    # Configure logging
    log_level = env_loader.get('LOG_LEVEL', 'INFO').upper()
    log_file = env_loader.get('LOG_FILE', 'automation.log')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("ConfigAutomation")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UnitMCP Configuration-based Automation Example")
    parser.add_argument("--host", type=str, default=None,
                        help="MCP server hostname or IP address")
    parser.add_argument("--port", type=int, default=None,
                        help="MCP server port")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to YAML configuration file")
    parser.add_argument("--duration", type=float, default=env_loader.get_float('DEMO_DURATION', 30.0),
                        help="Duration to run the demo in seconds")
    parser.add_argument("--env-file", type=str, default=None,
                        help="Path to .env file")
    
    args = parser.parse_args()
    
    # Load custom environment file if specified
    if args.env_file:
        env_loader = EnvLoader(args.env_file)
    
    # Log startup information
    logger.info("Starting UnitMCP Configuration-based Automation Example")
    logger.info(f"Server: {args.host or get_rpi_host()}:{args.port or get_rpi_port()}")
    logger.info(f"Config: {args.config or 'default'}")
    logger.info(f"Duration: {args.duration} seconds")
    
    # Create and run the automation example
    example = ConfigAutomationExample(
        host=args.host,
        port=args.port,
        config_file=args.config
    )
    
    try:
        await example.run_demo(args.duration)
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error running demo: {e}")
    finally:
        await example.cleanup()
        logger.info("Demo completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
