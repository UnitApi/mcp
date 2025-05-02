"""
Unit MCP Hardware Access Library

This library provides access to hardware resources through the Model Context Protocol (MCP).
It allows for controlling GPIO pins and other hardware components through various transport
protocols like HTTP, WebSockets, and MQTT.
"""

from .hardware_client import MCPHardwareClient
from .server import MCPServer

__version__ = "0.1.0"
