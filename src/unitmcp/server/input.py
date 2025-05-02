"""
input.py
"""

"""Input server for keyboard and mouse control."""

import asyncio
import platform
from typing import Dict, List

from .base import MCPServer
from ..protocols.hardware_protocol import MCPRequest, MCPResponse, MCPErrorCode

# Check if tkinter is available
try:
    import tkinter

    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

# Try to import input libraries
try:
    # If tkinter is not available, we need to handle the mouseinfo import error
    if not HAS_TKINTER:
        import sys
        import types

        # Create a mock mouseinfo module to prevent pyautogui from failing
        mock_mouseinfo = types.ModuleType("mouseinfo")
        mock_mouseinfo.MouseInfo = lambda: None
        sys.modules["mouseinfo"] = mock_mouseinfo

    import pynput
    from pynput import keyboard, mouse
    from pynput.keyboard import Key, Controller as KeyboardController
    from pynput.mouse import Button, Controller as MouseController

    HAS_INPUT_LIBS = True
except ImportError:
    HAS_INPUT_LIBS = False
    pyautogui = None

    # Mock classes for environments without input libraries
    class MockController:
        def type(self, text):
            pass

        def press(self, key):
            pass

        def release(self, key):
            pass

        def position(self):
            return (0, 0)

        def move(self, x, y):
            pass

        def click(self, button, count=1):
            pass

        def scroll(self, dx, dy):
            pass

    KeyboardController = MockController
    MouseController = MockController

try:
    import pyautogui
except Exception:
    pyautogui = None
    HAS_INPUT_LIBS = False


class InputServer(MCPServer):
    """MCP server for keyboard and mouse control."""

    def __init__(self):
        super().__init__()
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.recording = False
        self.recorded_events = []

        # Configure pyautogui safety features
        if HAS_INPUT_LIBS and pyautogui:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle input requests."""
        try:
            method_parts = request.method.split(".")
            if len(method_parts) < 2:
                return self.create_error_response(
                    request.id, MCPErrorCode.METHOD_NOT_FOUND, "Invalid method format"
                )

            action = method_parts[1]

            # Map methods to handlers
            handlers = {
                "typeText": self.type_text,
                "pressKey": self.press_key,
                "releaseKey": self.release_key,
                "hotkey": self.hotkey,
                "moveMouse": self.move_mouse,
                "click": self.click,
                "doubleClick": self.double_click,
                "rightClick": self.right_click,
                "scroll": self.scroll,
                "dragTo": self.drag_to,
                "getMousePosition": self.get_mouse_position,
                "screenshot": self.screenshot,
                "startRecording": self.start_recording,
                "stopRecording": self.stop_recording,
                "playbackRecording": self.playback_recording,
            }

            if action not in handlers:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Unknown input method: {action}",
                )

            return await handlers[action](request)

        except Exception as e:
            self.logger.error(f"Input error: {e}")
            return self.create_error_response(
                request.id, MCPErrorCode.INTERNAL_ERROR, str(e)
            )

    async def type_text(self, request: MCPRequest) -> MCPResponse:
        """Type text using keyboard."""
        text = request.params.get("text")

        if not text:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing text parameter"
            )

        try:
            if HAS_INPUT_LIBS and pyautogui:
                pyautogui.typewrite(text)
            else:
                self.keyboard.type(text)

            return MCPResponse(
                id=request.id, result={"status": "success", "text": text}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to type text: {e}"
            )

    async def press_key(self, request: MCPRequest) -> MCPResponse:
        """Press a specific key."""
        key = request.params.get("key")

        if not key:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing key parameter"
            )

        try:
            if HAS_INPUT_LIBS and pyautogui:
                pyautogui.keyDown(key)
            else:
                self.keyboard.press(key)

            return MCPResponse(id=request.id, result={"status": "success", "key": key})
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to press key: {e}"
            )

    async def release_key(self, request: MCPRequest) -> MCPResponse:
        """Release a specific key."""
        key = request.params.get("key")

        if not key:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing key parameter"
            )

        try:
            if HAS_INPUT_LIBS and pyautogui:
                pyautogui.keyUp(key)
            else:
                self.keyboard.release(key)

            return MCPResponse(id=request.id, result={"status": "success", "key": key})
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to release key: {e}"
            )

    async def hotkey(self, request: MCPRequest) -> MCPResponse:
        """Execute a keyboard hotkey combination."""
        keys = request.params.get("keys", [])

        if not keys:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing keys parameter"
            )

        try:
            if HAS_INPUT_LIBS and pyautogui:
                pyautogui.hotkey(*keys)
            else:
                # Simulate hotkey with keyboard controller
                for key in keys:
                    self.keyboard.press(key)
                for key in reversed(keys):
                    self.keyboard.release(key)

            return MCPResponse(
                id=request.id, result={"status": "success", "keys": keys}
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to execute hotkey: {e}",
            )

    async def move_mouse(self, request: MCPRequest) -> MCPResponse:
        """Move mouse to specific coordinates."""
        x = request.params.get("x")
        y = request.params.get("y")
        relative = request.params.get("relative", False)
        duration = request.params.get("duration", 0.1)

        if x is None or y is None:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing x or y parameter"
            )

        try:
            if HAS_INPUT_LIBS and pyautogui:
                if relative:
                    pyautogui.moveRel(x, y, duration=duration)
                else:
                    pyautogui.moveTo(x, y, duration=duration)
            else:
                if relative:
                    current_x, current_y = self.mouse.position()
                    self.mouse.move(current_x + x, current_y + y)
                else:
                    self.mouse.move(x, y)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "x": x, "y": y, "relative": relative},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to move mouse: {e}"
            )

    async def click(self, request: MCPRequest) -> MCPResponse:
        """Perform mouse click."""
        button = request.params.get("button", "left")
        clicks = request.params.get("clicks", 1)
        x = request.params.get("x")
        y = request.params.get("y")

        try:
            if HAS_INPUT_LIBS and pyautogui:
                if x is not None and y is not None:
                    pyautogui.click(x=x, y=y, button=button, clicks=clicks)
                else:
                    pyautogui.click(button=button, clicks=clicks)
            else:
                if x is not None and y is not None:
                    self.mouse.move(x, y)

                mouse_button = (
                    Button.left
                    if button == "left"
                    else Button.right if button == "right" else Button.middle
                )
                self.mouse.click(mouse_button, clicks)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "button": button, "clicks": clicks},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to click: {e}"
            )

    async def double_click(self, request: MCPRequest) -> MCPResponse:
        """Perform double click."""
        x = request.params.get("x")
        y = request.params.get("y")

        try:
            if HAS_INPUT_LIBS and pyautogui:
                if x is not None and y is not None:
                    pyautogui.doubleClick(x=x, y=y)
                else:
                    pyautogui.doubleClick()
            else:
                if x is not None and y is not None:
                    self.mouse.move(x, y)
                self.mouse.click(Button.left, 2)

            return MCPResponse(
                id=request.id, result={"status": "success", "action": "double_click"}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to double click: {e}"
            )

    async def right_click(self, request: MCPRequest) -> MCPResponse:
        """Perform right click."""
        x = request.params.get("x")
        y = request.params.get("y")

        try:
            if HAS_INPUT_LIBS and pyautogui:
                if x is not None and y is not None:
                    pyautogui.rightClick(x=x, y=y)
                else:
                    pyautogui.rightClick()
            else:
                if x is not None and y is not None:
                    self.mouse.move(x, y)
                self.mouse.click(Button.right, 1)

            return MCPResponse(
                id=request.id, result={"status": "success", "action": "right_click"}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to right click: {e}"
            )

    async def scroll(self, request: MCPRequest) -> MCPResponse:
        """Perform mouse scroll."""
        amount = request.params.get("amount", 0)
        horizontal = request.params.get("horizontal", False)

        try:
            if HAS_INPUT_LIBS and pyautogui:
                if horizontal:
                    pyautogui.hscroll(amount)
                else:
                    pyautogui.scroll(amount)
            else:
                if horizontal:
                    self.mouse.scroll(amount, 0)
                else:
                    self.mouse.scroll(0, amount)

            return MCPResponse(
                id=request.id,
                result={
                    "status": "success",
                    "amount": amount,
                    "horizontal": horizontal,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to scroll: {e}"
            )

    async def drag_to(self, request: MCPRequest) -> MCPResponse:
        """Drag mouse to specific coordinates."""
        x = request.params.get("x")
        y = request.params.get("y")
        duration = request.params.get("duration", 0.5)
        button = request.params.get("button", "left")

        if x is None or y is None:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing x or y parameter"
            )

        try:
            if HAS_INPUT_LIBS and pyautogui:
                pyautogui.dragTo(x, y, duration=duration, button=button)
            else:
                mouse_button = (
                    Button.left
                    if button == "left"
                    else Button.right if button == "right" else Button.middle
                )
                self.mouse.press(mouse_button)
                await asyncio.sleep(0.1)
                self.mouse.move(x, y)
                await asyncio.sleep(0.1)
                self.mouse.release(mouse_button)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "x": x, "y": y, "button": button},
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to drag: {e}"
            )

    async def get_mouse_position(self, request: MCPRequest) -> MCPResponse:
        """Get current mouse position."""
        try:
            if HAS_INPUT_LIBS and pyautogui:
                x, y = pyautogui.position()
            else:
                x, y = self.mouse.position()

            return MCPResponse(
                id=request.id, result={"status": "success", "x": x, "y": y}
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to get mouse position: {e}",
            )

    async def screenshot(self, request: MCPRequest) -> MCPResponse:
        """Take a screenshot."""
        region = request.params.get("region")  # (x, y, width, height)

        try:
            if HAS_INPUT_LIBS and pyautogui:
                if region:
                    screenshot = pyautogui.screenshot(region=region)
                else:
                    screenshot = pyautogui.screenshot()

                # Convert to base64 for transport
                import io
                import base64

                buffer = io.BytesIO()
                screenshot.save(buffer, format="PNG")
                image_data = base64.b64encode(buffer.getvalue()).decode()

                return MCPResponse(
                    id=request.id,
                    result={
                        "status": "success",
                        "image_data": image_data,
                        "format": "png",
                    },
                )
            else:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.HARDWARE_ERROR,
                    "Screenshot functionality not available",
                )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to take screenshot: {e}",
            )

    async def start_recording(self, request: MCPRequest) -> MCPResponse:
        """Start recording input events."""
        if self.recording:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Already recording"
            )

        self.recording = True
        self.recorded_events = []

        return MCPResponse(
            id=request.id, result={"status": "success", "message": "Recording started"}
        )

    async def stop_recording(self, request: MCPRequest) -> MCPResponse:
        """Stop recording input events."""
        if not self.recording:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Not recording"
            )

        self.recording = False
        events = self.recorded_events.copy()

        return MCPResponse(
            id=request.id,
            result={"status": "success", "events": events, "count": len(events)},
        )

    async def playback_recording(self, request: MCPRequest) -> MCPResponse:
        """Playback recorded input events."""
        events = request.params.get("events", self.recorded_events)
        speed = request.params.get("speed", 1.0)

        if not events:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "No events to playback"
            )

        try:
            for event in events:
                event_type = event.get("type")
                if event_type == "keyboard":
                    await self.type_text(
                        MCPRequest(
                            id=request.id,
                            method="input.typeText",
                            params={"text": event.get("text", "")},
                        )
                    )
                elif event_type == "mouse_move":
                    await self.move_mouse(
                        MCPRequest(
                            id=request.id,
                            method="input.moveMouse",
                            params={"x": event.get("x", 0), "y": event.get("y", 0)},
                        )
                    )
                elif event_type == "mouse_click":
                    await self.click(
                        MCPRequest(
                            id=request.id,
                            method="input.click",
                            params={
                                "button": event.get("button", "left"),
                                "x": event.get("x"),
                                "y": event.get("y"),
                            },
                        )
                    )

                # Delay between events
                delay = event.get("delay", 0.1) / speed
                await asyncio.sleep(delay)

            return MCPResponse(
                id=request.id,
                result={"status": "success", "events_played": len(events)},
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to playback recording: {e}",
            )
