"""MCP Protocol definitions."""

__version__ = "0.1.0"

from .mcp import MCPRequest, MCPResponse, MCPErrorCode

__all__ = [
    "MCPRequest",
    "MCPResponse",
    "MCPErrorCode",
]
