#!/usr/bin/env python3
"""
Object Recognition Client

This script implements the client-side of the object recognition example.
It handles image capture from a camera and displays the results.
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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.unitmcp.utils.env_loader import EnvLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ObjectRecognitionClient:
    """
    Client for the object recognition example.
    
    This class handles:
    - Camera capture
    - Image processing
    - Communication with the server
    - Display of results
    - Recording of video (optional)
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the object recognition client.
        
        Parameters
        ----------
        config_path : str
            Path to the client configuration file
        """
        self.config = self._load_config(config_path)
        self.camera = None
        self.reader = None
        self.writer = None
        self.recording = False
        self.video_writer = None
        self.running = False
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
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
        
        # Load camera settings
        self.camera_config = self.config['camera']
        
        # Load display settings
        self.display_config = self.config['display']
        
        # Load connection settings
        self.connection_config = self.config['connection']
        
        # Load recording settings
        self.recording_config = self.config['recording']
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load the client configuration from a YAML file.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
            
        Returns
        -------
        Dict[str, Any]
            Client configuration
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    async def connect(self) -> bool:
        """
        Connect to the object recognition server.
        
        Returns
        -------
        bool
            True if connection was successful, False otherwise
        """
        for attempt in range(self.connection_config['reconnect_attempts']):
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.connection_config['server_host'],
                    self.connection_config['server_port'],
                )
                logger.info(f"Connected to server at {self.connection_config['server_host']}:{self.connection_config['server_port']}")
                return True
            
            except (ConnectionRefusedError, OSError) as e:
                logger.error(f"Connection attempt {attempt + 1}/{self.connection_config['reconnect_attempts']} failed: {e}")
                
                if attempt < self.connection_config['reconnect_attempts'] - 1:
                    logger.info(f"Retrying in {self.connection_config['reconnect_delay']} seconds...")
                    await asyncio.sleep(self.connection_config['reconnect_delay'])
                else:
                    logger.error("Failed to connect to server after multiple attempts")
                    return False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to the server and receive a response.
        
        Parameters
        ----------
        message : Dict[str, Any]
            Message to send to the server
            
        Returns
        -------
        Dict[str, Any]
            Response from the server
        """
        if not self.reader or not self.writer:
            logger.error("Not connected to server")
            return {'type': 'error', 'message': 'Not connected to server'}
        
        try:
            # Encode the message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send the message length
            self.writer.write(len(message_bytes).to_bytes(4, byteorder='big'))
            
            # Send the message
            self.writer.write(message_bytes)
            await self.writer.drain()
            
            # Read the response length
            length_bytes = await asyncio.wait_for(
                self.reader.read(4),
                timeout=self.connection_config['timeout'],
            )
            
            if not length_bytes:
                logger.error("Connection closed by server")
                return {'type': 'error', 'message': 'Connection closed by server'}
            
            # Convert the length bytes to an integer
            response_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read the response
            response_bytes = await asyncio.wait_for(
                self.reader.read(response_length),
                timeout=self.connection_config['timeout'],
            )
            
            if not response_bytes:
                logger.error("Connection closed by server")
                return {'type': 'error', 'message': 'Connection closed by server'}
            
            # Decode the response
            response = json.loads(response_bytes.decode('utf-8'))
            
            return response
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for server response after {self.connection_config['timeout']} seconds")
            return {'type': 'error', 'message': 'Timeout waiting for server response'}
        
        except Exception as e:
            logger.exception(f"Error sending message to server: {e}")
            return {'type': 'error', 'message': f'Error: {str(e)}'}
    
    def initialize_camera(self) -> bool:
        """
        Initialize the camera.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Initialize the camera
            self.camera = cv2.VideoCapture(self.camera_config['device'])
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config['width'])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config['height'])
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_config['fps'])
            
            # Check if camera is opened
            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False
            
            logger.info(f"Camera initialized: {self.camera_config['width']}x{self.camera_config['height']} @ {self.camera_config['fps']} FPS")
            return True
        
        except Exception as e:
            logger.exception(f"Error initializing camera: {e}")
            return False
    
    def start_recording(self, frame_size: Tuple[int, int]):
        """
        Start recording video.
        
        Parameters
        ----------
        frame_size : Tuple[int, int]
            Size of the video frames (width, height)
        """
        if self.recording or not self.recording_config['enabled']:
            return
        
        try:
            # Create the output directory if it doesn't exist
            output_dir = Path(self.recording_config['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a filename based on the current date and time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"recording_{timestamp}.{self.recording_config['format']}"
            
            # Initialize the video writer
            fourcc = cv2.VideoWriter_fourcc(*self.recording_config['codec'])
            self.video_writer = cv2.VideoWriter(
                str(filename),
                fourcc,
                self.recording_config['fps'],
                frame_size,
            )
            
            self.recording = True
            logger.info(f"Started recording to {filename}")
        
        except Exception as e:
            logger.exception(f"Error starting recording: {e}")
    
    def stop_recording(self):
        """Stop recording video."""
        if not self.recording:
            return
        
        try:
            # Release the video writer
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            self.recording = False
            logger.info("Stopped recording")
        
        except Exception as e:
            logger.exception(f"Error stopping recording: {e}")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process a frame before sending it to the server.
        
        Parameters
        ----------
        frame : np.ndarray
            Frame to process
            
        Returns
        -------
        np.ndarray
            Processed frame
        """
        # Apply rotation if needed
        rotation = self.camera_config['rotation']
        if rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # Apply flipping if needed
        if self.camera_config['flip_horizontal'] and self.camera_config['flip_vertical']:
            frame = cv2.flip(frame, -1)
        elif self.camera_config['flip_horizontal']:
            frame = cv2.flip(frame, 1)
        elif self.camera_config['flip_vertical']:
            frame = cv2.flip(frame, 0)
        
        return frame
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draw bounding boxes and labels for detected objects.
        
        Parameters
        ----------
        frame : np.ndarray
            Frame to draw on
        detections : List[Dict[str, Any]]
            Detected objects
            
        Returns
        -------
        np.ndarray
            Frame with detections drawn
        """
        # Get colors for bounding boxes
        colors = self.display_config['colors']
        default_color = colors['default']
        
        # Get font scale and line thickness
        font_scale = self.display_config['font_scale']
        line_thickness = self.display_config['line_thickness']
        
        # Draw each detection
        for detection in detections:
            # Get the bounding box
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
            
            # Convert to integers
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Get the class name and confidence
            class_name = detection['class']['name']
            confidence = detection['confidence']
            
            # Get the color for this class
            color = colors.get(class_name, default_color)
            
            # Draw the bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, line_thickness)
            
            # Prepare the label
            label = f"{class_name}"
            if self.display_config['show_confidence']:
                label += f": {confidence:.2f}"
            
            # Get the size of the label
            (label_width, label_height), _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                line_thickness,
            )
            
            # Draw the label background
            cv2.rectangle(
                frame,
                (x1, y1 - label_height - 5),
                (x1 + label_width + 5, y1),
                color,
                -1,
            )
            
            # Draw the label text
            cv2.putText(
                frame,
                label,
                (x1 + 3, y1 - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                line_thickness,
                cv2.LINE_AA,
            )
        
        return frame
    
    def draw_fps(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw the FPS counter on the frame.
        
        Parameters
        ----------
        frame : np.ndarray
            Frame to draw on
            
        Returns
        -------
        np.ndarray
            Frame with FPS counter
        """
        if not self.display_config['show_fps']:
            return frame
        
        # Update FPS calculation
        self.frame_count += 1
        current_time = time.time()
        elapsed_time = current_time - self.last_fps_time
        
        if elapsed_time >= 1.0:
            self.fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.last_fps_time = current_time
        
        # Draw the FPS counter
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(
            frame,
            fps_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        
        return frame
    
    async def run(self):
        """Run the object recognition client."""
        self.running = True
        
        # Connect to the server
        if not await self.connect():
            print("Failed to connect to the server. Please make sure the server is running.")
            return
        
        # Initialize the camera
        if not self.initialize_camera():
            print("Failed to initialize the camera. Please check your camera settings.")
            return
        
        # Create a window for display
        if self.display_config['enabled']:
            window_name = self.display_config['window_name']
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            
            # Set window size
            cv2.resizeWindow(
                window_name,
                self.display_config['width'],
                self.display_config['height'],
            )
            
            # Set fullscreen if needed
            if self.display_config['fullscreen']:
                cv2.setWindowProperty(
                    window_name,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN,
                )
        
        try:
            while self.running:
                # Capture a frame
                ret, frame = self.camera.read()
                
                if not ret:
                    logger.error("Failed to capture frame")
                    await asyncio.sleep(0.1)
                    continue
                
                # Process the frame
                processed_frame = self.process_frame(frame)
                
                # Compress the frame for sending
                if self.connection_config['compression']['enabled']:
                    encode_param = [
                        int(cv2.IMWRITE_JPEG_QUALITY),
                        self.connection_config['compression']['quality'],
                    ]
                    _, encoded_frame = cv2.imencode(
                        f".{self.connection_config['compression']['format']}",
                        processed_frame,
                        encode_param,
                    )
                else:
                    _, encoded_frame = cv2.imencode('.png', processed_frame)
                
                # Convert to base64
                frame_base64 = base64.b64encode(encoded_frame).decode('utf-8')
                
                # Send the frame to the server
                message = {
                    'type': 'image',
                    'data': frame_base64,
                }
                
                # Send the message to the server
                response = await self.send_message(message)
                
                if response.get('type') == 'error':
                    logger.error(f"Error from server: {response.get('message')}")
                    await asyncio.sleep(0.1)
                    continue
                
                # Get the detections
                detections = response.get('detections', [])
                
                # Get the processed image from the server
                processed_image_base64 = response.get('processed_image')
                if processed_image_base64:
                    processed_image_bytes = base64.b64decode(processed_image_base64)
                    nparr = np.frombuffer(processed_image_bytes, np.uint8)
                    processed_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    processed_image = processed_frame
                
                # Draw detections on the frame
                display_frame = self.draw_detections(processed_image.copy(), detections)
                
                # Draw FPS counter
                display_frame = self.draw_fps(display_frame)
                
                # Display the frame
                if self.display_config['enabled']:
                    cv2.imshow(self.display_config['window_name'], display_frame)
                
                # Record the frame if recording is enabled
                if self.recording and self.video_writer:
                    self.video_writer.write(display_frame)
                
                # Check if recording should be started or stopped
                if self.recording_config['enabled'] and self.recording_config['trigger_on_detection']:
                    if detections and not self.recording:
                        self.start_recording(display_frame.shape[1::-1])
                    elif not detections and self.recording:
                        self.stop_recording()
                
                # Check for key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    # Quit
                    self.running = False
                elif key == ord('r'):
                    # Toggle recording
                    if self.recording:
                        self.stop_recording()
                    else:
                        self.start_recording(display_frame.shape[1::-1])
                
                # Limit the frame rate
                await asyncio.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\nStopping object recognition client...")
        
        except Exception as e:
            logger.exception(f"Error in object recognition client: {e}")
            print(f"Error: {e}")
        
        finally:
            # Clean up
            self.running = False
            
            # Stop recording
            self.stop_recording()
            
            # Release the camera
            if self.camera:
                self.camera.release()
            
            # Close all windows
            cv2.destroyAllWindows()
            
            # Close the connection
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
            
            print("Object recognition client stopped")


async def main():
    """Run the object recognition client."""
    # Load environment variables
    env_loader = EnvLoader()
    env_loader.load_env()
    
    # Get the configuration path
    config_path = os.path.join(os.path.dirname(__file__), "config", "client.yaml")
    
    # Create and run the client
    client = ObjectRecognitionClient(config_path)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
