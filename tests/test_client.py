import os
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock

from unitmcp.client.client import MCPHardwareClient

# Check if we should skip tkinter tests
SKIP_TKINTER_TESTS = os.environ.get("unitmcp_SKIP_TKINTER_TESTS") == "1"


class TestMCPHardwareClient:
    """Test MCPHardwareClient class."""

    @pytest.fixture
    def client(self):
        """Create client for testing."""
        return MCPHardwareClient(host="127.0.0.1", port=8889)

    @pytest.mark.asyncio
    async def test_connect(self, client):
        """Test client connection."""
        with patch("asyncio.open_connection") as mock_open:
            mock_reader = Mock()
            mock_writer = Mock()
            mock_open.return_value = (mock_reader, mock_writer)

            await client.connect()

            assert client._connected is True
            assert client._reader == mock_reader
            assert client._writer == mock_writer
            mock_open.assert_called_once_with("127.0.0.1", 8889)

    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Test client disconnection."""
        # Mock writer
        mock_writer = Mock()
        mock_writer.wait_closed = AsyncMock()
        client._writer = mock_writer
        client._connected = True

        await client.disconnect()

        assert client._connected is False
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_request(self, client):
        """Test sending request to server."""
        # Mock connection
        mock_reader = Mock()
        mock_writer = Mock()
        mock_reader.readuntil = AsyncMock()
        mock_writer.drain = AsyncMock()

        # Mock response
        response_data = {
            "jsonrpc": "2.0",
            "id": "test123",
            "result": {"status": "success"},
        }
        mock_reader.readuntil.return_value = json.dumps(response_data).encode() + b"\n"

        client._reader = mock_reader
        client._writer = mock_writer
        client._connected = True

        # Send request
        await client.send_request("test.method", {"param": "value"})

        # Verify
        mock_writer.write.assert_called_once()
        mock_writer.drain.assert_called_once()
        mock_reader.readuntil.assert_called_once_with(b"\n")

        # Check request format
        written_data = mock_writer.write.call_args[0][0]
        request_dict = json.loads(written_data.decode().strip())
        assert request_dict["method"] == "test.method"
        assert request_dict["params"]["param"] == "value"
        assert request_dict["params"]["client_id"] == client.client_id

    @pytest.mark.asyncio
    async def test_send_request_error(self, client):
        """Test handling error response."""
        # Mock connection
        mock_reader = Mock()
        mock_writer = Mock()
        mock_reader.readuntil = AsyncMock()
        mock_writer.drain = AsyncMock()

        # Mock error response
        response_data = {
            "jsonrpc": "2.0",
            "id": "test123",
            "error": {"code": -32600, "message": "Invalid request"},
        }
        mock_reader.readuntil.return_value = json.dumps(response_data).encode() + b"\n"

        client._reader = mock_reader
        client._writer = mock_writer
        client._connected = True

        # Send request and expect exception
        with pytest.raises(Exception, match="Invalid request"):
            await client.send_request("test.method", {})

    @pytest.mark.asyncio
    async def test_send_request_invalid_response(self, client):
        """Test sending request with invalid server response (no result or error)."""
        mock_reader = Mock()
        mock_writer = Mock()
        mock_reader.readuntil = AsyncMock()
        mock_writer.drain = AsyncMock()
        # Response missing both result and error
        response_data = {"jsonrpc": "2.0", "id": "test123"}
        mock_reader.readuntil.return_value = json.dumps(response_data).encode() + b"\n"
        client._reader = mock_reader
        client._writer = mock_writer
        client._connected = True
        with pytest.raises(Exception):
            await client.send_request("test.method", {})

    @pytest.mark.asyncio
    async def test_multiple_connect_disconnect(self, client):
        """Test multiple connect/disconnect calls."""
        with patch("asyncio.open_connection") as mock_open:
            mock_reader = Mock()
            mock_writer = Mock()
            mock_writer.wait_closed = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)
            await client.connect()
            await client.disconnect()
            # Connect again
            await client.connect()
            await client.disconnect()
            assert mock_open.call_count == 2
            assert mock_writer.close.call_count == 2
            assert mock_writer.wait_closed.call_count == 2

    @pytest.mark.asyncio
    async def test_unsupported_method(self, client):
        """Test sending request to unsupported method."""
        mock_reader = Mock()
        mock_writer = Mock()
        mock_reader.readuntil = AsyncMock()
        mock_writer.drain = AsyncMock()
        # Simulate error for unsupported method
        response_data = {
            "jsonrpc": "2.0",
            "id": "test123",
            "error": {"code": -32601, "message": "Method not found"},
        }
        mock_reader.readuntil.return_value = json.dumps(response_data).encode() + b"\n"
        client._reader = mock_reader
        client._writer = mock_writer
        client._connected = True
        with pytest.raises(Exception, match="Method not found"):
            await client.send_request("nonexistent.method", {})

    @pytest.mark.asyncio
    async def test_send_request_timeout(self, client):
        """Test send_request handles timeout during readuntil."""
        mock_reader = Mock()
        mock_writer = Mock()
        mock_writer.drain = AsyncMock()

        # Simulate timeout
        async def raise_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()

        mock_reader.readuntil = AsyncMock(side_effect=raise_timeout)
        client._reader = mock_reader
        client._writer = mock_writer
        client._connected = True
        with pytest.raises(asyncio.TimeoutError):
            await client.send_request("test.method", {})

    @pytest.mark.asyncio
    async def test_gpio_methods(self, client):
        """Test GPIO control methods."""
        with patch.object(client, "send_request") as mock_send:
            mock_send.return_value = {"status": "success"}

            # Test setup_pin
            await client.setup_pin(17, "OUT")
            mock_send.assert_called_with("gpio.setupPin", {"pin": 17, "mode": "OUT"})

            # Test write_pin
            await client.write_pin(17, True)
            mock_send.assert_called_with("gpio.writePin", {"pin": 17, "value": True})

            # Test read_pin
            await client.read_pin(17)
            mock_send.assert_called_with("gpio.readPin", {"pin": 17})

    @pytest.mark.asyncio
    async def test_led_methods(self, client):
        """Test LED control methods."""
        with patch.object(client, "send_request") as mock_send:
            mock_send.return_value = {"status": "success"}

            # Test setup_led
            await client.setup_led("led1", 17)
            mock_send.assert_called_with(
                "gpio.setupLED", {"device_id": "led1", "pin": 17}
            )

            # Test control_led
            await client.control_led("led1", "blink", on_time=0.5, off_time=0.5)
            mock_send.assert_called_with(
                "gpio.controlLED",
                {
                    "device_id": "led1",
                    "action": "blink",
                    "on_time": 0.5,
                    "off_time": 0.5,
                },
            )

    @pytest.mark.asyncio
    async def test_input_methods(self, client):
        """Test input control methods."""
        with patch.object(client, "send_request") as mock_send:
            mock_send.return_value = {"status": "success"}

            # Test type_text
            await client.type_text("Hello World")
            mock_send.assert_called_with("input.typeText", {"text": "Hello World"})

            # Test move_mouse
            await client.move_mouse(100, 200, relative=True, duration=0.5)
            mock_send.assert_called_with(
                "input.moveMouse",
                {"x": 100, "y": 200, "relative": True, "duration": 0.5},
            )

            # Test click
            await client.click("right", clicks=2, x=300, y=400)
            mock_send.assert_called_with(
                "input.click", {"button": "right", "clicks": 2, "x": 300, "y": 400}
            )

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager."""
        with patch.object(client, "connect") as mock_connect:
            with patch.object(client, "disconnect") as mock_disconnect:
                mock_connect.return_value = None
                mock_disconnect.return_value = None

                async with client as c:
                    assert c == client

                mock_connect.assert_called_once()
                mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skipif(SKIP_TKINTER_TESTS, reason="Tkinter not available")
    async def test_screenshot(self, client):
        """Test screenshot method."""
        with patch.object(client, "send_request") as mock_send:
            mock_send.return_value = {"status": "success", "image_data": "base64data"}

            # Test without region
            await client.screenshot()
            mock_send.assert_called_with("input.screenshot", {})

            # Test with region
            await client.screenshot(region=(0, 0, 800, 600))
            mock_send.assert_called_with(
                "input.screenshot", {"region": (0, 0, 800, 600)}
            )

    @pytest.mark.asyncio
    @pytest.mark.skipif(SKIP_TKINTER_TESTS, reason="Tkinter not available")
    async def test_hotkey(self, client):
        """Test hotkey method."""
        with patch.object(client, "send_request") as mock_send:
            mock_send.return_value = {"status": "success"}

            await client.hotkey("ctrl", "alt", "del")
            mock_send.assert_called_with(
                "input.hotkey", {"keys": ["ctrl", "alt", "del"]}
            )

    @pytest.mark.asyncio
    async def test_connection_error(self, client):
        """Test connection error handling."""
        with patch("asyncio.open_connection") as mock_open:
            mock_open.side_effect = ConnectionRefusedError("Connection refused")

            with pytest.raises(ConnectionRefusedError):
                await client.connect()

    @pytest.mark.asyncio
    async def test_auto_connect(self, client):
        """Test automatic connection on send_request."""
        assert client._connected is False

        with patch.object(client, "connect") as mock_connect:
            with patch.object(client, "_writer") as mock_writer:
                with patch.object(client, "_reader") as mock_reader:
                    mock_connect.return_value = None
                    mock_writer.drain = AsyncMock()
                    mock_reader.readuntil = AsyncMock()

                    # Mock response
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": "test123",
                        "result": {"status": "success"},
                    }
                    mock_reader.readuntil.return_value = (
                        json.dumps(response_data).encode() + b"\n"
                    )

                    # Should auto-connect
                    await client.send_request("test.method", {})

                    mock_connect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
