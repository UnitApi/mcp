"""
UnitMCP Runner Client Setup

This module provides functionality for setting up and managing the UnitMCP client
in the UnitMCP Runner environment.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ClientSetup:
    """
    Client setup for UnitMCP Runner.
    
    This class handles the setup and management of the UnitMCP client
    in the UnitMCP Runner environment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the client setup.
        
        Args:
            config: Configuration dictionary for the client
        """
        self.config = config
        self.server_host = config.get('server_host', 'localhost')
        self.server_port = config.get('server_port', 8888)
        self.client = None
        self.devices = {}
        self.logger = logging.getLogger("ClientSetup")
        
    async def initialize(self) -> bool:
        """
        Initialize the client setup.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing client setup for server {self.server_host}:{self.server_port}")
            
            # Import the client module
            from unitmcp.client.client import MCPHardwareClient
            
            # Create the client
            self.client = MCPHardwareClient(
                host=self.server_host,
                port=self.server_port
            )
            
            # Connect to the server
            if not await self.connect():
                self.logger.error("Failed to connect to server")
                return False
                
            # Load device configurations if specified
            if 'devices' in self.config:
                self.devices = self.config['devices']
                self.logger.info(f"Loaded {len(self.devices)} device configurations")
                
            # Otherwise, try to discover devices from the server
            else:
                await self.discover_devices()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing client setup: {e}")
            return False
            
    async def start(self) -> bool:
        """
        Start the UnitMCP client.
        
        Returns:
            True if start was successful, False otherwise
        """
        try:
            if not self.client:
                if not await self.initialize():
                    self.logger.error("Failed to initialize client")
                    return False
                    
            self.logger.info("Client started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting client: {e}")
            return False
            
    async def stop(self) -> bool:
        """
        Stop the UnitMCP client.
        
        Returns:
            True if stop was successful, False otherwise
        """
        try:
            if self.client:
                await self.disconnect()
                self.client = None
                
            self.logger.info("Client stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping client: {e}")
            return False
            
    async def connect(self) -> bool:
        """
        Connect to the UnitMCP server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        if not self.client:
            self.logger.error("Client not initialized")
            return False
            
        try:
            self.logger.info(f"Connecting to server at {self.server_host}:{self.server_port}")
            result = await self.client.connect()
            
            if not result:
                self.logger.error("Failed to connect to server")
                return False
                
            self.logger.info("Connected to server successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to server: {e}")
            return False
            
    async def disconnect(self) -> bool:
        """
        Disconnect from the UnitMCP server.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        if not self.client:
            self.logger.warning("Client not initialized, nothing to disconnect")
            return True
            
        try:
            self.logger.info("Disconnecting from server")
            result = await self.client.disconnect()
            
            if not result:
                self.logger.error("Failed to disconnect from server")
                return False
                
            self.logger.info("Disconnected from server successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from server: {e}")
            return False
            
    async def discover_devices(self) -> Dict[str, Any]:
        """
        Discover devices from the UnitMCP server.
        
        Returns:
            Dictionary of discovered devices
        """
        if not self.client:
            self.logger.error("Client not initialized")
            return {}
            
        try:
            self.logger.info("Discovering devices from server")
            result = await self.client.get_devices()
            
            if not result:
                self.logger.error("Failed to discover devices from server")
                return {}
                
            self.devices = result
            self.logger.info(f"Discovered {len(self.devices)} devices from server")
            return self.devices
            
        except Exception as e:
            self.logger.error(f"Error discovering devices from server: {e}")
            return {}
            
    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on a device.
        
        Args:
            command: Command to execute
            
        Returns:
            Dictionary with the result of the command execution
        """
        if not self.client:
            self.logger.error("Client not initialized")
            return {"success": False, "error": "Client not initialized"}
            
        try:
            # Extract command components
            device_id = command.get('device')
            action = command.get('action')
            parameters = command.get('parameters', {})
            
            if not device_id:
                self.logger.error("No device specified in command")
                return {"success": False, "error": "No device specified in command"}
                
            if not action:
                self.logger.error("No action specified in command")
                return {"success": False, "error": "No action specified in command"}
                
            # Check if the device exists
            if device_id not in self.devices:
                self.logger.error(f"Device {device_id} not found")
                return {"success": False, "error": f"Device {device_id} not found"}
                
            # Execute the command based on the action
            self.logger.info(f"Executing command: {action} on device {device_id} with parameters {parameters}")
            
            if action == 'turn_on':
                result = await self.client.turn_on(device_id)
            elif action == 'turn_off':
                result = await self.client.turn_off(device_id)
            elif action == 'toggle':
                result = await self.client.toggle(device_id)
            elif action == 'read':
                result = await self.client.read(device_id)
            elif action == 'write':
                value = parameters.get('value')
                if value is None:
                    return {"success": False, "error": "No value specified for write action"}
                result = await self.client.write(device_id, value)
            elif action == 'custom':
                method = parameters.get('method')
                args = parameters.get('args', {})
                if not method:
                    return {"success": False, "error": "No method specified for custom action"}
                result = await self.client.custom_action(device_id, method, args)
            else:
                self.logger.error(f"Unknown action: {action}")
                return {"success": False, "error": f"Unknown action: {action}"}
                
            return {
                "success": True,
                "device": device_id,
                "action": action,
                "parameters": parameters,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return {"success": False, "error": str(e)}
