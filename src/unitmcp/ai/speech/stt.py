#!/usr/bin/env python3
"""
Speech-to-Text Module for UnitMCP

This module provides speech-to-text capabilities for UnitMCP,
supporting various STT engines.
"""

import asyncio
import logging
import os
import tempfile
from abc import abstractmethod
from typing import Dict, Any, Optional, Union, BinaryIO

from ..common.model_interface import SpeechInterface

logger = logging.getLogger(__name__)

class STTConfig:
    """Base configuration for STT engines."""
    
    def __init__(
        self,
        language: str = "en-US",
        sample_rate: int = 16000,
        **kwargs
    ):
        """
        Initialize STT configuration.
        
        Parameters
        ----------
        language : str
            Language code (e.g., 'en-US', 'fr-FR')
        sample_rate : int
            Audio sample rate in Hz
        **kwargs
            Additional engine-specific parameters
        """
        self.language = language
        self.sample_rate = sample_rate
        self.additional_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "language": self.language,
            "sample_rate": self.sample_rate,
        }
        config_dict.update(self.additional_params)
        return config_dict


class STTModel(SpeechInterface):
    """
    Base class for STT models.
    
    This class implements the SpeechInterface for STT models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[STTConfig] = None
    ):
        """
        Initialize an STT model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[STTConfig]
            STT-specific configuration
        """
        super().__init__(model_id, config or STTConfig())
        
    async def process(self, input_data: bytes) -> str:
        """
        Process input audio using the STT model.
        
        Parameters
        ----------
        input_data : bytes
            Input audio data to convert to text
            
        Returns
        -------
        str
            Recognized text
        """
        return await self.speech_to_text(input_data)
    
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
    
    async def text_to_speech(self, text: str, **kwargs) -> bytes:
        """
        Not implemented for STT models.
        
        Raises
        ------
        NotImplementedError
            Always raised for STT models
        """
        raise NotImplementedError("Text-to-speech is not supported by STT models")


class WhisperConfig(STTConfig):
    """Configuration for OpenAI Whisper STT engine."""
    
    def __init__(
        self,
        model_size: str = "base",
        language: str = "en",
        task: str = "transcribe",
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Whisper configuration.
        
        Parameters
        ----------
        model_size : str
            Model size ('tiny', 'base', 'small', 'medium', 'large')
        language : str
            Language code (e.g., 'en', 'fr')
        task : str
            Task ('transcribe' or 'translate')
        device : Optional[str]
            Device to use ('cpu', 'cuda', etc.)
        **kwargs
            Additional engine-specific parameters
        """
        super().__init__(language, 16000, **kwargs)
        self.model_size = model_size
        self.task = task
        self.device = device
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = super().to_dict()
        config_dict.update({
            "model_size": self.model_size,
            "task": self.task,
            "device": self.device,
        })
        return config_dict


class WhisperModel(STTModel):
    """
    OpenAI Whisper STT model implementation.
    
    This class implements the STTModel interface for the Whisper engine.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[WhisperConfig] = None
    ):
        """
        Initialize a Whisper model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[WhisperConfig]
            Whisper-specific configuration
        """
        super().__init__(model_id, config or WhisperConfig())
        self.model = None
        
    async def initialize(self) -> bool:
        """
        Initialize the Whisper model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            import whisper
            
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Load the model
            self.model = await loop.run_in_executor(
                None,
                lambda: whisper.load_model(
                    self.config.model_size,
                    device=self.config.device
                )
            )
            
            self.is_initialized = True
            logger.info(f"Whisper model {self.config.model_size} initialized successfully")
            return True
        except ImportError:
            logger.error("Failed to import Whisper. Install it with: pip install openai-whisper")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            return False
    
    async def speech_to_text(self, audio_data: bytes, **kwargs) -> str:
        """
        Convert speech audio to text using Whisper.
        
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
        if not self.is_initialized:
            await self.initialize()
        
        # Merge configuration with any overrides
        params = self.config.to_dict()
        params.update(kwargs)
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Transcribe the audio
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    temp_path,
                    language=params.get("language"),
                    task=params.get("task", "transcribe"),
                )
            )
            
            return result.get("text", "")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
    
    async def cleanup(self) -> bool:
        """
        Clean up model resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        self.model = None
        self.is_initialized = False
        return True


class GoogleSpeechConfig(STTConfig):
    """Configuration for Google Speech-to-Text engine."""
    
    def __init__(
        self,
        language: str = "en-US",
        sample_rate: int = 16000,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Google Speech-to-Text configuration.
        
        Parameters
        ----------
        language : str
            Language code (e.g., 'en-US', 'fr-FR')
        sample_rate : int
            Audio sample rate in Hz
        api_key : Optional[str]
            Google Cloud API key (defaults to GOOGLE_API_KEY environment variable)
        **kwargs
            Additional engine-specific parameters
        """
        super().__init__(language, sample_rate, **kwargs)
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = super().to_dict()
        config_dict.update({
            "api_key": self.api_key,
        })
        return config_dict


class GoogleSpeechModel(STTModel):
    """
    Google Speech-to-Text model implementation.
    
    This class implements the STTModel interface for the Google Speech-to-Text engine.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[GoogleSpeechConfig] = None
    ):
        """
        Initialize a Google Speech-to-Text model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[GoogleSpeechConfig]
            Google Speech-specific configuration
        """
        super().__init__(model_id, config or GoogleSpeechConfig())
        self.client = None
        
    async def initialize(self) -> bool:
        """
        Initialize the Google Speech-to-Text client.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            from google.cloud import speech
            
            # Set the API key if provided
            if self.config.api_key:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.config.api_key
            
            # Create the client
            self.client = speech.SpeechClient()
            
            self.is_initialized = True
            logger.info("Google Speech-to-Text client initialized successfully")
            return True
        except ImportError:
            logger.error("Failed to import Google Cloud Speech. Install it with: pip install google-cloud-speech")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Google Speech-to-Text client: {e}")
            return False
    
    async def speech_to_text(self, audio_data: bytes, **kwargs) -> str:
        """
        Convert speech audio to text using Google Speech-to-Text.
        
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
        if not self.is_initialized:
            await self.initialize()
        
        from google.cloud import speech
        
        # Merge configuration with any overrides
        params = self.config.to_dict()
        params.update(kwargs)
        
        # Run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        
        # Create the recognition config
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=params.get("sample_rate", 16000),
            language_code=params.get("language", "en-US"),
        )
        
        # Create the audio object
        audio = speech.RecognitionAudio(content=audio_data)
        
        # Perform the speech recognition
        response = await loop.run_in_executor(
            None,
            lambda: self.client.recognize(config=config, audio=audio)
        )
        
        # Process the response
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        
        return transcript
    
    async def cleanup(self) -> bool:
        """
        Clean up client resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        self.client = None
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = [
    'STTConfig', 
    'STTModel',
    'WhisperConfig', 
    'WhisperModel',
    'GoogleSpeechConfig', 
    'GoogleSpeechModel',
]
