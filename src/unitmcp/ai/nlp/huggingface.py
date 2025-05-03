#!/usr/bin/env python3
"""
Hugging Face Integration Module for UnitMCP

This module provides integration with Hugging Face Transformers for natural language
processing in UnitMCP, including tokenization, entity extraction, and more.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union

from ..common.model_interface import NLPInterface

logger = logging.getLogger(__name__)

class HuggingFaceConfig:
    """Configuration for Hugging Face models."""
    
    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        task: str = "text-classification",
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Hugging Face configuration.
        
        Parameters
        ----------
        model_name : str
            Name of the Hugging Face model to use
        task : str
            Task to perform (e.g., 'text-classification', 'token-classification', 'question-answering')
        device : Optional[str]
            Device to use ('cpu', 'cuda', etc.)
        **kwargs
            Additional model-specific parameters
        """
        self.model_name = model_name
        self.task = task
        self.device = device
        self.additional_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "model_name": self.model_name,
            "task": self.task,
            "device": self.device,
        }
        config_dict.update(self.additional_params)
        return config_dict


class HuggingFaceNLPModel(NLPInterface):
    """
    Hugging Face NLP model implementation.
    
    This class implements the NLPInterface for Hugging Face Transformers models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[HuggingFaceConfig] = None
    ):
        """
        Initialize a Hugging Face model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[HuggingFaceConfig]
            Hugging Face-specific configuration
        """
        super().__init__(model_id, config or HuggingFaceConfig())
        self.pipeline = None
        self.tokenizer = None
        
    async def initialize(self) -> bool:
        """
        Initialize the Hugging Face model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            from transformers import pipeline, AutoTokenizer
            
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Load the pipeline
            self.pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    task=self.config.task,
                    model=self.config.model_name,
                    device=self.config.device
                )
            )
            
            # Load the tokenizer
            self.tokenizer = await loop.run_in_executor(
                None,
                lambda: AutoTokenizer.from_pretrained(self.config.model_name)
            )
            
            self.is_initialized = True
            logger.info(f"Hugging Face model {self.config.model_name} initialized successfully")
            return True
        except ImportError:
            logger.error("Failed to import transformers. Install it with: pip install transformers")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face model: {e}")
            return False
    
    async def process(self, input_data: str) -> Any:
        """
        Process input text using the Hugging Face model.
        
        Parameters
        ----------
        input_data : str
            Input text to process
            
        Returns
        -------
        Any
            Processed output data
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        
        # Process the text
        result = await loop.run_in_executor(
            None,
            lambda: self.pipeline(input_data)
        )
        
        return result
    
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
        if not self.is_initialized:
            await self.initialize()
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        
        # Tokenize the text
        tokens = await loop.run_in_executor(
            None,
            lambda: self.tokenizer.tokenize(text)
        )
        
        return tokens
    
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
        if not self.is_initialized:
            await self.initialize()
        
        # Check if the model is suitable for entity extraction
        if self.config.task != "token-classification" and self.config.task != "ner":
            # Create a new pipeline for NER
            from transformers import pipeline
            
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Create a temporary NER pipeline
            ner_pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    task="ner",
                    device=self.config.device
                )
            )
            
            # Process the text
            entities = await loop.run_in_executor(
                None,
                lambda: ner_pipeline(text)
            )
        else:
            # Use the existing pipeline
            loop = asyncio.get_event_loop()
            
            # Process the text
            entities = await loop.run_in_executor(
                None,
                lambda: self.pipeline(text)
            )
        
        # Format the entities
        formatted_entities = []
        for entity in entities:
            formatted_entities.append({
                "text": entity["word"],
                "start": entity.get("start"),
                "end": entity.get("end"),
                "label": entity["entity"],
                "score": entity["score"],
            })
        
        return formatted_entities
    
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
        if not self.is_initialized:
            await self.initialize()
        
        # Check if the model is suitable for sentiment analysis
        if self.config.task != "text-classification" and self.config.task != "sentiment-analysis":
            # Create a new pipeline for sentiment analysis
            from transformers import pipeline
            
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Create a temporary sentiment analysis pipeline
            sentiment_pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    task="sentiment-analysis",
                    device=self.config.device
                )
            )
            
            # Process the text
            sentiment = await loop.run_in_executor(
                None,
                lambda: sentiment_pipeline(text)
            )
        else:
            # Use the existing pipeline
            loop = asyncio.get_event_loop()
            
            # Process the text
            sentiment = await loop.run_in_executor(
                None,
                lambda: self.pipeline(text)
            )
        
        # Format the sentiment
        if isinstance(sentiment, list):
            sentiment = sentiment[0]
        
        return {
            "label": sentiment["label"],
            "score": sentiment["score"],
        }
    
    async def cleanup(self) -> bool:
        """
        Clean up model resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        self.pipeline = None
        self.tokenizer = None
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = ['HuggingFaceConfig', 'HuggingFaceNLPModel']
