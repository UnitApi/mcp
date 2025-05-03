"""
YAML Configuration Parser for UnitMCP

This module provides a parser for YAML-based device and automation configurations.
"""

import yaml
from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class YamlConfigParser:
    """
    Parser for YAML-based device and automation configurations.
    
    This class handles parsing and validation of YAML configurations
    for devices and automations in UnitMCP.
    """
    
    def __init__(self):
        """Initialize the YAML config parser."""
        self._device_schemas = {
            'led': self._validate_led_config,
            'button': self._validate_button_config,
            'traffic_light': self._validate_traffic_light_config,
            'display': self._validate_display_config,
            'gpio': self._validate_gpio_config,
            'i2c': self._validate_i2c_config
        }
    
    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML configuration content.
        
        Args:
            content: The YAML configuration content as a string
        
        Returns:
            A dictionary containing the parsed configuration
        
        Raises:
            ValueError: If the YAML cannot be parsed or the configuration is invalid
        """
        try:
            config = yaml.safe_load(content)
            if not isinstance(config, dict):
                raise ValueError("YAML configuration must be a dictionary")
            
            # Process the configuration based on its type
            if 'devices' in config:
                return self._process_device_config(config)
            elif 'automation' in config or 'automations' in config:
                return self._process_automation_config(config)
            else:
                # Generic configuration
                return config
                
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            raise ValueError(f"Invalid YAML content: {e}")
    
    def _process_device_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process device configuration.
        
        Args:
            config: The device configuration dictionary
        
        Returns:
            The processed device configuration
        
        Raises:
            ValueError: If the device configuration is invalid
        """
        processed_config = {'devices': {}}
        
        # Handle different device configuration formats
        devices = config.get('devices', {})
        
        # Format 1: Dictionary of devices
        if isinstance(devices, dict):
            for device_id, device_config in devices.items():
                # Ensure device has a type
                if 'type' not in device_config:
                    raise ValueError(f"Device '{device_id}' is missing a type")
                
                device_type = device_config['type']
                
                # Validate device configuration based on type
                if device_type in self._device_schemas:
                    self._device_schemas[device_type](device_id, device_config)
                
                # Add device to processed config
                processed_config['devices'][device_id] = device_config
        
        # Format 2: List of devices
        elif isinstance(devices, list):
            for device in devices:
                # Ensure device has a name and type
                if 'name' not in device:
                    raise ValueError("Device is missing a name")
                if 'type' not in device and 'platform' not in device:
                    raise ValueError(f"Device '{device['name']}' is missing a type or platform")
                
                device_id = device['name']
                device_type = device.get('type', device.get('platform'))
                
                # Validate device configuration based on type
                if device_type in self._device_schemas:
                    self._device_schemas[device_type](device_id, device)
                
                # Add device to processed config
                processed_config['devices'][device_id] = device
        
        else:
            raise ValueError("Invalid devices configuration format")
        
        # Add any global configuration
        for key, value in config.items():
            if key != 'devices':
                processed_config[key] = value
        
        return processed_config
    
    def _process_automation_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process automation configuration.
        
        Args:
            config: The automation configuration dictionary
        
        Returns:
            The processed automation configuration
        
        Raises:
            ValueError: If the automation configuration is invalid
        """
        processed_config = {}
        
        # Handle single automation
        if 'automation' in config:
            automation = config['automation']
            self._validate_automation(automation)
            processed_config['automation'] = automation
        
        # Handle multiple automations
        elif 'automations' in config:
            automations = config['automations']
            if not isinstance(automations, dict):
                raise ValueError("Automations must be a dictionary")
            
            processed_automations = {}
            for automation_id, automation in automations.items():
                self._validate_automation(automation)
                processed_automations[automation_id] = automation
            
            processed_config['automations'] = processed_automations
        
        # Add any global configuration
        for key, value in config.items():
            if key not in ['automation', 'automations']:
                processed_config[key] = value
        
        return processed_config
    
    def _validate_automation(self, automation: Dict[str, Any]) -> None:
        """
        Validate automation configuration.
        
        Args:
            automation: The automation configuration
        
        Raises:
            ValueError: If the automation configuration is invalid
        """
        # Check for required fields
        if 'trigger' not in automation:
            raise ValueError("Automation must have a trigger")
        
        if 'action' not in automation:
            raise ValueError("Automation must have an action")
        
        # Validate trigger
        trigger = automation['trigger']
        if not isinstance(trigger, dict):
            raise ValueError("Trigger must be a dictionary")
        
        if 'platform' not in trigger:
            raise ValueError("Trigger must have a platform")
    
    def _validate_led_config(self, device_id: str, config: Dict[str, Any]) -> None:
        """
        Validate LED device configuration.
        
        Args:
            device_id: The device ID
            config: The device configuration
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if 'pin' not in config:
            raise ValueError(f"LED device '{device_id}' is missing a pin")
    
    def _validate_button_config(self, device_id: str, config: Dict[str, Any]) -> None:
        """
        Validate button device configuration.
        
        Args:
            device_id: The device ID
            config: The device configuration
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if 'pin' not in config:
            raise ValueError(f"Button device '{device_id}' is missing a pin")
    
    def _validate_traffic_light_config(self, device_id: str, config: Dict[str, Any]) -> None:
        """
        Validate traffic light device configuration.
        
        Args:
            device_id: The device ID
            config: The device configuration
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if 'red_pin' not in config:
            raise ValueError(f"Traffic light device '{device_id}' is missing a red_pin")
        if 'yellow_pin' not in config:
            raise ValueError(f"Traffic light device '{device_id}' is missing a yellow_pin")
        if 'green_pin' not in config:
            raise ValueError(f"Traffic light device '{device_id}' is missing a green_pin")
    
    def _validate_display_config(self, device_id: str, config: Dict[str, Any]) -> None:
        """
        Validate display device configuration.
        
        Args:
            device_id: The device ID
            config: The device configuration
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if 'display_type' not in config:
            raise ValueError(f"Display device '{device_id}' is missing a display_type")
    
    def _validate_gpio_config(self, device_id: str, config: Dict[str, Any]) -> None:
        """
        Validate GPIO device configuration.
        
        Args:
            device_id: The device ID
            config: The device configuration
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if 'pin' not in config:
            raise ValueError(f"GPIO device '{device_id}' is missing a pin")
        if 'mode' not in config:
            raise ValueError(f"GPIO device '{device_id}' is missing a mode")
    
    def _validate_i2c_config(self, device_id: str, config: Dict[str, Any]) -> None:
        """
        Validate I2C device configuration.
        
        Args:
            device_id: The device ID
            config: The device configuration
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if 'address' not in config:
            raise ValueError(f"I2C device '{device_id}' is missing an address")
