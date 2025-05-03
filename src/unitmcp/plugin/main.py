"""
Main entry point for the UnitMCP Claude Plugin.

This module provides the main plugin class that handles
initialization, command processing, and response generation.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional, Union

from unitmcp.plugin.core.hardware_client import PluginHardwareClient
from unitmcp.plugin.core.dsl_integration import DslIntegration
from unitmcp.plugin.state.conversation_state import ConversationStateManager

logger = logging.getLogger(__name__)

class ClaudeUnitMCPPlugin:
    """
    Main entry point for the Claude UnitMCP plugin.
    
    This class handles plugin registration, initialization,
    and command processing.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the plugin.
        
        Args:
            config_path: Path to the plugin configuration file
        """
        self.config = self._load_config(config_path)
        
        # Set up simulation mode
        simulation_mode = self.config.get("simulation_mode", True)
        if "SIMULATION" in os.environ:
            simulation_mode = os.environ["SIMULATION"] == "1"
        
        # Set up logging
        verbose = self.config.get("verbose", False)
        if "VERBOSE" in os.environ:
            verbose = os.environ["VERBOSE"] == "1"
        
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=log_level)
        
        # Initialize components
        self.hardware_client = PluginHardwareClient(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 8888),
            simulation_mode=simulation_mode
        )
        
        self.dsl_integration = DslIntegration(simulation_mode=simulation_mode)
        self.conversation_state = ConversationStateManager()
        
        logger.info(f"Plugin initialized with simulation_mode={simulation_mode}")
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load the plugin configuration."""
        default_config = {
            "host": "localhost",
            "port": 8888,
            "simulation_mode": True,
            "verbose": False
        }
        
        if not config_path:
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return {**default_config, **config}
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return default_config
        
    async def initialize(self):
        """Initialize the plugin and connect to hardware."""
        logger.info("Initializing plugin")
        
        # Connect to hardware
        await self.hardware_client.connect()
        
        logger.info("Plugin initialized")
        
    async def process_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query from Claude.
        
        Args:
            query: Dictionary containing the query information
                - text: The text of the query
                - user_id: Identifier for the user
                - conversation_id: Identifier for the conversation
                
        Returns:
            A dictionary containing the response information
        """
        # Update conversation state
        self.conversation_state.update(query)
        
        # Extract hardware-related intents
        intents = await self._extract_hardware_intents(query["text"])
        
        if not intents:
            return {"has_hardware_intent": False}
            
        # Process each hardware intent
        results = []
        for intent in intents:
            result = await self.hardware_client.execute_nl_command(intent)
            results.append(result)
            
            # Update conversation state with device and action references
            if result.get("status") == "success" and "parsed_command" in result:
                parsed_command = result["parsed_command"]
                if "device_id" in parsed_command:
                    self.conversation_state.update_device_reference(
                        query.get("conversation_id", "default"),
                        parsed_command["device_id"]
                    )
                if "action" in parsed_command:
                    self.conversation_state.update_action_reference(
                        query.get("conversation_id", "default"),
                        parsed_command["action"]
                    )
            
        # Generate a natural language response
        response = self._generate_response(results, query)
        
        return {
            "has_hardware_intent": True,
            "results": results,
            "response": response
        }
    
    async def _extract_hardware_intents(self, text: str) -> List[str]:
        """
        Extract hardware-related intents from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            A list of hardware-related intent strings
        """
        # Simple heuristic: look for device-related keywords
        device_keywords = ["led", "light", "button", "switch", "display", "screen", "traffic light"]
        action_keywords = ["turn on", "turn off", "press", "show", "set", "blink"]
        
        # Check if the text contains device and action keywords
        has_device = any(keyword in text.lower() for keyword in device_keywords)
        has_action = any(keyword in text.lower() for keyword in action_keywords)
        
        if has_device and has_action:
            return [text]
        
        return []
    
    def _generate_response(self, results: List[Dict[str, Any]], query: Dict[str, Any]) -> str:
        """
        Generate a natural language response based on command results.
        
        Args:
            results: List of command execution results
            query: The original query information
            
        Returns:
            A natural language response string
        """
        # For a single result
        if len(results) == 1:
            result = results[0]
            
            if result.get("status") == "success":
                parsed_command = result.get("parsed_command", {})
                device_type = parsed_command.get("device_type", "device")
                device_id = parsed_command.get("device_id", "unknown")
                action = parsed_command.get("action", "action")
                
                return f"I've {action}ed the {device_type} ({device_id}) for you."
            else:
                return f"I couldn't complete that action: {result.get('error', 'Unknown error')}"
        
        # For multiple results
        success_count = sum(1 for r in results if r.get("status") == "success")
        
        if success_count == len(results):
            return f"I've completed all {len(results)} actions successfully."
        elif success_count > 0:
            return f"I've completed {success_count} out of {len(results)} actions. Some actions couldn't be completed."
        else:
            return "I couldn't complete any of the requested actions."
