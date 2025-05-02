"""
camera.py
"""

"""Camera server for video capture and image processing."""

import asyncio
import base64
import io
from typing import Dict, Any, Optional, List

from .base import MCPServer
from ..protocols.hardware_protocol import MCPRequest, MCPResponse, MCPErrorCode

try:
    import cv2
    import numpy as np
    from PIL import Image

    HAS_CAMERA = True
except ImportError:
    HAS_CAMERA = False

    # Mock classes for environments without camera support
    class MockVideoCapture:
        def __init__(self, device=0):
            self.device = device

        def isOpened(self):
            return False

        def read(self):
            return False, None

        def release(self):
            pass

        def get(self, prop):
            return 0

        def set(self, prop, value):
            return False

    cv2 = type(
        "cv2",
        (),
        {
            "VideoCapture": MockVideoCapture,
            "CAP_PROP_FRAME_WIDTH": 3,
            "CAP_PROP_FRAME_HEIGHT": 4,
            "CAP_PROP_FPS": 5,
        },
    )()


class CameraServer(MCPServer):
    """MCP server for camera device control."""

    def __init__(self):
        super().__init__()
        self.cameras: Dict[str, cv2.VideoCapture] = {}
        self.active_streams: Dict[str, bool] = {}
        self.recording_tasks: Dict[str, asyncio.Task] = {}

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle camera requests."""
        try:
            method_parts = request.method.split(".")
            if len(method_parts) < 2:
                return self.create_error_response(
                    request.id, MCPErrorCode.METHOD_NOT_FOUND, "Invalid method format"
                )

            action = method_parts[1]

            # Map methods to handlers
            handlers = {
                "listCameras": self.list_cameras,
                "openCamera": self.open_camera,
                "closeCamera": self.close_camera,
                "captureImage": self.capture_image,
                "startRecording": self.start_recording,
                "stopRecording": self.stop_recording,
                "setCameraProperty": self.set_camera_property,
                "getCameraProperty": self.get_camera_property,
                "detectFaces": self.detect_faces,
                "detectMotion": self.detect_motion,
            }

            if action not in handlers:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Unknown camera method: {action}",
                )

            return await handlers[action](request)

        except Exception as e:
            self.logger.error(f"Camera error: {e}")
            return self.create_error_response(
                request.id, MCPErrorCode.INTERNAL_ERROR, str(e)
            )

    async def list_cameras(self, request: MCPRequest) -> MCPResponse:
        """List available camera devices."""
        if not HAS_CAMERA:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, "Camera support not available"
            )

        try:
            cameras = []

            # Check for available cameras (up to 10 devices)
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras.append(
                        {
                            "id": i,
                            "name": f"Camera {i}",
                            "available": True,
                            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                            "fps": int(cap.get(cv2.CAP_PROP_FPS)),
                        }
                    )
                    cap.release()

            return MCPResponse(
                id=request.id, result={"status": "success", "cameras": cameras}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to list cameras: {e}"
            )

    async def open_camera(self, request: MCPRequest) -> MCPResponse:
        """Open a camera device."""
        camera_id = request.params.get("camera_id", 0)
        device_name = request.params.get("device_name", f"camera_{camera_id}")

        if device_name in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} already open",
            )

        try:
            camera = cv2.VideoCapture(camera_id)
            if not camera.isOpened():
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.HARDWARE_ERROR,
                    f"Failed to open camera {camera_id}",
                )

            # Set default properties
            width = request.params.get("width", 640)
            height = request.params.get("height", 480)
            fps = request.params.get("fps", 30)

            camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            camera.set(cv2.CAP_PROP_FPS, fps)

            self.cameras[device_name] = camera
            self.active_streams[device_name] = False

            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "device_name": device_name,
                    "camera_id": camera_id,
                    "properties": {
                        "width": int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        "height": int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        "fps": int(camera.get(cv2.CAP_PROP_FPS)),
                    },
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to open camera: {e}"
            )

    async def close_camera(self, request: MCPRequest) -> MCPResponse:
        """Close a camera device."""
        device_name = request.params.get("device_name")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        try:
            # Stop any recordings
            if device_name in self.recording_tasks:
                self.recording_tasks[device_name].cancel()
                del self.recording_tasks[device_name]

            # Release camera
            self.cameras[device_name].release()
            del self.cameras[device_name]
            del self.active_streams[device_name]

            return MCPResponse(
                id=request.id, result={"status": "success", "device_name": device_name}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to close camera: {e}"
            )

    async def capture_image(self, request: MCPRequest) -> MCPResponse:
        """Capture a single image from camera."""
        device_name = request.params.get("device_name")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        try:
            camera = self.cameras[device_name]
            ret, frame = camera.read()

            if not ret:
                return self.create_error_response(
                    request.id, MCPErrorCode.HARDWARE_ERROR, "Failed to capture frame"
                )

            # Convert to desired format
            format_type = request.params.get("format", "jpeg")
            quality = request.params.get("quality", 90)

            # Encode image
            if format_type == "jpeg":
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                ret, buffer = cv2.imencode(".jpg", frame, encode_param)
            elif format_type == "png":
                ret, buffer = cv2.imencode(".png", frame)
            else:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.INVALID_PARAMS,
                    f"Unsupported format: {format_type}",
                )

            if not ret:
                return self.create_error_response(
                    request.id, MCPErrorCode.HARDWARE_ERROR, "Failed to encode image"
                )

            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode("utf-8")

            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "image_data": image_base64,
                    "format": format_type,
                    "width": frame.shape[1],
                    "height": frame.shape[0],
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to capture image: {e}"
            )

    async def start_recording(self, request: MCPRequest) -> MCPResponse:
        """Start video recording."""
        device_name = request.params.get("device_name")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        if device_name in self.recording_tasks:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Already recording on {device_name}",
            )

        try:
            camera = self.cameras[device_name]

            # Get recording parameters
            duration = request.params.get("duration", 0)  # 0 for continuous
            fps = request.params.get("fps", 30)
            output_format = request.params.get("format", "mp4")

            # Start recording task
            task = asyncio.create_task(
                self._record_video(device_name, camera, duration, fps, output_format)
            )
            self.recording_tasks[device_name] = task

            return MCPResponse(
                id=request.id,
                result={
                    "status": "recording_started",
                    "device_name": device_name,
                    "format": output_format,
                    "fps": fps,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to start recording: {e}",
            )

    async def _record_video(
        self,
        device_name: str,
        camera: cv2.VideoCapture,
        duration: float,
        fps: int,
        output_format: str,
    ):
        """Record video in background task."""
        frames = []
        start_time = asyncio.get_event_loop().time()

        try:
            while True:
                ret, frame = camera.read()
                if ret:
                    frames.append(frame)

                # Check if duration exceeded
                if duration > 0:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= duration:
                        break

                await asyncio.sleep(1.0 / fps)

                # Check if recording was cancelled
                if device_name not in self.recording_tasks:
                    break

        except asyncio.CancelledError:
            pass
        finally:
            # Store recorded frames (in a real implementation, you'd save to file)
            if device_name in self.recording_tasks:
                self.recording_tasks[device_name] = frames

    async def stop_recording(self, request: MCPRequest) -> MCPResponse:
        """Stop video recording and return video data."""
        device_name = request.params.get("device_name")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        if device_name not in self.recording_tasks:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Not recording on {device_name}",
            )

        try:
            # Cancel recording task
            task = self.recording_tasks[device_name]
            task.cancel()

            # Wait for task to complete
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Get recorded frames
            frames = self.recording_tasks.get(device_name, [])
            if isinstance(frames, asyncio.Task):
                frames = []

            del self.recording_tasks[device_name]

            # Convert frames to video (simplified)
            if frames:
                # In a real implementation, you'd encode to video format
                # For now, return frame count and metadata
                return MCPResponse(
                    id=request.id,
                    result={
                        "status": "recording_stopped",
                        "device_name": device_name,
                        "frame_count": len(frames),
                        "duration": len(frames) / 30.0,  # Assuming 30 fps
                    },
                )
            else:
                return MCPResponse(
                    id=request.id,
                    result={
                        "status": "recording_stopped",
                        "device_name": device_name,
                        "frame_count": 0,
                        "duration": 0,
                    },
                )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to stop recording: {e}",
            )

    async def set_camera_property(self, request: MCPRequest) -> MCPResponse:
        """Set camera property."""
        device_name = request.params.get("device_name")
        property_name = request.params.get("property")
        value = request.params.get("value")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        if not property_name or value is None:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing property or value"
            )

        try:
            camera = self.cameras[device_name]

            # Map property names to OpenCV constants
            property_map = {
                "width": cv2.CAP_PROP_FRAME_WIDTH,
                "height": cv2.CAP_PROP_FRAME_HEIGHT,
                "fps": cv2.CAP_PROP_FPS,
                "brightness": cv2.CAP_PROP_BRIGHTNESS,
                "contrast": cv2.CAP_PROP_CONTRAST,
                "saturation": cv2.CAP_PROP_SATURATION,
                "hue": cv2.CAP_PROP_HUE,
                "gain": cv2.CAP_PROP_GAIN,
                "exposure": cv2.CAP_PROP_EXPOSURE,
            }

            if property_name not in property_map:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.INVALID_PARAMS,
                    f"Unknown property: {property_name}",
                )

            success = camera.set(property_map[property_name], value)
            actual_value = camera.get(property_map[property_name])

            return MCPResponse(
                id=request.id,
                result={
                    "status": "success" if success else "failed",
                    "property": property_name,
                    "requested_value": value,
                    "actual_value": actual_value,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to set property: {e}"
            )

    async def get_camera_property(self, request: MCPRequest) -> MCPResponse:
        """Get camera property."""
        device_name = request.params.get("device_name")
        property_name = request.params.get("property")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        try:
            camera = self.cameras[device_name]

            # Map property names to OpenCV constants
            property_map = {
                "width": cv2.CAP_PROP_FRAME_WIDTH,
                "height": cv2.CAP_PROP_FRAME_HEIGHT,
                "fps": cv2.CAP_PROP_FPS,
                "brightness": cv2.CAP_PROP_BRIGHTNESS,
                "contrast": cv2.CAP_PROP_CONTRAST,
                "saturation": cv2.CAP_PROP_SATURATION,
                "hue": cv2.CAP_PROP_HUE,
                "gain": cv2.CAP_PROP_GAIN,
                "exposure": cv2.CAP_PROP_EXPOSURE,
            }

            if property_name:
                if property_name not in property_map:
                    return self.create_error_response(
                        request.id,
                        MCPErrorCode.INVALID_PARAMS,
                        f"Unknown property: {property_name}",
                    )

                value = camera.get(property_map[property_name])
                return MCPResponse(
                    id=request.id,
                    result={
                        "status": "success",
                        "property": property_name,
                        "value": value,
                    },
                )
            else:
                # Get all properties
                properties = {}
                for name, prop in property_map.items():
                    properties[name] = camera.get(prop)

                return MCPResponse(
                    id=request.id,
                    result={"status": "success", "properties": properties},
                )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to get property: {e}"
            )

    async def detect_faces(self, request: MCPRequest) -> MCPResponse:
        """Detect faces in camera frame."""
        device_name = request.params.get("device_name")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        try:
            camera = self.cameras[device_name]
            ret, frame = camera.read()

            if not ret:
                return self.create_error_response(
                    request.id, MCPErrorCode.HARDWARE_ERROR, "Failed to capture frame"
                )

            # Load face detection classifier
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            # Convert results
            face_list = []
            for x, y, w, h in faces:
                face_list.append(
                    {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
                )

            # Optionally return image with faces marked
            if request.params.get("mark_faces", False):
                for x, y, w, h in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                ret, buffer = cv2.imencode(".jpg", frame)
                if ret:
                    image_base64 = base64.b64encode(buffer).decode("utf-8")
                else:
                    image_base64 = None
            else:
                image_base64 = None

            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "faces": face_list,
                    "count": len(face_list),
                    "marked_image": image_base64,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to detect faces: {e}"
            )

    async def detect_motion(self, request: MCPRequest) -> MCPResponse:
        """Detect motion between frames."""
        device_name = request.params.get("device_name")

        if not device_name or device_name not in self.cameras:
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                f"Camera {device_name} not found",
            )

        try:
            camera = self.cameras[device_name]

            # Capture two frames
            ret1, frame1 = camera.read()
            await asyncio.sleep(0.1)  # Small delay between frames
            ret2, frame2 = camera.read()

            if not (ret1 and ret2):
                return self.create_error_response(
                    request.id, MCPErrorCode.HARDWARE_ERROR, "Failed to capture frames"
                )

            # Convert to grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            # Calculate difference
            diff = cv2.absdiff(gray1, gray2)

            # Apply threshold
            threshold = request.params.get("threshold", 25)
            _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

            # Find contours
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Filter significant motion
            min_area = request.params.get("min_area", 500)
            motion_areas = []

            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    motion_areas.append(
                        {
                            "x": int(x),
                            "y": int(y),
                            "width": int(w),
                            "height": int(h),
                            "area": int(area),
                        }
                    )

            # Optionally return image with motion highlighted
            if request.params.get("mark_motion", False):
                for area in motion_areas:
                    x, y, w, h = area["x"], area["y"], area["width"], area["height"]
                    cv2.rectangle(frame2, (x, y), (x + w, y + h), (0, 255, 0), 2)

                ret, buffer = cv2.imencode(".jpg", frame2)
                if ret:
                    image_base64 = base64.b64encode(buffer).decode("utf-8")
                else:
                    image_base64 = None
            else:
                image_base64 = None

            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "motion_detected": len(motion_areas) > 0,
                    "motion_areas": motion_areas,
                    "count": len(motion_areas),
                    "marked_image": image_base64,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to detect motion: {e}"
            )

    def __del__(self):
        """Cleanup camera resources."""
        for camera in self.cameras.values():
            camera.release()
