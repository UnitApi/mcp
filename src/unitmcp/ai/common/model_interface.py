#!/usr/bin/env python3
"""
AI Model Interface Module for UnitMCP

This module defines the base interfaces for all AI models in UnitMCP.
It provides a unified interface for different AI models, allowing
the rest of the system to interact with them in a consistent way.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic

logger = logging.getLogger(__name__)

# Type variable for model-specific configuration
T = TypeVar('T')

class AIModelInterface(ABC, Generic[T]):
    """
    Abstract base class for AI models.
    
    This class defines the interface that all AI model implementations must follow.
    It implements the Strategy Pattern for AI models, allowing different models
    to be used interchangeably.
    """
    
    def __init__(self, model_id: str, config: Optional[T] = None):
        """
        Initialize an AI model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[T]
            Model-specific configuration
        """
        self.model_id = model_id
        self.config = config
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """
        Process input data using the model.
        
        Parameters
        ----------
        input_data : Any
            Input data to process
            
        Returns
        -------
        Any
            Processed output data
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Clean up model resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        pass
    
    async def __aenter__(self):
        """
        Enter the async context manager.
        
        Returns
        -------
        AIModelInterface
            The model instance
        """
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async context manager.
        
        Parameters
        ----------
        exc_type : type
            Exception type
        exc_val : Exception
            Exception value
        exc_tb : traceback
            Exception traceback
        """
        await self.cleanup()


class LLMInterface(AIModelInterface):
    """
    Interface for Language Model (LLM) models.
    
    This class extends the base AI model interface with LLM-specific methods.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass


class NLPInterface(AIModelInterface):
    """
    Interface for Natural Language Processing (NLP) models.
    
    This class extends the base AI model interface with NLP-specific methods.
    """
    
    @abstractmethod
    async def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words or subwords.
        
        Parameters
        ----------
        text : str
            Input text
            
        Returns
        -------
        List[str]
            List of tokens
        """
        pass
    
    @abstractmethod
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Parameters
        ----------
        text : str
            Input text
            
        Returns
        -------
        List[Dict[str, Any]]
            List of extracted entities with their types and positions
        """
        pass
    
    @abstractmethod
    async def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment in text.
        
        Parameters
        ----------
        text : str
            Input text
            
        Returns
        -------
        Dict[str, Any]
            Sentiment analysis results
        """
        pass


class SpeechInterface(AIModelInterface):
    """
    Interface for Speech Processing models.
    
    This class extends the base AI model interface with speech-specific methods.
    """
    
    @abstractmethod
    async def text_to_speech(self, text: str, **kwargs) -> bytes:
        """
        Convert text to speech audio.
        
        Parameters
        ----------
        text : str
            Input text
        **kwargs
            Additional parameters for speech synthesis
            
        Returns
        -------
        bytes
            Audio data
        """
        pass
    
    @abstractmethod
    async def speech_to_text(self, audio_data: bytes, **kwargs) -> str:
        """
        Convert speech audio to text.
        
        Parameters
        ----------
        audio_data : bytes
            Audio data
        **kwargs
            Additional parameters for speech recognition
            
        Returns
        -------
        str
            Recognized text
        """
        pass


class VisionInterface(AIModelInterface):
    """
    Interface for Computer Vision models.
    
    This class extends the base AI model interface with vision-specific methods.
    """
    
    @abstractmethod
    async def detect_objects(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Detect objects in an image.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for object detection
            
        Returns
        -------
        List[Dict[str, Any]]
            List of detected objects with their bounding boxes and confidence scores
        """
        pass
    
    @abstractmethod
    async def image_classification(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Classify an image.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for image classification
            
        Returns
        -------
        List[Dict[str, Any]]
            List of classification results with confidence scores
        """
        pass
    
    @abstractmethod
    async def image_captioning(self, image_data: bytes, **kwargs) -> str:
        """
        Generate a caption for an image.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for image captioning
            
        Returns
        -------
        str
            Generated caption
        """
        pass


# Import AsyncIterator for type hints
from typing import AsyncIterator
