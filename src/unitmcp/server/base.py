"""
base.py
"""

"""Base MCP server implementation."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..protocols.hardware_protocol import MCPRequest, MCPResponse, MCPErrorCode
from ..security.permissions import PermissionManager
from ..utils.logger import get_logger


class MCPServer(ABC):
    """Base class for MCP servers."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.permission_manager = permission_manager or PermissionManager()

    @abstractmethod
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming request."""
        pass

    def check_permission(self, client_id: str, resource: str) -> bool:
        """Check if client has permission to access resource."""
        return self.permission_manager.check_permission(client_id, resource)

    def create_error_response(
        self, request_id: str, code: MCPErrorCode, message: str
    ) -> MCPResponse:
        """Create error response."""
        return MCPResponse(
            id=request_id, error={"code": code.value, "message": message}
        )


class MCPHardwareServer:
    """Main MCP hardware server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8888,
        permission_manager: Optional[PermissionManager] = None,
    ):
        self.host = host
        self.port = port
        self.permission_manager = permission_manager or PermissionManager()
        self.logger = get_logger("MCPHardwareServer")
        self.servers: Dict[str, MCPServer] = {}
        self._running = False

    def register_server(self, prefix: str, server: MCPServer):
        """Register a hardware server."""
        self.servers[prefix] = server
        server.permission_manager = self.permission_manager
        self.logger.info(f"Registered server for prefix: {prefix}")

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle incoming client connection."""
        client_addr = writer.get_extra_info("peername")
        self.logger.info(f"New client connected: {client_addr}")

        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break

                try:
                    # Parse request
                    request = MCPRequest.from_json(data.decode())
                    self.logger.debug(f"Received request: {request.method}")

                    # Extract client ID
                    client_id = request.params.get("client_id", "unknown")

                    # Route request to appropriate server
                    prefix = request.method.split(".")[0]

                    if prefix not in self.servers:
                        response = MCPResponse(
                            id=request.id,
                            error={
                                "code": MCPErrorCode.METHOD_NOT_FOUND.value,
                                "message": f"No server for prefix: {prefix}",
                            },
                        )
                    else:
                        # Check permissions
                        if not self.permission_manager.check_permission(
                            client_id, prefix
                        ):
                            response = MCPResponse(
                                id=request.id,
                                error={
                                    "code": MCPErrorCode.PERMISSION_DENIED.value,
                                    "message": f"Permission denied for {prefix}",
                                },
                            )
                        else:
                            server = self.servers[prefix]
                            response = await server.handle_request(request)

                    # Send response
                    writer.write(response.to_json().encode())
                    await writer.drain()

                except json.JSONDecodeError:
                    self.logger.error("Invalid JSON received")
                    error_response = MCPResponse(
                        id="unknown",
                        error={
                            "code": MCPErrorCode.PARSE_ERROR.value,
                            "message": "Invalid JSON",
                        },
                    )
                    writer.write(error_response.to_json().encode())
                    await writer.drain()
                except Exception as e:
                    self.logger.error(f"Error handling request: {e}")
                    error_response = MCPResponse(
                        id=request.id if "request" in locals() else "unknown",
                        error={
                            "code": MCPErrorCode.INTERNAL_ERROR.value,
                            "message": str(e),
                        },
                    )
                    writer.write(error_response.to_json().encode())
                    await writer.drain()

        except Exception as e:
            self.logger.error(f"Client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.logger.info(f"Client disconnected: {client_addr}")

    async def start(self):
        """Start the MCP server."""
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        self._running = True
        self.logger.info(f"MCP Hardware Server started on {self.host}:{self.port}")

        async with server:
            await server.serve_forever()

    def stop(self):
        """Stop the server."""
        self._running = False
        self.logger.info("Server stopping...")
