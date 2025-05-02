#!/usr/bin/env python3

import unitmcp.server
import asyncio

async def main():
    server = unitmcp.server.MCPHardwareServer(host="127.0.0.1", port=8888)
    server.register_server("gpio", unitmcp.server.GPIOServer())
    server.register_server("input", unitmcp.server.InputServer())
    server.register_server("audio", unitmcp.server.AudioServer())
    server.register_server("camera", unitmcp.server.CameraServer())
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
