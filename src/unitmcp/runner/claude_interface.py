"""
UnitMCP Runner Claude Interface

This module provides integration with Anthropic Claude LLM for UnitMCP Runner.
"""

import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List

from unitmcp.runner.llm_interface import LLMInterface

logger = logging.getLogger(__name__)


class ClaudeInterface(LLMInterface):
    """
    Interface for Anthropic Claude LLM in UnitMCP Runner.
    
    This class implements the LLMInterface for the Claude LLM.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Claude interface.
        
        Args:
            config: Configuration dictionary for Claude
        """
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'claude-3-opus-20240229')
        self.base_url = config.get('base_url', 'https://api.anthropic.com/v1/messages')
        self.session = None
        self.system_prompt = config.get('system_prompt', """
            You are an AI assistant that helps control hardware devices through the UnitMCP system.
            You can control devices like LEDs, buttons, sensors, and more.
            When given a natural language command, convert it to a structured format that UnitMCP can understand.
            Always respond with valid JSON that includes the device, action, and any parameters needed.
        """)
        
    async def initialize(self) -> bool:
        """
        Initialize the Claude interface.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            if not self.api_key:
                self.logger.error("API key not provided for Claude interface")
                return False
                
            self.logger.info(f"Initializing Claude interface with model {self.model}")
            self.session = aiohttp.ClientSession()
            
            # Test the API key with a simple request
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 10,
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "system": "Respond with 'OK' to test the API connection."
            }
            
            async with self.session.post(self.base_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Failed to connect to Claude API: {error_text}")
                    return False
                    
                self.logger.info("Claude API connection successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Error initializing Claude interface: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
            
    async def start(self) -> bool:
        """
        Start the Claude interface.
        
        Returns:
            True if start was successful, False otherwise
        """
        if not self.session:
            return await self.initialize()
        return True
            
    async def stop(self) -> bool:
        """
        Stop the Claude interface.
        
        Returns:
            True if stop was successful, False otherwise
        """
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Claude interface: {e}")
            return False
            
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a response from Claude.
        
        Args:
            prompt: The prompt to send to Claude
            context: Optional context information for Claude
            
        Returns:
            Dictionary with the Claude response and additional information
        """
        if not self.session:
            if not await self.initialize():
                return {"success": False, "error": "Failed to initialize Claude interface"}
                
        try:
            # Prepare the request headers
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # Prepare the messages
            messages = [{"role": "user", "content": prompt}]
            
            # Add context messages if provided
            if context and "messages" in context:
                messages = context["messages"] + messages
                
            # Prepare the request payload
            payload = {
                "model": self.model,
                "max_tokens": 1024,
                "messages": messages,
                "system": self.system_prompt
            }
            
            # Send the request to Claude
            async with self.session.post(self.base_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Error from Claude API: {error_text}")
                    return {"success": False, "error": f"Claude API error: {error_text}"}
                    
                data = await response.json()
                
                # Extract the response content
                response_content = ""
                if "content" in data and len(data["content"]) > 0:
                    response_content = data["content"][0].get("text", "")
                
                return {
                    "success": True,
                    "response": response_content,
                    "model": self.model,
                    "usage": data.get("usage", {}),
                    "id": data.get("id", "")
                }
                
        except Exception as e:
            self.logger.error(f"Error generating response from Claude: {e}")
            return {"success": False, "error": str(e)}
            
    async def process_hardware_command(self, command: str, available_devices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a hardware command using Claude.
        
        Args:
            command: Natural language command to process
            available_devices: Dictionary of available hardware devices
            
        Returns:
            Dictionary with the processed command and additional information
        """
        # Create a prompt that includes information about available devices
        devices_info = "\n".join([f"- {device_id}: {device['type']} ({device.get('name', 'Unnamed')})" 
                                 for device_id, device in available_devices.items()])
        
        prompt = f"""
        Available devices:
        {devices_info}
        
        User command: {command}
        
        Convert this command to a JSON format that UnitMCP can understand.
        The JSON should include:
        - device: The ID of the device to control
        - action: The action to perform (e.g., turn_on, turn_off, read, etc.)
        - parameters: Any additional parameters needed for the action
        
        Respond ONLY with the JSON, no other text.
        """
        
        # Generate response from Claude
        response = await self.generate_response(prompt)
        
        if not response.get("success", False):
            return response
            
        # Try to parse the response as JSON
        try:
            # Extract JSON from the response text
            response_text = response.get("response", "")
            
            # Look for JSON block in the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}")
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end+1]
                command_data = json.loads(json_text)
                
                return {
                    "success": True,
                    "command": command,
                    "parsed_command": command_data,
                    "raw_response": response_text
                }
            else:
                # Try to find a JSON array
                json_start = response_text.find("[")
                json_end = response_text.rfind("]")
                
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end+1]
                    command_data = json.loads(json_text)
                    
                    return {
                        "success": True,
                        "command": command,
                        "parsed_command": command_data,
                        "raw_response": response_text
                    }
                else:
                    self.logger.error(f"No valid JSON found in Claude response: {response_text}")
                    return {"success": False, "error": "No valid JSON found in Claude response"}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON from Claude response: {e}")
            return {"success": False, "error": f"Error parsing JSON: {str(e)}", "raw_response": response.get("response", "")}
        except Exception as e:
            self.logger.error(f"Error processing hardware command: {e}")
            return {"success": False, "error": str(e)}
