"""
test_server.py
"""

"""Tests for MCP server functionality."""

import os
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock

from unitmcp.protocols.hardware_protocol import MCPRequest, MCPResponse
from unitmcp.server.base import MCPServer, MCPHardwareServer
from unitmcp.server.gpio import GPIOServer
from unitmcp.server.input import InputServer, HAS_INPUT_LIBS
from unitmcp.security.permissions import PermissionManager

# Check if we should skip tkinter tests
SKIP_TKINTER_TESTS = os.environ.get("unitmcp_SKIP_TKINTER_TESTS") == "1"


class TestMCPServer:
    """Test MCPServer base class."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock server for testing."""

        class MockServer(MCPServer):
            async def handle_request(self, request):
                return MCPResponse(id=request.id, result={"echo": request.params})

        return MockServer()

    def test_server_initialization(self, mock_server):
        """Test server initialization."""
        assert mock_server.permission_manager is not None
        assert mock_server.logger is not None

    def test_check_permission(self, mock_server):
        """Test permission checking."""
        mock_server.permission_manager.grant_permission("client1", "test")
        assert mock_server.check_permission("client1", "test") is True
        assert mock_server.check_permission("client2", "test") is False

    @pytest.mark.asyncio
    async def test_handle_request(self, mock_server):
        """Test request handling."""
        request = MCPRequest(
            id="test123", method="test.echo", params={"message": "hello"}
        )

        response = await mock_server.handle_request(request)
        assert response.id == "test123"
        assert response.result["echo"]["message"] == "hello"


class TestMCPHardwareServer:
    """Test MCPHardwareServer class."""

    @pytest.fixture
    def hardware_server(self):
        """Create hardware server for testing."""
        return MCPHardwareServer(host="127.0.0.1", port=8889)

    def test_register_server(self, hardware_server):
        """Test server registration."""
        gpio_server = GPIOServer()
        hardware_server.register_server("gpio", gpio_server)

        assert "gpio" in hardware_server.servers
        assert hardware_server.servers["gpio"] == gpio_server

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)  # Add a 5-second timeout to prevent hanging
    @pytest.mark.skipif(SKIP_TKINTER_TESTS, reason="Tkinter not available")
    async def test_handle_client_request(self, hardware_server):
        """Test client request handling."""
        # Register a mock server
        mock_server = Mock(spec=MCPServer)
        mock_server.handle_request = AsyncMock(
            return_value=MCPResponse(id="test123", result={"status": "success"})
        )
        hardware_server.register_server("test", mock_server)

        # Grant permission
        hardware_server.permission_manager.grant_permission("client1", "test")

        # Mock reader and writer
        reader = AsyncMock()
        # First read returns data, second read returns empty to terminate the loop
        reader.read.side_effect = [
            json.dumps(
                {
                    "id": "test123",
                    "method": "test.action",
                    "params": {"client_id": "client1"},
                }
            ).encode(),
            b"",  # Empty data to terminate the loop
        ]

        writer = Mock()
        writer.get_extra_info.return_value = "127.0.0.1:12345"
        writer.write = Mock()
        writer.drain = AsyncMock()
        writer.close = Mock()
        writer.wait_closed = AsyncMock()

        # Handle client request
        await hardware_server.handle_client(reader, writer)

        # Verify server was called
        mock_server.handle_request.assert_called_once()
        writer.write.assert_called_once()
        writer.close.assert_called_once()
        writer.wait_closed.assert_called_once()


class TestGPIOServer:
    """Test GPIO server functionality."""

    @pytest.fixture
    def gpio_server(self):
        """Create GPIO server for testing."""
        return GPIOServer()

    @pytest.mark.asyncio
    async def test_setup_pin(self, gpio_server):
        """Test GPIO pin setup."""
        request = MCPRequest(
            id="test123", method="gpio.setupPin", params={"pin": 17, "mode": "OUT"}
        )

        with patch("unitmcp.server.gpio.GPIO") as mock_gpio:
            response = await gpio_server.handle_request(request)

            assert response.result["status"] == "success"
            assert response.result["pin"] == 17
            mock_gpio.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_pin(self, gpio_server):
        """Test GPIO pin write."""
        request = MCPRequest(
            id="test123", method="gpio.writePin", params={"pin": 17, "value": True}
        )

        with patch("unitmcp.server.gpio.GPIO") as mock_gpio:
            response = await gpio_server.handle_request(request)

            assert response.result["status"] == "success"
            mock_gpio.output.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_led(self, gpio_server):
        """Test LED setup."""
        request = MCPRequest(
            id="test123",
            method="gpio.setupLED",
            params={"device_id": "led1", "pin": 17},
        )

        with patch("unitmcp.server.gpio.LED") as mock_led:
            response = await gpio_server.handle_request(request)

            assert response.result["status"] == "success"
            assert "led1" in gpio_server.devices
            mock_led.assert_called_once_with(17)


class TestInputServer:
    """Test input server functionality."""

    @pytest.fixture
    def input_server(self):
        """Create input server for testing."""
        return InputServer()

    @pytest.mark.asyncio
    async def test_type_text(self, input_server):
        """Test typing text."""
        request = MCPRequest(
            id="test123", method="input.typeText", params={"text": "Hello World"}
        )

        with patch("unitmcp.server.input.pyautogui") as mock_pyautogui:
            response = await input_server.handle_request(request)

            assert response.result["status"] == "success"
            assert response.result["text"] == "Hello World"
            mock_pyautogui.typewrite.assert_called_once_with("Hello World")

    @pytest.mark.asyncio
    async def test_move_mouse(self, input_server):
        """Test mouse movement."""
        request = MCPRequest(
            id="test123",
            method="input.moveMouse",
            params={"x": 100, "y": 200, "duration": 0.1},
        )

        with patch("unitmcp.server.input.pyautogui") as mock_pyautogui:
            response = await input_server.handle_request(request)

            assert response.result["status"] == "success"
            assert response.result["x"] == 100
            assert response.result["y"] == 200
            mock_pyautogui.moveTo.assert_called_once_with(100, 200, duration=0.1)

    @pytest.mark.asyncio
    async def test_click(self, input_server):
        """Test mouse click."""
        request = MCPRequest(
            id="test123",
            method="input.click",
            params={"button": "left", "x": 100, "y": 200},
        )

        with patch("unitmcp.server.input.pyautogui") as mock_pyautogui:
            response = await input_server.handle_request(request)

            assert response.result["status"] == "success"
            mock_pyautogui.click.assert_called_once_with(
                x=100, y=200, button="left", clicks=1
            )


if __name__ == "__main__":
    pytest.main([__file__])
