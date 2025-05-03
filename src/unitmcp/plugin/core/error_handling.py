"""
Error handling components for UnitMCP Claude Plugin.

This module provides specialized error handling for natural language
command processing in the UnitMCP Claude Plugin.
"""

import logging
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional, Union, Callable

logger = logging.getLogger(__name__)

class ErrorContext:
    """Contextual information for error handling"""
    def __init__(self, component: str, operation: str, device_id: Optional[str] = None):
        self.component = component
        self.operation = operation
        self.device_id = device_id
        self.timestamp = datetime.now()
        self.trace_id = str(uuid.uuid4())

class NLErrorContext(ErrorContext):
    """Extended error context with natural language information"""
    def __init__(self, component: str, operation: str, nl_command: str, 
                 parsed_command: Optional[Dict[str, Any]] = None):
        super().__init__(component, operation, 
                         device_id=parsed_command.get("device_id") if parsed_command else None)
        self.nl_command = nl_command
        self.parsed_command = parsed_command
        self.ambiguity_score = self._calculate_ambiguity(nl_command)
        
    def _calculate_ambiguity(self, nl_command: str) -> float:
        """Calculate an ambiguity score for the command"""
        # Simple heuristic: count potentially ambiguous terms
        ambiguous_terms = ["it", "this", "that", "there", "here", "the device", "the light"]
        score = 0.0
        for term in ambiguous_terms:
            if term in nl_command.lower():
                score += 0.2  # Increase score for each ambiguous term
        return min(score, 1.0)  # Cap at 1.0

class AmbiguousDeviceError(Exception):
    """Error raised when a device reference is ambiguous"""
    def __init__(self, message: str, possible_devices: List[str]):
        super().__init__(message)
        self.possible_devices = possible_devices

class UnknownActionError(Exception):
    """Error raised when an action is not recognized for a device"""
    def __init__(self, message: str, device_type: str):
        super().__init__(message)
        self.device_type = device_type

class ParameterError(Exception):
    """Error raised when there's an issue with command parameters"""
    def __init__(self, message: str, param_name: str, details: Dict[str, Any]):
        super().__init__(message)
        self.param_name = param_name
        self.details = details

class ErrorHandler:
    """Centralized error handler for UnitMCP"""
    @staticmethod
    def handle(error: Exception, context: ErrorContext, 
               recovery_strategy: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Handle an error with context information.
        
        Args:
            error: The exception that occurred
            context: Context information for the error
            recovery_strategy: Optional function to attempt recovery
            
        Returns:
            A dictionary with error information and status
        """
        logger.error(f"[{context.trace_id}] Error in {context.component}.{context.operation}: {str(error)}")
        
        if recovery_strategy:
            try:
                return recovery_strategy(error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {str(recovery_error)}")
        
        return {"status": "error", "error": str(error), "context": vars(context)}

class NLErrorHandler:
    """
    Specialized error handler for natural language command processing.
    
    This handler extends the core UnitMCP error handling with
    specific features for conversational interfaces.
    """
    
    def __init__(self, core_handler: Optional[ErrorHandler] = None):
        self.core_handler = core_handler or ErrorHandler()
    
    def handle_command_error(self, error: Exception, nl_command: str, 
                            parsed_command: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an error that occurred during command processing.
        
        Args:
            error: The exception that occurred
            nl_command: The original natural language command
            parsed_command: The parsed command (if parsing succeeded)
            
        Returns:
            A user-friendly error message and suggested corrections
        """
        # Create context with natural language information
        context = NLErrorContext(
            component="nl_command_parser",
            operation="parse_command",
            nl_command=nl_command,
            parsed_command=parsed_command
        )
        
        # Log with the core handler
        self.core_handler.handle(error, context)
        
        # Generate a user-friendly response
        if isinstance(error, AmbiguousDeviceError):
            return self._handle_ambiguous_device(nl_command, error.possible_devices)
        elif isinstance(error, UnknownActionError):
            return self._handle_unknown_action(nl_command, error.device_type)
        elif isinstance(error, ParameterError):
            return self._handle_parameter_error(nl_command, error.param_name, error.details)
        else:
            return self._handle_generic_error(nl_command, error)
    
    def _handle_ambiguous_device(self, nl_command: str, possible_devices: List[str]) -> Dict[str, Any]:
        """Handle an ambiguous device reference."""
        device_list = ", ".join(possible_devices)
        return {
            "status": "error",
            "error": f"I'm not sure which device you're referring to. Did you mean one of these: {device_list}?",
            "error_type": "ambiguous_device",
            "possible_devices": possible_devices,
            "nl_command": nl_command,
            "suggestions": [f"Use the {device} to..." for device in possible_devices[:3]]
        }
    
    def _handle_unknown_action(self, nl_command: str, device_type: str) -> Dict[str, Any]:
        """Handle an unknown action for a device type."""
        # Get supported actions for this device type
        supported_actions = self._get_supported_actions(device_type)
        action_list = ", ".join(supported_actions)
        
        return {
            "status": "error",
            "error": f"I'm not sure what action you want to perform with the {device_type}. Supported actions are: {action_list}.",
            "error_type": "unknown_action",
            "device_type": device_type,
            "supported_actions": supported_actions,
            "nl_command": nl_command,
            "suggestions": [f"{action} the {device_type}" for action in supported_actions[:3]]
        }
    
    def _handle_parameter_error(self, nl_command: str, param_name: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a parameter error."""
        return {
            "status": "error",
            "error": f"There's an issue with the {param_name} parameter: {details.get('message', 'Invalid value')}",
            "error_type": "parameter_error",
            "param_name": param_name,
            "details": details,
            "nl_command": nl_command,
            "suggestions": details.get("suggestions", [])
        }
    
    def _handle_generic_error(self, nl_command: str, error: Exception) -> Dict[str, Any]:
        """Handle a generic error."""
        return {
            "status": "error",
            "error": f"I couldn't process your command: {str(error)}",
            "error_type": "generic_error",
            "nl_command": nl_command,
            "suggestions": [
                "Try rephrasing your command",
                "Specify the device type more clearly",
                "Use simpler language"
            ]
        }
    
    def _get_supported_actions(self, device_type: str) -> List[str]:
        """Get supported actions for a device type."""
        # This would be loaded from a configuration in a real implementation
        actions_map = {
            "led": ["on", "off", "blink"],
            "button": ["press", "release"],
            "display": ["show", "clear"],
            "traffic_light": ["set_color", "cycle"]
        }
        return actions_map.get(device_type, [])
