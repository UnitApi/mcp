#!/usr/bin/env python3
"""
Object Recognition Server

This script implements the server-side of the object recognition example.
It handles image processing, object detection, and action triggering.
"""

import asyncio
import base64
import cv2
import json
import logging
import numpy as np
import os
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.unitmcp.utils.env_loader import EnvLoader
from src.unitmcp.ai import (
    # Vision models
    YOLOConfig, YOLOModel,
    ImageProcessingConfig, ImageProcessingModel,
)
from src.unitmcp.platforms.adapters.platform_adapter import get_platform_adapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ObjectRecognitionServer:
    """
    Server for the object recognition example.
    
    This class handles:
    - WebSocket connections from clients
    - Image processing
    - Object detection
    - Action triggering based on detected objects
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the object recognition server.
        
        Parameters
        ----------
        config_path : str
            Path to the server configuration file
        """
        self.config = self._load_config(config_path)
        self.clients = set()
        self.object_detector = None
        self.image_processor = None
        self.platform_adapter = None
        self.running = False
        
        # Configure logging
        log_config = self.config['logging']
        log_level = getattr(logging, log_config['level'])
        
        logger.setLevel(log_level)
        
        if log_config.get('file'):
            file_handler = logging.FileHandler(log_config['file'])
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(file_handler)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load the server configuration from a YAML file.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
            
        Returns
        -------
        Dict[str, Any]
            Server configuration
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    async def initialize(self) -> bool:
        """
        Initialize the vision models and hardware control.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Initialize the object detection model
            object_detection_config = self.config['vision']['object_detection']
            provider = object_detection_config['provider']
            
            if provider == 'yolo':
                yolo_config = YOLOConfig(
                    model_version=object_detection_config['model'],
                    confidence_threshold=object_detection_config['confidence_threshold'],
                    nms_threshold=object_detection_config['nms_threshold'],
                    device=object_detection_config['device'],
                )
                self.object_detector = YOLOModel("object-recognition", yolo_config)
            
            else:
                logger.error(f"Unsupported object detection provider: {provider}")
                return False
            
            # Initialize the object detector
            if not await self.object_detector.initialize():
                logger.error(f"Failed to initialize {provider} model")
                return False
            
            # Initialize the image processor
            image_processing_config = self.config['vision']['image_processing']
            
            image_processor_config = ImageProcessingConfig(
                resize=tuple(image_processing_config['resize']),
                normalize=image_processing_config['normalize'],
            )
            self.image_processor = ImageProcessingModel("image-processor", image_processor_config)
            
            # Initialize the image processor
            if not await self.image_processor.initialize():
                logger.error("Failed to initialize image processor")
                return False
            
            # Initialize hardware control if enabled
            if self.config['hardware']['enabled']:
                platform = self.config['hardware']['platform']
                
                # Get the platform adapter
                self.platform_adapter = get_platform_adapter(platform)
                
                if not self.platform_adapter:
                    logger.error(f"Failed to get platform adapter for {platform}")
                    return False
                
                # Initialize the platform adapter
                if not await self.platform_adapter.initialize():
                    logger.error(f"Failed to initialize platform adapter for {platform}")
                    return False
                
                logger.info(f"Initialized hardware control for {platform}")
            
            logger.info("Server initialization complete")
            return True
        
        except Exception as e:
            logger.exception(f"Error initializing server: {e}")
            return False
    
    async def start(self):
        """Start the WebSocket server."""
        server_config = self.config['server']
        host = server_config['host']
        port = server_config['port']
        
        # Initialize the server
        if not await self.initialize():
            logger.error("Failed to initialize server, exiting")
            return
        
        # Start the WebSocket server
        self.running = True
        
        try:
            server = await asyncio.start_server(
                self.handle_client,
                host,
                port,
            )
            
            logger.info(f"Server started on {host}:{port}")
            
            async with server:
                await server.serve_forever()
        
        except Exception as e:
            logger.exception(f"Error starting server: {e}")
            self.running = False
    
    async def handle_client(self, reader, writer):
        """
        Handle a client connection.
        
        Parameters
        ----------
        reader : asyncio.StreamReader
            Stream reader for the client connection
        writer : asyncio.StreamWriter
            Stream writer for the client connection
        """
        addr = writer.get_extra_info('peername')
        logger.info(f"New client connected: {addr}")
        
        # Add the client to the set of connected clients
        client = (reader, writer)
        self.clients.add(client)
        
        try:
            while self.running:
                # Read the message length (4 bytes)
                length_bytes = await reader.read(4)
                if not length_bytes:
                    break
                
                # Convert the length bytes to an integer
                message_length = int.from_bytes(length_bytes, byteorder='big')
                
                # Read the message
                message_bytes = await reader.read(message_length)
                if not message_bytes:
                    break
                
                # Decode the message
                message = json.loads(message_bytes.decode('utf-8'))
                
                # Process the message
                response = await self.process_message(message)
                
                # Encode the response
                response_bytes = json.dumps(response).encode('utf-8')
                
                # Send the response length
                writer.write(len(response_bytes).to_bytes(4, byteorder='big'))
                
                # Send the response
                writer.write(response_bytes)
                await writer.drain()
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(f"Error handling client {addr}: {e}")
        
        finally:
            # Remove the client from the set of connected clients
            self.clients.remove(client)
            
            # Close the connection
            writer.close()
            await writer.wait_closed()
            
            logger.info(f"Client disconnected: {addr}")
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message from a client.
        
        Parameters
        ----------
        message : Dict[str, Any]
            Message from the client
            
        Returns
        -------
        Dict[str, Any]
            Response to the client
        """
        message_type = message.get('type')
        
        if message_type == 'image':
            # Process image data
            image_data = message.get('data')
            
            # Convert image data from base64 to bytes
            import base64
            image_bytes = base64.b64decode(image_data)
            
            # Process the image
            start_time = time.time()
            result = await self.process_image(image_bytes)
            processing_time = time.time() - start_time
            
            # Add processing time to the result
            result['processing_time'] = processing_time
            
            return result
        
        else:
            # Unknown message type
            return {
                'type': 'error',
                'message': f"Unknown message type: {message_type}",
            }
    
    async def process_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Process an image for object detection.
        
        Parameters
        ----------
        image_bytes : bytes
            Image data
            
        Returns
        -------
        Dict[str, Any]
            Processing result
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    'type': 'error',
                    'message': "Failed to decode image",
                }
            
            # Process the image
            image_processing_config = self.config['vision']['image_processing']
            
            # Resize the image if needed
            if image_processing_config.get('resize'):
                width, height = image_processing_config['resize']
                image = cv2.resize(image, (width, height))
            
            # Convert to grayscale if needed
            if image_processing_config.get('grayscale'):
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # Convert back to BGR for object detection
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            # Apply blur if needed
            blur_size = image_processing_config.get('blur')
            if blur_size:
                image = cv2.GaussianBlur(image, (blur_size, blur_size), 0)
            
            # Apply edge detection if needed
            if image_processing_config.get('edges'):
                image = cv2.Canny(image, 100, 200)
                # Convert back to BGR for object detection
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            # Detect objects
            detections = await self.object_detector.detect_objects(cv2.imencode('.jpg', image)[1].tobytes())
            
            # Filter detections based on objects of interest
            highlight_classes = self.config['objects']['highlight']
            filtered_detections = []
            
            for detection in detections:
                class_name = detection['class']['name']
                if class_name in highlight_classes:
                    filtered_detections.append(detection)
            
            # Check for objects that should trigger actions
            actions = []
            for detection in filtered_detections:
                class_name = detection['class']['name']
                confidence = detection['confidence']
                
                # Check if this object has an action configured
                if class_name in self.config['objects']['actions']:
                    action_config = self.config['objects']['actions'][class_name]
                    
                    if action_config['enabled'] and confidence >= action_config['min_confidence']:
                        # Trigger the action
                        action_result = await self.trigger_action(
                            class_name,
                            confidence,
                            action_config,
                        )
                        
                        actions.append({
                            'object': class_name,
                            'confidence': confidence,
                            'action': action_config['action'],
                            'result': action_result,
                        })
            
            # Encode the processed image
            _, processed_image_bytes = cv2.imencode('.jpg', image)
            processed_image_base64 = base64.b64encode(processed_image_bytes).decode('utf-8')
            
            return {
                'type': 'detection_result',
                'detections': filtered_detections,
                'actions': actions,
                'processed_image': processed_image_base64,
            }
        
        except Exception as e:
            logger.exception(f"Error processing image: {e}")
            return {
                'type': 'error',
                'message': f"Error processing image: {str(e)}",
            }
    
    async def trigger_action(self, object_class: str, confidence: float, action_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger an action based on a detected object.
        
        Parameters
        ----------
        object_class : str
            Class of the detected object
        confidence : float
            Confidence of the detection
        action_config : Dict[str, Any]
            Action configuration
            
        Returns
        -------
        Dict[str, Any]
            Result of the action
        """
        action_type = action_config['action']
        
        if action_type == 'log':
            # Log the detection
            message = action_config['message']
            logger.info(f"{message}: {object_class} detected with confidence {confidence:.2f}")
            
            return {
                'success': True,
                'message': message,
            }
        
        elif action_type == 'alert':
            # Log the detection
            message = action_config['message']
            logger.warning(f"ALERT: {message}: {object_class} detected with confidence {confidence:.2f}")
            
            return {
                'success': True,
                'message': f"Alert triggered: {message}",
            }
        
        elif action_type == 'trigger_gpio':
            # Check if hardware control is enabled
            if not self.config['hardware']['enabled'] or not self.platform_adapter:
                return {
                    'success': False,
                    'message': "Hardware control is not enabled",
                }
            
            # Get the GPIO pin for the object
            pin_key = f"{object_class}_detected"
            pin = self.config['hardware']['gpio_pins'].get(pin_key)
            
            if not pin:
                return {
                    'success': False,
                    'message': f"No GPIO pin configured for {object_class} detection",
                }
            
            try:
                # Set the pin high
                await self.platform_adapter.set_pin(pin, True)
                
                # Schedule a task to set the pin low after 1 second
                async def reset_pin():
                    await asyncio.sleep(1)
                    await self.platform_adapter.set_pin(pin, False)
                
                asyncio.create_task(reset_pin())
                
                return {
                    'success': True,
                    'message': f"Triggered GPIO pin {pin} for {object_class} detection",
                    'pin': pin,
                }
            
            except Exception as e:
                logger.exception(f"Error triggering GPIO: {e}")
                return {
                    'success': False,
                    'message': f"Error triggering GPIO: {str(e)}",
                }
        
        else:
            return {
                'success': False,
                'message': f"Unknown action type: {action_type}",
            }
    
    async def cleanup(self):
        """Clean up resources."""
        self.running = False
        
        # Close all client connections
        for reader, writer in self.clients:
            writer.close()
        
        # Clean up vision models
        if self.object_detector:
            await self.object_detector.cleanup()
        
        if self.image_processor:
            await self.image_processor.cleanup()
        
        # Clean up hardware control
        if self.platform_adapter:
            await self.platform_adapter.cleanup()
        
        logger.info("Server cleanup complete")


async def main():
    """Run the object recognition server."""
    # Load environment variables
    env_loader = EnvLoader()
    env_loader.load_env()
    
    # Get the configuration path
    config_path = os.path.join(os.path.dirname(__file__), "config", "server.yaml")
    
    # Create and start the server
    server = ObjectRecognitionServer(config_path)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
