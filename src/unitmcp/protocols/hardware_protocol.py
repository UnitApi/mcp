"""
hardware_protocol.py
"""

"""Hardware control protocol definitions using JSON-RPC format."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
from enum import Enum


class MCPErrorCode(Enum):
    """Standard error codes for hardware protocol."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    PERMISSION_DENIED = -32001
    HARDWARE_ERROR = -32002


@dataclass
class MCPRequest:
    """Hardware control request format."""

    id: str
    method: str
    params: Dict[str, Any]

    def to_json(self) -> str:
        """Convert request to JSON string."""
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": self.id,
                "method": self.method,
                "params": self.params,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "MCPRequest":
        """Create request from JSON string."""
        obj = json.loads(data)
        return cls(id=obj["id"], method=obj["method"], params=obj.get("params", {}))


@dataclass
class MCPResponse:
    """Hardware control response format."""

    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert response to JSON string."""
        obj = {"jsonrpc": "2.0", "id": self.id}
        if self.result is not None:
            obj["result"] = self.result
        if self.error is not None:
            obj["error"] = self.error
        return json.dumps(obj)

    @classmethod
    def from_json(cls, data: str) -> "MCPResponse":
        """Create response from JSON string."""
        obj = json.loads(data)
        return cls(id=obj["id"], result=obj.get("result"), error=obj.get("error"))
