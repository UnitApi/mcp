"""
Claude 3.7 Integration for UnitMCP

This module provides integration with Claude 3.7 for natural language
processing of commands in UnitMCP.
"""

import asyncio
import json
import logging
import os
import re
import requests
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class ClaudeIntegration:
    """
    Integration with Claude 3.7 for natural language processing.
    
    This class provides methods for processing natural language commands
    using Claude 3.7 and converting them to UnitMCP commands.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude integration.
        
        Args:
            api_key: Optional API key for Claude 3.7.
                    If not provided, it will be loaded from the CLAUDE_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not self.api_key:
            logger.warning("Claude API key not provided. Using simulation mode.")
        
        # Load prompts
        self._load_prompts()
    
    async def process_command(self, natural_language: str) -> Dict[str, Any]:
        """
        Process a natural language command using Claude 3.7.
        
        Args:
            natural_language: The natural language command
        
        Returns:
            A dictionary containing the processed command
        
        Raises:
            ValueError: If the command cannot be processed
        """
        # Build the prompt
        prompt = self._build_prompt(natural_language)
        
        # Call the Claude API
        response = await self._call_claude_api(prompt)
        
        # Parse the response
        return self._parse_response(response)
    
    def _load_prompts(self) -> None:
        """Load prompts for different command types."""
        self._prompts = {
            'device_control': self._load_prompt('device_control'),
            'automation': self._load_prompt('automation'),
            'system': self._load_prompt('system'),
            'general': self._load_prompt('general')
        }
    
    def _load_prompt(self, prompt_type: str) -> str:
        """
        Load a prompt template.
        
        Args:
            prompt_type: The type of prompt to load
        
        Returns:
            The prompt template
        """
        # Default prompts
        default_prompts = {
            'device_control': """
            Convert the following natural language command into a UnitMCP device control command:
            
            Command: {command}
            
            Output the result as a JSON object with the following structure:
            {{
                "command_type": "device_control",
                "target": "device_id",
                "action": "specific action to perform",
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }}
            }}
            
            Only output valid JSON, nothing else.
            """,
            
            'automation': """
            Convert the following natural language command into a UnitMCP automation command:
            
            Command: {command}
            
            Output the result as a JSON object with the following structure:
            {{
                "command_type": "automation",
                "target": "automation_id",
                "action": "enable|disable|trigger",
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }}
            }}
            
            Only output valid JSON, nothing else.
            """,
            
            'system': """
            Convert the following natural language command into a UnitMCP system command:
            
            Command: {command}
            
            Output the result as a JSON object with the following structure:
            {{
                "command_type": "system",
                "target": "system component",
                "action": "specific action to perform",
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }}
            }}
            
            Only output valid JSON, nothing else.
            """,
            
            'general': """
            Convert the following natural language command into a UnitMCP command:
            
            Command: {command}
            
            Output the result as a JSON object with the following structure:
            {{
                "command_type": "device_control|automation|system",
                "target": "device_id or system component",
                "action": "specific action to perform",
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }}
            }}
            
            Only output valid JSON, nothing else.
            """
        }
        
        # Try to load from file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            'prompts',
            f'{prompt_type}.txt'
        )
        
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load prompt from file: {e}")
        
        # Return default prompt
        return default_prompts.get(prompt_type, default_prompts['general'])
    
    def _build_prompt(self, command: str) -> str:
        """
        Build a prompt for Claude 3.7.
        
        Args:
            command: The natural language command
        
        Returns:
            The prompt for Claude 3.7
        """
        # Determine the command type
        command_type = self._detect_command_type(command)
        
        # Get the appropriate prompt
        prompt_template = self._prompts.get(command_type, self._prompts['general'])
        
        # Fill in the command
        return prompt_template.format(command=command)
    
    def _detect_command_type(self, command: str) -> str:
        """
        Detect the type of command.
        
        Args:
            command: The natural language command
        
        Returns:
            The detected command type
        """
        command = command.lower()
        
        # Device control keywords
        device_keywords = ['turn on', 'turn off', 'activate', 'deactivate', 'set', 'adjust']
        if any(keyword in command for keyword in device_keywords):
            return 'device_control'
        
        # Automation keywords
        automation_keywords = ['automation', 'trigger', 'when', 'if', 'enable', 'disable']
        if any(keyword in command for keyword in automation_keywords):
            return 'automation'
        
        # System keywords
        system_keywords = ['system', 'restart', 'status', 'config', 'configuration']
        if any(keyword in command for keyword in system_keywords):
            return 'system'
        
        # Default to general
        return 'general'
    
    async def _call_claude_api(self, prompt: str) -> str:
        """
        Call the Claude 3.7 API.
        
        Args:
            prompt: The prompt for Claude 3.7
        
        Returns:
            The response from Claude 3.7
        
        Raises:
            ValueError: If the API call fails
        """
        # Check if we have an API key
        if not self.api_key:
            # Simulation mode
            return self._simulate_claude_response(prompt)
        
        try:
            # Import the required libraries
            import httpx
            
            # Prepare the request
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            data = {
                "model": "claude-3-opus-20240229",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000
            }
            
            # Make the request
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                # Parse the response
                result = response.json()
                
                # Extract the content
                if 'content' in result and len(result['content']) > 0:
                    return result['content'][0]['text']
                else:
                    raise ValueError("Empty response from Claude API")
        
        except ImportError:
            logger.warning("httpx library not installed. Using simulation mode.")
            return self._simulate_claude_response(prompt)
        
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise ValueError(f"Error calling Claude API: {e}")
    
    def _simulate_claude_response(self, prompt: str) -> str:
        """
        Simulate a response from Claude 3.7.
        
        Args:
            prompt: The prompt for Claude 3.7
        
        Returns:
            A simulated response
        """
        # Extract the command from the prompt
        command_match = re.search(r'Command: (.+)', prompt)
        if not command_match:
            return json.dumps({
                "error": "Could not extract command from prompt"
            })
        
        command = command_match.group(1).lower()
        
        # Simulate different command types
        if 'turn on' in command or 'activate' in command:
            # Extract device from command
            device_match = re.search(r'(turn on|activate) (?:the )?(.+)', command)
            device = device_match.group(2) if device_match else "light"
            
            return json.dumps({
                "command_type": "device_control",
                "target": f"{device.replace(' ', '_')}",
                "action": "activate",
                "parameters": {}
            })
        
        elif 'turn off' in command or 'deactivate' in command:
            # Extract device from command
            device_match = re.search(r'(turn off|deactivate) (?:the )?(.+)', command)
            device = device_match.group(2) if device_match else "light"
            
            return json.dumps({
                "command_type": "device_control",
                "target": f"{device.replace(' ', '_')}",
                "action": "deactivate",
                "parameters": {}
            })
        
        elif 'set' in command:
            # Extract device and parameter from command
            set_match = re.search(r'set (?:the )?(.+) to (.+)', command)
            if set_match:
                device = set_match.group(1)
                value = set_match.group(2)
                
                # Try to convert value to number
                try:
                    if value.isdigit():
                        value = int(value)
                    elif '.' in value and all(c.isdigit() or c == '.' for c in value):
                        value = float(value)
                except ValueError:
                    pass
                
                return json.dumps({
                    "command_type": "device_control",
                    "target": f"{device.replace(' ', '_')}",
                    "action": "set_value",
                    "parameters": {
                        "value": value
                    }
                })
        
        elif 'status' in command:
            return json.dumps({
                "command_type": "system",
                "target": "system",
                "action": "status",
                "parameters": {}
            })
        
        # Default response
        return json.dumps({
            "command_type": "device_control",
            "target": "unknown_device",
            "action": "unknown_action",
            "parameters": {}
        })
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the response from Claude 3.7.
        
        Args:
            response: The response from Claude 3.7
        
        Returns:
            The parsed command
        
        Raises:
            ValueError: If the response cannot be parsed
        """
        try:
            # Extract JSON from the response
            json_match = re.search(r'({.+})', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Try to parse the entire response as JSON
            return json.loads(response)
        
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Error parsing Claude response: {e}")
            logger.debug(f"Response: {response}")
            
            return {
                "error": "Failed to parse Claude response",
                "raw_response": response
            }
