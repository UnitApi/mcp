"""
UnitMCP Computer Vision Module

This module provides computer vision capabilities for UnitMCP,
including image processing, object detection, and face analysis.
"""

from .image_processing import (
    ImageProcessingConfig,
    ImageProcessingModel,
)

from .object_detection import (
    ObjectDetectionConfig,
    ObjectDetectionModel,
    YOLOConfig,
    YOLOModel,
)

from .face_analysis import (
    FaceAnalysisConfig,
    FaceAnalysisModel,
    FaceDetector,
)

__all__ = [
    # Image Processing
    'ImageProcessingConfig',
    'ImageProcessingModel',
    
    # Object Detection
    'ObjectDetectionConfig',
    'ObjectDetectionModel',
    'YOLOConfig',
    'YOLOModel',
    
    # Face Analysis
    'FaceAnalysisConfig',
    'FaceAnalysisModel',
    'FaceDetector',
]
