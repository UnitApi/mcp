#!/usr/bin/env python3
"""
LED Control Example

This example demonstrates how to control an LED using the MCP Hardware Client.
"""

import logging
import asyncio
import os
from unitmcp import MCPHardwareClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to demonstrate LED control.
    """
    client = MCPHardwareClient(RPI_HOST, RPI_PORT)
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to the MCP server: {e}")
        return
    try:
        pin = 17
        logger.info(f"Setting up GPIO pin {pin} as output")
        result = await client.setup_pin(pin, "output")
        logger.info(f"Setup result: {result}")

        logger.info("Turning on the LED")
        result = await client.control_led("led1", "on")
        logger.info(f"Control result: {result}")

        await asyncio.sleep(2)

        logger.info("Blinking the LED")
        for _ in range(5):
            await client.write_pin(pin, 1)
            await asyncio.sleep(0.5)
            await client.write_pin(pin, 0)
            await asyncio.sleep(0.5)

        logger.info("Turning off the LED")
        result = await client.control_led("led1", "off")
        logger.info(f"Control result: {result}")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await client.disconnect()
        logger.info("Example completed")

if __name__ == "__main__":
    asyncio.run(main())
