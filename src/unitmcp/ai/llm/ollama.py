#!/usr/bin/env python3
"""
Ollama LLM Integration for UnitMCP

This module provides integration with Ollama language models for UnitMCP.
It implements the LLMInterface for Ollama models.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncIterator, Union

try:
    import ollama
except ImportError:
    raise ImportError(
        "Ollama package not found. Install it with: pip install ollama"
    )

from ..common.model_interface import LLMInterface

logger = logging.getLogger(__name__)

class OllamaConfig:
    """Configuration for Ollama models."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 11434,
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Initialize Ollama configuration.
        
        Parameters
        ----------
        host : str
            Ollama server host
        port : int
            Ollama server port
        model : str
            Model name to use
        temperature : float
            Sampling temperature (0.0 to 1.0)
        max_tokens : int
            Maximum number of tokens to generate
        **kwargs
            Additional model parameters
        """
        self.host = host
        self.port = port
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.additional_params = kwargs
        
    @property
    def base_url(self) -> str:
        """Get the base URL for the Ollama API."""
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        config_dict.update(self.additional_params)
        return config_dict


class OllamaModel(LLMInterface):
    """
    Ollama language model implementation.
    
    This class implements the LLMInterface for Ollama models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[OllamaConfig] = None
    ):
        """
        Initialize an Ollama model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[OllamaConfig]
            Ollama-specific configuration
        """
        super().__init__(model_id, config or OllamaConfig())
        self.client = None
        
    async def initialize(self) -> bool:
        """
        Initialize the Ollama model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Configure the Ollama client
            ollama.set_host(self.config.base_url)
            
            # Check if the model exists
            models = ollama.list()
            model_exists = any(model["name"] == self.config.model for model in models.get("models", []))
            
            if not model_exists:
                logger.warning(f"Model {self.config.model} not found. Attempting to pull it.")
                ollama.pull(self.config.model)
            
            self.is_initialized = True
            logger.info(f"Ollama model {self.config.model} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Ollama model: {e}")
            return False
    
    async def process(self, input_data: Union[str, List[Dict[str, str]]]) -> Any:
        """
        Process input data using the Ollama model.
        
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
        
        # Merge configuration with any overrides
        params = self.config.to_dict()
        params.update(kwargs)
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama.generate(
                model=self.config.model,
                prompt=prompt,
                options=params
            )
        )
        
        return response.get("response", "")
    
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
        
        # Convert messages to Ollama format if needed
        ollama_messages = messages
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama.chat(
                model=self.config.model,
                messages=ollama_messages,
                options=params
            )
        )
        
        return response
    
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
        
        # Convert messages to Ollama format if needed
        ollama_messages = messages
        
        # Create a queue to communicate between threads
        queue = asyncio.Queue()
        
        async def stream_processor():
            try:
                # Run in a separate thread to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                
                def stream_callback():
                    stream = ollama.chat(
                        model=self.config.model,
                        messages=ollama_messages,
                        options=params,
                        stream=True
                    )
                    for chunk in stream:
                        loop.call_soon_threadsafe(lambda c=chunk: asyncio.create_task(queue.put(c)))
                    loop.call_soon_threadsafe(lambda: asyncio.create_task(queue.put(None)))
                
                # Start the stream in a separate thread
                await loop.run_in_executor(None, stream_callback)
                
                # Process the stream
                while True:
                    chunk = await queue.get()
                    if chunk is None:
                        break
                    yield chunk
            except Exception as e:
                logger.error(f"Error in stream_chat: {e}")
                raise
        
        async for chunk in stream_processor():
            yield chunk
    
    async def cleanup(self) -> bool:
        """
        Clean up model resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = ['OllamaConfig', 'OllamaModel']
