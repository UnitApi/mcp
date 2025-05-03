#!/usr/bin/env python3
"""
Configuration-based automation example for UnitMCP.

This example demonstrates how to use YAML configuration files to define
automation rules, triggers, and actions for controlling Raspberry Pi hardware.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

try:
    import yaml
except ImportError:
    print("PyYAML not found, trying to install...")
    os.system(f"{sys.executable} -m pip install pyyaml")
    import yaml

# Add project root to Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader
except ImportError:
    print("Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient
        from unitmcp.utils import EnvLoader
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()

# Configure logging
logging.basicConfig(
    level=env.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ConfigAutomation")


class ConfigAutomation:
    """Configuration-based automation system for UnitMCP."""

    def __init__(self, config_file: str = None, host: str = None, port: int = None):
        """
        Initialize the configuration automation system.
        
        Args:
            config_file: Path to the YAML configuration file
            host: Host address of the Raspberry Pi
            port: Port number for the MCP server
        """
        if config_file:
            self.config_file = config_file
        else:
            # Use the new configuration path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            self.config_file = os.path.join(project_root, "configs", "yaml", "automation", "default.yaml")
            
        self.host = host or env.get('RPI_HOST', 'localhost')
        self.port = port or env.get_int('RPI_PORT', 8080)
        self.client = MCPHardwareClient(self.host, self.port)
        self.logger = logging.getLogger("ConfigAutomation")
        self.config = {}
        self.devices = {}
        self.sequences = {}
        self.triggers = {}

    def load_config(self) -> bool:
        """
        Load configuration from YAML file.
        
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        try:
            self.logger.info(f"Loading configuration from {self.config_file}")
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
                
            # Extract devices, sequences, and triggers
            self.devices = self.config.get('devices', {})
            self.sequences = self.config.get('sequences', {})
            self.triggers = self.config.get('triggers', {})
            
            self.logger.info("Configuration loaded successfully")
            self.logger.debug(f"Devices: {list(self.devices.keys())}")
            self.logger.debug(f"Sequences: {list(self.sequences.keys())}")
            self.logger.debug(f"Triggers: {list(self.triggers.keys())}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False

    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to MCP server at {self.host}:{self.port}")
            await self.client.connect()
            self.logger.info("Connected to MCP server")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from the MCP server.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            await self.client.disconnect()
            self.logger.info("Disconnected from MCP server")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from MCP server: {e}")
            return False

    async def setup_devices(self) -> bool:
        """
        Set up devices defined in the configuration.
        
        Returns:
            True if all devices were set up successfully, False otherwise
        """
        try:
            self.logger.info("Setting up devices from configuration...")
            
            for device_id, device_config in self.devices.items():
                device_type = device_config.get('type')
                
                if device_type == 'led':
                    pin = device_config.get('pin', env.get_int('LED_PIN', 17))
                    self.logger.info(f"Setting up LED {device_id} on pin {pin}")
                    await self.client.setup_led(device_id, pin)
                    
                elif device_type == 'button':
                    pin = device_config.get('pin', env.get_int('BUTTON_PIN', 27))
                    self.logger.info(f"Setting up button {device_id} on pin {pin}")
                    await self.client.setup_button(device_id, pin)
                    
                elif device_type == 'traffic_light':
                    red_pin = device_config.get('red_pin', env.get_int('RED_PIN', 17))
                    yellow_pin = device_config.get('yellow_pin', env.get_int('YELLOW_PIN', 27))
                    green_pin = device_config.get('green_pin', env.get_int('GREEN_PIN', 22))
                    self.logger.info(f"Setting up traffic light {device_id} with pins {red_pin}, {yellow_pin}, {green_pin}")
                    await self.client.setup_traffic_light(device_id, red_pin, yellow_pin, green_pin)
                    
                else:
                    self.logger.warning(f"Unknown device type: {device_type} for device {device_id}")
            
            self.logger.info("All devices set up successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error setting up devices: {e}")
            return False

    async def run_sequence(self, sequence_name: str) -> bool:
        """
        Run a sequence defined in the configuration.
        
        Args:
            sequence_name: Name of the sequence to run
            
        Returns:
            True if sequence ran successfully, False otherwise
        """
        try:
            if sequence_name not in self.sequences:
                self.logger.error(f"Sequence {sequence_name} not found in configuration")
                return False
                
            sequence = self.sequences[sequence_name]
            steps = sequence.get('steps', [])
            
            self.logger.info(f"Running sequence: {sequence_name} with {len(steps)} steps")
            
            for i, step in enumerate(steps):
                step_type = step.get('type')
                device_id = step.get('device')
                action = step.get('action')
                params = step.get('params', {})
                
                self.logger.info(f"Step {i+1}: {step_type} - {action} on {device_id}")
                
                if step_type == 'led':
                    if action == 'on':
                        await self.client.control_led(device_id, 'on')
                    elif action == 'off':
                        await self.client.control_led(device_id, 'off')
                    elif action == 'blink':
                        on_time = params.get('on_time', env.get_float('FAST_BLINK', 0.1))
                        off_time = params.get('off_time', env.get_float('FAST_BLINK', 0.1))
                        count = params.get('count', 5)
                        await self.client.control_led(device_id, 'blink', on_time=on_time, off_time=off_time, blink_count=count)
                
                elif step_type == 'button':
                    if action == 'wait_press':
                        self.logger.info("Waiting for button press...")
                        while True:
                            result = await self.client.read_button(device_id)
                            if result.get('value') == 1:
                                self.logger.info("Button pressed! Continuing...")
                                break
                            await asyncio.sleep(0.1)
                
                elif step_type == 'traffic_light':
                    state = action
                    duration = params.get('duration')
                    await self.client.control_traffic_light(device_id, state, duration=duration)
                
                elif step_type == 'delay':
                    duration = params.get('duration', 1.0)
                    self.logger.info(f"Delaying for {duration} seconds")
                    await asyncio.sleep(duration)
                
                else:
                    self.logger.warning(f"Unknown step type: {step_type}")
                
                # Default delay between steps
                if i < len(steps) - 1 and step_type != 'delay':
                    await asyncio.sleep(0.5)
            
            self.logger.info(f"Sequence {sequence_name} completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error running sequence {sequence_name}: {e}")
            return False

    async def run_automation(self) -> bool:
        """
        Run the automation system based on configuration.
        
        Returns:
            True if automation ran successfully, False otherwise
        """
        try:
            # Load configuration
            if not self.load_config():
                return False
                
            # Connect to server
            if not await self.connect():
                return False
                
            # Set up devices
            if not await self.setup_devices():
                return False
                
            # Run main sequence if defined
            self.logger.info("Running automation sequence...")
            main_sequence = self.config.get('main_sequence', 'main')
            
            if main_sequence in self.sequences:
                await self.run_sequence(main_sequence)
            else:
                self.logger.warning(f"Main sequence '{main_sequence}' not found in configuration")
                
                # Try to run the first sequence found
                if self.sequences:
                    first_sequence = next(iter(self.sequences.keys()))
                    self.logger.info(f"Running first available sequence: {first_sequence}")
                    await self.run_sequence(first_sequence)
            
            self.logger.info("Automation completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error running automation: {e}")
            return False
        finally:
            # Disconnect from server
            await self.disconnect()


async def main():
    """Main entry point for the configuration automation example."""
    print("UnitMCP Configuration Automation Example")
    print("=======================================")
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Automation Example")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--host", type=str, help="Raspberry Pi host address")
    parser.add_argument("--port", type=int, help="MCP server port")
    
    args = parser.parse_args()
    
    # Create automation system
    automation = ConfigAutomation(
        config_file=args.config,
        host=args.host,
        port=args.port
    )
    
    try:
        # Run automation
        success = await automation.run_automation()
        
        if success:
            print("Automation completed successfully")
        else:
            print("Automation failed")
            
    except KeyboardInterrupt:
        print("\nAutomation interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
