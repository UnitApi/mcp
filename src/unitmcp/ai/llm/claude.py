#!/usr/bin/env python3
"""
Claude LLM Integration for UnitMCP

This module provides integration with Anthropic's Claude language models for UnitMCP.
It implements the LLMInterface for Claude models.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, AsyncIterator, Union

try:
    import anthropic
except ImportError:
    raise ImportError(
        "Anthropic package not found. Install it with: pip install anthropic"
    )

from ..common.model_interface import LLMInterface

logger = logging.getLogger(__name__)

class ClaudeConfig:
    """Configuration for Claude models."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Initialize Claude configuration.
        
        Parameters
        ----------
        api_key : Optional[str]
            Anthropic API key (defaults to ANTHROPIC_API_KEY environment variable)
        model : str
            Model name to use
        temperature : float
            Sampling temperature (0.0 to 1.0)
        max_tokens : int
            Maximum number of tokens to generate
        **kwargs
            Additional model parameters
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not provided. Set the ANTHROPIC_API_KEY environment variable "
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


class ClaudeModel(LLMInterface):
    """
    Claude language model implementation.
    
    This class implements the LLMInterface for Claude models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[ClaudeConfig] = None
    ):
        """
        Initialize a Claude model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[ClaudeConfig]
            Claude-specific configuration
        """
        super().__init__(model_id, config or ClaudeConfig())
        self.client = None
        
    async def initialize(self) -> bool:
        """
        Initialize the Claude model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            self.client = anthropic.Anthropic(api_key=self.config.api_key)
            self.is_initialized = True
            logger.info(f"Claude model {self.config.model} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Claude model: {e}")
            return False
    
    async def process(self, input_data: Union[str, List[Dict[str, str]]]) -> Any:
        """
        Process input data using the Claude model.
        
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
        
        # Convert prompt to messages format for Claude
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, **kwargs)
        
        return response.get("content", [{"text": ""}])[0]["text"]
    
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
        
        # Convert messages to Claude format if needed
        claude_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Map roles to Claude's expected format
            if role == "system":
                # Handle system messages for Claude
                if not claude_messages:
                    # If this is the first message, add it as a system prompt
                    params["system"] = content
                else:
                    # Otherwise, add it as a user message
                    claude_messages.append({"role": "user", "content": f"[System] {content}"})
            else:
                claude_messages.append({"role": role, "content": content})
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                messages=claude_messages,
                model=params.pop("model"),
                max_tokens=params.pop("max_tokens"),
                temperature=params.pop("temperature", 0.7),
                **params
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
        
        # Convert messages to Claude format if needed
        claude_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Map roles to Claude's expected format
            if role == "system":
                # Handle system messages for Claude
                if not claude_messages:
                    # If this is the first message, add it as a system prompt
                    params["system"] = content
                else:
                    # Otherwise, add it as a user message
                    claude_messages.append({"role": "user", "content": f"[System] {content}"})
            else:
                claude_messages.append({"role": role, "content": content})
        
        # Create a queue to communicate between threads
        queue = asyncio.Queue()
        
        async def stream_processor():
            try:
                # Run in a separate thread to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                
                def stream_callback():
                    with self.client.messages.stream(
                        messages=claude_messages,
                        model=params.pop("model"),
                        max_tokens=params.pop("max_tokens"),
                        temperature=params.pop("temperature", 0.7),
                        stream=True,
                        **params
                    ) as stream:
                        for chunk in stream:
                            if chunk.type == "content_block_delta":
                                loop.call_soon_threadsafe(
                                    lambda c=chunk: asyncio.create_task(queue.put(c))
                                )
                        loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(queue.put(None))
                        )
                
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
        self.client = None
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = ['ClaudeConfig', 'ClaudeModel']
