"""
UnitMCP AI Module

This module provides artificial intelligence capabilities for UnitMCP,
including language models, natural language processing, speech processing,
and computer vision.
"""

from .common.model_interface import (
    AIModelInterface,
    LLMInterface,
    NLPInterface,
    SpeechInterface,
    VisionInterface
)

# Import LLM submodule
from .llm import (
    ollama,
    claude,
    openai,
)

# Import NLP submodule
from .nlp import (
    HuggingFaceConfig,
    HuggingFaceNLPModel,
    SpacyConfig,
    SpacyNLPModel,
)

# Import Speech submodule
from .speech import (
    TTSConfig, 
    TTSModel,
    PyTTSX3Config, 
    PyTTSX3Model,
    GTTSConfig, 
    GTTSModel,
    STTConfig, 
    STTModel,
    WhisperConfig, 
    WhisperModel,
    GoogleSpeechConfig, 
    GoogleSpeechModel,
    AudioAnalysisConfig,
    AudioAnalysisModel,
    AudioFeatureExtractor,
)

# Import Vision submodule
from .vision import (
    ImageProcessingConfig,
    ImageProcessingModel,
    ObjectDetectionConfig,
    ObjectDetectionModel,
    YOLOConfig,
    YOLOModel,
    FaceAnalysisConfig,
    FaceAnalysisModel,
    FaceDetector,
)

__all__ = [
    # Base interfaces
    'AIModelInterface',
    'LLMInterface',
    'NLPInterface',
    'SpeechInterface',
    'VisionInterface',
    
    # LLM models
    'ollama',
    'claude',
    'openai',
    
    # NLP models
    'HuggingFaceConfig',
    'HuggingFaceNLPModel',
    'SpacyConfig',
    'SpacyNLPModel',
    
    # Speech models
    'TTSConfig', 
    'TTSModel',
    'PyTTSX3Config', 
    'PyTTSX3Model',
    'GTTSConfig', 
    'GTTSModel',
    'STTConfig', 
    'STTModel',
    'WhisperConfig', 
    'WhisperModel',
    'GoogleSpeechConfig', 
    'GoogleSpeechModel',
    'AudioAnalysisConfig',
    'AudioAnalysisModel',
    'AudioFeatureExtractor',
    
    # Vision models
    'ImageProcessingConfig',
    'ImageProcessingModel',
    'ObjectDetectionConfig',
    'ObjectDetectionModel',
    'YOLOConfig',
    'YOLOModel',
    'FaceAnalysisConfig',
    'FaceAnalysisModel',
    'FaceDetector',
]
