"""
DSL integration for UnitMCP Claude Plugin.

This module provides integration with the UnitMCP DSL system
for configuration loading and command execution.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class DslIntegration:
    """
    Integrates with the UnitMCP DSL system.
    
    This class provides access to DSL functionality for
    the Claude plugin.
    """
    
    def __init__(self, simulation_mode=True):
        """
        Initialize the DSL integration.
        
        Args:
            simulation_mode: Whether to run in simulation mode
        """
        try:
            from unitmcp.dsl.integration import DslHardwareIntegration
            self.dsl_integration = DslHardwareIntegration(simulation=simulation_mode)
            logger.info("DSL integration initialized")
        except ImportError as e:
            logger.error(f"Failed to import DslHardwareIntegration: {str(e)}")
            self.dsl_integration = None
        
        self.simulation_mode = simulation_mode
        self.devices = {}
    
    async def load_config(self, config_text: str) -> Dict[str, Any]:
        """
        Load a DSL configuration from text.
        
        Args:
            config_text: The configuration text in YAML format
            
        Returns:
            A dictionary containing the loaded devices and other configuration
        """
        if not self.dsl_integration:
            logger.error("DSL integration not available")
            return {"status": "error", "error": "DSL integration not available"}
        
        try:
            logger.info("Loading DSL configuration")
            result = await self.dsl_integration.load_config(config_text)
            logger.info(f"Loaded configuration with {len(result.get('devices', {}))} devices")
            return result
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def load_config_file(self, config_path: str) -> Dict[str, Any]:
        """
        Load a DSL configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            A dictionary containing the loaded devices and other configuration
        """
        if not os.path.exists(config_path):
            logger.error(f"Configuration file not found: {config_path}")
            return {"status": "error", "error": f"Configuration file not found: {config_path}"}
        
        try:
            with open(config_path, 'r') as f:
                config_text = f.read()
            
            return await self.load_config(config_text)
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def initialize_devices(self) -> Dict[str, Any]:
        """
        Initialize all devices in the loaded configuration.
        
        Returns:
            A dictionary containing the initialization results
        """
        if not self.dsl_integration:
            logger.error("DSL integration not available")
            return {"status": "error", "error": "DSL integration not available"}
        
        try:
            logger.info("Initializing devices")
            result = await self.dsl_integration.initialize_devices()
            logger.info("Devices initialized")
            return result
        except Exception as e:
            logger.error(f"Error initializing devices: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command using the DSL integration.
        
        Args:
            command: The command to execute
            
        Returns:
            A dictionary containing the command execution result
        """
        if not self.dsl_integration:
            logger.error("DSL integration not available")
            return {"status": "error", "error": "DSL integration not available"}
        
        try:
            logger.info(f"Executing command: {command}")
            result = await self.dsl_integration.execute_command(command)
            logger.info(f"Command executed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_device(self, device_id: str) -> Any:
        """
        Get a device by ID.
        
        Args:
            device_id: The ID of the device
            
        Returns:
            The device object, or None if not found
        """
        if not self.dsl_integration:
            logger.error("DSL integration not available")
            return None
        
        try:
            return self.dsl_integration.get_device(device_id)
        except Exception as e:
            logger.error(f"Error getting device: {str(e)}")
            return None
