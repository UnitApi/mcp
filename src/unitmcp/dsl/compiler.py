"""
DSL Compiler for UnitMCP

This module provides the main compiler interface for processing
various DSL formats and converting them to UnitMCP commands or objects.
"""

import json
import yaml
from typing import Dict, Any, Union, Optional
import logging

logger = logging.getLogger(__name__)

class DslCompiler:
    """
    Main compiler for UnitMCP DSL formats.
    
    This class handles the parsing and compilation of various DSL formats
    into UnitMCP commands or configuration objects.
    """
    
    def __init__(self):
        """Initialize the DSL compiler."""
        self._parsers = {
            'yaml': self._parse_yaml,
            'json': self._parse_json,
            'text': self._parse_text
        }
    
    def compile(self, content: str, format_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Compile DSL content into UnitMCP configuration or commands.
        
        Args:
            content: The DSL content as a string
            format_type: Optional format type ('yaml', 'json', 'text').
                         If not provided, the format will be auto-detected.
        
        Returns:
            A dictionary containing the compiled configuration or commands
        
        Raises:
            ValueError: If the content cannot be parsed or the format is invalid
        """
        if not content:
            raise ValueError("Empty DSL content provided")
        
        # Auto-detect format if not specified
        if not format_type:
            format_type = self._detect_format(content)
        
        # Parse the content based on the format
        if format_type not in self._parsers:
            raise ValueError(f"Unsupported DSL format: {format_type}")
        
        parsed_content = self._parsers[format_type](content)
        
        # Validate the parsed content
        self._validate(parsed_content)
        
        # Convert to UnitMCP format
        return self._convert(parsed_content)
    
    def _detect_format(self, content: str) -> str:
        """
        Detect the format of the DSL content.
        
        Args:
            content: The DSL content as a string
        
        Returns:
            The detected format type ('yaml', 'json', or 'text')
        """
        content = content.strip()
        
        # Check if it's JSON
        if content.startswith('{') and content.endswith('}'):
            return 'json'
        
        # Check if it's YAML
        if ':' in content and not content.startswith('#!'):
            return 'yaml'
        
        # Default to text
        return 'text'
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML content.
        
        Args:
            content: The YAML content as a string
        
        Returns:
            The parsed YAML as a dictionary
        
        Raises:
            ValueError: If the YAML cannot be parsed
        """
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            raise ValueError(f"Invalid YAML content: {e}")
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON content.
        
        Args:
            content: The JSON content as a string
        
        Returns:
            The parsed JSON as a dictionary
        
        Raises:
            ValueError: If the JSON cannot be parsed
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            raise ValueError(f"Invalid JSON content: {e}")
    
    def _parse_text(self, content: str) -> Dict[str, Any]:
        """
        Parse text content (e.g., arrow notation or natural language).
        
        Args:
            content: The text content as a string
        
        Returns:
            A dictionary representation of the text content
        """
        # Basic implementation for arrow notation (sensor -> action)
        if '->' in content:
            parts = [p.strip() for p in content.split('->')]
            if len(parts) >= 2:
                return {
                    'trigger': parts[0],
                    'action': parts[1]
                }
        
        # Default to treating as a command
        return {
            'command': content
        }
    
    def _validate(self, parsed_content: Dict[str, Any]) -> None:
        """
        Validate the parsed content.
        
        Args:
            parsed_content: The parsed content as a dictionary
        
        Raises:
            ValueError: If the content is invalid
        """
        # Basic validation - ensure we have a dictionary
        if not isinstance(parsed_content, dict):
            raise ValueError("Parsed content must be a dictionary")
        
        # More validation will be added in the future
    
    def _convert(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert the parsed content to UnitMCP format.
        
        Args:
            parsed_content: The parsed content as a dictionary
        
        Returns:
            The converted content in UnitMCP format
        """
        # Detect the content type
        if 'devices' in parsed_content:
            return self._convert_device_config(parsed_content)
        elif 'automation' in parsed_content or 'trigger' in parsed_content:
            return self._convert_automation(parsed_content)
        elif 'nodes' in parsed_content:
            return self._convert_flow(parsed_content)
        else:
            return self._convert_command(parsed_content)
    
    def _convert_device_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert device configuration to UnitMCP format.
        
        Args:
            config: The device configuration
        
        Returns:
            The converted device configuration
        """
        # For now, just return the config as-is
        # In the future, this will map to the device factory format
        return config
    
    def _convert_automation(self, automation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert automation configuration to UnitMCP format.
        
        Args:
            automation: The automation configuration
        
        Returns:
            The converted automation configuration
        """
        # For now, just return the automation as-is
        # In the future, this will map to the automation system format
        return automation
    
    def _convert_flow(self, flow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert flow configuration to UnitMCP format.
        
        Args:
            flow: The flow configuration
        
        Returns:
            The converted flow configuration
        """
        # For now, just return the flow as-is
        # In the future, this will map to the pipeline system format
        return flow
    
    def _convert_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert command to UnitMCP format.
        
        Args:
            command: The command
        
        Returns:
            The converted command
        """
        # For now, just return the command as-is
        # In the future, this will map to the command system format
        return command

    def detect_format(self, content: str) -> str:
        """
        Detect the format of the DSL content.
        
        Args:
            content: The DSL content to analyze
                
        Returns:
            str: The detected format ('yaml', 'json', or 'unknown')
        """
        content = content.strip()
        
        # Try to parse as YAML
        try:
            import yaml
            yaml.safe_load(content)
            return 'yaml'
        except yaml.YAMLError:
            pass
        
        # Try to parse as JSON
        try:
            import json
            json.loads(content)
            return 'json'
        except json.JSONDecodeError:
            pass
        
        # Unknown format
        return 'unknown'
