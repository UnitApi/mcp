"""
llm_mcp.py
"""

"""Integration of MCP Python SDK for LLM-based hardware control."""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Callable, Awaitable

from mcp.server.fastmcp import FastMCP, Context

# Import MCPHardwareClient lazily to avoid circular imports
from ..utils.logger import get_logger

# Configure logging
logger = get_logger("LLM_MCP")


class LLMMCPHardwareServer:
    """
    LLM MCP Hardware Server.

    This class integrates the MCP Python SDK with the unitmcp hardware control system,
    allowing LLMs to control hardware through natural language.
    """

    def __init__(
        self,
        server_name: str,
        rpi_host: str = "localhost",
        rpi_port: int = 8080,
        dependencies: Optional[List[str]] = None,
    ):
        """
        Initialize the LLM MCP Hardware Server.

        Args:
            server_name: Name of the MCP server
            rpi_host: Hostname or IP address of the Raspberry Pi
            rpi_port: Port number of the Raspberry Pi MCP server
            dependencies: List of Python package dependencies
        """
        self.server_name = server_name
        self.rpi_host = rpi_host
        self.rpi_port = rpi_port
        self.dependencies = dependencies or []

        # Create FastMCP server
        self.mcp = FastMCP(server_name, dependencies=self.dependencies)

        # Hardware client instance (lazy initialization)
        self._hardware_client = None

        # Register default tools
        self._register_default_tools()

    async def get_hardware_client(self):
        """
        Get or create the hardware client.

        Returns:
            MCPHardwareClient: The hardware client instance
        """
        # Import MCPHardwareClient lazily to avoid circular imports
        from ..client.client import MCPHardwareClient

        if self._hardware_client is None or not getattr(
            self._hardware_client, "is_connected", False
        ):
            self._hardware_client = MCPHardwareClient(self.rpi_host, self.rpi_port)
            await self._hardware_client.connect()

        return self._hardware_client

    def _register_default_tools(self):
        """Register default hardware control tools."""

        @self.mcp.tool()
        async def control_led(pin: int, state: str) -> Dict[str, Any]:
            """
            Control an LED connected to a GPIO pin.

            Args:
                pin: The GPIO pin number the LED is connected to
                state: The desired state ('on', 'off', or 'blink')

            Returns:
                A dictionary with the result of the operation
            """
            client = await self.get_hardware_client()

            try:
                # Set up the pin as output
                await client.setup_pin(pin, "output")

                if state.lower() == "on":
                    await client.write_pin(pin, 1)
                    return {"success": True, "message": f"LED on pin {pin} turned on"}
                elif state.lower() == "off":
                    await client.write_pin(pin, 0)
                    return {"success": True, "message": f"LED on pin {pin} turned off"}
                elif state.lower() == "blink":
                    # Blink 3 times
                    for _ in range(3):
                        await client.write_pin(pin, 1)
                        await asyncio.sleep(0.5)
                        await client.write_pin(pin, 0)
                        await asyncio.sleep(0.5)
                    return {
                        "success": True,
                        "message": f"LED on pin {pin} blinked 3 times",
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Unknown state: {state}. Use 'on', 'off', or 'blink'",
                    }
            except Exception as e:
                logger.error(f"Error controlling LED: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}

        @self.mcp.tool()
        async def record_audio(
            duration: int = 3, sample_rate: int = 44100, channels: int = 1
        ) -> Dict[str, Any]:
            """
            Record audio using the Raspberry Pi's microphone.

            Args:
                duration: Recording duration in seconds
                sample_rate: Audio sample rate
                channels: Number of audio channels (1 for mono, 2 for stereo)

            Returns:
                A dictionary with the result of the operation
            """
            client = await self.get_hardware_client()

            try:
                params = {
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "channels": channels,
                }

                logger.info(f"Recording audio for {duration} seconds...")
                result = await client.send_request("audio.record", params)

                if result.get("success", True):
                    return {
                        "success": True,
                        "message": f"Audio recorded successfully for {duration} seconds",
                        "details": result,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Recording failed: {result.get('message', 'Unknown error')}",
                        "details": result,
                    }
            except Exception as e:
                logger.error(f"Error recording audio: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}

        @self.mcp.tool()
        async def play_audio(file_path: str) -> Dict[str, Any]:
            """
            Play an audio file on the Raspberry Pi.

            Args:
                file_path: Path to the audio file (.wav or .mp3)

            Returns:
                A dictionary with the result of the operation
            """
            client = await self.get_hardware_client()

            try:
                params = {"file_path": file_path}

                logger.info(f"Playing audio file: {file_path}")
                result = await client.send_request("audio.play", params)

                if result.get("success", True):
                    return {
                        "success": True,
                        "message": f"Audio played successfully: {file_path}",
                        "details": result,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Playing audio failed: {result.get('message', 'Unknown error')}",
                        "details": result,
                    }
            except Exception as e:
                logger.error(f"Error playing audio: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}

        @self.mcp.tool()
        async def get_sensor_reading(
            sensor_type: str, pin: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Get a reading from a sensor connected to the Raspberry Pi.

            Args:
                sensor_type: Type of sensor ('temperature', 'humidity', 'motion', etc.)
                pin: GPIO pin number the sensor is connected to (if applicable)

            Returns:
                A dictionary with the sensor reading
            """
            client = await self.get_hardware_client()

            try:
                params = {"sensor_type": sensor_type}

                if pin is not None:
                    params["pin"] = pin

                logger.info(f"Getting {sensor_type} sensor reading...")
                result = await client.send_request("sensor.read", params)

                if result.get("success", True):
                    return {
                        "success": True,
                        "sensor_type": sensor_type,
                        "reading": result.get("reading"),
                        "unit": result.get("unit"),
                        "message": f"Successfully read {sensor_type} sensor",
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Sensor reading failed: {result.get('message', 'Unknown error')}",
                        "details": result,
                    }
            except Exception as e:
                logger.error(f"Error getting sensor reading: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}

        @self.mcp.tool()
        async def list_available_hardware() -> Dict[str, Any]:
            """
            List all available hardware devices connected to the Raspberry Pi.

            Returns:
                A dictionary with the list of available hardware
            """
            client = await self.get_hardware_client()

            try:
                result = await client.send_request("hardware.list", {})

                if result.get("success", True):
                    return {
                        "success": True,
                        "devices": result.get("devices", []),
                        "message": "Successfully listed available hardware",
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to list hardware: {result.get('message', 'Unknown error')}",
                        "details": result,
                    }
            except Exception as e:
                logger.error(f"Error listing hardware: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}

        @self.mcp.resource("hardware://status")
        async def get_hardware_status() -> str:
            """
            Get the current status of the hardware system.

            Returns:
                A string with the current hardware status
            """
            client = await self.get_hardware_client()

            try:
                result = await client.send_request("system.status", {})

                if result.get("success", True):
                    status_data = result.get("status", {})

                    # Format the status information as a string
                    status_lines = [
                        "# Hardware System Status",
                        "",
                        f"- Connected to: {self.rpi_host}:{self.rpi_port}",
                        f"- System uptime: {status_data.get('uptime', 'Unknown')}",
                        f"- CPU temperature: {status_data.get('cpu_temp', 'Unknown')}",
                        f"- Memory usage: {status_data.get('memory_usage', 'Unknown')}",
                        f"- Disk usage: {status_data.get('disk_usage', 'Unknown')}",
                        "",
                        "## Connected Devices",
                    ]

                    # Add connected devices
                    devices = status_data.get("devices", [])
                    if devices:
                        for device in devices:
                            status_lines.append(
                                f"- {device.get('name')}: {device.get('status')}"
                            )
                    else:
                        status_lines.append("- No devices connected")

                    return "\n".join(status_lines)
                else:
                    return f"Error getting hardware status: {result.get('message', 'Unknown error')}"
            except Exception as e:
                logger.error(f"Error getting hardware status: {e}")
                return f"Error getting hardware status: {str(e)}"

    def register_tool(self, func: Callable) -> Callable:
        """
        Register a custom tool with the MCP server.

        Args:
            func: The function to register as a tool

        Returns:
            The registered function
        """
        return self.mcp.tool()(func)

    def register_resource(self, uri_template: str) -> Callable:
        """
        Register a custom resource with the MCP server.

        Args:
            uri_template: The URI template for the resource

        Returns:
            A decorator that registers the function as a resource
        """
        return self.mcp.resource(uri_template)

    def run(self):
        """Run the MCP server."""
        self.mcp.run()

    async def run_async(self):
        """Run the MCP server asynchronously."""
        await self.mcp.run_async()

    def get_sse_app(self):
        """Get the SSE app for the MCP server."""
        return self.mcp.sse_app()
