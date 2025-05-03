"""
UnitMCP Runner Ollama Interface

This module provides integration with Ollama LLM for UnitMCP Runner.
"""

import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List

from unitmcp.runner.llm_interface import LLMInterface

logger = logging.getLogger(__name__)


class OllamaInterface(LLMInterface):
    """
    Interface for Ollama LLM in UnitMCP Runner.
    
    This class implements the LLMInterface for the Ollama LLM.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Ollama interface.
        
        Args:
            config: Configuration dictionary for Ollama
        """
        super().__init__(config)
        self.model = config.get('model', 'llama3')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 11434)
        self.base_url = f"http://{self.host}:{self.port}"
        self.session = None
        self.system_prompt = config.get('system_prompt', """
            You are an AI assistant that helps control hardware devices through the UnitMCP system.
            You can control devices like LEDs, buttons, sensors, and more.
            When given a natural language command, convert it to a structured format that UnitMCP can understand.
            Always respond with valid JSON that includes the device, action, and any parameters needed.
        """)
        
    async def initialize(self) -> bool:
        """
        Initialize the Ollama interface.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing Ollama interface with model {self.model}")
            self.session = aiohttp.ClientSession()
            
            # Check if Ollama is available
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status != 200:
                    self.logger.error(f"Failed to connect to Ollama: {response.status}")
                    return False
                    
                data = await response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                if self.model not in models:
                    self.logger.warning(f"Model {self.model} not found in Ollama. Available models: {models}")
                    self.logger.warning(f"Will attempt to pull the model when needed.")
                
            self.logger.info("Ollama interface initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing Ollama interface: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
            
    async def start(self) -> bool:
        """
        Start the Ollama interface.
        
        Returns:
            True if start was successful, False otherwise
        """
        if not self.session:
            return await self.initialize()
        return True
            
    async def stop(self) -> bool:
        """
        Stop the Ollama interface.
        
        Returns:
            True if stop was successful, False otherwise
        """
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Ollama interface: {e}")
            return False
            
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a response from Ollama.
        
        Args:
            prompt: The prompt to send to Ollama
            context: Optional context information for Ollama
            
        Returns:
            Dictionary with the Ollama response and additional information
        """
        if not self.session:
            if not await self.initialize():
                return {"success": False, "error": "Failed to initialize Ollama interface"}
                
        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": self.system_prompt,
                "stream": False
            }
            
            # Add context if provided
            if context:
                payload["context"] = context.get("context", [])
                
            # Send the request to Ollama
            async with self.session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Error from Ollama: {error_text}")
                    return {"success": False, "error": f"Ollama error: {error_text}"}
                    
                data = await response.json()
                
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "context": data.get("context", []),
                    "model": self.model
                }
                
        except Exception as e:
            self.logger.error(f"Error generating response from Ollama: {e}")
            return {"success": False, "error": str(e)}
            
    async def process_hardware_command(self, command: str, available_devices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a hardware command using Ollama.
        
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
        
        # Generate response from Ollama
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
                self.logger.error(f"No valid JSON found in Ollama response: {response_text}")
                return {"success": False, "error": "No valid JSON found in Ollama response"}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON from Ollama response: {e}")
            return {"success": False, "error": f"Error parsing JSON: {str(e)}", "raw_response": response.get("response", "")}
        except Exception as e:
            self.logger.error(f"Error processing hardware command: {e}")
            return {"success": False, "error": str(e)}
