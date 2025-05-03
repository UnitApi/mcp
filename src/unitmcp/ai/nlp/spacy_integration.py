#!/usr/bin/env python3
"""
spaCy Integration Module for UnitMCP

This module provides integration with spaCy for natural language processing
in UnitMCP, including tokenization, entity extraction, and more.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union

from ..common.model_interface import NLPInterface

logger = logging.getLogger(__name__)

class SpacyConfig:
    """Configuration for spaCy models."""
    
    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        disable: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize spaCy configuration.
        
        Parameters
        ----------
        model_name : str
            Name of the spaCy model to use
        disable : Optional[List[str]]
            Pipeline components to disable
        **kwargs
            Additional model-specific parameters
        """
        self.model_name = model_name
        self.disable = disable or []
        self.additional_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "model_name": self.model_name,
            "disable": self.disable,
        }
        config_dict.update(self.additional_params)
        return config_dict


class SpacyNLPModel(NLPInterface):
    """
    spaCy NLP model implementation.
    
    This class implements the NLPInterface for spaCy models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[SpacyConfig] = None
    ):
        """
        Initialize a spaCy model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[SpacyConfig]
            spaCy-specific configuration
        """
        super().__init__(model_id, config or SpacyConfig())
        self.nlp = None
        
    async def initialize(self) -> bool:
        """
        Initialize the spaCy model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            import spacy
            
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Load the model
            self.nlp = await loop.run_in_executor(
                None,
                lambda: spacy.load(
                    self.config.model_name,
                    disable=self.config.disable
                )
            )
            
            self.is_initialized = True
            logger.info(f"spaCy model {self.config.model_name} initialized successfully")
            return True
        except ImportError:
            logger.error("Failed to import spaCy. Install it with: pip install spacy")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize spaCy model: {e}")
            return False
    
    async def process(self, input_data: str) -> Any:
        """
        Process input text using the spaCy model.
        
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
        doc = await loop.run_in_executor(
            None,
            lambda: self.nlp(input_data)
        )
        
        # Convert the document to a dictionary
        result = {
            "text": doc.text,
            "tokens": [token.text for token in doc],
            "entities": [
                {
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "label": ent.label_
                }
                for ent in doc.ents
            ],
            "sentences": [sent.text for sent in doc.sents],
        }
        
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
        
        # Process the text
        doc = await loop.run_in_executor(
            None,
            lambda: self.nlp(text)
        )
        
        return [token.text for token in doc]
    
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
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        
        # Process the text
        doc = await loop.run_in_executor(
            None,
            lambda: self.nlp(text)
        )
        
        return [
            {
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "label": ent.label_
            }
            for ent in doc.ents
        ]
    
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
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        
        # Process the text
        doc = await loop.run_in_executor(
            None,
            lambda: self.nlp(text)
        )
        
        # Check if the model has sentiment analysis capability
        if not doc.has_extension("sentiment"):
            logger.warning(
                f"The spaCy model {self.config.model_name} does not have sentiment analysis capability. "
                "Use a model with sentiment analysis or add a sentiment analysis component to the pipeline."
            )
            return {"sentiment": None, "polarity": 0.0, "subjectivity": 0.0}
        
        # Get sentiment
        sentiment = doc._.sentiment
        
        return {
            "sentiment": sentiment,
            "polarity": getattr(doc._, "sentiment_polarity", 0.0),
            "subjectivity": getattr(doc._, "sentiment_subjectivity", 0.0),
        }
    
    async def cleanup(self) -> bool:
        """
        Clean up model resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        self.nlp = None
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = ['SpacyConfig', 'SpacyNLPModel']
