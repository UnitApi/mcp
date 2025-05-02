"""Hardware Protocol definitions."""

__version__ = "0.1.0"

from .hardware_protocol import MCPRequest, MCPResponse, MCPErrorCode


# Import LLMMCPHardwareServer lazily to avoid circular imports
def get_llm_mcp_hardware_server():
    from .llm_mcp import LLMMCPHardwareServer

    return LLMMCPHardwareServer


__all__ = [
    "MCPRequest",
    "MCPResponse",
    "MCPErrorCode",
    "get_llm_mcp_hardware_server",
]
