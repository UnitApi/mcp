"""MCP Hardware Access Library."""

__version__ = "0.1.0"

from .client.client import MCPHardwareClient
from .server.base import MCPServer
from .security.permissions import PermissionManager

__all__ = [
    "MCPHardwareClient",
    "MCPServer",
    "PermissionManager",
]