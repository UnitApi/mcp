#!/usr/bin/env python3

import unitmcp
import asyncio

async def main():
    try:
        try:
            async with unitmcp.MCPHardwareClient() as client:
                await client.control_led("led1", "on")
        except ConnectionRefusedError as e:
            print(f"Could not connect to MCP hardware server: {e}")
            # Optionally: mock response or skip test logic here
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())