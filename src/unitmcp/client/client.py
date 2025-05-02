"""
client.py
"""

"""MCP Hardware client implementation."""

import asyncio
import json
import time
from typing import Dict, Any, Optional

from ..protocols.hardware_protocol import MCPRequest, MCPResponse
from ..utils.logger import get_logger


class MCPHardwareClient:
    """Client for MCP hardware server."""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 8888, client_id: str = None
    ):
        self.host = host
        self.port = port
        self.client_id = client_id or f"client_{int(time.time())}"
        self.logger = get_logger("MCPHardwareClient")
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    async def connect(self):
        """Connect to MCP server."""
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.host, self.port
            )
            self._connected = True
            self.logger.info(f"Connected to MCP server at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._connected = False
            self.logger.info("Disconnected from MCP server")

    async def send_request(
        self, method: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send request to MCP server."""
        if not self._connected:
            await self.connect()

        # Add client ID to params
        if params is None:
            params = {}
        params["client_id"] = self.client_id

        # Create request
        request = MCPRequest(
            id=str(int(time.time() * 1000)), method=method, params=params
        )

        try:
            # Send request
            self._writer.write(request.to_json().encode() + b"\n")
            await self._writer.drain()

            # Read response
            data = await self._reader.readuntil(b"\n")
            response = MCPResponse.from_json(data.decode())

            if response.error:
                raise Exception(response.error.get("message", "Unknown error"))

            if response.result is None:
                raise Exception("Invalid response: missing both result and error.")

            return response.result

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise

    # GPIO control methods
    async def setup_pin(self, pin: int, mode: str = "OUT") -> Dict[str, Any]:
        """Setup GPIO pin."""
        return await self.send_request("gpio.setupPin", {"pin": pin, "mode": mode})

    async def write_pin(self, pin: int, value: bool) -> Dict[str, Any]:
        """Write to GPIO pin."""
        return await self.send_request("gpio.writePin", {"pin": pin, "value": value})

    async def read_pin(self, pin: int) -> Dict[str, Any]:
        """Read from GPIO pin."""
        return await self.send_request("gpio.readPin", {"pin": pin})

    async def setup_led(self, device_id: str, pin: int) -> Dict[str, Any]:
        """Setup LED device."""
        return await self.send_request(
            "gpio.setupLED", {"device_id": device_id, "pin": pin}
        )

    async def control_led(
        self, device_id: str, action: str, **kwargs
    ) -> Dict[str, Any]:
        """Control LED device."""
        params = {"device_id": device_id, "action": action}
        params.update(kwargs)
        return await self.send_request("gpio.controlLED", params)

    # Input control methods
    async def type_text(self, text: str) -> Dict[str, Any]:
        """Type text using keyboard."""
        return await self.send_request("input.typeText", {"text": text})

    async def press_key(self, key: str) -> Dict[str, Any]:
        """Press a specific key."""
        return await self.send_request("input.pressKey", {"key": key})

    async def release_key(self, key: str) -> Dict[str, Any]:
        """Release a specific key."""
        return await self.send_request("input.releaseKey", {"key": key})

    async def hotkey(self, *keys: str) -> Dict[str, Any]:
        """Execute keyboard hotkey."""
        return await self.send_request("input.hotkey", {"keys": list(keys)})

    async def move_mouse(
        self, x: int, y: int, relative: bool = False, duration: float = 0.1
    ) -> Dict[str, Any]:
        """Move mouse to coordinates."""
        return await self.send_request(
            "input.moveMouse",
            {"x": x, "y": y, "relative": relative, "duration": duration},
        )

    async def click(
        self,
        button: str = "left",
        clicks: int = 1,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform mouse click."""
        params = {"button": button, "clicks": clicks}
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y

        return await self.send_request("input.click", params)

    async def double_click(
        self, x: Optional[int] = None, y: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform double click."""
        params = {}
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y

        return await self.send_request("input.doubleClick", params)

    async def right_click(
        self, x: Optional[int] = None, y: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform right click."""
        params = {}
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y

        return await self.send_request("input.rightClick", params)

    async def scroll(self, amount: int, horizontal: bool = False) -> Dict[str, Any]:
        """Perform mouse scroll."""
        return await self.send_request(
            "input.scroll", {"amount": amount, "horizontal": horizontal}
        )

    async def drag_to(
        self, x: int, y: int, duration: float = 0.5, button: str = "left"
    ) -> Dict[str, Any]:
        """Drag mouse to coordinates."""
        return await self.send_request(
            "input.dragTo", {"x": x, "y": y, "duration": duration, "button": button}
        )

    async def get_mouse_position(self) -> Dict[str, Any]:
        """Get current mouse position."""
        return await self.send_request("input.getMousePosition")

    async def screenshot(self, region: Optional[tuple] = None) -> Dict[str, Any]:
        """Take a screenshot."""
        params = {}
        if region:
            params["region"] = region

        return await self.send_request("input.screenshot", params)

    # Context manager support
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
