"""
UnitMCP Speech Processing Module

This module provides speech processing capabilities for UnitMCP,
including text-to-speech, speech-to-text, and audio analysis.
"""

from .tts import (
    TTSConfig, 
    TTSModel,
    PyTTSX3Config, 
    PyTTSX3Model,
    GTTSConfig, 
    GTTSModel,
)

from .stt import (
    STTConfig, 
    STTModel,
    WhisperConfig, 
    WhisperModel,
    GoogleSpeechConfig, 
    GoogleSpeechModel,
)

from .audio_analysis import (
    AudioAnalysisConfig,
    AudioAnalysisModel,
    AudioFeatureExtractor,
)

__all__ = [
    # TTS
    'TTSConfig', 
    'TTSModel',
    'PyTTSX3Config', 
    'PyTTSX3Model',
    'GTTSConfig', 
    'GTTSModel',
    
    # STT
    'STTConfig', 
    'STTModel',
    'WhisperConfig', 
    'WhisperModel',
    'GoogleSpeechConfig', 
    'GoogleSpeechModel',
    
    # Audio Analysis
    'AudioAnalysisConfig',
    'AudioAnalysisModel',
    'AudioFeatureExtractor',
]
