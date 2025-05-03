#!/usr/bin/env python3
"""
OpenAI LLM Integration for UnitMCP

This module provides integration with OpenAI language models for UnitMCP.
It implements the LLMInterface for OpenAI models.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, AsyncIterator, Union

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    raise ImportError(
        "OpenAI package not found. Install it with: pip install openai"
    )

from ..common.model_interface import LLMInterface

logger = logging.getLogger(__name__)

class OpenAIConfig:
    """Configuration for OpenAI models."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Initialize OpenAI configuration.
        
        Parameters
        ----------
        api_key : Optional[str]
            OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        model : str
            Model name to use
        temperature : float
            Sampling temperature (0.0 to 1.0)
        max_tokens : int
            Maximum number of tokens to generate
        **kwargs
            Additional model parameters
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set the OPENAI_API_KEY environment variable "
                "or pass it explicitly."
            )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.additional_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        config_dict.update(self.additional_params)
        return config_dict


class OpenAIModel(LLMInterface):
    """
    OpenAI language model implementation.
    
    This class implements the LLMInterface for OpenAI models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[OpenAIConfig] = None
    ):
        """
        Initialize an OpenAI model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[OpenAIConfig]
            OpenAI-specific configuration
        """
        super().__init__(model_id, config or OpenAIConfig())
        self.client = None
        
    async def initialize(self) -> bool:
        """
        Initialize the OpenAI model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            self.client = AsyncOpenAI(api_key=self.config.api_key)
            self.is_initialized = True
            logger.info(f"OpenAI model {self.config.model} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI model: {e}")
            return False
    
    async def process(self, input_data: Union[str, List[Dict[str, str]]]) -> Any:
        """
        Process input data using the OpenAI model.
        
        Parameters
        ----------
        input_data : Union[str, List[Dict[str, str]]]
            Input data to process (prompt or chat messages)
            
        Returns
        -------
        Any
            Processed output data
        """
        if isinstance(input_data, str):
            return await self.generate_text(input_data)
        elif isinstance(input_data, list):
            return await self.chat(input_data)
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Parameters
        ----------
        prompt : str
            Input prompt
        **kwargs
            Additional parameters for text generation
            
        Returns
        -------
        str
            Generated text
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Convert prompt to messages format for OpenAI
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, **kwargs)
        
        return response.choices[0].message.content
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Generate a chat response based on a conversation history.
        
        Parameters
        ----------
        messages : List[Dict[str, str]]
            List of messages in the conversation history
        **kwargs
            Additional parameters for chat generation
            
        Returns
        -------
        Dict[str, Any]
            Chat response
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Merge configuration with any overrides
        params = self.config.to_dict()
        params.update(kwargs)
        
        # Extract model from params to pass separately
        model = params.pop("model")
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **params
            )
            return response
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream a chat response based on a conversation history.
        
        Parameters
        ----------
        messages : List[Dict[str, str]]
            List of messages in the conversation history
        **kwargs
            Additional parameters for chat generation
            
        Returns
        -------
        AsyncIterator[Dict[str, Any]]
            Stream of chat response chunks
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Merge configuration with any overrides
        params = self.config.to_dict()
        params.update(kwargs)
        
        # Extract model from params to pass separately
        model = params.pop("model")
        
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **params
            )
            
            async for chunk in stream:
                yield chunk
        except Exception as e:
            logger.error(f"Error in stream_chat: {e}")
            raise
    
    async def cleanup(self) -> bool:
        """
        Clean up model resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        self.client = None
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = ['OpenAIConfig', 'OpenAIModel']
