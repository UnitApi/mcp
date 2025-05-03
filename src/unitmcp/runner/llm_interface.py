"""
UnitMCP Runner LLM Interface

This module provides an abstract interface for LLM integration in UnitMCP Runner.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMInterface(ABC):
    """
    Abstract interface for LLM integration.
    
    This class defines the common interface for all LLM implementations
    used in the UnitMCP Runner.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM interface.
        
        Args:
            config: Configuration dictionary for the LLM
        """
        self.config = config
        self.logger = logging.getLogger(f"LLM.{self.__class__.__name__}")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the LLM interface.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
        
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the LLM interface.
        
        Returns:
            True if start was successful, False otherwise
        """
        pass
        
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the LLM interface.
        
        Returns:
            True if stop was successful, False otherwise
        """
        pass
        
    @abstractmethod
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context information for the LLM
            
        Returns:
            Dictionary with the LLM response and additional information
        """
        pass
        
    @abstractmethod
    async def process_hardware_command(self, command: str, available_devices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a hardware command using the LLM.
        
        Args:
            command: Natural language command to process
            available_devices: Dictionary of available hardware devices
            
        Returns:
            Dictionary with the processed command and additional information
        """
        pass
