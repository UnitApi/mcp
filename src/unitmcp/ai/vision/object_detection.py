#!/usr/bin/env python3
"""
Object Detection Module for UnitMCP

This module provides object detection capabilities for UnitMCP,
supporting various object detection models like YOLO.
"""

import asyncio
import logging
import os
import tempfile
from abc import abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple, BinaryIO

from ..common.model_interface import VisionInterface

logger = logging.getLogger(__name__)

class ObjectDetectionConfig:
    """Base configuration for object detection models."""
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.4,
        **kwargs
    ):
        """
        Initialize object detection configuration.
        
        Parameters
        ----------
        confidence_threshold : float
            Confidence threshold for detections
        nms_threshold : float
            Non-maximum suppression threshold
        **kwargs
            Additional model-specific parameters
        """
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.additional_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = {
            "confidence_threshold": self.confidence_threshold,
            "nms_threshold": self.nms_threshold,
        }
        config_dict.update(self.additional_params)
        return config_dict


class ObjectDetectionModel(VisionInterface):
    """
    Base class for object detection models.
    
    This class implements the VisionInterface for object detection models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[ObjectDetectionConfig] = None
    ):
        """
        Initialize an object detection model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[ObjectDetectionConfig]
            Object detection-specific configuration
        """
        super().__init__(model_id, config or ObjectDetectionConfig())
    
    async def process(self, input_data: bytes) -> List[Dict[str, Any]]:
        """
        Process input image using the object detection model.
        
        Parameters
        ----------
        input_data : bytes
            Input image data to process
            
        Returns
        -------
        List[Dict[str, Any]]
            List of detected objects
        """
        return await self.detect_objects(input_data)
    
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
            List of detected objects with bounding boxes and classes
        """
        pass
    
    async def process_image(self, image_data: bytes, **kwargs) -> bytes:
        """
        Process an image.
        
        This method is not fully implemented in the base object detection model.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for image processing
            
        Returns
        -------
        bytes
            Original image data (not processed)
        """
        logger.warning("Image processing is not fully implemented in the base object detection model")
        return image_data
    
    async def extract_features(self, image_data: bytes, **kwargs) -> Dict[str, Any]:
        """
        Extract features from an image.
        
        This method is not fully implemented in the base object detection model.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for feature extraction
            
        Returns
        -------
        Dict[str, Any]
            Empty dictionary (not implemented in base class)
        """
        logger.warning("Feature extraction is not fully implemented in the base object detection model")
        return {}
    
    async def image_classification(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Not fully implemented in the base object detection model.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for image classification
            
        Returns
        -------
        List[Dict[str, Any]]
            Empty list (not implemented in base class)
        """
        logger.warning("Image classification is not fully implemented in the base object detection model")
        return []
    
    async def image_captioning(self, image_data: bytes, **kwargs) -> str:
        """
        Not implemented in the base object detection model.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for image captioning
            
        Returns
        -------
        str
            Empty string (not implemented in base class)
        """
        logger.warning("Image captioning is not implemented in the base object detection model")
        return ""


class YOLOConfig(ObjectDetectionConfig):
    """Configuration for YOLO object detection models."""
    
    def __init__(
        self,
        model_version: str = "yolov8n",
        input_size: int = 640,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.4,
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize YOLO configuration.
        
        Parameters
        ----------
        model_version : str
            YOLO model version (e.g., 'yolov8n', 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x')
        input_size : int
            Input image size
        confidence_threshold : float
            Confidence threshold for detections
        nms_threshold : float
            Non-maximum suppression threshold
        device : Optional[str]
            Device to use ('cpu', 'cuda', etc.)
        **kwargs
            Additional model-specific parameters
        """
        super().__init__(confidence_threshold, nms_threshold, **kwargs)
        self.model_version = model_version
        self.input_size = input_size
        self.device = device
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config_dict = super().to_dict()
        config_dict.update({
            "model_version": self.model_version,
            "input_size": self.input_size,
            "device": self.device,
        })
        return config_dict


class YOLOModel(ObjectDetectionModel):
    """
    YOLO object detection model implementation.
    
    This class implements the ObjectDetectionModel interface for YOLO models.
    """
    
    def __init__(
        self,
        model_id: str,
        config: Optional[YOLOConfig] = None
    ):
        """
        Initialize a YOLO model.
        
        Parameters
        ----------
        model_id : str
            Unique identifier for the model
        config : Optional[YOLOConfig]
            YOLO-specific configuration
        """
        super().__init__(model_id, config or YOLOConfig())
        self.model = None
        
    async def initialize(self) -> bool:
        """
        Initialize the YOLO model.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            from ultralytics import YOLO
            
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Load the model
            self.model = await loop.run_in_executor(
                None,
                lambda: YOLO(self.config.model_version)
            )
            
            self.is_initialized = True
            logger.info(f"YOLO model {self.config.model_version} initialized successfully")
            return True
        except ImportError:
            logger.error("Failed to import ultralytics. Install it with: pip install ultralytics")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize YOLO model: {e}")
            return False
    
    async def detect_objects(self, image_data: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Detect objects in an image using YOLO.
        
        Parameters
        ----------
        image_data : bytes
            Image data
        **kwargs
            Additional parameters for object detection
            
        Returns
        -------
        List[Dict[str, Any]]
            List of detected objects with bounding boxes and classes
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Merge configuration with any overrides
        params = self.config.to_dict()
        params.update(kwargs)
        
        # Create a temporary file to save the image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            
            # Run inference
            results = await loop.run_in_executor(
                None,
                lambda: self.model(
                    temp_path,
                    conf=params["confidence_threshold"],
                    iou=params["nms_threshold"],
                    device=params["device"]
                )
            )
            
            # Process results
            detections = []
            
            for result in results:
                # Get the boxes and class information
                boxes = result.boxes
                
                for i, box in enumerate(boxes):
                    # Get the bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # Get the confidence score
                    confidence = box.conf[0].item()
                    
                    # Get the class ID and name
                    class_id = box.cls[0].item()
                    class_name = result.names[class_id]
                    
                    # Create a detection object
                    detection = {
                        "bbox": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "width": x2 - x1,
                            "height": y2 - y1,
                        },
                        "class": {
                            "id": int(class_id),
                            "name": class_name,
                        },
                        "confidence": confidence,
                    }
                    
                    detections.append(detection)
            
            return detections
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


# Update the module's __all__ list
__all__ = [
    'ObjectDetectionConfig',
    'ObjectDetectionModel',
    'YOLOConfig',
    'YOLOModel',
]
