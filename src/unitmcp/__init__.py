"""MCP Hardware Access Library."""

__version__ = "0.1.16"

from .client.client import MCPHardwareClient
from .client.shell import MCPShell
from .server.base import MCPServer
from .security.permissions import PermissionManager
from .pipeline.pipeline import Pipeline, PipelineManager

__all__ = [
    "MCPHardwareClient",
    "MCPShell",
    "MCPServer",
    "PermissionManager",
    "Pipeline",
    "PipelineManager",
]
