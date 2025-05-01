"""Start MCP Hardware server with all components."""

import asyncio
import argparse
from unitmcp import MCPServer, PermissionManager
from unitmcp.server import (
    GPIOServer, InputServer, AudioServer, CameraServer
)


async def start_server(host="127.0.0.1", port=8888, components=None):
    """Start the MCP Hardware server."""
    # Create permission manager
    permission_manager = PermissionManager()

    # Grant default permissions (adjust as needed)
    permission_manager.grant_permission("client_*", "gpio")
    permission_manager.grant_permission("client_*", "input")
    permission_manager.grant_permission("client_*", "audio")
    permission_manager.grant_permission("client_*", "camera")

    # Create main server
    server = MCPServer(host=host, port=port, permission_manager=permission_manager)

    # Register components
    if components is None or "gpio" in components:
        server.register_server("gpio", GPIOServer())
        print("✓ GPIO server registered")

    if components is None or "input" in components:
        server.register_server("input", InputServer())
        print("✓ Input server registered")

    if components is None or "audio" in components:
        server.register_server("audio", AudioServer())
        print("✓ Audio server registered")

    if components is None or "camera" in components:
        server.register_server("camera", CameraServer())
        print("✓ Camera server registered")

    # Start server
    print(f"\nStarting MCP Hardware Server on {host}:{port}")
    print("Press Ctrl+C to stop")

    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Hardware Server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8888, help="Server port")
    parser.add_argument("--components", nargs="+",
                        choices=["gpio", "input", "audio", "camera"],
                        help="Components to enable (default: all)")

    args = parser.parse_args()

    asyncio.run(start_server(args.host, args.port, args.components))