"""
Natural Language Command Parser for UnitMCP Claude Plugin.

This module provides functionality to parse natural language commands
into structured hardware commands for UnitMCP.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class NLCommandParser:
    """
    Parses natural language commands into structured hardware commands.
    
    This parser extracts device types, actions, and parameters from
    natural language input and maps them to UnitMCP commands.
    """
    
    def __init__(self, language_model=None):
        self.language_model = language_model
        self.device_patterns = self._load_device_patterns()
        self.action_patterns = self._load_action_patterns()
    
    async def parse_command(self, natural_language_input: str) -> dict:
        """
        Parse a natural language command into a structured command format.
        
        Args:
            natural_language_input: The natural language command from the user
            
        Returns:
            A dictionary containing the parsed command with device type,
            action, and parameters
        """
        logger.debug(f"Parsing command: {natural_language_input}")
        
        # For complex queries, defer to the language model
        if self.language_model and self._is_complex_query(natural_language_input):
            return await self._parse_with_language_model(natural_language_input)
            
        # For simpler queries, use pattern matching
        return self._parse_with_patterns(natural_language_input)
    
    def _load_device_patterns(self) -> Dict[str, List[str]]:
        """Load device recognition patterns."""
        # In a real implementation, these would be loaded from a configuration file
        return {
            "led": [r"led", r"light", r"lamp"],
            "button": [r"button", r"switch", r"push\s*button"],
            "display": [r"display", r"screen", r"lcd", r"monitor"],
            "traffic_light": [r"traffic\s*light", r"signal"]
        }
    
    def _load_action_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Load action recognition patterns for each device type."""
        # In a real implementation, these would be loaded from a configuration file
        return {
            "led": {
                "on": [r"turn\s*on", r"activate", r"light\s*up"],
                "off": [r"turn\s*off", r"deactivate", r"shut\s*off"],
                "blink": [r"blink", r"flash", r"strobe"]
            },
            "button": {
                "press": [r"press", r"push", r"click"],
                "release": [r"release", r"let\s*go"]
            },
            "display": {
                "show": [r"show", r"display", r"write"],
                "clear": [r"clear", r"erase", r"reset"]
            },
            "traffic_light": {
                "set_color": [r"set\s*to", r"change\s*to", r"make\s*it"],
                "cycle": [r"cycle", r"sequence", r"run\s*through"]
            }
        }
    
    def _is_complex_query(self, query: str) -> bool:
        """Determine if a query is complex and requires the language model."""
        # Simple heuristic: if the query is long or contains multiple clauses
        if len(query.split()) > 10 or "," in query or "and" in query.lower():
            return True
        return False
    
    async def _parse_with_language_model(self, query: str) -> dict:
        """Parse a complex query using the language model."""
        if not self.language_model:
            logger.warning("Language model requested but not available")
            return self._parse_with_patterns(query)
        
        try:
            # This would call the language model API
            # For now, we'll return a placeholder
            logger.info("Using language model to parse complex query")
            return {
                "device_type": "led",
                "device_id": "led1",
                "action": "on",
                "parameters": {}
            }
        except Exception as e:
            logger.error(f"Error using language model: {str(e)}")
            return self._parse_with_patterns(query)
    
    def _parse_with_patterns(self, query: str) -> dict:
        """Parse a query using pattern matching."""
        query = query.lower()
        
        # Extract device type
        device_type = self._extract_device_type(query)
        if not device_type:
            logger.warning(f"No device type found in query: {query}")
            return {"status": "error", "error": "No device type recognized"}
        
        # Extract action
        action = self._extract_action(query, device_type)
        if not action:
            logger.warning(f"No action found for device type {device_type} in query: {query}")
            return {"status": "error", "error": f"No action recognized for {device_type}"}
        
        # Extract parameters
        parameters = self._extract_parameters(query, device_type, action)
        
        # Extract device ID (in a real implementation, this would be more sophisticated)
        device_id = f"{device_type}1"
        
        return {
            "device_type": device_type,
            "device_id": device_id,
            "action": action,
            "parameters": parameters
        }
    
    def _extract_device_type(self, query: str) -> Optional[str]:
        """Extract the device type from the query."""
        for device_type, patterns in self.device_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return device_type
        return None
    
    def _extract_action(self, query: str, device_type: str) -> Optional[str]:
        """Extract the action for a device type from the query."""
        if device_type not in self.action_patterns:
            return None
        
        for action, patterns in self.action_patterns[device_type].items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return action
        return None
    
    def _extract_parameters(self, query: str, device_type: str, action: str) -> dict:
        """Extract parameters for the action from the query."""
        parameters = {}
        
        # Device-specific parameter extraction
        if device_type == "led" and action == "blink":
            # Extract frequency parameter for LED blinking
            freq_match = re.search(r"(\d+)\s*(hz|times|per\s*second)", query, re.IGNORECASE)
            if freq_match:
                parameters["frequency"] = int(freq_match.group(1))
        
        elif device_type == "traffic_light" and action == "set_color":
            # Extract color parameter for traffic light
            if "red" in query:
                parameters["color"] = "red"
            elif "yellow" in query or "amber" in query:
                parameters["color"] = "yellow"
            elif "green" in query:
                parameters["color"] = "green"
        
        elif device_type == "display" and action == "show":
            # Extract text parameter for display
            text_match = re.search(r"[\"'](.+?)[\"']", query)
            if text_match:
                parameters["text"] = text_match.group(1)
            else:
                # Try to extract text after "show" or "display"
                text_match = re.search(r"(show|display)\s+(.+)$", query, re.IGNORECASE)
                if text_match:
                    parameters["text"] = text_match.group(2).strip()
        
        return parameters
