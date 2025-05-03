#!/usr/bin/env python3
"""
Audio Analysis Module for UnitMCP

This module provides audio analysis capabilities for UnitMCP,
including feature extraction and audio classification.
"""

import asyncio
import logging
import os
import tempfile
from abc import abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple, BinaryIO

from ..common.model_interface import AIModelInterface

logger = logging.getLogger(__name__)

class AudioAnalysisConfig:
    """Base configuration for audio analysis models."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        n_fft: int = 2048,
        hop_length: int = 512,
        **kwargs
    ):
        """
        Initialize audio analysis configuration.
        
        Parameters
        ----------
        sample_rate : int
            Audio sample rate in Hz
        n_fft : int
            FFT window size
        hop_length : int
            Number of samples between successive frames
        **kwargs
            Additional model-specific parameters
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.additional_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "sample_rate": self.sample_rate,
            "n_fft": self.n_fft,
            "hop_length": self.hop_length,
        }
        config_dict.update(self.additional_params)
        return config_dict


class AudioAnalysisModel(AIModelInterface):
    """
    Base class for audio analysis models.
    
    This class implements the AIModelInterface for audio analysis models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[AudioAnalysisConfig] = None
    ):
        """
        Initialize an audio analysis model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[AudioAnalysisConfig]
            Audio analysis-specific configuration
        """
        super().__init__(model_id, config or AudioAnalysisConfig())
    
    @abstractmethod
    async def analyze_audio(self, audio_data: bytes, **kwargs) -> Dict[str, Any]:
        """
        Analyze audio data.
        
        Parameters
        ----------
        audio_data : bytes
            Audio data
        **kwargs
            Additional parameters for audio analysis
            
        Returns
        -------
        Dict[str, Any]
            Analysis results
        """
        pass
    
    async def process(self, input_data: bytes) -> Dict[str, Any]:
        """
        Process input audio using the audio analysis model.
        
        Parameters
        ----------
        input_data : bytes
            Input audio data to analyze
            
        Returns
        -------
        Dict[str, Any]
            Analysis results
        """
        return await self.analyze_audio(input_data)


class AudioFeatureExtractor(AudioAnalysisModel):
    """
    Audio feature extraction model.
    
    This class implements the AudioAnalysisModel interface for extracting
    features from audio data, such as MFCCs, spectrograms, and onsets.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[AudioAnalysisConfig] = None
    ):
        """
        Initialize an audio feature extractor.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[AudioAnalysisConfig]
            Audio analysis-specific configuration
        """
        super().__init__(model_id, config or AudioAnalysisConfig())
        
    async def initialize(self) -> bool:
        """
        Initialize the audio feature extractor.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Try to import librosa
            import librosa
            import numpy as np
            
            self.is_initialized = True
            logger.info("Audio feature extractor initialized successfully")
            return True
        except ImportError:
            logger.error("Failed to import librosa. Install it with: pip install librosa")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize audio feature extractor: {e}")
            return False
    
    async def analyze_audio(self, audio_data: bytes, **kwargs) -> Dict[str, Any]:
        """
        Extract features from audio data.
        
        Parameters
        ----------
        audio_data : bytes
            Audio data
        **kwargs
            Additional parameters for feature extraction
            
        Returns
        -------
        Dict[str, Any]
            Extracted features
        """
        if not self.is_initialized:
            await self.initialize()
        
        import librosa
        import numpy as np
        
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
            
            # Load the audio file
            y, sr = await loop.run_in_executor(
                None,
                lambda: librosa.load(
                    temp_path,
                    sr=params.get("sample_rate", 16000)
                )
            )
            
            # Extract features
            features = {}
            
            # Extract MFCCs
            if kwargs.get("extract_mfcc", True):
                mfccs = await loop.run_in_executor(
                    None,
                    lambda: librosa.feature.mfcc(
                        y=y,
                        sr=sr,
                        n_mfcc=params.get("n_mfcc", 13)
                    )
                )
                features["mfcc"] = mfccs.tolist()
            
            # Extract spectrogram
            if kwargs.get("extract_spectrogram", True):
                spectrogram = await loop.run_in_executor(
                    None,
                    lambda: np.abs(librosa.stft(
                        y,
                        n_fft=params.get("n_fft", 2048),
                        hop_length=params.get("hop_length", 512)
                    ))
                )
                features["spectrogram"] = spectrogram.tolist()
            
            # Extract onsets
            if kwargs.get("extract_onsets", True):
                onsets = await loop.run_in_executor(
                    None,
                    lambda: librosa.onset.onset_detect(
                        y=y,
                        sr=sr,
                        hop_length=params.get("hop_length", 512)
                    )
                )
                features["onsets"] = onsets.tolist()
            
            # Extract tempo
            if kwargs.get("extract_tempo", True):
                tempo, _ = await loop.run_in_executor(
                    None,
                    lambda: librosa.beat.beat_track(
                        y=y,
                        sr=sr,
                        hop_length=params.get("hop_length", 512)
                    )
                )
                features["tempo"] = float(tempo)
            
            # Extract pitch
            if kwargs.get("extract_pitch", True):
                pitches, magnitudes = await loop.run_in_executor(
                    None,
                    lambda: librosa.piptrack(
                        y=y,
                        sr=sr,
                        n_fft=params.get("n_fft", 2048),
                        hop_length=params.get("hop_length", 512)
                    )
                )
                features["pitch"] = {
                    "mean": float(np.mean(pitches[pitches > 0])) if np.any(pitches > 0) else 0,
                    "std": float(np.std(pitches[pitches > 0])) if np.any(pitches > 0) else 0,
                }
            
            return features
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
        self.is_initialized = False
        return True


# Update the module's __all__ list
__all__ = [
    'AudioAnalysisConfig',
    'AudioAnalysisModel',
    'AudioFeatureExtractor',
]
