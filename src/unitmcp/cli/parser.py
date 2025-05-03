"""
UnitMCP Command Parser

This module provides the command parser for the UnitMCP CLI,
which handles parsing and executing commands.
"""

import argparse
import asyncio
import logging
import os
import shlex
import yaml
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class CommandParser:
    """
    Parser for UnitMCP CLI commands.
    
    This class handles parsing and executing commands for the UnitMCP CLI.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8081, config: Dict[str, Any] = None):
        """
        Initialize the command parser.
        
        Args:
            host: Host address for the UnitMCP server
            port: Port for the UnitMCP server
            config: Optional configuration dictionary
        """
        self.host = host
        self.port = port
        self.config = config or {}
        
        # Initialize command handlers
        self._command_handlers = {
            'device': self._handle_device_command,
            'automation': self._handle_automation_command,
            'system': self._handle_system_command,
            'nl': self._handle_nl_command
        }
        
        # Initialize client connection
        self._client = None
    
    async def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Execute a command.
        
        Args:
            args: Command arguments
        
        Returns:
            Command result
        
        Raises:
            ValueError: If the command is invalid
        """
        # Ensure we have a command
        if not hasattr(args, 'command') or args.command is None:
            return {'error': 'No command specified'}
        
        # Get the command handler
        command = args.command
        if command not in self._command_handlers:
            return {'error': f"Unknown command: {command}"}
        
        # Execute the command
        handler = self._command_handlers[command]
        return await handler(args)
    
    def parse_shell_command(self, command_str: str) -> Optional[argparse.Namespace]:
        """
        Parse a shell command string.
        
        Args:
            command_str: Command string
        
        Returns:
            Parsed arguments, or None if parsing failed
        """
        if not command_str.strip():
            return None
        
        try:
            # Split the command string
            parts = shlex.split(command_str)
            
            # Create a namespace with the command
            args = argparse.Namespace()
            args.command = parts[0]
            
            # Add subcommand if present
            if len(parts) > 1:
                args.subcommand = parts[1]
            
            # Add remaining arguments
            if len(parts) > 2:
                args.args = parts[2:]
            
            # Add host and port
            args.host = self.host
            args.port = self.port
            
            return args
        
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            return None
    
    def parse(self, command_str: str) -> Optional[argparse.Namespace]:
        """
        Parse a command string into a structured command.
        This is an alias for parse_shell_command.
        
        Args:
            command_str: Command string
            
        Returns:
            Parsed arguments, or None if parsing failed
        """
        return self.parse_shell_command(command_str)
    
    async def _handle_device_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Handle a device command.
        
        Args:
            args: Command arguments
        
        Returns:
            Command result
        """
        # Ensure we have a client connection
        await self._ensure_client()
        
        # Handle device commands
        if not hasattr(args, 'subcommand') or args.subcommand is None:
            return {'error': 'No device subcommand specified'}
        
        subcommand = args.subcommand
        
        if subcommand == 'list':
            # List all devices
            return await self._client.list_devices()
        
        elif subcommand == 'info':
            # Get device information
            if not hasattr(args, 'device_id') or args.device_id is None:
                return {'error': 'No device ID specified'}
            
            return await self._client.get_device_info(args.device_id)
        
        elif subcommand == 'control':
            # Control a device
            if not hasattr(args, 'device_id') or args.device_id is None:
                return {'error': 'No device ID specified'}
            
            if not hasattr(args, 'action') or args.action is None:
                return {'error': 'No action specified'}
            
            # Parse parameters
            params = {}
            if hasattr(args, 'parameters') and args.parameters:
                for param in args.parameters:
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = self._parse_value(value)
            
            return await self._client.control_device(
                args.device_id,
                args.action,
                params
            )
        
        else:
            return {'error': f"Unknown device subcommand: {subcommand}"}
    
    async def _handle_automation_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Handle an automation command.
        
        Args:
            args: Command arguments
        
        Returns:
            Command result
        """
        # Ensure we have a client connection
        await self._ensure_client()
        
        # Handle automation commands
        if not hasattr(args, 'subcommand') or args.subcommand is None:
            return {'error': 'No automation subcommand specified'}
        
        subcommand = args.subcommand
        
        if subcommand == 'list':
            # List all automations
            return await self._client.list_automations()
        
        elif subcommand == 'load':
            # Load an automation from a file
            if not hasattr(args, 'file') or args.file is None:
                return {'error': 'No file specified'}
            
            # Read the file
            try:
                with open(args.file, 'r') as f:
                    content = f.read()
            except Exception as e:
                return {'error': f"Error reading file: {e}"}
            
            return await self._client.load_automation(content)
        
        elif subcommand == 'enable':
            # Enable an automation
            if not hasattr(args, 'automation_id') or args.automation_id is None:
                return {'error': 'No automation ID specified'}
            
            return await self._client.enable_automation(args.automation_id)
        
        elif subcommand == 'disable':
            # Disable an automation
            if not hasattr(args, 'automation_id') or args.automation_id is None:
                return {'error': 'No automation ID specified'}
            
            return await self._client.disable_automation(args.automation_id)
        
        else:
            return {'error': f"Unknown automation subcommand: {subcommand}"}
    
    async def _handle_system_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Handle a system command.
        
        Args:
            args: Command arguments
        
        Returns:
            Command result
        """
        # Ensure we have a client connection
        await self._ensure_client()
        
        # Handle system commands
        if not hasattr(args, 'subcommand') or args.subcommand is None:
            return {'error': 'No system subcommand specified'}
        
        subcommand = args.subcommand
        
        if subcommand == 'status':
            # Get system status
            return await self._client.get_system_status()
        
        elif subcommand == 'restart':
            # Restart the system
            return await self._client.restart_system()
        
        else:
            return {'error': f"Unknown system subcommand: {subcommand}"}
    
    async def _handle_nl_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Handle a natural language command.
        
        Args:
            args: Command arguments
        
        Returns:
            Command result
        """
        # Check if we have a natural language command
        if not hasattr(args, 'command') or args.command is None:
            return {'error': 'No natural language command specified'}
        
        # Import the Claude integration
        try:
            from unitmcp.llm.claude import ClaudeIntegration
            claude = ClaudeIntegration()
        except ImportError:
            return {
                'error': 'Claude integration not available. '
                         'Please install the required dependencies.'
            }
        
        # Process the natural language command
        try:
            # Join the command parts if it's a list
            if isinstance(args.command, list):
                command = ' '.join(args.command)
            else:
                command = args.command
            
            # Process the command using Claude
            result = await claude.process_command(command)
            
            # Execute the resulting command
            if 'command_type' in result:
                # Ensure we have a client connection
                await self._ensure_client()
                
                if result['command_type'] == 'device_control':
                    return await self._client.control_device(
                        result['target'],
                        result['action'],
                        result.get('parameters', {})
                    )
                
                elif result['command_type'] == 'automation':
                    # Handle automation commands
                    if result['action'] == 'enable':
                        return await self._client.enable_automation(result['target'])
                    elif result['action'] == 'disable':
                        return await self._client.disable_automation(result['target'])
                    else:
                        return {'error': f"Unknown automation action: {result['action']}"}
                
                elif result['command_type'] == 'system':
                    # Handle system commands
                    if result['action'] == 'status':
                        return await self._client.get_system_status()
                    elif result['action'] == 'restart':
                        return await self._client.restart_system()
                    else:
                        return {'error': f"Unknown system action: {result['action']}"}
                
                else:
                    return {'error': f"Unknown command type: {result['command_type']}"}
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing natural language command: {e}")
            return {'error': f"Error processing natural language command: {e}"}
    
    async def _ensure_client(self) -> None:
        """
        Ensure we have a client connection.
        
        Raises:
            ConnectionError: If the client connection cannot be established
        """
        if self._client is None:
            try:
                # Import the client
                from unitmcp.client.hardware_client import HardwareClient
                
                # Create the client
                self._client = HardwareClient(self.host, self.port)
                
                # Connect to the server
                await self._client.connect()
            
            except ImportError:
                raise ConnectionError(
                    'Hardware client not available. '
                    'Please install the required dependencies.'
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to server: {e}")
    
    def _parse_value(self, value_str: str) -> Any:
        """
        Parse a value string.
        
        Args:
            value_str: Value string
        
        Returns:
            Parsed value
        """
        # Try to parse as a number
        try:
            # Integer
            if value_str.isdigit():
                return int(value_str)
            
            # Float
            if '.' in value_str and all(c.isdigit() or c == '.' for c in value_str):
                return float(value_str)
        except ValueError:
            pass
        
        # Boolean
        if value_str.lower() in ('true', 'yes', 'on'):
            return True
        if value_str.lower() in ('false', 'no', 'off'):
            return False
        
        # String
        return value_str
