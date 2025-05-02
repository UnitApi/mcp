on rpi_control we have several important Python scripts that handle Raspberry Pi interactions:
- `diagnose_and_setup.py`: For hardware diagnostics and setup
- `enhanced_hardware_client.py` and `enhanced_hardware_server.py`: Client-server architecture for hardware control
- `simple_client.py` and `simple_server.py`: Simplified versions focused on audio
- `speaker_control.py`: Audio functionality
- `setup_lcd.py`: LCD display setup and testing

Let's create a practical DSL implementation that can work with these existing scripts. I'll focus on designing a YAML-based DSL that can define configurations and automations while leveraging  existing codebase.

Here's a practical implementation plan:

## 1. DSL Design Example for UnitMCP

First, let's create a basic DSL example in YAML format that defines a simple device configuration:

```yaml
# device_config.yaml
---
device:
  name: raspberry_pi_4
  description: Main controller for home automation
  location: living_room

connections:
  network:
    type: wifi
    ssid: home_network
    ip: 192.168.1.100
    port: 8082

hardware:
  gpio:
    - pin: 18
      name: living_room_led
      type: output
      initial_state: off
    - pin: 23
      name: motion_sensor
      type: input
      pull: up

  i2c:
    - address: 0x27
      type: lcd
      name: status_display
      rows: 2
      cols: 16

  audio:
    output: default
    volume: 80

automations:
  - name: motion_light
    trigger:
      type: gpio
      pin: 23
      state: high
    condition:
      type: time
      after: sunset
      before: sunrise
    action:
      - type: gpio
        pin: 18
        state: on
      - type: lcd
        text: Motion detected
        line: 0
      - type: audio
        play: alerts/motion.wav
```

## 2. DSL Parser Implementation

Now, let's write a Python script that can parse this DSL and use  existing scripts to execute the commands:

```python
#!/usr/bin/env python3
"""
UnitMCP DSL Parser

This script parses the UnitMCP YAML-based DSL and executes commands
using the existing hardware control scripts.
"""

import argparse
import logging
import os
import subprocess
import sys
import yaml
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class UnitMCPExecutor:
    def __init__(self, config_file: str, host: str = 'localhost', port: int = 8082):
        """Initialize the UnitMCP executor with a configuration file."""
        self.config_file = config_file
        self.host = host
        self.port = port
        self.config = None
        self.automation_running = False

    def load_config(self) -> bool:
        """Load the configuration from the YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Successfully loaded configuration from {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def validate_config(self) -> bool:
        """Validate the loaded configuration."""
        if not self.config:
            logger.error("No configuration loaded")
            return False

        # Check required sections
        required_sections = ['device', 'connections']
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required section: {section}")
                return False

        logger.info("Configuration validation passed")
        return True

    def setup_hardware(self) -> bool:
        """Set up the hardware according to the configuration."""
        if not self.config:
            return False

        success = True

        # Set up GPIO pins
        if 'hardware' in self.config and 'gpio' in self.config['hardware']:
            for gpio in self.config['hardware']['gpio']:
                pin = gpio.get('pin')
                state = gpio.get('initial_state', 'off')
                if pin and state:
                    if state.lower() in ['on', 'high', '1', 'true']:
                        state_str = 'on'
                    else:
                        state_str = 'off'
                    success &= self._execute_gpio_command(pin, state_str)

        # Set up LCD if present
        if 'hardware' in self.config and 'i2c' in self.config['hardware']:
            for i2c_device in self.config['hardware']['i2c']:
                if i2c_device.get('type') == 'lcd':
                    # Clear the LCD first
                    success &= self._execute_lcd_command(clear=True)

                    # Display device name
                    device_name = self.config['device'].get('name', 'UnitMCP')
                    success &= self._execute_lcd_command(text=device_name, line=0)

                    # Display IP address
                    ip = self.config['connections']['network'].get('ip', 'Unknown IP')
                    success &= self._execute_lcd_command(text=ip, line=1)

        return success

    def run_automations(self) -> None:
        """Run the automations defined in the configuration."""
        if not self.config or 'automations' not in self.config:
            logger.warning("No automations defined")
            return

        self.automation_running = True
        logger.info("Starting automation loop")

        try:
            while self.automation_running:
                for automation in self.config['automations']:
                    self._check_and_execute_automation(automation)
                time.sleep(1)  # Check automations every second
        except KeyboardInterrupt:
            logger.info("Automation loop interrupted by user")
        finally:
            self.automation_running = False

    def _check_and_execute_automation(self, automation: Dict[str, Any]) -> None:
        """Check if an automation's trigger conditions are met and execute it if they are."""
        name = automation.get('name', 'Unnamed')
        trigger = automation.get('trigger')
        condition = automation.get('condition')
        actions = automation.get('action', [])

        if not trigger or not actions:
            return

        # TODO: Implement trigger checking logic
        # For now, we'll simulate triggers manually
        trigger_active = self._check_trigger(trigger)
        condition_met = self._check_condition(condition) if condition else True

        if trigger_active and condition_met:
            logger.info(f"Executing automation: {name}")
            for action in actions:
                self._execute_action(action)

    def _check_trigger(self, trigger: Dict[str, Any]) -> bool:
        """Check if a trigger condition is met."""
        # This is a placeholder for actual trigger checking logic
        # In a real implementation, this would query the hardware status
        # For testing, return False to prevent automatic execution
        return False

    def _check_condition(self, condition: Dict[str, Any]) -> bool:
        """Check if a condition is met."""
        condition_type = condition.get('type')

        if condition_type == 'time':
            # Time-based condition
            current_time = datetime.now().time()
            after_time = condition.get('after')
            before_time = condition.get('before')

            # TODO: Implement proper time checking
            return True

        return True

    def _execute_action(self, action: Dict[str, Any]) -> bool:
        """Execute an action based on its type."""
        action_type = action.get('type')

        if action_type == 'gpio':
            pin = action.get('pin')
            state = action.get('state')
            if pin is not None and state is not None:
                return self._execute_gpio_command(pin, state)

        elif action_type == 'lcd':
            text = action.get('text')
            line = action.get('line', 0)
            clear = action.get('clear', False)
            return self._execute_lcd_command(text, line, clear)

        elif action_type == 'audio':
            audio_file = action.get('play')
            if audio_file:
                return self._execute_audio_command(audio_file)

        logger.warning(f"Unknown action type: {action_type}")
        return False

    def _execute_gpio_command(self, pin: int, state: str) -> bool:
        """Execute a GPIO command using the enhanced_hardware_client.py script."""
        try:
            client_script = os.path.join(os.path.dirname(__file__), 'enhanced_hardware_client.py')
            cmd = [
                sys.executable, client_script,
                '--host', self.host,
                '--port', str(self.port),
                '--command', 'gpio',
                '--pin', str(pin),
                '--state', state
            ]

            logger.info(f"Executing GPIO command: pin {pin} to {state}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"GPIO command result: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"GPIO command failed: {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Error executing GPIO command: {e}")
            return False

    def _execute_lcd_command(self, text: Optional[str] = None, line: int = 0, clear: bool = False) -> bool:
        """Execute an LCD command using the enhanced_hardware_client.py script."""
        try:
            client_script = os.path.join(os.path.dirname(__file__), 'enhanced_hardware_client.py')
            cmd = [
                sys.executable, client_script,
                '--host', self.host,
                '--port', str(self.port),
                '--command', 'lcd',
            ]

            if clear:
                cmd.extend(['--clear'])
                logger.info("Executing LCD clear command")
            else:
                cmd.extend(['--text', text, '--line', str(line)])
                logger.info(f"Executing LCD command: text '{text}' on line {line}")

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"LCD command result: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"LCD command failed: {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Error executing LCD command: {e}")
            return False

    def _execute_audio_command(self, audio_file: str) -> bool:
        """Execute an audio command using the simple_client.py script."""
        try:
            client_script = os.path.join(os.path.dirname(__file__), 'simple_client.py')
            cmd = [
                sys.executable, client_script,
                '--host', self.host,
                '--port', '8081',  # Note: Different port for audio server
                '--file', audio_file,
                '--remote'
            ]

            logger.info(f"Executing audio command: play {audio_file}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Audio command result: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio command failed: {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Error executing audio command: {e}")
            return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='UnitMCP DSL Parser and Executor')
    parser.add_argument('--config', required=True, help='Path to the DSL configuration file')
    parser.add_argument('--host', default='localhost', help='Hardware control server hostname or IP')
    parser.add_argument('--port', type=int, default=8082, help='Hardware control server port')
    parser.add_argument('--setup-only', action='store_true', help='Only set up hardware, don\'t run automations')
    args = parser.parse_args()

    # Initialize the executor
    executor = UnitMCPExecutor(args.config, args.host, args.port)

    # Load and validate configuration
    if not executor.load_config() or not executor.validate_config():
        logger.error("Configuration error, exiting")
        return 1

    # Set up hardware
    if not executor.setup_hardware():
        logger.error("Hardware setup failed, exiting")
        return 1

    logger.info("Hardware setup completed successfully")

    # Run automations if not in setup-only mode
    if not args.setup_only:
        executor.run_automations()

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## 3. Testing Trigger Mechanism

Now, let's create a simple script to simulate triggers for testing automations:

```python
#!/usr/bin/env python3
"""
UnitMCP Trigger Simulator

This script simulates triggers for testing UnitMCP automations.
"""

import argparse
import json
import logging
import os
import socket
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def send_trigger(host: str, port: int, trigger_type: str, params: dict) -> bool:
    """Send a trigger to the UnitMCP server."""
    try:
        # Create a socket connection to the server
        logger.info(f"Connecting to server at {host}:{port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))

            # Create the command
            command = {
                "action": "trigger",
                "trigger_type": trigger_type,
                "params": params,
                "timestamp": datetime.now().isoformat()
            }

            # Send the command
            command_json = json.dumps(command)
            logger.info(f"Sending command: {command_json}")
            s.sendall(command_json.encode())

            # Receive the response
            response_data = s.recv(1024)
            if not response_data:
                logger.error("No response received")
                return False

            response = json.loads(response_data.decode())
            logger.info(f"Received response: {response}")

            return response.get("status") == "success"
    except Exception as e:
        logger.error(f"Error sending trigger: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='UnitMCP Trigger Simulator')
    parser.add_argument('--host', default='localhost', help='Server hostname or IP')
    parser.add_argument('--port', type=int, default=8082, help='Server port')
    parser.add_argument('--type', required=True, choices=['gpio', 'time', 'custom'], help='Trigger type')
    parser.add_argument('--pin', type=int, help='GPIO pin number (for gpio trigger)')
    parser.add_argument('--state', choices=['high', 'low'], help='GPIO pin state (for gpio trigger)')
    args = parser.parse_args()

    # Build the trigger parameters
    params = {}
    if args.type == 'gpio':
        if args.pin is None or args.state is None:
            logger.error("Pin and state are required for GPIO trigger")
            return 1
        params["pin"] = args.pin
        params["state"] = args.state

    # Send the trigger
    success = send_trigger(args.host, args.port, args.type, params)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
```

## 4. Extended DSL Example

Here's a more comprehensive example showing more capabilities:

```yaml
# full_config.yaml
---
device:
  name: home_automation_hub
  description: Central hub for home automation
  location: hallway

connections:
  network:
    type: ethernet
    ip: 192.168.1.10
    port: 8082
  mqtt:
    broker: mqtt.home.local
    port: 1883
    username: homeauto
    password: ${MQTT_PASSWORD}  # Environment variable

hardware:
  gpio:
    - pin: 18
      name: front_door_led
      type: output
      initial_state: off
    - pin: 23
      name: front_door_sensor
      type: input
      pull: up
    - pin: 24
      name: garage_door_sensor
      type: input
      pull: up
    - pin: 25
      name: doorbell_button
      type: input
      pull: up

  i2c:
    - address: 0x27
      type: lcd
      name: status_display
      rows: 2
      cols: 16
    - address: 0x68
      type: rtc
      name: real_time_clock

  audio:
    output: default
    volume: 80

  led_matrix:
    enabled: true
    brightness: 50

variables:
  home_mode: "normal"  # Can be "normal", "away", "vacation"
  notification_enabled: true
  door_chime_sound: "sounds/door_chime.wav"

automations:
  - name: front_door_alert
    trigger:
      type: gpio
      pin: 23
      state: high
    condition:
      type: variable
      name: home_mode
      value: "away"
    action:
      - type: gpio
        pin: 18
        state: on
      - type: lcd
        text: "Front door opened!"
        line: 0
      - type: lcd
        text: "${current_time}"
        line: 1
      - type: audio
        play: "alerts/intrusion.wav"
      - type: notification
        message: "Front door opened while away mode active!"
        priority: high

  - name: doorbell
    trigger:
      type: gpio
      pin: 25
      state: high
    action:
      - type: audio
        play: "${door_chime_sound}"
      - type: lcd
        text: "Doorbell"
        line: 0
      - type: lcd
        text: "${current_time}"
        line: 1
      - type: led_matrix
        action: text
        text: "DOOR"

  - name: status_update
    trigger:
      type: schedule
      interval: 60  # seconds
    action:
      - type: lcd
        text: "${device.name}"
        line: 0
      - type: lcd
        text: "${current_time}"
        line: 1

  - name: night_mode
    trigger:
      type: time
      at: "22:00:00"
    action:
      - type: variable
        name: home_mode
        value: "night"
      - type: lcd
        text: "Night mode"
        line: 0
      - type: gpio
        pin: 18
        state: off

  - name: morning_mode
    trigger:
      type: time
      at: "07:00:00"
    condition:
      type: day
      days: [monday, tuesday, wednesday, thursday, friday]
    action:
      - type: variable
        name: home_mode
        value: "normal"
      - type: lcd
        text: "Good morning!"
        line: 0
      - type: audio
        play: "sounds/morning.wav"

pipelines:
  - name: alarm_sequence
    steps:
      - name: flash_lights
        action:
          type: gpio
          pin: 18
          state: on
        delay: 0.5  # seconds
      - name: lights_off
        action:
          type: gpio
          pin: 18
          state: off
        delay: 0.5  # seconds
      - name: repeat
        count: 5
        go_to: flash_lights
```

## 5. Additional DSL Features

To make this DSL more practical, we should add a few more advanced features:

### Environment Variable Support

```python
def resolve_env_vars(config):
    """Recursively resolve environment variables in a configuration dict."""
    if isinstance(config, dict):
        return {k: resolve_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        # Extract the environment variable name
        env_var = config[2:-1]
        return os.environ.get(env_var, f"[ENV NOT FOUND: {env_var}]")
    else:
        return config
```

### Template Variables

```python
def resolve_template_vars(config, variables):
    """Recursively resolve template variables in a configuration dict."""
    if isinstance(config, dict):
        return {k: resolve_template_vars(v, variables) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_template_vars(item, variables) for item in config]
    elif isinstance(config, str) and "${" in config and "}" in config:
        # Process template variables
        result = config
        for var_name, var_value in variables.items():
            placeholder = "${" + var_name + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        return result
    else:
        return config
```

### Scheduled Triggers

```python
def check_scheduled_triggers(automations, last_check_time):
    """Check for automations with scheduled triggers."""
    current_time = time.time()
    triggered_automations = []

    for automation in automations:
        trigger = automation.get('trigger', {})
        if trigger.get('type') == 'schedule':
            interval = trigger.get('interval', 60)  # Default to 1 minute
            if current_time - last_check_time.get(automation['name'], 0) >= interval:
                triggered_automations.append(automation)
                last_check_time[automation['name']] = current_time

    return triggered_automations
```

## 6. DSL Validation Schema

To ensure the DSL is valid, we can create a JSON schema:

```python
import jsonschema

# Define the JSON schema for UnitMCP DSL validation
UNITMCP_DSL_SCHEMA = {
    "type": "object",
    "required": ["device", "connections"],
    "properties": {
        "device": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "location": {"type": "string"}
            }
        },
        "connections": {
            "type": "object",
            "properties": {
                "network": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["wifi", "ethernet"]},
                        "ip": {"type": "string"},
                        "port": {"type": "integer"}
                    }
                }
                # ... more connection types
            }
        },
        "hardware": {
            "type": "object",
            "properties": {
                "gpio": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["pin"],
                        "properties": {
                            "pin": {"type": "integer"},
                            "name": {"type": "string"},
                            "type": {"type": "string", "enum": ["input", "output"]},
                            "initial_state": {"type": "string", "enum": ["on", "off"]}
                        }
                    }
                },
                # ... more hardware types
            }
        },
        "automations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "trigger", "action"],
                "properties": {
                    "name": {"type": "string"},
                    "trigger": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"}
                            # Specific trigger types have different properties
                        }
                    },
                    "condition": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"}
                            # Specific condition types have different properties
                        }
                    },
                    "action": {
                        "oneOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"}
                                    # Specific action types have different properties
                                }
                            },
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"}
                                        # Specific action types have different properties
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
}

def validate_dsl(config):
    """Validate a UnitMCP DSL configuration against the schema."""
    try:
        jsonschema.validate(instance=config, schema=UNITMCP_DSL_SCHEMA)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)
```

## 7. Integration with Existing UnitMCP Scripts

Finally, let's create a modified version of the main script that integrates with  existing Python files:

```python
#!/usr/bin/env python3
"""
UnitMCP DSL Integration with Existing Scripts

This script integrates the UnitMCP DSL with the existing hardware control scripts.
"""

import argparse
import logging
import os
import sys
import yaml
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional

# Local imports - adjust paths as needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import diagnose_and_setup  # For hardware diagnostics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class UnitMCPIntegrator:
    def __init__(self, config_file: str, host: str = 'localhost', port: int = 8082):
        """Initialize the UnitMCP integrator with a configuration file."""
        self.config_file = config_file
        self.host = host
        self.port = port
        self.config = None
        self.server_process = None
        self.automation_thread = None
        self.running = False
        self.last_check_time = {}

    def load_and_validate_config(self) -> bool:
        """Load and validate the configuration."""
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)

            # TODO: Implement schema validation
            logger.info(f"Successfully loaded configuration from {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def run_diagnostics(self) -> bool:
        """Run hardware diagnostics using the diagnose_and_setup module."""
        logger.info("Running hardware diagnostics...")
        try:
            # Use the existing diagnostics script
            result = diagnose_and_setup.main()
            return result == 0
        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            return False

    def start_server(self) -> bool:
        """Start the hardware control server."""
        logger.info("Starting hardware control server...")
        try:
            server_script = os.path.join(os.path.dirname(__file__), 'enhanced_hardware_server.py')

            # Check if simulation mode is enabled
            simulation_arg = []
            if self.config.get('simulation_mode', False):
                simulation_arg = ['--simulate']

            # Start the server as a subprocess
            self.server_process = subprocess.Popen(
                [sys.executable, server_script, '--host', self.host, '--port', str(self.port)] + simulation_arg,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a moment for the server to start
            time.sleep(2)

            # Check if the server is running
            if self.server_process.poll() is not None:
                stderr = self.server_process.stderr.read()
                logger.error(f"Server failed to start: {stderr}")
                return False

            logger.info("Hardware control server started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False

    def setup_hardware(self) -> bool:
        """Set up the hardware according to the configuration."""
        if not self.config:
            return False

        logger.info("Setting up hardware...")

        success = True

        # Set up GPIO pins
        if 'hardware' in self.config and 'gpio' in self.config['hardware']:
            for gpio in self.config['hardware']['gpio']:
                pin = gpio.get('pin')
                pin_type = gpio.get('type', 'output')

                # For output pins, set initial state
                if pin_type == 'output':
                    state = gpio.get('initial_state', 'off')
                    success &= self._execute_command('gpio', [
                        '--pin', str(pin),
                        '--state', state
                    ])

        # Set up LCD if present
        if 'hardware' in self.config and 'i2c' in self.config['hardware']:
            for i2c_device in self.config['hardware']['i2c']:
                if i2c_device.get('type') == 'lcd':
                    # Clear the LCD
                    success &= self._execute_command('lcd', ['--clear'])

                    # Display welcome message
                    device_name = self.config['device'].get('name', 'UnitMCP')
                    success &= self._execute_command('lcd', [
                        '--text', f"Welcome to {device_name}",
                        '--line', '0'
                    ])

                    # Display current time
                    current_time = datetime.now().strftime('%H:%M:%S')
                    success &= self._execute_command('lcd', [
                        '--text', current_time,
                        '--line', '1'
                    ])


        logger.info(f"Hardware setup {'completed successfully' if success else 'failed'}")
        return success

    def start_automations(self) -> None:
        """Start the automation loop in a separate thread."""
        if self.automation_thread and self.automation_thread.is_alive():
            logger.warning("Automation thread is already running")
            return

        self.running = True
        self.automation_thread = threading.Thread(target=self._automation_loop)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        logger.info("Automation loop started")

    def stop_automations(self) -> None:
        """Stop the automation loop."""
        self.running = False
        if self.automation_thread:
            self.automation_thread.join(timeout=5)
        logger.info("Automation loop stopped")

    def _automation_loop(self) -> None:
        """Run the automation loop."""
        if not self.config or 'automations' not in self.config:
            logger.warning("No automations defined")
            return

        automations = self.config['automations']

        while self.running:
            try:
                # Check scheduled triggers
                current_time = datetime.now()
                for automation in automations:
                    trigger = automation.get('trigger', {})

                    # Handle time-based triggers
                    if trigger.get('type') == 'time':
                        trigger_time = trigger.get('at')
                        if trigger_time:
                            # Parse the trigger time
                            trigger_time_obj = datetime.strptime(trigger_time, '%H:%M:%S').time()
                            current_time_obj = current_time.time()

                            # Check if the current time matches the trigger time (within a minute)
                            if (current_time_obj.hour == trigger_time_obj.hour and
                                current_time_obj.minute == trigger_time_obj.minute and
                                current_time_obj.second >= trigger_time_obj.second and
                                current_time_obj.second < trigger_time_obj.second + 60):

                                # Check conditions if present
                                condition = automation.get('condition')
                                if not condition or self._check_condition(condition):
                                    logger.info(f"Time-based trigger fired for: {automation.get('name')}")
                                    self._execute_actions(automation.get('action', []))

                    # Handle scheduled triggers
                    elif trigger.get('type') == 'schedule':
                        interval = trigger.get('interval', 60)  # Default to 1 minute
                        last_run = self.last_check_time.get(automation.get('name'), 0)

                        if time.time() - last_run >= interval:
                            # Update last run time
                            self.last_check_time[automation.get('name')] = time.time()

                            # Check conditions if present
                            condition = automation.get('condition')
                            if not condition or self._check_condition(condition):
                                logger.info(f"Schedule-based trigger fired for: {automation.get('name')}")
                                self._execute_actions(automation.get('action', []))

                # Sleep to avoid high CPU usage
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in automation loop: {e}")
                time.sleep(5)  # Sleep longer on error

    def _check_condition(self, condition: Dict[str, Any]) -> bool:
        """Check if a condition is met."""
        condition_type = condition.get('type')

        if condition_type == 'time':
            # Time range condition
            current_time = datetime.now().time()
            after_time_str = condition.get('after')
            before_time_str = condition.get('before')

            if after_time_str and before_time_str:
                after_time = datetime.strptime(after_time_str, '%H:%M:%S').time()
                before_time = datetime.strptime(before_time_str, '%H:%M:%S').time()

                # Handle overnight ranges
                if after_time > before_time:  # Spans midnight
                    return current_time >= after_time or current_time <= before_time
                else:
                    return after_time <= current_time <= before_time

        elif condition_type == 'day':
            # Day of week condition
            days = condition.get('days', [])
            current_day = datetime.now().strftime('%A').lower()
            return current_day in [d.lower() for d in days]

        elif condition_type == 'variable':
            # Variable condition
            var_name = condition.get('name')
            var_value = condition.get('value')

            if var_name and var_value is not None:
                # Get the current variable value
                current_value = self.config.get('variables', {}).get(var_name)
                return current_value == var_value

        # Default to True if condition type not recognized
        return True

    def _execute_actions(self, actions: List[Dict[str, Any]]) -> None:
        """Execute a list of actions."""
        if not isinstance(actions, list):
            actions = [actions]

        for action in actions:
            action_type = action.get('type')

            if action_type == 'gpio':
                pin = action.get('pin')
                state = action.get('state')
                if pin is not None and state is not None:
                    self._execute_command('gpio', [
                        '--pin', str(pin),
                        '--state', state
                    ])

            elif action_type == 'lcd':
                text = action.get('text')
                line = action.get('line', 0)
                clear = action.get('clear', False)

                if clear:
                    self._execute_command('lcd', ['--clear'])
                elif text:
                    # Resolve variables in text
                    resolved_text = self._resolve_variables(text)
                    self._execute_command('lcd', [
                        '--text', resolved_text,
                        '--line', str(line)
                    ])

            elif action_type == 'audio':
                audio_file = action.get('play')
                if audio_file:
                    # Resolve variables in audio file path
                    resolved_file = self._resolve_variables(audio_file)
                    self._execute_command('speaker', [
                        '--sub-action', 'play_file',
                        '--audio-file', resolved_file
                    ])

            elif action_type == 'led_matrix':
                led_action = action.get('action')
                if led_action == 'text':
                    text = action.get('text')
                    x = action.get('x', 0)
                    y = action.get('y', 0)
                    if text:
                        # Resolve variables in text
                        resolved_text = self._resolve_variables(text)
                        self._execute_command('led_matrix', [
                            '--led-action', 'text',
                            '--text', resolved_text,
                            '--x', str(x),
                            '--y', str(y)
                        ])
                elif led_action == 'clear':
                    self._execute_command('led_matrix', [
                        '--led-action', 'clear'
                    ])

            elif action_type == 'variable':
                var_name = action.get('name')
                var_value = action.get('value')
                if var_name and var_value is not None:
                    # Update the variable
                    if 'variables' not in self.config:
                        self.config['variables'] = {}
                    self.config['variables'][var_name] = var_value
                    logger.info(f"Updated variable '{var_name}' to '{var_value}'")

            elif action_type == 'notification':
                message = action.get('message')
                priority = action.get('priority', 'normal')
                if message:
                    # Resolve variables in message
                    resolved_message = self._resolve_variables(message)
                    logger.info(f"NOTIFICATION [{priority}]: {resolved_message}")
                    # In a real implementation, this would send the notification

            elif action_type == 'pipeline':
                pipeline_name = action.get('name')
                if pipeline_name and 'pipelines' in self.config:
                    # Find and execute the pipeline
                    for pipeline in self.config.get('pipelines', []):
                        if pipeline.get('name') == pipeline_name:
                            self._execute_pipeline(pipeline)
                            break

            elif action_type == 'wait':
                seconds = action.get('seconds', 1)
                logger.info(f"Waiting for {seconds} seconds")
                time.sleep(seconds)

            else:
                logger.warning(f"Unknown action type: {action_type}")

    def _execute_pipeline(self, pipeline: Dict[str, Any]) -> None:
        """Execute a pipeline of steps."""
        steps = pipeline.get('steps', [])
        step_index = 0
        max_iterations = 100  # Safety limit

        while step_index < len(steps) and max_iterations > 0:
            step = steps[step_index]
            step_name = step.get('name', f"step_{step_index}")

            logger.info(f"Executing pipeline step: {step_name}")

            # Execute the action
            action = step.get('action')
            if action:
                self._execute_actions([action])

            # Handle flow control
            repeat = step.get('repeat', False)
            if repeat:
                go_to = step.get('go_to')
                count = step.get('count', 1)

                if go_to:
                    # Find the step index for go_to
                    for i, s in enumerate(steps):
                        if s.get('name') == go_to:
                            if count > 1:
                                # Update the count
                                step['count'] = count - 1
                                step_index = i
                            else:
                                # Move to the next step
                                step_index += 1
                            break
                    else:
                        # If go_to not found, move to the next step
                        step_index += 1
                else:
                    # No go_to specified, move to the next step
                    step_index += 1
            else:
                # Regular step, move to the next one
                step_index += 1

            # Handle delay
            delay = step.get('delay')
            if delay:
                time.sleep(float(delay))

            max_iterations -= 1

        if max_iterations <= 0:
            logger.warning("Pipeline execution exceeded maximum iterations")

    def _resolve_variables(self, text: str) -> str:
        """Resolve variables in a string."""
        if not isinstance(text, str):
            return str(text)

        # Handle special variables
        special_vars = {
            "${current_time}": datetime.now().strftime('%H:%M:%S'),
            "${current_date}": datetime.now().strftime('%Y-%m-%d'),
            "${device.name}": self.config.get('device', {}).get('name', 'UnitMCP'),
            "${device.location}": self.config.get('device', {}).get('location', 'Unknown')
        }

        result = text

        # Replace special variables
        for var_name, var_value in special_vars.items():
            result = result.replace(var_name, var_value)

        # Replace user-defined variables
        for var_name, var_value in self.config.get('variables', {}).items():
            placeholder = "${" + var_name + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))

        # Handle environment variables
        if "${" in result and "}" in result:
            import re
            env_vars = re.findall(r'\${([^}]+)}', result)
            for env_var in env_vars:
                if env_var in os.environ:
                    result = result.replace("${" + env_var + "}", os.environ[env_var])

        return result

    def _execute_command(self, command: str, args: List[str]) -> bool:
        """Execute a command using the hardware client script."""
        try:
            client_script = os.path.join(os.path.dirname(__file__), 'enhanced_hardware_client.py')
            cmd = [
                sys.executable, client_script,
                '--host', self.host,
                '--port', str(self.port),
                '--command', command
            ] + args

            logger.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.debug(f"Command executed successfully")
                return True
            else:
                logger.error(f"Command failed: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources."""
        # Stop automations
        self.stop_automations()

        # Stop server
        if self.server_process:
            logger.info("Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server did not terminate gracefully, forcing...")
                self.server_process.kill()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='UnitMCP DSL Integrator')
    parser.add_argument('--config', required=True, help='Path to the DSL configuration file')
    parser.add_argument('--host', default='localhost', help='Hardware control server hostname or IP')
    parser.add_argument('--port', type=int, default=8082, help='Hardware control server port')
    parser.add_argument('--no-server', action='store_true', help='Do not start the hardware server')
    parser.add_argument('--no-automations', action='store_true', help='Do not run automations')
    parser.add_argument('--skip-diagnostics', action='store_true', help='Skip hardware diagnostics')
    args = parser.parse_args()

    # Initialize the integrator
    integrator = UnitMCPIntegrator(args.config, args.host, args.port)

    # Load and validate configuration
    if not integrator.load_and_validate_config():
        logger.error("Configuration error, exiting")
        return 1

    # Run diagnostics if not skipped
    if not args.skip_diagnostics:
        if not integrator.run_diagnostics():
            logger.warning("Hardware diagnostics reported issues")
            # Continue anyway, as some devices might still work

    # Start server if not disabled
    if not args.no_server:
        if not integrator.start_server():
            logger.error("Failed to start hardware control server")
            return 1

    # Set up hardware
    if not integrator.setup_hardware():
        logger.error("Hardware setup failed")
        # Continue anyway, as partial setup might have succeeded

    # Start automations if not disabled
    if not args.no_automations:
        integrator.start_automations()

    try:
        # Keep running until interrupted
        logger.info("UnitMCP DSL Integrator running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Clean up
        integrator.cleanup()

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## 8. Testing Script

Let's create a simple testing script that verifies the DSL functionality with  existing hardware control scripts:

```python
#!/usr/bin/env python3
"""
UnitMCP DSL Test Script

This script tests the UnitMCP DSL implementation with the existing hardware control scripts.
"""

import argparse
import logging
import os
import sys
import yaml
import time
import subprocess
import tempfile
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Sample DSL for testing
TEST_DSL_CONFIG = """
---
device:
  name: test_device
  description: Test device for UnitMCP DSL
  location: test_lab

connections:
  network:
    type: ethernet
    ip: 127.0.0.1
    port: 8082

simulation_mode: true

hardware:
  gpio:
    - pin: 18
      name: test_led
      type: output
      initial_state: off

  i2c:
    - address: 0x27
      type: lcd
      name: test_lcd
      rows: 2
      cols: 16

variables:
  test_mode: "active"
  test_message: "Hello, UnitMCP!"

automations:
  - name: test_sequence
    trigger:
      type: manual
    action:
      - type: lcd
        clear: true
      - type: lcd
        text: "${test_message}"
        line: 0
      - type: lcd
        text: "${current_time}"
        line: 1
      - type: wait
        seconds: 2
      - type: gpio
        pin: 18
        state: on
      - type: wait
        seconds: 2
      - type: gpio
        pin: 18
        state: off
"""

def create_test_config() -> str:
    """Create a temporary test configuration file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml', mode='w') as f:
            f.write(TEST_DSL_CONFIG)
            config_file = f.name

        logger.info(f"Created test configuration file: {config_file}")
        return config_file
    except Exception as e:
        logger.error(f"Error creating test configuration: {e}")
        sys.exit(1)

def run_test(config_file: str, host: str, port: int) -> bool:
    """Run the UnitMCP DSL test."""
    try:
        # Start the hardware server
        server_script = os.path.join(os.path.dirname(__file__), 'enhanced_hardware_server.py')
        server_process = subprocess.Popen(
            [sys.executable, server_script, '--host', host, '--port', str(port), '--simulate'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        logger.info("Started hardware server in simulation mode")
        time.sleep(2)  # Wait for server to start

        if server_process.poll() is not None:
            stderr = server_process.stderr.read()
            logger.error(f"Server failed to start: {stderr}")
            return False

        try:
            # Test LCD command
            logger.info("Testing LCD command...")
            lcd_result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(os.path.dirname(__file__), 'enhanced_hardware_client.py'),
                    '--host', host,
                    '--port', str(port),
                    '--command', 'lcd',
                    '--text', 'DSL Test',
                    '--line', '0'
                ],
                check=True, capture_output=True, text=True
            )
            logger.info(f"LCD command result: {lcd_result.stdout.strip()}")

            # Test GPIO command
            logger.info("Testing GPIO command...")
            gpio_result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(os.path.dirname(__file__), 'enhanced_hardware_client.py'),
                    '--host', host,
                    '--port', str(port),
                    '--command', 'gpio',
                    '--pin', '18',
                    '--state', 'on'
                ],
                check=True, capture_output=True, text=True
            )
            logger.info(f"GPIO command result: {gpio_result.stdout.strip()}")

            # Test DSL integrator
            logger.info("Testing DSL integrator...")
            integrator_script = os.path.join(os.path.dirname(__file__), 'unitmcp_dsl_integrator.py')
            integrator_result = subprocess.run(
                [
                    sys.executable, integrator_script,
                    '--config', config_file,
                    '--host', host,
                    '--port', str(port),
                    '--no-server',  # Don't start a new server
                    '--skip-diagnostics'
                ],
                timeout=10,  # Limit test duration
                capture_output=True,
                text=True
            )

            if integrator_result.returncode == 0:
                logger.info("DSL integrator test passed")
                return True
            else:
                logger.error(f"DSL integrator test failed: {integrator_result.stderr}")
                return False

        finally:
            # Stop the server
            logger.info("Stopping hardware server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server did not terminate gracefully, forcing...")
                server_process.kill()

    except Exception as e:
        logger.error(f"Error running test: {e}")
        return False
    finally:
        # Clean up the test configuration file
        try:
            os.unlink(config_file)
            logger.info(f"Removed test configuration file: {config_file}")
        except:
            pass

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='UnitMCP DSL Test Script')
    parser.add_argument('--host', default='localhost', help='Host for testing')
    parser.add_argument('--port', type=int, default=8082, help='Port for testing')
    args = parser.parse_args()

    logger.info("Starting UnitMCP DSL test...")

    # Create temporary test configuration
    config_file = create_test_config()

    # Run the test
    success = run_test(config_file, args.host, args.port)

    if success:
        logger.info("All tests passed successfully!")
        return 0
    else:
        logger.error("Tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## 9. Summary and Recommendations

Based on the DSL implementation and integration with  existing rpi_remote scripts, here are some key recommendations:

1. **Leverage Existing Code**: The DSL implementation leverages  existing `enhanced_hardware_client.py` and `enhanced_hardware_server.py` scripts, making use of their proven functionality.

2. **Modular Design**: Keep the DSL parser separate from the hardware control code, allowing each to evolve independently.

3. **Gradual Migration**: Start by implementing simple DSL configurations that mirror  existing functionality, then gradually add more complex features.

4. **Environmental Variables**: Use environment variables for sensitive information like passwords and API keys.

5. **Thorough Validation**: Implement comprehensive schema validation to catch configuration errors early.

6. **Error Handling**: Implement robust error handling to deal with hardware failures, network issues, etc.

7. **Testing in Simulation Mode**: Always test new DSL features in simulation mode before deploying to real hardware.

8. **Documentation**: Create detailed documentation for the DSL syntax and examples to help users adopt it.

The implementation provides a clean, declarative way to configure  hardware and define automations, while building on the stable foundation of  existing scripts. This approach gives you both flexibility and reliability.

Would you like me to go into more detail on any particular aspect of the implementation, or would you like to see how to implement a specific feature in the DSL?