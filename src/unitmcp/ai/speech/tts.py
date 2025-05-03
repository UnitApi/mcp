#!/usr/bin/env python3
"""
Text-to-Speech Module for UnitMCP

This module provides text-to-speech capabilities for UnitMCP,
supporting various TTS engines.
"""

import asyncio
import logging
import os
import tempfile
from abc import abstractmethod
from typing import Dict, Any, Optional, Union, Tuple

from ..common.model_interface import SpeechInterface

logger = logging.getLogger(__name__)

class TTSConfig:
    """Base configuration for TTS engines."""
    
    def __init__(
        self,
        voice: Optional[str] = None,
        rate: int = 150,
        volume: float = 1.0,
        **kwargs
    ):
        """
        Initialize TTS configuration.
        
        Parameters
        ----------
        voice : Optional[str]
            Voice identifier to use
        rate : int
            Speech rate (words per minute)
        volume : float
            Volume level (0.0 to 1.0)
        **kwargs
            Additional engine-specific parameters
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.additional_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "voice": self.voice,
            "rate": self.rate,
            "volume": self.volume,
        }
        config_dict.update(self.additional_params)
        return config_dict


class TTSModel(SpeechInterface):
    """
    Base class for TTS models.
    
    This class implements the SpeechInterface for TTS models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[TTSConfig] = None
    ):
        """
        Initialize a TTS model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[TTSConfig]
            TTS-specific configuration
        """
        super().__init__(model_id, config or TTSConfig())
        
    async def process(self, input_data: str) -> bytes:
        """
        Process input text using the TTS model.
        
        Parameters
        ----------
        input_data : str
            Input text to convert to speech
            
        Returns
        -------
        bytes
            Audio data
        """
        return await self.text_to_speech(input_data)
    
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
    
    async def speech_to_text(self, audio_data: bytes, **kwargs) -> str:
        """
        Not implemented for TTS models.
        
        Raises
        ------
        NotImplementedError
            Always raised for TTS models
        """
        raise NotImplementedError("Speech-to-text is not supported by TTS models")


class PyTTSX3Config(TTSConfig):
    """Configuration for pyttsx3 TTS engine."""
    
    def __init__(
        self,
        voice: Optional[str] = None,
        rate: int = 150,
        volume: float = 1.0,
        **kwargs
    ):
        """
        Initialize pyttsx3 configuration.
        
        Parameters
        ----------
        voice : Optional[str]
            Voice identifier to use
        rate : int
            Speech rate (words per minute)
        volume : float
            Volume level (0.0 to 1.0)
        **kwargs
            Additional engine-specific parameters
        """
        super().__init__(voice, rate, volume, **kwargs)


class PyTTSX3Model(TTSModel):
    """
    pyttsx3 TTS model implementation.
    
    This class implements the TTSModel interface for the pyttsx3 engine.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[PyTTSX3Config] = None
    ):
        """
        Initialize a pyttsx3 model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[PyTTSX3Config]
            pyttsx3-specific configuration
        """
        super().__init__(model_id, config or PyTTSX3Config())
        self.engine = None
        
    async def initialize(self) -> bool:
        """
        Initialize the pyttsx3 engine.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            import pyttsx3
            
            # Initialize the engine in a separate thread
            loop = asyncio.get_event_loop()
            self.engine = await loop.run_in_executor(None, pyttsx3.init)
            
            # Configure the engine
            if self.config.voice:
                voices = await loop.run_in_executor(None, self.engine.getProperty, 'voices')
                for voice in voices:
                    if self.config.voice in voice.id:
                        await loop.run_in_executor(None, self.engine.setProperty, 'voice', voice.id)
                        break
            
            await loop.run_in_executor(None, self.engine.setProperty, 'rate', self.config.rate)
            await loop.run_in_executor(None, self.engine.setProperty, 'volume', self.config.volume)
            
            self.is_initialized = True
            logger.info(f"pyttsx3 engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            return False
    
    async def text_to_speech(self, text: str, **kwargs) -> bytes:
        """
        Convert text to speech audio using pyttsx3.
        
        Parameters
        ----------
        text : str
            Input text
        **kwargs
            Additional parameters for speech synthesis
            
        Returns
        -------
        bytes
            Audio data in WAV format
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Save speech to the temporary file
            await loop.run_in_executor(None, self.engine.save_to_file, text, temp_path)
            await loop.run_in_executor(None, self.engine.runAndWait)
            
            # Read the audio data
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
    
    async def cleanup(self) -> bool:
        """
        Clean up engine resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        if self.engine:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.engine.stop)
                self.engine = None
            except Exception as e:
                logger.warning(f"Error during pyttsx3 cleanup: {e}")
        
        self.is_initialized = False
        return True


class GTTSConfig(TTSConfig):
    """Configuration for Google Text-to-Speech (gTTS) engine."""
    
    def __init__(
        self,
        language: str = "en",
        slow: bool = False,
        **kwargs
    ):
        """
        Initialize gTTS configuration.
        
        Parameters
        ----------
        language : str
            Language code (e.g., 'en', 'fr', 'es')
        slow : bool
            Whether to use slower speech rate
        **kwargs
            Additional engine-specific parameters
        """
        super().__init__(None, 0, 1.0, **kwargs)
        self.language = language
        self.slow = slow
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = super().to_dict()
        config_dict.update({
            "language": self.language,
            "slow": self.slow,
        })
        return config_dict


class GTTSModel(TTSModel):
    """
    Google Text-to-Speech (gTTS) model implementation.
    
    This class implements the TTSModel interface for the gTTS engine.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[GTTSConfig] = None
    ):
        """
        Initialize a gTTS model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[GTTSConfig]
            gTTS-specific configuration
        """
        super().__init__(model_id, config or GTTSConfig())
        
    async def initialize(self) -> bool:
        """
        Initialize the gTTS engine.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Try to import gTTS
            from gtts import gTTS
            self.is_initialized = True
            logger.info("gTTS engine initialized successfully")
            return True
        except ImportError:
            logger.error("Failed to import gTTS. Install it with: pip install gtts")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize gTTS engine: {e}")
            return False
    
    async def text_to_speech(self, text: str, **kwargs) -> bytes:
        """
        Convert text to speech audio using gTTS.
        
        Parameters
        ----------
        text : str
            Input text
        **kwargs
            Additional parameters for speech synthesis
            
        Returns
        -------
        bytes
            Audio data in MP3 format
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Import gTTS
        from gtts import gTTS
        
        # Merge configuration with any overrides
        params = self.config.to_dict()
        params.update(kwargs)
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Create gTTS object and save to file
            def generate_speech():
                tts = gTTS(
                    text=text,
                    lang=params.get("language", "en"),
                    slow=params.get("slow", False)
                )
                tts.save(temp_path)
            
            await loop.run_in_executor(None, generate_speech)
            
            # Read the audio data
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
    
    async def cleanup(self) -> bool:
        """
        Clean up engine resources.
        
        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = [
    'TTSConfig', 
    'TTSModel',
    'PyTTSX3Config', 
    'PyTTSX3Model',
    'GTTSConfig', 
    'GTTSModel',
]
